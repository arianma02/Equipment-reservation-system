from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.database import get_connection
from app.security import decode_access_token

from jwt.exceptions import InvalidTokenError

bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        user_id = int(payload.get("sub"))
    except (InvalidTokenError, ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid token")

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, email, role, status FROM users WHERE id = %s", (user_id,)
            )
            user = cursor.fetchone()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    if user["status"] == "disabled":
        raise HTTPException(status_code=403, detail="Account is disabled")

    return user


def get_current_admin(
    current_user=Depends(get_current_user),
):
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required",
        )

    return current_user
