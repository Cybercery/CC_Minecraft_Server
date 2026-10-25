import threading
import signal
import logging
from mcrcon import MCRcon
from backend.config import settings

logger = logging.getLogger(__name__)

# MCRcon registers a signal handler in __init__ which fails if called from a worker thread
_orig_signal = signal.signal
def _safe_signal(sig, handler):
    if threading.current_thread() is threading.main_thread():
        try:
            return _orig_signal(sig, handler)
        except Exception:
            return None
    return None

signal.signal = _safe_signal


class RconService:
    def __init__(self, host: str = "minecraft", port: int = 25575, password: str = None):
        self.host = host
        self.port = port
        self.password = password

    def _get_password(self):
        return self.password or settings.RCON_PASSWORD or ""

    def execute_command(self, command: str) -> str:
        pwd = self._get_password()
        if not pwd:
            raise ValueError("RCON_PASSWORD is not set.")
        
        try:
            with MCRcon(self.host, pwd, port=self.port, timeout=5) as mcr:
                resp = mcr.command(command)
                return resp
        except Exception as e:
            logger.error(f"RCON execution error: {e}")
            raise

    def get_player_list(self) -> dict:
        try:
            raw = self.execute_command("list")
            # Typical Paper/Spigot output: "There are 0 of a max of 20 players online:" or similar
            # Example: "There are 1 of a max of 20 players online: Player1"
            parts = raw.split(":")
            players = []
            if len(parts) > 1 and parts[1].strip():
                players = [p.strip() for p in parts[1].split(",") if p.strip()]
            return {
                "raw": raw,
                "online_count": len(players),
                "players": players
            }
        except Exception as e:
            logger.warning(f"Could not fetch player list via RCON: {e}")
            return {
                "raw": str(e),
                "online_count": 0,
                "players": []
            }

rcon_service = RconService()
