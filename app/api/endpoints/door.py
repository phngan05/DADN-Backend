import json
from fastapi import APIRouter, HTTPException, Depends
from app.core.door_auth import get_password_hash, verify_password
from app.core.security import get_current_user_id
from app.schemas.door_auth import PasswordUpdate, DoorAccessRequest
from app.schemas.noti import NotiCreate
from app.api.endpoints.noti import create_notification

PASSWORD_FILE = "app\\core\\door_auth.json"

router = APIRouter()

def save_to_json(hashed_password: str):
    with open(PASSWORD_FILE, "w") as f:
        json.dump({"hashed_password": hashed_password}, f)

def read_from_json():
    with open(PASSWORD_FILE, "r") as f:
        data = json.load(f)
        return data.get("hashed_password")

@router.post("")
async def verify_door_password(data: DoorAccessRequest):
    """Kiểm tra mật khẩu để mở cửa"""
    
    stored_hash = read_from_json()
    
    if not stored_hash:
        raise HTTPException(
            status_code=404, 
            detail="Hệ thống chưa thiết lập mật khẩu cửa."
        )

    is_match = verify_password(data.password, stored_hash)

    if not is_match:
        return False

    return True

@router.put("")
async def update_password(data: PasswordUpdate, user_id: str = Depends(get_current_user_id)):
    """Cập nhật mật khẩu cửa"""
    current_hash = read_from_json()
    if not current_hash:
        raise HTTPException(status_code=404, detail="No password set for the door.")

    if not verify_password(data.old_password, current_hash):
        raise HTTPException(status_code=401, detail="Current password is incorrect")

    new_hashed = get_password_hash(data.new_password)
    save_to_json(new_hashed)
    noti = NotiCreate(
        title="Door Password Changed",
        body=f"Password of the door has been changed successfully!",
        noti_type="Website",
    )
    create_notification(noti, user_id)
    return True