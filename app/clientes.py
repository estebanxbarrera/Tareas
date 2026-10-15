"""Clientes HTTP hacia los servicios de los otros equipos.

Implementa el manejo de fallos de la sección J del contrato:
  - tiempo de espera de 3 segundos
  - 2 reintentos con esperas de 1 y 2 segundos
  - circuit breaker: tras 5 fallos seguidos se pausan las llamadas 30 segundos
  - un servicio que no responde nunca se interpreta como "el dato no existe"
"""
import asyncio
import logging

import httpx

from app.config import config
from app.errores import ServicioNoDisponible
from app.utilidades import ahora

log = logging.getLogger("ms-tareas.clientes")


class Circuito:
    def __init__(self):
        self.fallos = 0
        self.abierto_hasta = None

    def abierto(self) -> bool:
        if self.abierto_hasta and ahora() < self.abierto_hasta:
            return True
        return False

    def registrar_fallo(self):
        self.fallos += 1
        if self.fallos >= config.fallos_para_abrir_circuito:
            from datetime import timedelta

            self.abierto_hasta = ahora() + timedelta(seconds=config.segundos_circuito_abierto)
            self.fallos = 0

    def registrar_exito(self):
        self.fallos = 0
        self.abierto_hasta = None


class ClienteServicio:
    """Devuelve None cuando el proveedor responde 404, y lanza 503 si no responde."""

    def __init__(self, nombre: str, url_base: str):
        self.nombre = nombre
        self.url_base = url_base.rstrip("/")
        self.circuito = Circuito()

    async def _llamar(self, metodo: str, ruta: str, json: dict | None = None):
        if self.circuito.abierto():
            log.warning("Circuito abierto para %s, no se intenta la llamada", self.nombre)
            raise ServicioNoDisponible(
                f"El servicio de {self.nombre} no está disponible en este momento"
            )

        url = f"{self.url_base}{ruta}"
        esperas = [0.0] + config.esperas  # primer intento + reintentos
        ultimo_error = None

        for numero, espera in enumerate(esperas, start=1):
            if espera:
                await asyncio.sleep(espera)
            try:
                async with httpx.AsyncClient(timeout=config.timeout_segundos) as cliente:
                    r = await cliente.request(metodo, url, json=json)
                if r.status_code == 404:
                    self.circuito.registrar_exito()
                    return None
                if r.status_code >= 500:
                    ultimo_error = f"respuesta {r.status_code}"
                    log.warning("%s respondió %s (intento %s)", self.nombre, r.status_code, numero)
                    continue
                self.circuito.registrar_exito()
                cuerpo = r.json()
                # Acepta tanto la estructura acordada como una respuesta plana.
                return cuerpo.get("datos", cuerpo) if isinstance(cuerpo, dict) else cuerpo
            except (httpx.TimeoutException, httpx.TransportError) as e:
                ultimo_error = str(e) or type(e).__name__
                log.warning("Sin respuesta de %s (intento %s): %s", self.nombre, numero, ultimo_error)

        self.circuito.registrar_fallo()
        log.error("El servicio de %s no respondió. Último error: %s", self.nombre, ultimo_error)
        raise ServicioNoDisponible(
            f"El servicio de {self.nombre} no está disponible en este momento"
        )

    async def obtener(self, ruta: str):
        return await self._llamar("GET", ruta)

    async def publicar(self, ruta: str, json: dict):
        return await self._llamar("POST", ruta, json)


usuarios = ClienteServicio("usuarios", config.url_usuarios)
materias = ClienteServicio("materias", config.url_materias)
grupos = ClienteServicio("grupos", config.url_grupos)
notificaciones = ClienteServicio("notificaciones", config.url_notificaciones)


# ---------------------------------------------------------------------------
# Datos simulados: se usan solo mientras los otros equipos no tengan su servicio.
# Reglas para poder probar todos los casos del contrato:
#   usuario_id / materia_id / grupo_id = 999999  -> no existe (404)
#   usuario_id = 888888                          -> existe pero inactivo
#   integrantes del grupo simulado               -> [1, 2, 3, 692464]
# ---------------------------------------------------------------------------
INTEGRANTES_SIMULADOS = [1, 2, 3, 692464]


async def consultar_usuario(usuario_id: int):
    if config.simular_servicios:
        if usuario_id == 999999:
            return None
        return {"usuario_id": usuario_id, "nombre": "Estudiante de prueba",
                "activo": usuario_id != 888888}
    return await usuarios.obtener(f"/api/v1/usuarios/{usuario_id}")


async def consultar_materia(materia_id: int):
    if config.simular_servicios:
        if materia_id == 999999:
            return None
        return {"materia_id": materia_id, "nombre": "Sistemas Distribuidos"}
    return await materias.obtener(f"/api/v1/materias/{materia_id}")


async def consultar_grupo(grupo_id: int):
    if config.simular_servicios:
        if grupo_id == 999999:
            return None
        return {"grupo_id": grupo_id, "nombre": "Grupo de estudio",
                "integrantes": INTEGRANTES_SIMULADOS}
    return await grupos.obtener(f"/api/v1/grupos/{grupo_id}")


async def enviar_notificacion(evento: dict):
    if config.simular_servicios:
        if config.simular_notificaciones_caidas:
            raise ServicioNoDisponible("El servicio de notificaciones no está disponible")
        log.info("Notificación simulada: %s", evento)
        return {"notificacion_id": 0}
    return await notificaciones.publicar("/api/v1/notificaciones", evento)
