import json
import os
import uuid
import hashlib
from datetime import datetime
from typing import Optional
from backend.app.schemas.auth import User, UserCreate

USERS_FILE = "users.json"
ADMIN_EMAIL = "admin@liftops.ai" # Hardcoded Admin

class UserRepository:
    def __init__(self):
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(USERS_FILE):
            with open(USERS_FILE, "w") as f:
                json.dump([], f)

    def _load(self):
        with open(USERS_FILE, "r") as f:
            return json.load(f)

    def _save(self, users):
        with open(USERS_FILE, "w") as f:
            json.dump(users, f, indent=4)

    def _hash_password(self, password: str) -> str:
        # Simple hash for demo purposes (production should use bcrypt)
        return hashlib.sha256(password.encode()).hexdigest()

    def get_by_email(self, email: str) -> Optional[dict]:
        users = self._load()
        for u in users:
            if u["email"] == email:
                return u
        return None

    def create_user(self, user_in: UserCreate) -> dict:
        users = self._load()
        
        # Check if exists
        if self.get_by_email(user_in.email):
            raise ValueError("Email already registered")

        # Determine Role/Tier
        is_admin = user_in.email == ADMIN_EMAIL
        role = "admin" if is_admin else "user"
        tier = "commander" if is_admin else "pilot"

        new_user = {
            "id": str(uuid.uuid4()),
            "email": user_in.email,
            "full_name": user_in.full_name,
            "password_hash": self._hash_password(user_in.password),
            "role": role,
            "tier": tier,
            "created_at": datetime.now().isoformat()
        }
        
        users.append(new_user)
        self._save(users)
        return new_user

    def authenticate(self, email, password) -> Optional[dict]:
        user = self.get_by_email(email)
        if not user:
            return None
        if user["password_hash"] == self._hash_password(password):
            return user
        return None
    
    def upgrade_tier(self, email: str, tier: str):
        users = self._load()
        for u in users:
            if u["email"] == email:
                u["tier"] = tier
                self._save(users)
                return u
        return None

user_repo = UserRepository()
