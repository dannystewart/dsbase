from __future__ import annotations

import hashlib
import hmac
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

from dsbase.log import LocalLogger

if TYPE_CHECKING:
    from collections.abc import Callable

logger = LocalLogger().get_logger()

AUTHORIZED_FINGERPRINTS = [
    "14d17037b9900d5a540ab946a4b66b6d76186001fe341f4afe85955ab212788d",
]


def _get_ssh_key_fingerprint() -> str:
    """Generate a fingerprint based on the user's SSH public key."""
    ssh_paths = [Path.home() / ".ssh" / "id_rsa.pub", Path.home() / ".ssh" / "id_ed25519.pub"]

    for ssh_path in ssh_paths:
        if ssh_path.exists():
            try:
                ssh_key = ssh_path.read_text(encoding="utf-8").strip()
                return hashlib.sha256(ssh_key.encode()).hexdigest()
            except Exception:
                continue
    return ""


def verify_execution() -> bool:
    """Verify if execution is allowed on this machine."""
    current_fingerprint = _get_ssh_key_fingerprint()

    if not current_fingerprint:
        logger.error("Could not generate SSH key fingerprint.")
        return False

    for fingerprint in AUTHORIZED_FINGERPRINTS:
        if hmac.compare_digest(current_fingerprint, fingerprint):
            return True

    logger.error("Unauthorized execution attempt detected.")
    return False


def require_auth(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to require authorization before running a function."""

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if not verify_execution():
            sys.exit(1)
        return func(*args, **kwargs)

    return wrapper


def enforce_auth() -> None:
    """Enforce authentication for the current script."""
    if not verify_execution():
        logger.error("Authentication failed. Exiting.")
        sys.exit(1)


if __name__ == "__main__":
    print(_get_ssh_key_fingerprint())
