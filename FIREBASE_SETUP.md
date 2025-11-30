# 🔥 Firebase Authentication Setup

## ⚠️ PENTING: Setup Firebase Auth Sebelum Menggunakan Sistem

Sistem CallBot Research memerlukan Firebase Authentication untuk login. Ikuti langkah-langkah berikut:

---

## 📋 Langkah 1: Aktifkan Firebase Authentication

### 1.1 Buka Firebase Console
- Kunjungi: **https://console.firebase.google.com**
- Login dengan akun Google Anda
- Pilih project: **clankk-e61f8**

### 1.2 Navigasi ke Authentication
- Di sidebar kiri, klik **Build**
- Klik **Authentication**
- Klik tombol **Get Started** (jika ini pertama kali)

### 1.3 Enable Email/Password Sign-in
1. Klik tab **Sign-in method**
2. Klik **Email/Password** dari daftar providers
3. Toggle switch **Enable** menjadi ON
4. **Jangan centang** "Email link (passwordless sign-in)" untuk saat ini
5. Klik tombol **Save**

✅ **Firebase Authentication sekarang sudah aktif!**

---

## 📋 Langkah 2: Buat Admin User

Setelah Authentication diaktifkan, buat user admin pertama:

```bash
cd /app/backend
python create_admin.py
```

**Output yang diharapkan:**
```
✅ Firebase Auth user created: AbCdEfGhIjKlMnOpQr
✅ Firestore user document created

🎉 Admin user created successfully!
📧 Email: admin@callbot.com
🔑 Password: admin123
💰 Initial Balance: $1000.0

ℹ️  Use these credentials to login to the system
```

---

## 📋 Langkah 3: Login ke Sistem

1. Buka browser dan akses:
   ```
   https://callbot-research.preview.emergentagent.com
   ```

2. Login dengan credentials:
   - **Email:** `admin@callbot.com`
   - **Password:** `admin123`

3. Setelah login, Anda akan melihat Dashboard dengan:
   - Real-time call logs
   - Call setup form
   - User management (Admin only)
   - Balance display

---

## 🔧 Troubleshooting

### Error: "CONFIGURATION_NOT_FOUND"
**Penyebab:** Firebase Authentication belum diaktifkan

**Solusi:**
1. Pastikan Anda sudah mengikuti Langkah 1 dengan benar
2. Pastikan Email/Password provider sudah **enabled**
3. Tunggu 1-2 menit untuk propagasi perubahan
4. Coba jalankan `create_admin.py` lagi

### Error: "EMAIL_ALREADY_EXISTS"
**Penyebab:** Admin user sudah dibuat sebelumnya

**Solusi:**
- Gunakan credentials yang sama untuk login
- Atau delete user dari Firebase Console dan buat ulang

### Login Failed
**Penyebab:** Backend belum terhubung dengan Firebase

**Solusi:**
```bash
# Check backend logs
tail -n 50 /var/log/supervisor/backend.err.log

# Restart backend
sudo supervisorctl restart backend
```

---

## 📱 Fitur-Fitur yang Tersedia

### 🔐 Authentication
- Login dengan email/password
- Role-based access (Admin/User)
- Device restriction (1 device per user)
- Secure token management

### 👥 User Management (Admin Only)
- Create new users
- Set initial balance
- Assign roles (Admin/User)
- Delete users
- Update user balance

### 📞 Call Management
- Initiate voice calls
- Configure call messages
- Real-time call monitoring
- OTP gathering
- Call recording

### 💰 Balance & Payments
- View current balance
- Top-up via USDT TRC20 (Mock)
- Top-up via Bank Transfer (Mock)
- Admin payment verification

### 📊 Real-time Features
- WebSocket live updates
- Call event logs
- Telegram notifications
- OTP forwarding to Telegram

---

## 🎯 Next Steps

Setelah setup berhasil:

1. **Login sebagai Admin**
2. **Create User pertama** dari User Management
3. **Set balance** untuk user tersebut
4. **Test call** dengan user tersebut
5. **Monitor real-time logs** di dashboard

---

## 📞 Kontak Support

Jika mengalami masalah:
- Check backend logs: `tail -n 100 /var/log/supervisor/backend.err.log`
- Check frontend logs: `tail -n 100 /var/log/supervisor/frontend.err.log`
- Browser console: Press F12 untuk debug frontend

---

**Happy Researching! 🚀**
