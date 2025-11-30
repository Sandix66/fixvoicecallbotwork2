from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Literal
from datetime import datetime

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str
    role: Literal["admin", "user"] = "user"

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    username: str
    role: Literal["admin", "user"] = "user"

class UserResponse(BaseModel):
    uid: str
    email: str
    username: str
    role: str
    balance: float
    device_id: Optional[str] = None
    telegram_id: Optional[str] = None
    created_at: Optional[str] = None

class UpdateBalance(BaseModel):
    amount: float

class ChangePassword(BaseModel):
    old_password: str
    new_password: str

class LinkTelegram(BaseModel):
    telegram_id: str

# Call Schemas
class CallEvent(BaseModel):
    time: str
    event: str
    data: Optional[dict] = None

class CallCreate(BaseModel):
    from_number: str
    to_number: str
    recipient_name: str
    service_name: str
    call_type: Literal["otp", "custom", "spoof"]
    provider: Literal["signalwire", "infobip"] = "signalwire"
    template: Optional[str] = "login-3"
    language: str = "en-US"
    tts_voice: str = "Aurora"
    step_1_message: str
    step_2_message: str
    step_3_message: str
    accepted_message: str
    rejected_message: str
    digits: int = 6

class SpoofCallCreate(BaseModel):
    from_number: str
    to_number: str
    spoofed_caller_id: str
    from_display_name: str
    recipient_name: str
    service_name: str
    provider: Literal["infobip_sip"] = "infobip_sip"
    language: str = "en-US"
    tts_voice: str = "Aurora"
    step_1_message: str
    step_2_message: str
    step_3_message: str
    accepted_message: str
    rejected_message: str
    digits: int = 6

class CallResponse(BaseModel):
    call_id: str
    user_id: str
    from_number: str
    to_number: str
    recipient_name: Optional[str] = None
    service_name: str
    call_type: str
    status: str
    events: List[CallEvent]
    recording_url: Optional[str] = None
    created_at: str

class CallControl(BaseModel):
    action: Literal["accept", "reject", "end"]
    message: Optional[str] = None

# SignalWire Schemas
class SignalWireNumber(BaseModel):
    phone_number: str
    assigned_to_user_id: Optional[str] = None
    is_active: bool = True

class SignalWireCredentials(BaseModel):
    project_id: str
    token: str
    space_url: str

# Payment Schemas
class PaymentInitiate(BaseModel):
    amount: float
    method: Literal["usdt", "bank_transfer"]

class PaymentResponse(BaseModel):
    payment_id: str
    user_id: str
    amount: float
    method: str
    status: Literal["pending", "completed", "failed"]
    transaction_hash: Optional[str] = None
    qr_code_url: Optional[str] = None
    bank_details: Optional[dict] = None
    created_at: str

# Auth Schemas
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    device_id: Optional[str] = None

class LoginResponse(BaseModel):
    token: str
    user: UserResponse

class TokenVerify(BaseModel):
    token: str