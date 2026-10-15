"""Validación del header Authorization (error 401 del contrato).

En esta primera entrega solo se verifica que el token venga presente y bien formado.
En la segunda entrega, si en la reunión se acuerda que cada servicio valide el token,
aquí se agrega la llamada al servicio de Usuarios.
"""
from fastapi import Header

from app.errores import NoAutorizado


async def verificar_token(authorization: str | None = Header(default=None)) -> str:
    if not authorization:
        raise NoAutorizado("Falta el header Authorization")
    partes = authorization.split()
    if len(partes) != 2 or partes[0].lower() != "bearer" or not partes[1].strip():
        raise NoAutorizado("El header Authorization debe tener el formato: Bearer <token>")
    return partes[1]
