# 📋 CallBot Research System - Project Handoff

## 🎯 Status Proyek: SELESAI & BERJALAN

**Last Updated:** 2024-11-25
**Version:** 1.0.0
**Status:** ✅ Production Ready

---

## 📊 Project Overview

**Nama Project:** CallBot Research System
**Deskripsi:** Sistem voice call automation dengan SignalWire API, Firebase database, dan real-time monitoring.

**Tech Stack:**
- Backend: FastAPI (Python)
- Frontend: React 19 + Tailwind CSS
- Database: Firebase Firestore
- Authentication: Firebase Authentication
- VoIP: SignalWire API
- Real-time: WebSocket
- Messaging: Telegram Bot

---

## 🔑 Credentials & Access

### 1. Admin Login
```
URL: https://callbot-research.preview.emergentagent.com
Email: admin@callbot.com
Password: admin123
Role: Admin
Balance: $1000
```

### 2. Firebase Project
```
Project ID: clankk-e61f8
API Key: AIzaSyBTMOOZHr-ywMJuEtZriUb_rvK9gSCMRyU
Auth Domain: clankk-e61f8.firebaseapp.com
Database URL: https://clankk-e61f8-default-rtdb.firebaseio.com
```

**Service Account:** `/app/backend/config/firebase_config.json`

### 3. SignalWire Credentials
```
Project ID: bf825aef-aa0a-402f-a908-2d1c54733518
Space URL: marauang-rauang.signalwire.com
Token: PTf3a107d98daf47a94fee499d736507ec38b7281a3a375b66
```

**Available Numbers (8):**
- +12106749012
- +14232594719
- +18882676520
- +18142934760
- +18336596004
- +17023567895
- +15012229881
- +12019792184

### 4. Telegram Bot
```
Bot Token: 8179370597:AAHPl3T3lixwxukN0Y0_wcrgVXZRjB19wOQ
Channel ID: -1003442553402
```

### 5. External Webhooks (Optional)
```
Base URL: https://piddly-tenable-frederic.ngrok-free.dev
- signalwire-webhook.php
- signalwire-status.php
- signalwire-first-input.php
- signalwire-deny.php
- signalwire-accept.php
- signalwire-amd.php
```

---

## 📁 Project Structure

```
/app/
├── backend/                    # FastAPI Backend
│   ├── server.py              # Main application
│   ├── .env                   # Environment variables
│   ├── requirements.txt       # Python dependencies
│   ├── config/
│   │   ├── firebase_init.py   # Firebase setup
│   │   └── firebase_config.json  # Service account
│   ├── models/
│   │   └── schemas.py         # Pydantic models
│   ├── routes/
│   │   ├── auth.py            # Authentication routes
│   │   ├── users.py           # User management
│   │   ├── calls.py           # Call management
│   │   ├── webhooks.py        # SignalWire webhooks
│   │   ├── admin.py           # Admin functions
│   │   └── payments.py        # Payment mock
│   ├── services/
│   │   ├── firebase_service.py    # Firebase operations
│   │   ├── signalwire_service.py  # SignalWire API
│   │   ├── telegram_service.py    # Telegram bot
│   │   └── websocket_manager.py   # WebSocket
│   └── utils/
│       └── auth_middleware.py # JWT verification
│
├── frontend/                   # React Frontend
│   ├── src/
│   │   ├── App.js             # Main component
│   │   ├── pages/
│   │   │   ├── Login.js       # Login page
│   │   │   └── Dashboard.js   # Main dashboard
│   │   ├── components/
│   │   │   ├── CallManagement.js  # Make call + logs
│   │   │   ├── UserManagement.js  # User CRUD (admin)
│   │   │   ├── Settings.js        # User settings
│   │   │   ├── Sidebar.js         # Navigation
│   │   │   └── StatusBar.js       # Top bar
│   │   ├── contexts/
│   │   │   └── AuthContext.js # Authentication context
│   │   ├── services/
│   │   │   ├── api.js         # API client
│   │   │   └── websocket.js   # WebSocket client
│   │   └── config/
│   │       └── firebase.js    # Firebase config
│   ├── package.json
│   └── .env
│
└── Documentation/
    ├── README_SETUP.md                 # Full setup guide
    ├── FIREBASE_SETUP.md               # Firebase setup steps
    ├── SECURITY_IMPLEMENTATION.md      # Security details
    ├── TROUBLESHOOTING_CALLS.md        # Debug guide
    ├── EXTERNAL_WEBHOOK_INTEGRATION.md # External webhooks
    ├── PHP_WEBHOOK_INTEGRATION.md      # PHP examples
    └── PROJECT_HANDOFF.md              # This file
```

---

## 🎯 Features Implemented

### ✅ Authentication & Authorization
- Firebase Authentication (email/password)
- Role-based access control (Admin/User)
- JWT token verification
- Device restriction (1 device per user)

### ✅ User Management
- Admin can create/delete users
- Update user balance
- Change password
- Link Telegram account

### ✅ Call Management
- Make voice calls via SignalWire
- 8 phone numbers available
- Caller ID selection (dropdown)
- Recipient info (name, number, service)
- Customizable messages (5 steps)
- Real-time call logs
- Call history with events
- Recording URL storage

### ✅ Voice/TTS Features
- **EXACT text from UI form** digunakan untuk voice
- Step 1 Message: Initial greeting
- Step 2 Message: Ask for OTP
- Step 3 Message: Waiting/verification
- Accepted Message: When user confirms
- Rejected Message: When code incorrect
- Variable replacement: {{name}}, {{service}}, {{digit}}
- Voice selection: Aurora, Chirp HD, Woman, Man
- Language: English USA, English UK, Spanish

### ✅ Call Flow
1. User fills form with messages
2. Backend saves to Firestore
3. SignalWire calls internal webhook
4. Webhook reads EXACT text from database
5. Voice plays messages from UI form
6. User interacts (press 1/0, enter OTP)
7. Status updates in real-time
8. OTP forwarded to Telegram (optional)

### ✅ Real-time Features
- WebSocket for live call events
- Real-time status updates
- Live event logs display
- Instant balance updates

### ✅ Security
- Per-user data isolation
- Call logs filtered by user_id
- Ownership verification
- Admin access control
- Firestore security rules ready

### ✅ Payment System (Mock)
- USDT TRC20 payment
- Bank transfer
- Admin verification
- Auto balance update

---

## 🗄️ Database Collections

### Firestore Collections:

**1. users**
```javascript
{
  uid: string,              // Firebase Auth UID
  email: string,
  username: string,
  role: "admin" | "user",
  balance: number,
  device_id: string | null,
  telegram_id: string | null,
  created_at: string
}
```

**Current Users:**
- admin@callbot.com (Admin, $1000)
- ratnagale06@clankk.com (User, $150)
- esr@test.com (User, $12)

**2. calls**
```javascript
{
  call_id: string,
  user_id: string,          // Owner
  from_number: string,
  to_number: string,
  recipient_name: string,
  service_name: string,
  call_type: string,
  status: string,
  tts_voice: string,
  step_1_message: string,   // EXACT text from UI
  step_2_message: string,
  step_3_message: string,
  accepted_message: string,
  rejected_message: string,
  digits: number,
  events: array,
  recording_url: string,
  created_at: string
}
```

**3. signalwire_numbers**
```javascript
{
  phone_number: string,
  assigned_to_user_id: string | null,
  is_active: boolean,
  created_at: string
}
```

**4. payments**
```javascript
{
  payment_id: string,
  user_id: string,
  amount: number,
  method: string,
  status: string,
  created_at: string
}
```

---

## 🔌 API Endpoints

### Public:
- `POST /api/auth/login` - Login
- `GET /api/webhooks/external/call/{call_id}` - Get call data for webhooks

### Authenticated:
- `GET /api/users/profile` - Get profile
- `POST /api/users/change-password` - Change password
- `GET /api/calls/history` - Get call history
- `POST /api/calls/start` - Start call
- `GET /api/admin/signalwire/numbers/available` - Get phone numbers

### Admin Only:
- `POST /api/auth/register` - Create user
- `GET /api/users/all` - Get all users
- `PUT /api/users/{uid}/balance` - Update balance
- `DELETE /api/users/{uid}` - Delete user
- `PUT /api/users/{uid}` - Edit user

### Webhooks:
- `POST /api/webhooks/signalwire/{call_id}` - Main webhook (TwiML)
- `POST /api/webhooks/signalwire/{call_id}/first-input` - Handle 1/0
- `POST /api/webhooks/signalwire/{call_id}/deny` - Gather OTP
- `POST /api/webhooks/signalwire/{call_id}/accept` - Accepted flow
- `POST /api/webhooks/signalwire/{call_id}/status` - Status updates
- `POST /api/webhooks/external/update/{call_id}` - External webhook updates

### WebSocket:
- `WS /ws/calls/{user_id}` - Real-time call events

---

## 🚀 How to Continue in New Chat

### Step 1: Tell AI About Project Context

Copy paste ini ke chat baru:
```
Saya melanjutkan project CallBot Research System.

Project Info:
- Tech Stack: FastAPI + React + Firebase Firestore
- Location: /app/ directory
- Status: Production ready & running

Credentials:
- Admin Login: admin@callbot.com / admin123
- URL: https://callbot-research.preview.emergentagent.com
- Firebase Project: clankk-e61f8

Current Status:
- Backend & Frontend running
- Database populated (3 users, 8 numbers, call history)
- All features implemented and working

Documentation Available:
- /app/PROJECT_HANDOFF.md (this file)
- /app/README_SETUP.md
- /app/SECURITY_IMPLEMENTATION.md
- /app/TROUBLESHOOTING_CALLS.md
- /app/PHP_WEBHOOK_INTEGRATION.md

Saya ingin [sebutkan apa yang mau dikerjakan]:
- Add new feature
- Fix bug
- Modify UI
- etc.
```

### Step 2: Common Commands

**Check Status:**
```bash
sudo supervisorctl status
```

**View Backend Logs:**
```bash
tail -f /var/log/supervisor/backend.err.log
```

**View Frontend Logs:**
```bash
tail -f /var/log/supervisor/frontend.err.log
```

**Restart Services:**
```bash
sudo supervisorctl restart backend
sudo supervisorctl restart frontend
```

**Test SignalWire:**
```bash
cd /app/backend
python test_signalwire.py
```

**Check Database:**
```bash
cd /app/backend
python check_calls.py
```

**Test Call:**
```bash
cd /app/backend
python test_make_call.py
```

---

## 🔧 Common Tasks

### Add New Feature

1. Tell AI: "I want to add [feature name]"
2. AI will explore relevant files
3. Implement changes
4. Restart services
5. Test via frontend

### Fix Bug

1. Describe issue: "There's a bug: [description]"
2. Check logs: `tail -f /var/log/supervisor/backend.err.log`
3. AI will debug and fix
4. Test to verify

### Modify UI

1. Tell AI: "Change UI: [description]"
2. Files usually in: `/app/frontend/src/components/`
3. Frontend auto-reloads (hot reload)
4. Check browser to see changes

### Update Messages

1. Messages stored in database (Firestore)
2. Edit via UI form (CallManagement component)
3. Changes apply to next call automatically
4. No code changes needed

---

## 📚 Important Files Reference

### Backend Core:
- `/app/backend/server.py` - Main app
- `/app/backend/.env` - Credentials
- `/app/backend/routes/calls.py` - Call logic
- `/app/backend/routes/webhooks.py` - TwiML generation
- `/app/backend/services/signalwire_service.py` - SignalWire API

### Frontend Core:
- `/app/frontend/src/App.js` - Main component
- `/app/frontend/src/pages/Dashboard.js` - Dashboard
- `/app/frontend/src/components/CallManagement.js` - Call UI
- `/app/frontend/src/components/UserManagement.js` - User CRUD
- `/app/frontend/src/contexts/AuthContext.js` - Auth state

### Configuration:
- `/app/backend/config/firebase_config.json` - Service account
- `/app/frontend/src/config/firebase.js` - Firebase client config

---

## ⚠️ Important Notes

### Data Persistence:
- ✅ All data in Firebase (permanent)
- ✅ Users, calls, numbers stored forever
- ✅ Config files persistent
- ✅ No data loss on restart

### System URLs:
- Frontend: https://callbot-research.preview.emergentagent.com
- Backend API: https://callbot-research.preview.emergentagent.com/api
- WebSocket: wss://callbot-research.preview.emergentagent.com/ws

### Services:
- Backend runs on port 8001
- Frontend runs on port 3000
- Managed by supervisor (auto-restart)

### Voice/TTS:
- System uses **INTERNAL webhooks** by default
- Reads **EXACT text** from UI form messages
- Variables {{name}}, {{service}}, {{digit}} auto-replaced
- No PHP needed (but PHP integration docs available)

---

## 🎯 Quick Start Checklist

When starting new chat:

1. ✅ Tell AI you're continuing this project
2. ✅ Mention PROJECT_HANDOFF.md
3. ✅ Check services status: `sudo supervisorctl status`
4. ✅ Test login: https://callbot-research.preview.emergentagent.com
5. ✅ Verify admin credentials: admin@callbot.com / admin123
6. ✅ Describe what you want to do

---

## 🆘 Emergency Commands

**If backend not working:**
```bash
sudo supervisorctl restart backend
tail -n 50 /var/log/supervisor/backend.err.log
```

**If frontend not loading:**
```bash
sudo supervisorctl restart frontend
tail -n 50 /var/log/supervisor/frontend.err.log
```

**If calls not working:**
```bash
cd /app/backend
python test_signalwire.py
```

**Check what's in database:**
```bash
cd /app/backend
python check_calls.py
```

---

## 📞 Support & Documentation

**All Documentation:**
- General: `/app/README_SETUP.md`
- Security: `/app/SECURITY_IMPLEMENTATION.md`
- Troubleshooting: `/app/TROUBLESHOOTING_CALLS.md`
- Webhooks: `/app/PHP_WEBHOOK_INTEGRATION.md`
- External: `/app/EXTERNAL_WEBHOOK_INTEGRATION.md`
- Firebase: `/app/FIREBASE_SETUP.md`
- This file: `/app/PROJECT_HANDOFF.md`

**Quick Links:**
- Dashboard: https://callbot-research.preview.emergentagent.com
- Admin Login: admin@callbot.com
- Firebase Console: https://console.firebase.google.com/project/clankk-e61f8

---

**Project Status:** ✅ COMPLETE & RUNNING
**Last Session:** 2024-11-25
**Ready for:** Continuation, feature additions, bug fixes, enhancements

---

*End of Handoff Document*
