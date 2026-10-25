import hmac
import hashlib
import random
import string
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from backend.config import settings
from backend.database import db_session
import logging

logger = logging.getLogger(__name__)

class VerificationService:
    @staticmethod
    def _hash_code(code: str) -> str:
        secret = (settings.CODE_HMAC_SECRET or "default-secret-key").encode("utf-8")
        normalized = code.strip().upper().encode("utf-8")
        return hmac.new(secret, normalized, hashlib.sha256).hexdigest()

    _generation_history: dict = {}
    _failed_attempts: dict = {}

    @classmethod
    def check_generate_rate_limit(cls, uid: str, max_requests: int = 10, window_seconds: int = 60) -> bool:
        now = datetime.now(timezone.utc).timestamp()
        history = [ts for ts in cls._generation_history.get(uid, []) if now - ts < window_seconds]
        if len(history) >= max_requests:
            return False
        history.append(now)
        cls._generation_history[uid] = history
        return True

    @classmethod
    def check_verify_rate_limit(cls, uuid: str, max_failures: int = 5, window_seconds: int = 60) -> bool:
        now = datetime.now(timezone.utc).timestamp()
        failures = [ts for ts in cls._failed_attempts.get(uuid, []) if now - ts < window_seconds]
        return len(failures) < max_failures

    @classmethod
    def record_failed_attempt(cls, uuid: str):
        now = datetime.now(timezone.utc).timestamp()
        failures = [ts for ts in cls._failed_attempts.get(uuid, []) if now - ts < 60]
        failures.append(now)
        cls._failed_attempts[uuid] = failures

    @classmethod
    def reset_rate_limits(cls):
        cls._generation_history.clear()
        cls._failed_attempts.clear()

    @classmethod
    def generate_code(cls, uid: str, ttl_seconds: Optional[int] = None) -> Tuple[str, datetime]:
        ttl = ttl_seconds or settings.VERIFICATION_CODE_TTL_SECONDS or 300
        # 6-character alphanumeric uppercase code
        raw_code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        code_hash = cls._hash_code(raw_code)
        
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=ttl)
        
        with db_session() as conn:
            # Invalidate any existing unused codes for this user
            conn.execute("DELETE FROM verification_sessions WHERE uid = ?", (uid,))
            conn.execute(
                """
                INSERT INTO verification_sessions (code_hash, uid, expires_at, used)
                VALUES (?, ?, ?, 0)
                """,
                (code_hash, uid, expires_at.isoformat())
            )
            
        return raw_code, expires_at

    @classmethod
    def verify_and_link(cls, raw_code: str, minecraft_uuid: str, minecraft_username: str) -> dict:
        if not cls.check_verify_rate_limit(minecraft_uuid):
            return {"success": False, "error": "Too many failed verification attempts. Please wait 1 minute."}

        code_hash = cls._hash_code(raw_code)
        now_str = datetime.now(timezone.utc).isoformat()
        
        with db_session() as conn:
            cursor = conn.execute(
                """
                SELECT code_hash, uid, expires_at, used
                FROM verification_sessions
                WHERE code_hash = ?
                """,
                (code_hash,)
            )
            session = cursor.fetchone()
            
            if not session:
                cls.record_failed_attempt(minecraft_uuid)
                return {"success": False, "error": "Invalid verification code"}
            
            if session["used"] != 0:
                cls.record_failed_attempt(minecraft_uuid)
                return {"success": False, "error": "Verification code has already been used"}
            
            # Compare expiration (isoformat string comparison works correctly for UTC)
            if session["expires_at"] < now_str:
                cls.record_failed_attempt(minecraft_uuid)
                return {"success": False, "error": "Verification code has expired"}
            
            uid = session["uid"]
            
            # Check if this minecraft_uuid is already linked to another web user
            cursor_check = conn.execute(
                "SELECT uid FROM minecraft_links WHERE minecraft_uuid = ?",
                (minecraft_uuid,)
            )
            existing_link = cursor_check.fetchone()
            if existing_link and existing_link["uid"] != uid:
                return {
                    "success": False,
                    "error": "This Minecraft player is already linked to another user account. Please unlink it first."
                }

            # Mark code as used
            conn.execute("UPDATE verification_sessions SET used = 1 WHERE code_hash = ?", (code_hash,))
            
            # Create or update minecraft_link
            conn.execute(
                """
                INSERT INTO minecraft_links (uid, minecraft_uuid, minecraft_username, linked_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(uid) DO UPDATE SET
                    minecraft_uuid = excluded.minecraft_uuid,
                    minecraft_username = excluded.minecraft_username,
                    linked_at = CURRENT_TIMESTAMP
                """,
                (uid, minecraft_uuid, minecraft_username)
            )
            
            return {
                "success": True,
                "uid": uid,
                "minecraft_uuid": minecraft_uuid,
                "minecraft_username": minecraft_username
            }

    @staticmethod
    def get_link_by_uuid(minecraft_uuid: str) -> Optional[dict]:
        with db_session() as conn:
            cursor = conn.execute(
                """
                SELECT m.uid, m.minecraft_uuid, m.minecraft_username, m.linked_at, u.email, u.role
                FROM minecraft_links m
                JOIN users u ON m.uid = u.uid
                WHERE m.minecraft_uuid = ?
                """,
                (minecraft_uuid,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_link_by_uid(uid: str) -> Optional[dict]:
        with db_session() as conn:
            cursor = conn.execute(
                """
                SELECT uid, minecraft_uuid, minecraft_username, linked_at
                FROM minecraft_links
                WHERE uid = ?
                """,
                (uid,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    @classmethod
    def lookup_code(cls, raw_code: str) -> Optional[dict]:
        """Look up a verification session by raw code without consuming it."""
        code_hash = cls._hash_code(raw_code)
        with db_session() as conn:
            cursor = conn.execute(
                "SELECT code_hash, uid, expires_at, used FROM verification_sessions WHERE code_hash = ?",
                (code_hash,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def unlink_by_uid(uid: str) -> bool:
        with db_session() as conn:
            cursor = conn.execute("DELETE FROM minecraft_links WHERE uid = ?", (uid,))
            return cursor.rowcount > 0

verification_service = VerificationService()
