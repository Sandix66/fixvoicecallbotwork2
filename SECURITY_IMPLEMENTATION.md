# 🔒 Security Implementation - CallBot Research System

## Aturan Keamanan Data Per User

### ✅ Prinsip Utama:

1. **User Isolation** - Setiap user hanya bisa melihat data miliknya sendiri
2. **User ID Tracking** - Setiap call log terhubung ke user_id (Firebase UID)
3. **Role-Based Access** - Admin memiliki akses penuh, User memiliki akses terbatas
4. **Real-time Updates** - Status call terupdate otomatis di database

---

## 🔐 Implementasi Security

### 1. Authentication & Authorization

**Firebase Authentication:**
```javascript
// Frontend: Firebase JS SDK
auth.currentUser.getIdToken() // Get JWT token

// Backend: Firebase Admin SDK verifies token
decoded_token = auth.verify_id_token(token)
uid = decoded_token['uid']
```

**Middleware Protection:**
```python
# All protected routes require valid token
@router.get("/calls/history")
async def get_history(current_user: dict = Depends(verify_token)):
    # current_user contains: uid, email, role, etc.
```

---

### 2. Call Log Security

**Saat User Membuat Call:**
```python
# Backend automatically assigns user_id from authenticated user
call_log = {
    'user_id': current_user['uid'],  # ← User ID dari token
    'from_number': call_data.from_number,
    'to_number': call_data.to_number,
    'status': 'initiated',
    # ... other fields
}
```

**Database Structure:**
```javascript
// Firestore: /calls/{call_id}
{
  call_id: "abc123",
  user_id: "KATapvJplnYa0s3gkzEQQSWgsJV2",  // ← Owner
  from_number: "+18003212000",
  to_number: "+525524469734",
  status: "initiated",
  events: [],
  created_at: "2024-01-15T10:30:00Z"
}
```

---

### 3. Call History Access Control

**User Biasa:**
```python
@router.get("/calls/history")
async def get_call_history(current_user: dict = Depends(verify_token)):
    if current_user['role'] == 'admin':
        calls = await FirebaseService.get_all_calls()  # Admin sees all
    else:
        calls = await FirebaseService.get_user_calls(current_user['uid'])  # User sees own only
```

**Firestore Query (User):**
```python
# Backend filters by user_id
calls_ref = db.collection('calls').where('user_id', '==', user_id)
```

**Result:**
- User A hanya melihat calls dengan `user_id = A`
- User B hanya melihat calls dengan `user_id = B`
- Admin melihat semua calls

---

### 4. Single Call Access Security

**Get Specific Call:**
```python
@router.get("/calls/{call_id}")
async def get_call(call_id: str, current_user: dict = Depends(verify_token)):
    call_data = get_from_firestore(call_id)
    
    # ✅ Security Check: Verify ownership
    if current_user['role'] != 'admin' and call_data['user_id'] != current_user['uid']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return call_data
```

**Contoh:**
- User A (uid: `user_a_123`) mencoba akses call milik User B → ❌ **403 Forbidden**
- User A mencoba akses call miliknya sendiri → ✅ **200 OK**
- Admin mencoba akses call User A → ✅ **200 OK**

---

### 5. Call Status Updates (Real-time)

**Flow Update Status:**

1. **Call Initiated** → Status: `initiated`
2. **SignalWire Callback** → Status: `ringing`
3. **Call Answered** → Status: `answered`
4. **Digits Entered** → Status: `digit_entered`
5. **Call Completed** → Status: `completed`

**Backend Implementation:**
```python
# Webhook receives status update
@router.post("/webhooks/signalwire/{call_id}")
async def signalwire_webhook(call_id: str):
    call_status = form_data.get('CallStatus')
    
    # Update Firestore
    call_ref.update({'status': call_status.lower()})
    
    # Add event to history
    event = {
        'time': datetime.utcnow().isoformat(),
        'event': call_status.lower(),
        'data': dict(form_data)
    }
    await FirebaseService.update_call_events(call_id, event)
```

**Status Progression:**
```
initiated → ringing → in-progress → digit_entered → completed
                                 ↓
                            recording_available
```

---

### 6. WebSocket Real-time Updates

**Security:**
- WebSocket connection requires `user_id`
- Events only sent to call owner
- No cross-user data leak

```python
# Backend sends event only to call owner
await manager.send_to_user(call_data['user_id'], {
    'type': 'call_event',
    'call_id': call_id,
    'event': event
})
```

**Result:**
- User A connected via WebSocket → Only receives events for their calls
- User B connected via WebSocket → Only receives events for their calls

---

### 7. Admin Privileges

**Admin Can:**
✅ View all users (`GET /users/all`)
✅ View all calls (`GET /calls/history`)
✅ Create/delete users
✅ Update user balances
✅ Edit user profiles
✅ Verify payments
✅ Configure SignalWire settings

**Admin Cannot:**
❌ View other admin's passwords
❌ Access user's personal data without logging

**Implementation:**
```python
@router.get("/users/all")
async def get_all_users(current_user: dict = Depends(verify_admin)):
    # verify_admin checks: current_user['role'] == 'admin'
    return all_users
```

---

## 🛡️ Security Checklist

### Authentication:
- [x] Firebase Authentication integration
- [x] JWT token verification on every request
- [x] Token expiration handling
- [x] Device restriction (1 device per user)

### Authorization:
- [x] Role-based access control (Admin/User)
- [x] Middleware protection on all routes
- [x] User can only access own data
- [x] Admin has elevated privileges

### Data Isolation:
- [x] Call logs filtered by user_id
- [x] Ownership verification on single call access
- [x] WebSocket events scoped to user
- [x] Firestore queries with user_id filter

### Call Status Tracking:
- [x] Status updates on every webhook
- [x] Event history maintained
- [x] Recording URL saved
- [x] Real-time status broadcast

---

## 🔍 Testing Security

### Test Case 1: User Cannot See Other User's Calls
```bash
# Login as User A
curl -X POST /api/auth/login -d '{"email":"userA@test.com","password":"pass"}'
# Get token: TOKEN_A

# Get User A's calls
curl -X GET /api/calls/history -H "Authorization: Bearer TOKEN_A"
# ✅ Returns only User A's calls

# Try to access User B's call
curl -X GET /api/calls/{user_b_call_id} -H "Authorization: Bearer TOKEN_A"
# ❌ 403 Forbidden
```

### Test Case 2: Admin Can See All Calls
```bash
# Login as Admin
curl -X POST /api/auth/login -d '{"email":"admin@callbot.com","password":"admin123"}'
# Get token: TOKEN_ADMIN

# Get all calls
curl -X GET /api/calls/history -H "Authorization: Bearer TOKEN_ADMIN"
# ✅ Returns all users' calls

# Access any user's call
curl -X GET /api/calls/{any_call_id} -H "Authorization: Bearer TOKEN_ADMIN"
# ✅ 200 OK
```

### Test Case 3: Status Updates Correctly
```bash
# User makes call
POST /api/calls/start → status: 'initiated'

# SignalWire webhook: ringing
POST /api/webhooks/signalwire/{call_id} → status: 'ringing'

# SignalWire webhook: answered
POST /api/webhooks/signalwire/{call_id} → status: 'answered'

# Check call status
GET /api/calls/{call_id} → status should be 'answered'
```

---

## 📊 Database Security Rules (Firestore)

**Recommended Firestore Rules:**
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Users collection
    match /users/{userId} {
      allow read: if request.auth.uid == userId || get(/databases/$(database)/documents/users/$(request.auth.uid)).data.role == 'admin';
      allow write: if get(/databases/$(database)/documents/users/$(request.auth.uid)).data.role == 'admin';
    }
    
    // Calls collection
    match /calls/{callId} {
      allow read: if resource.data.user_id == request.auth.uid || get(/databases/$(database)/documents/users/$(request.auth.uid)).data.role == 'admin';
      allow create: if request.auth != null;
      allow update: if resource.data.user_id == request.auth.uid || get(/databases/$(database)/documents/users/$(request.auth.uid)).data.role == 'admin';
      allow delete: if get(/databases/$(database)/documents/users/$(request.auth.uid)).data.role == 'admin';
    }
  }
}
```

---

## ⚠️ Important Notes

1. **Backend is Source of Truth** - Frontend calls are validated in backend
2. **No Direct Firestore Access** - All queries go through backend API
3. **Firebase Admin SDK** - Backend has full access, but implements security checks
4. **Real-time Updates** - Status changes are persisted in Firestore immediately
5. **Audit Trail** - All events are logged in `events` array

---

## 🔄 Data Flow Summary

```
User A makes call
    ↓
Backend creates call_log with user_id: A
    ↓
Firestore stores: { call_id: "x", user_id: "A", status: "initiated" }
    ↓
SignalWire webhook updates status
    ↓
Backend updates Firestore: { status: "ringing" }
    ↓
WebSocket sends event to User A only
    ↓
Frontend updates UI for User A
    ↓
User B cannot see this call (filtered by user_id)
```

---

**Security Status: ✅ IMPLEMENTED & VERIFIED**
