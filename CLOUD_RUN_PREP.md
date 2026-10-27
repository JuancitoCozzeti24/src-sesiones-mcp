# Preparación de SRC para Cloud Run

Esta rama agrega un contenedor independiente para cada servicio MCP. Los archivos originales de Render y sus servicios permanecen intactos.

| Servicio | Dockerfile | Inicio |
|---|---|---|
| Sesiones | `Dockerfile.cloudrun-sesiones` | `uvicorn server:app` |
| Fichas | `Dockerfile.cloudrun-fichas` | `uvicorn fichas_src.server:app` |

Cloud Run debe proporcionar `PORT`; el fallback local es 8080. `PUBLIC_BASE_URL` debe apuntar a la URL pública real del servicio correspondiente.

## Persistencia pendiente

Ambos servidores guardan los documentos generados en directorios locales (`GENERATED_DIR` y `FICHAS_GENERATED_DIR`). El disco de una instancia de Cloud Run es temporal: un reinicio, una nueva instancia o el escalado a cero puede hacer que un archivo generado ya no esté disponible. Antes de depender de las herramientas en producción se debe elegir y verificar una ubicación persistente, o cambiar la entrega para que el documento se devuelva dentro de la misma respuesta.

La configuración de transporte actual permite Streamable HTTP en `/mcp`. La prueba pública deberá comprobar salud, descubrimiento de herramientas y generación/descarga de archivos sin enviar documentos reales de alumnos.

## Costos

La imagen no configura ni crea recursos facturables. Para desplegar, usar facturación por solicitud, mínimo de instancias 0 y un máximo bajo. La compilación usa Cloud Build y Artifact Registry, que tienen cuotas y precios separados; revisar el costo total del proyecto antes de iniciar.
