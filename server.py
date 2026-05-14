import os

import mysql.connector
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from passlib.context import CryptContext
from pydantic import BaseModel

import registration

# Load environment variables from .env file
load_dotenv()

app = FastAPI()
app.include_router(registration.router)
# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# --- Database Dependency ---
def get_db():
    connection = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=os.getenv("DB_PORT", 3306),
    )
    return connection


# --- Models ---
class LoginRequest(BaseModel):
    username: str
    password: str


# --- Routes ---


@app.post("/login")
async def login(payload: LoginRequest):
    db = get_db()
    # dictionary=True is essential for accessing columns by name
    cursor = db.cursor(dictionary=True)

    try:
        # We must select u.id and r.role_id explicitly
        query = """
            SELECT 
                u.id, 
                u.username, 
                u.password, 
                u.is_active,
                r.description AS role_name, 
                r.role_id AS role_id
            FROM users u
            LEFT JOIN user_roles ur ON u.id = ur.user_id
            LEFT JOIN roles r ON ur.role_id = r.role_id
            WHERE u.username = %s
        """
        cursor.execute(query, (payload.username,))
        user = cursor.fetchone()

        # 1. Check if user exists
        # 2. Verify password
        if user and pwd_context.verify(payload.password, user["password"]):
            if not user.get("is_active", True):
                raise HTTPException(status_code=403, detail="Account is deactivated")

            # FIX: Use 'role_name' because of your SQL alias 'AS role_name'
            return {
                "id": user["id"],
                "username": user["username"],
                "role": user["role_name"] if user["role_name"] else "User",
                "role_id": user["role_id"] if user["role_id"] else 0,
                "status": "success",
            }

        # If authentication fails
        raise HTTPException(status_code=401, detail="Invalid username or password")

    except Exception as e:
        print(f"Server Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    finally:
        cursor.close()
        db.close()
