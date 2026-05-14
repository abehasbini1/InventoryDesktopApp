import os

import mysql.connector
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from passlib.context import CryptContext
from pydantic import BaseModel

load_dotenv()
router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserRegister(BaseModel):
    username: str
    email: str
    password: str


def get_db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT", 3306)),
    )


@router.post("/register")
def register(user: UserRegister):
    db = None
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
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
        db.commit()

        return {"status": "success", "message": "User created successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")
    finally:
        if db:
            db.close()
