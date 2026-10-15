"""Configuración del microservicio. Todo se puede cambiar desde el archivo .env."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    # --- Identificación del servicio ---
    nombre_servicio: str = "ms-tareas"
    version_api: str = "v1"
    version_contrato: str = "1.0"
    zona_horaria: str = "America/Bogota"  # UTC-5, acordado en el contrato

    # --- Base de datos MySQL ---
    base_datos_url: str = (
        "mysql+pymysql://root:root@localhost:3306/campusstudy_tareas?charset=utf8mb4"
    )

    # --- Servicios de los otros equipos (segunda entrega) ---
    url_usuarios: str = "http://localhost:8008"
    url_materias: str = "http://localhost:8009"
    url_grupos: str = "http://localhost:8002"
    url_notificaciones: str = "http://localhost:8007"

    # Mientras los demás servicios no existan, se responden con datos simulados.
    # En la segunda entrega basta con poner esto en false.
    simular_servicios: bool = True
    # Permite probar el caso 5 del contrato: Notificaciones caído.
    simular_notificaciones_caidas: bool = False

    # --- Manejo de fallos (sección J del contrato) ---
    timeout_segundos: float = 3.0
    esperas_reintento: str = "1,2"       # segundos entre reintentos
    fallos_para_abrir_circuito: int = 5
    segundos_circuito_abierto: int = 30
    minutos_reintento_eventos: int = 5
    horas_maximo_evento: int = 24

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def esperas(self) -> list[float]:
        return [float(x) for x in self.esperas_reintento.split(",") if x.strip()]


config = Config()
