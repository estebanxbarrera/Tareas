# Microservicio de Tareas — CampusStudy

Primera entrega del Grupo #1, asignatura Sistemas Distribuidos (UNIMINUTO).
Implementa el **Contrato de Interfaz e Integración v1.0** del servicio de Tareas.

- Lenguaje: Python 3.11 o superior
- Framework: FastAPI
- Base de datos: MySQL 8
- API: `/api/v1/`

---

## 1. Requisitos

- Python 3.11+
- MySQL 8 (XAMPP, MySQL Server o Docker)
- Visual Studio Code con la extensión **Python**. Opcional: **REST Client** para ejecutar `docs/pruebas.http`.

## 2. Instalación en Visual Studio Code

```bash
# 1. Abrir la carpeta del proyecto en VS Code
code ms-tareas

# 2. Crear el entorno virtual
python -m venv .venv

# Windows
.venv\Scripts\activate
# Linux o macOS
source .venv/bin/activate

# 3. Instalar las dependencias
pip install -r requirements.txt
```

En VS Code: `Ctrl+Shift+P` → **Python: Select Interpreter** → elegir `.venv`.

## 3. Crear la base de datos

```bash
mysql -u root -p < sql/esquema.sql
```

Si prefieres que las tablas se creen solas, basta con que exista la base de datos
`campusstudy_tareas`: el servicio crea las tablas al arrancar.

## 4. Configurar el archivo .env

```bash
cp .env.example .env     # en Windows: copy .env.example .env
```

Edita `BASE_DATOS_URL` con tu usuario y contraseña de MySQL.

## 5. Ejecutar el servicio

```bash
uvicorn app.main:app --reload --port 8001
```

- Documentación interactiva (Swagger): http://localhost:8001/docs
- Verificación rápida: http://localhost:8001/salud

## 6. Ejecutar las pruebas

```bash
pytest -v
```

Las pruebas cubren los ocho casos de la sección L del contrato y usan SQLite,
así que no necesitan MySQL encendido.

---

## 7. Operaciones implementadas

| # | Método y endpoint | Descripción | Respuesta |
|---|---|---|---|
| 1 | `POST /api/v1/tareas` | Crear tarea | 201 |
| 2 | `GET /api/v1/tareas/{tarea_id}` | Consultar una tarea | 200 / 404 |
| 3 | `GET /api/v1/tareas?usuario_id=&materia_id=&grupo_id=&estado=&pagina=&tamano=` | Listar con filtros | 200 / 400 |
| 4 | `PUT /api/v1/tareas/{tarea_id}` | Actualizar datos | 200 / 404 |
| 5 | `PUT /api/v1/tareas/{tarea_id}/estado` | Cambiar estado | 200 / 400 |
| 6 | `DELETE /api/v1/tareas/{tarea_id}` | Cancelar (eliminación lógica) | 200 / 404 |
| 7 | `GET /api/v1/tareas/resumen?usuario_id=` | Resumen para Estadísticas | 200 |

Todas exigen el header `Authorization: Bearer <token>`; sin él se responde 401.

**Estructura de respuesta**

```json
{ "exito": true, "datos": { }, "mensaje": "Operación realizada correctamente" }
{ "exito": false, "error": { "codigo": 404, "tipo": "RECURSO_NO_ENCONTRADO", "mensaje": "..." } }
```

**Transiciones de estado**

```
pendiente → en_progreso → completada
pendiente / en_progreso → cancelada
completada y cancelada son estados finales
```

---

## 8. Modo simulado (solo para esta primera entrega)

Como los servicios de Usuarios, Materias, Grupos y Notificaciones todavía no existen,
el archivo `.env` trae `SIMULAR_SERVICIOS=true`. Con esa opción, el servicio responde
con datos de prueba en lugar de llamar por red.

Identificadores reservados para probar los errores del contrato:

| Valor | Resultado |
|---|---|
| `usuario_id`, `materia_id` o `grupo_id` = `999999` | El proveedor responde 404 → Tareas devuelve 400 |
| `usuario_id` = `888888` | El usuario existe pero está inactivo → 400 |
| Integrantes del grupo simulado | `[1, 2, 3, 692464]` |
| `SIMULAR_NOTIFICACIONES_CAIDAS=true` | La tarea se crea (201) y el evento queda pendiente |

## 9. Qué cambia para la segunda entrega (integración)

El código ya está preparado para conectarse con los demás equipos. Para integrar:

1. En `.env`, poner `SIMULAR_SERVICIOS=false` y escribir las URLs reales de los
   servicios de Usuarios, Materias, Grupos y Notificaciones.
2. No hay que tocar la lógica: `app/clientes.py` ya hace las llamadas reales con el
   tiempo de espera, los reintentos y el circuit breaker del contrato.
3. Revisar con cada equipo que los campos coincidan con lo acordado:
   - Usuarios debe devolver `usuario_id`, `nombre` y `activo`
   - Materias debe devolver `materia_id` y `nombre`
   - Grupos debe devolver `grupo_id`, `nombre` e `integrantes` como lista de `usuario_id`
   - Notificaciones debe aceptar `usuario_id`, `tipo`, `referencia_id`, `mensaje` y `fecha_evento`
4. Si en la reunión se acuerda que cada servicio valide el token contra Usuarios,
   agregar esa llamada en `app/seguridad.py` (está marcado el punto exacto).
5. Si se acuerda otra estructura de respuesta, el único archivo a cambiar es
   `app/respuestas.py`.

## 10. Manejo de fallos implementado

- Tiempo de espera de 3 segundos por llamada.
- Dos reintentos, con esperas de 1 y 2 segundos.
- Tras 5 fallos seguidos, el servicio deja de llamar al proveedor por 30 segundos.
- Si Usuarios, Materias o Grupos no responden: la tarea **no** se crea y se devuelve 503.
  Nunca se interpreta "sin respuesta" como "el dato no existe".
- Si Notificaciones no responde: la tarea sí se crea y el evento queda en la tabla
  `eventos_pendientes`, con reintentos cada 5 minutos hasta por 24 horas.

## 11. Estructura del proyecto

```
ms-tareas/
├── app/
│   ├── main.py             API, middleware de X-Request-Id y manejo de errores
│   ├── config.py           Configuración leída desde .env
│   ├── database.py         Conexión a MySQL
│   ├── models.py           Tablas tareas y eventos_pendientes
│   ├── esquemas.py         Validaciones y reglas de datos del contrato
│   ├── servicios.py        Lógica de las operaciones 1 a 7
│   ├── clientes.py         Llamadas a otros servicios, reintentos y circuit breaker
│   ├── notificaciones.py   Envío de eventos y cola de pendientes
│   ├── seguridad.py        Validación del header Authorization
│   ├── errores.py          Errores 400, 401, 404, 500 y 503
│   ├── respuestas.py       Estructura estándar de respuesta
│   ├── utilidades.py       Formatos de fecha y hora (UTC-5)
│   └── routers/tareas.py   Endpoints
├── sql/esquema.sql
├── tests/test_contrato.py  Casos de la sección L del contrato
├── docs/pruebas.http
├── requirements.txt
└── .env.example
```
