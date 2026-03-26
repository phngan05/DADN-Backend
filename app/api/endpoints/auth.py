from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Depends, APIRouter, HTTPException
from app.core.database import supabase_client
from app.core.security import get_password_hash, verify_password, create_access_token
from app.schemas.user import UserCreate

router = APIRouter()

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Query user
    response = supabase_client.table("USER")\
        .select("*")\
        .eq("username", form_data.username)\
        .execute()
    
    if not response.data:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    user = response.data[0]
    
    if not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    # Create Token
    access_token = create_access_token(data={"sub": user["user_id"]})
    
    return {"access_token": access_token, "token_type": "bearer"}



@router.post("/register")
def register_user(user_in: UserCreate):
    # Encoding password
    hashed_password = get_password_hash(user_in.password)
    
    # Data
    user_data = {
        "full_name": user_in.full_name,
        "username": user_in.username,
        "password": hashed_password,
    }
    
    print(f"Dữ liệu gửi đi: {user_data}")
    
    try:
        # Insert data
        response = supabase_client.table("USER").insert(user_data).execute()
        
        # Return data
        if response.data:
            return {"message": "User created successfully", "user": response.data[0]}
            
    except Exception as e:
        print(f"LỖI SUPABASE: {str(e)}")
        raise HTTPException(
            status_code=400, 
            detail=f"Lỗi: {str(e)}"
        )