# SRC Sesiones Quincenales — Plugin MCP v0.1

Primer prototipo del complemento que convierte la plantilla institucional de sesiones quincenales en una herramienta invocable desde un host MCP (por ejemplo, ChatGPT cuando la cuenta/workspace permita apps MCP personalizadas).

## Qué hace esta versión

- Conserva `MASTER_SRC_TEMPLATE.docx` como plantilla maestra.
- Expone herramientas MCP para consultar campos y generar el DOCX.
- Mantiene negrita selectiva: solo etiquetas/subtítulos.
- Convierte los subapartados de Inicio, Desarrollo y Cierre en párrafos Word reales, con separación visual.
- Sirve el Word generado mediante `/download/{file_id}`.
- Incluye configuración base para Render.

## Herramientas MCP

- `get_template_info`: devuelve los campos y reglas del formato.
- `generate_quincena_docx`: recibe los campos redactados y fabrica el Word.
- `get_generated_document`: comprueba si un archivo generado sigue disponible.

## Ejecutar localmente

Requiere Python 3.10+.

```bash
python -m venv .venv
# Windows
.venv\\Scripts\\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
uvicorn server:app --host 127.0.0.1 --port 8000
```

Salud: `http://127.0.0.1:8000/health`
MCP: `http://127.0.0.1:8000/mcp`

Para probar con MCP Inspector:

```bash
npx @modelcontextprotocol/inspector@latest
```

## Despliegue en Render

El repositorio ya trae `render.yaml`. Tras desplegar, configura `PUBLIC_BASE_URL` con la URL pública, por ejemplo `https://src-sesiones-mcp.onrender.com`.

El endpoint que se conectará al host MCP será:

```text
https://TU-SERVICIO.onrender.com/mcp
```

## Estado / próximo paso

v0.1 usa los seis bloques de sesión preparados en la plantilla prototipo. La próxima versión debe clonar o eliminar bloques de sesión dinámicamente según la cantidad real de clases de la quincena y luego incorporar la interfaz web opcional.
