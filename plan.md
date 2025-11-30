# CallBot Research System – Firebase → MongoDB Migration Plan

## 1) Objectives
- Replace Firebase Firestore with MongoDB (Motor) for: users, calls, signalwire_numbers, payments, provider_config.
- Replace Firebase Auth with JWT-based auth (email/password), preserve roles: admin | user.
- Keep API contract stable under `/api/*`, add `/ws/*` for realtime, bind backend to 0.0.0.0:8001.
- Preserve core voice call flow with SignalWire (initiate → webhook events → realtime updates → history).
- Deliver a working MVP fast, then expand; test end-to-end after each phase.

## 2) Phased Implementation (Core-first)

### Phase 1: Core POC (Required) – SignalWire + Mongo + Webhooks + WS
Scope (minimal, unauthenticated):
- Backend:
  - Add Mongo connection using env MONGO_URL; create collections: calls, provider_config.
  - Define Pydantic models (UUID ids, timezone-aware datetimes).
  - Implement endpoints:
    - POST `/api/calls/start` (input: to_number, from_number, messages, voice) → create call doc, attempt SignalWire call (reads creds from provider_config) → return call_id.
    - POST `/api/webhooks/signalwire/{call_id}/status` → append event to call doc, broadcast via WS.
    - GET `/api/health` → status including Mongo connectivity.
  - WebSocket `/ws/calls/{user_id?}` (for POC, broadcast all or by call_id channel) to push live events.
- Frontend (temporary POC screen, no auth):
  - Simple form: to_number, from_number, Start Call button; Live Events panel (WS) and Last Call status.
- Testing:
  - Use Testing Agent to: 1) call `/api/calls/start` with dummy numbers, 2) simulate webhook posts to status endpoint, 3) assert Mongo writes and WS updates.
- User stories (POC):
  1. As an operator, I can enter a destination number and start a call.
  2. As an operator, I can see real-time call events displayed instantly.
  3. As an operator, I can refresh and still see the latest call status from Mongo.
  4. As an operator, I see clear error toasts if call initiation fails.
  5. As an operator, I can copy the generated call_id to debug or replay webhooks.

### Phase 2: V1 App Development (JWT + Mongo services + Core UI)
- Backend:
  - Introduce JWT auth: `/api/auth/register` (admin only), `/api/auth/login`, `/api/users/profile`.
  - Collections: users (email, password_hash, role, balance, device_id, telegram_id, created_at), calls, signalwire_numbers, payments, provider_config.
  - Services layer for Mongo CRUD; remove all firebase_admin usage.
  - Replace old routes (auth, users, calls, admin, payments, webhooks) to use Mongo; maintain URL shape.
- Frontend:
  - Replace Firebase client with JWT flow (AuthContext, token storage, protected routes).
  - Pages: Login, Dashboard, CallManagement (form with exact TTS texts), CallHistory (paginated), Live logs.
  - Use existing Shadcn components; fetch design via design_agent and apply tokens.
- Testing:
  - Run Testing Agent (both): auth flow, start call, webhook simulation, history listing, WS streaming.
- User stories (V1):
  1. As an admin, I can log in and land on the dashboard.
  2. As an admin, I can create a user with role user and initial balance.
  3. As a user, I can log in and start a call with custom messages.
  4. As a user, I can view my call history filtered by my account.
  5. As a user, I receive real-time updates during an active call.

### Phase 3: Feature Expansion (Admin + Numbers + Telegram + Payments)
- Backend & Frontend:
  - Admin: users CRUD, balance update; numbers listing/assignment; provider_config CRUD (SignalWire, Telegram) stored in Mongo.
  - Telegram integration: save bot token/channel; forward OTP event; toggle on/off.
  - Payments (mock): record payments, admin verification, balance update.
  - External webhooks compatibility endpoints.
- Testing:
  - End-to-end scenarios for admin/user flows; WS reconnection; config updates.
- User stories (Expansion):
  1. As an admin, I can assign a SignalWire number to a user.
  2. As an admin, I can update balances and see them reflected instantly.
  3. As a user, I can link my Telegram and receive OTP notifications.
  4. As a user, I can see recording URLs and event timelines per call.
  5. As an admin, I can update provider credentials safely from the UI.

### Phase 4: Hardening & Optional Data Migration
- Add indexes (unique: users.email, numbers.phone_number; compound: calls.user_id+created_at desc).
- Add server-side validation, idempotent webhook handling, rate limiting, structured logging.
- Optional Firebase→Mongo migrator script (reads Firestore via service account; writes to Mongo with field mapping).
- Final E2E with Testing Agent; performance sanity checks.
- User stories (Hardening):
  1. As an admin, I can run a migration and get a summary report (inserted/skipped/failed).
  2. As an operator, reconnection to WS resumes live updates without page reload.
  3. As an admin, I can search/filter calls by number/date.
  4. As a user, I can download my call history as CSV.
  5. As a developer, I see zero critical errors in supervisor logs over a full test run.

## 3) Implementation Steps (High-level)
1. Copy repo code into current /app, keep `/api` routes and port 8001; do not alter .env values.
2. Create Mongo adapter (Motor) and Pydantic models (UUID ids, datetime with timezone.utc).
3. Phase 1 POC: implement minimal `/api/calls/start`, status webhook, WS broadcast; temporary POC UI; run Testing Agent; fix until green.
4. Replace Firebase services with Mongo services across routes; introduce JWT auth; update frontend to JWT.
5. Implement numbers/admin/payments/telegram on Mongo; add provider_config CRUD.
6. Add indexes and security hardening; optional Firestore→Mongo import script.

## 4) Next Actions (Immediate)
- Create provider_config collection with SignalWire creds from the previous project (stored via admin endpoint or seed script).
- Seed an admin user in Mongo (email: admin@callbot.com, password: admin123, role: admin, balance: 1000) using bcrypt.
- Ship Phase 1 POC endpoints + tiny POC UI and verify via Testing Agent.

## 5) Success Criteria
- Phase 1: `/api/calls/start` returns 200, call doc stored, webhook events append, WS pushes updates; tests pass.
- Phase 2: JWT login works, protected routes enforced, start-call + live updates + history work for user scope.
- Phase 3: Admin CRUD, numbers, telegram, payments all functional with persisted config in Mongo.
- Phase 4: No firebase_admin in codebase; indexes created; supervisor logs clean; full E2E tests green.

