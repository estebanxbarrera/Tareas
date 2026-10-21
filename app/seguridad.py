"""Validación del header Authorization (error 401 del contrato).

En esta primera entrega solo se verifica que el token venga presente y bien formado.
En la segunda entrega, si en la reunión se acuerda que cada servicio valide el token,
aquí se agrega la llamada al servicio de Usuarios.
"""
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.errores import NoAutorizado

esquema_token = HTTPBearer(auto_error=False, description="Token emitido por el servicio de Usuarios")


async def verificar_token(
    credenciales: HTTPAuthorizationCredentials | None = Depends(esquema_token),
) -> str:
    if credenciales is None:
        raise NoAutorizado("Falta el header Authorization o no tiene el formato: Bearer <token>")
    if not credenciales.credentials.strip():
        raise NoAutorizado("El token no puede estar vacío")
    return credenciales.credentials