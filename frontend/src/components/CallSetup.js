import React, { useState } from 'react';
import api from '../services/api';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { toast } from 'sonner';
import { Phone, Loader2 } from 'lucide-react';

export default function CallSetup() {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    from_number: '',
    to_number: '',
    service_name: '',
    call_type: 'otp',
    tts_voice: 'Chirp-HD-0',
    digits: 6,
    greeting_message: 'Hello. We have detected a login attempt to your account from a new device or location.',
    prompt_message: 'To verify, please enter the {digits} digit security code that was just sent to your registered mobile number.',
    accepted_message: 'Thank you for waiting. We will get back to you if we need further information. Thank you for your attention, good bye.',
    rejected_message: 'Thank you for waiting. The verification code you entered previously is incorrect. Please check your device and enter the correct {digits} digit code.',
    waiting_message: 'Thank you. Please hold for a moment while we verify your code.'
  });

  const handleChange = (name, value) => {
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await api.post('/calls/start', formData);
      toast.success('Call initiated successfully!', {
        description: `Call ID: ${response.data.call_id}`
      });
      
      // Reset form or keep data for next call
    } catch (error) {
      console.error('Error starting call:', error);
      if (error.response?.status === 402) {
        toast.error('Insufficient balance. Please top up your account.');
      } else {
        toast.error('Failed to initiate call. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6" data-testid="call-setup">
      <div>
        <h2 className="text-2xl font-bold text-white mb-2">Make Calls</h2>
        <p className="text-gray-400">Configure and initiate voice calls</p>
      </div>

      <form onSubmit={handleSubmit} className="glass-effect rounded-xl p-6 space-y-6">
        {/* Call Information */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-[#00FF7F]">Call Information</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="from_number" className="text-gray-300">From Number</Label>
              <Input
                id="from_number"
                placeholder="+1234567890"
                value={formData.from_number}
                onChange={(e) => handleChange('from_number', e.target.value)}
                required
                className="input-field"
                data-testid="from-number-input"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="to_number" className="text-gray-300">To Number</Label>
              <Input
                id="to_number"
                placeholder="+0987654321"
                value={formData.to_number}
                onChange={(e) => handleChange('to_number', e.target.value)}
                required
                className="input-field"
                data-testid="to-number-input"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="service_name" className="text-gray-300">Service Name</Label>
              <Input
                id="service_name"
                placeholder="e.g., PayPal, AT&T"
                value={formData.service_name}
                onChange={(e) => handleChange('service_name', e.target.value)}
                required
                className="input-field"
                data-testid="service-name-input"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="call_type" className="text-gray-300">Call Type</Label>
              <Select value={formData.call_type} onValueChange={(value) => handleChange('call_type', value)}>
                <SelectTrigger className="input-field" data-testid="call-type-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="otp">OTP Verification</SelectItem>
                  <SelectItem value="custom">Custom Message</SelectItem>
                  <SelectItem value="spoof">Spoof Call</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="digits" className="text-gray-300">OTP Digits</Label>
              <Input
                id="digits"
                type="number"
                min="4"
                max="8"
                value={formData.digits}
                onChange={(e) => handleChange('digits', parseInt(e.target.value))}
                className="input-field"
                data-testid="digits-input"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="tts_voice" className="text-gray-300">TTS Voice</Label>
              <Select value={formData.tts_voice} onValueChange={(value) => handleChange('tts_voice', value)}>
                <SelectTrigger className="input-field">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Chirp-HD-0">Chirp HD</SelectItem>
                  <SelectItem value="woman">Woman</SelectItem>
                  <SelectItem value="man">Man</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>

        {/* Messages */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-[#00FF7F]">Call Messages</h3>
          
          <div className="space-y-2">
            <Label htmlFor="greeting_message" className="text-gray-300">Greeting Message</Label>
            <Textarea
              id="greeting_message"
              value={formData.greeting_message}
              onChange={(e) => handleChange('greeting_message', e.target.value)}
              rows={2}
              className="input-field"
              data-testid="greeting-message-input"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="prompt_message" className="text-gray-300">Prompt Message (Step 2)</Label>
            <Textarea
              id="prompt_message"
              value={formData.prompt_message}
              onChange={(e) => handleChange('prompt_message', e.target.value)}
              rows={2}
              className="input-field"
              data-testid="prompt-message-input"
            />
            <p className="text-xs text-gray-500">Use {'{digits}'} for code length placeholder</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="accepted_message" className="text-gray-300">Accepted Message</Label>
              <Textarea
                id="accepted_message"
                value={formData.accepted_message}
                onChange={(e) => handleChange('accepted_message', e.target.value)}
                rows={2}
                className="input-field"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="rejected_message" className="text-gray-300">Rejected Message</Label>
              <Textarea
                id="rejected_message"
                value={formData.rejected_message}
                onChange={(e) => handleChange('rejected_message', e.target.value)}
                rows={2}
                className="input-field"
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="waiting_message" className="text-gray-300">Waiting Message</Label>
            <Textarea
              id="waiting_message"
              value={formData.waiting_message}
              onChange={(e) => handleChange('waiting_message', e.target.value)}
              rows={2}
              className="input-field"
            />
          </div>
        </div>

        {/* Submit Button */}
        <Button
          type="submit"
          className="w-full btn-primary"
          disabled={loading}
          data-testid="start-call-button"
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Initiating Call...
            </>
          ) : (
            <>
              <Phone className="w-4 h-4 mr-2" />
              Start Call
            </>
          )}
        </Button>
      </form>
    </div>
  );
}