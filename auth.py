import os

import mysql.connector
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from passlib.context import CryptContext
from pydantic import BaseModel

# Initialize Security Context
load_dotenv()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
app = FastAPI()


# --- SCHEMAS ---
class UserLoginSchema(BaseModel):
    username: str
    password: str


class UserRegisterSchema(BaseModel):
    username: str
    email: str
    password: str


# --- DB UTILITY ---
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT", 3306)),  # Cast to int and provide default
    )


# --- ENDPOINTS ---


@app.post("/register")
def register(user: UserRegisterSchema):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Check uniqueness
        cursor.execute(
            "SELECT id FROM users WHERE username=%s OR email=%s",
            (user.username, user.email),
        )
        if cursor.fetchone():
            raise HTTPException(
                status_code=400, detail="Username or Email already taken"
            )

        hashed_pw = pwd_context.hash(user.password)
        sql = "INSERT INTO users (username, email, password, is_active) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, (user.username, user.email, hashed_pw, True))
        conn.commit()

        return {"status": "success", "message": "User registered successfully"}

    except mysql.connector.Error as err:
        print(f"Registration DB Error: {err}")  # Log to console
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        cursor.close()
        conn.close()


@app.post("/login")
def login(user_credentials: UserLoginSchema):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        sql = """
            SELECT u.id, u.username, u.password, u.is_active, r.description, r.role_id 
            FROM users u
            LEFT JOIN user_roles ur ON u.id = ur.user_id
            LEFT JOIN roles r ON ur.role_id = r.role_id
            WHERE u.username = %s
        """
        cursor.execute(sql, (user_credentials.username,))
        user = cursor.fetchone()

        # Check if user exists BEFORE verifying password
        if not user or not pwd_context.verify(
            user_credentials.password, user["password"]
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Username or Password",
            )

        if not user["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated."
            )

        # Return the payload the Tkinter Dashboard needs
        return {
            "status": "success",
            "id": user["id"],
            "username": user["username"],
            "role": user["description"] if user["description"] else "No Role",
            "role_id": user["role_id"] if user["role_id"] else 0,
            "access_token": "mock-jwt-token-for-now",
        }

    except Exception as e:
        print(f"Login Logic Error: {e}")  # This helps you find the bug in the terminal
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        cursor.close()
        conn.close()
