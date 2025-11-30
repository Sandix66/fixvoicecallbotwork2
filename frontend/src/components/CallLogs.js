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
    <div className="space-y-6" data-testid="call-logs">
      <div>
        <h2 className="text-2xl font-bold text-white mb-2">Call Logs</h2>
        <p className="text-gray-400">Real-time call event monitoring</p>
      </div>

      {/* Unified Call Information Panel */}
      <div className="glass-effect rounded-xl p-6 space-y-6">
        {/* LIVE EVENTS Section */}
        <div className="space-y-3">
          <h3 className="text-lg font-semibold text-[#00FF7F] mb-4">LIVE EVENTS</h3>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-gray-400 text-sm mb-1">Status:</p>
              <p className="text-white font-semibold">{currentCall?.status || 'initiated'}</p>
            </div>
            <div>
              <p className="text-gray-400 text-sm mb-1">Answered By:</p>
              <p className="text-white font-semibold">{getAnsweredBy()}</p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-gray-400 text-sm mb-1">Code:</p>
              <p className="text-white font-semibold">{getCode()}</p>
            </div>
            <div>
              <p className="text-gray-400 text-sm mb-1">Recording URL:</p>
              <div className="text-white font-semibold break-all">{getRecordingUrl()}</div>
            </div>
          </div>

          <div>
            <p className="text-gray-400 text-sm mb-1">Responses:</p>
            <p className="text-white font-semibold">{getResponses()}</p>
          </div>
        </div>

        {/* Call Information Section */}
        <div className="border-t border-gray-700 pt-6">
          <h3 className="text-lg font-semibold text-[#00FF7F] mb-4">Call Information:</h3>
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-gray-400 text-sm mb-1">Caller Id:</p>
                <p className="text-white">{currentCall?.from_number || '-'}</p>
              </div>
              <div>
                <p className="text-gray-400 text-sm mb-1">Recipient Name:</p>
                <p className="text-white">{currentCall?.recipient_name || '-'}</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-gray-400 text-sm mb-1">Recipient Number:</p>
                <p className="text-white">{currentCall?.to_number || '-'}</p>
              </div>
              <div>
                <p className="text-gray-400 text-sm mb-1">Service Name:</p>
                <p className="text-white">{currentCall?.service_name || '-'}</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-gray-400 text-sm mb-1">Required Digit:</p>
                <p className="text-white">{currentCall?.digits || 6}</p>
              </div>
              <div>
                <p className="text-gray-400 text-sm mb-1">Language:</p>
                <p className="text-white">{currentCall?.language || 'en-US'}</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-gray-400 text-sm mb-1">Voice:</p>
                <p className="text-white">{currentCall?.tts_voice || 'Aurora'}</p>
              </div>
              <div></div>
            </div>
          </div>
        </div>

        {/* Hangup Button */}
        <div className="border-t border-gray-700 pt-6">
          <Button
            onClick={handleHangup}
            disabled={loading || !currentCall}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-lg transition-colors flex items-center justify-center"
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
        </div>

        {/* Loading Message */}
        {!currentCall && (
          <div className="text-center py-8">
            <p className="text-gray-400">Fetching data. Please do not refresh browser.</p>
          </div>
        )}
      </div>
    </div>
  );
}