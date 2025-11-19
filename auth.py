# auth.py
from fastapi import Request

def login_user(request: Request, user_id: int, email: str):
    request.session["user"] = {
        "user_id": user_id,
        "email": email
    }

def logout_user(request: Request):
    request.session.clear()

def is_logged_in(request: Request):
    return "user" in request.session

def require_login(request: Request):
    if "user" not in request.session:
        return False
    return True
