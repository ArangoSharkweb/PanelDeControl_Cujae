import asyncio
import logging

from app.config import settings

log = logging.getLogger("ldap")


async def authenticate_ldap(username: str, password: str) -> bool:
    """Valida credenciales contra LDAP institucional CUJAE.

    Usa bind simple en thread para no bloquear el loop.

    Args:
        username: uid del usuario.
        password: clave.

    Returns:
        True si el bind es exitoso. Si el servidor LDAP no responde
        (desconectado/inaccesible) devuelve False: el login no debe 500.
    """
    if not settings.LDAP_URL:
        return False

    def _bind() -> bool:
        from ldap3 import Connection, Server

        server = Server(settings.LDAP_URL, connect_timeout=5)
        user_dn = f"uid={username},{settings.LDAP_BASE_DN}"
        conn = Connection(server, user=user_dn, password=password, auto_bind=False)
        try:
            return bool(conn.bind())
        except Exception as exc:  # noqa: BLE001 - LDAP caido no debe tumbar el login
            log.warning("LDAP no disponible (%s): %s", settings.LDAP_URL, exc)
            return False
        finally:
            try:
                conn.unbind()
            except Exception:
                pass

    return await asyncio.to_thread(_bind)
