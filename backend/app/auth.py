import secrets

from fastapi import Header, HTTPException

from .config import settings


def requiere_admin(x_admin_token: str = Header(default="")) -> None:
    """Protección simple por token para el panel. Reemplazar por usuarios/JWT antes de producción."""
    if not secrets.compare_digest(x_admin_token, settings.admin_token):
        raise HTTPException(status_code=401, detail="Token inválido")
