import hmac
import os

from fastapi import Header, HTTPException


def require_control_token(
    authorization: str | None = Header(default=None),
) -> None:
    expected = os.getenv("CONTROL_API_TOKEN", "").strip()
    if not expected:
        # Fail closed when the server has not been configured.
        raise HTTPException(
            status_code=503,
            detail="Control API authentication is not configured.",
        )

    scheme, _, supplied = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not supplied:
        raise HTTPException(status_code=401, detail="Authentication required.")

    if not hmac.compare_digest(supplied, expected):
        raise HTTPException(status_code=403, detail="Invalid control token.")
