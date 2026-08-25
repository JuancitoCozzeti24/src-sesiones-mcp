from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any
import os
import re
import uuid

from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from starlette.applications import Starlette
from starlette.responses import FileResponse, JSONResponse, PlainTextResponse
from starlette.routing import Mount, Route

from .generator_exact import generate_ficha_pdf as render_ficha_pdf

BASE_DIR = Path(__file__).resolve().parent
GENERATED_DIR = Path(os.getenv('FICHAS_GENERATED_DIR', str(BASE_DIR / 'generated')))
GENERATED_DIR.mkdir(parents=True, exist_ok=True)
PUBLIC_BASE_URL = os.getenv('PUBLIC_BASE_URL', '').rstrip('/')

mcp = MCPServer(
    'SRC Fichas Didácticas',
    version='0.2.0',
    instructions=(
        'Genera fichas didácticas de Matemática en PDF siguiendo SRC_FICHA_MAESTRA_V1, '
        'reconstruida a partir del modelo institucional aprobado. Conserva la misma lógica visual: '
        'encabezado institucional, bloque curricular, teoría visual, práctica fácil en dos columnas, '
        'nivel intermedio, nivel reto, autoevaluación y pie institucional. No inventes un diseño alternativo. '
        'La ficha estándar tiene exactamente tres páginas y doce ejercicios: 6 fáciles, 4 intermedios y 2 retos.'
    ),
)


def _safe_pdf_name(name: str) -> str:
    name = (name or 'FICHA_SRC.pdf').strip()
    if not name.lower().endswith('.pdf'):
        name += '.pdf'
    stem = Path(name).stem
    stem = re.sub(r'[^A-Za-z0-9ÁÉÍÓÚÜÑáéíóúüñ._ -]+', '_', stem).strip(' ._')
    return (stem or 'FICHA_SRC') + '.pdf'


def _find_generated(file_id: str) -> Path | None:
    for path in GENERATED_DIR.glob(f'{file_id}__*.pdf'):
        if path.is_file():
            return path
    return None


def _validate_spec(spec: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in ('title', 'grade', 'curriculum', 'pages'):
        if key not in spec or spec.get(key) in (None, '', [], {}):
            errors.append(f'Falta el campo requerido: {key}')
    curriculum = spec.get('curriculum') or {}
    for key in ('competencia', 'desempeno'):
        if not str(curriculum.get(key, '')).strip():
            errors.append(f'Falta curriculum.{key}')
    if not curriculum.get('capacidades'):
        errors.append('Falta curriculum.capacidades')
    pages = spec.get('pages') or []
    if pages and len(pages) != 3:
        errors.append('La plantilla maestra requiere exactamente 3 páginas.')
    if len(pages) == 3:
        if len(pages[0].get('cards', [])) < 4:
            errors.append('La página 1 requiere 4 tarjetas de teoría.')
        if len(pages[0].get('operations', [])) < 4:
            errors.append('La página 1 requiere 4 bloques de explicación/procedimiento.')
        if len(pages[1].get('exercises', [])) < 6:
            errors.append('La página 2 requiere 6 ejercicios de nivel fácil.')
        if len(pages[2].get('intermediate', [])) < 4:
            errors.append('La página 3 requiere 4 ejercicios de nivel intermedio.')
        if len(pages[2].get('challenge', [])) < 2:
            errors.append('La página 3 requiere 2 ejercicios de nivel reto.')
    return errors


@mcp.tool()
def get_ficha_template_info() -> dict:
    """Devuelve la estructura exacta que debe preparar ChatGPT para generar una ficha SRC."""
    return {
        'template': 'SRC_FICHA_MAESTRA_V1',
        'version': '0.2.0',
        'output': 'PDF A4 vertical de 3 páginas',
        'source_model': 'Ficha institucional de Operaciones con Matrices aprobada como referencia visual.',
        'fixed_structure': [
            'Página 1: encabezado SRC + bloque curricular completo + 4 tarjetas de teoría + 4 bloques de procedimiento + palabras clave + aplicaciones + consejo.',
            'Página 2: encabezado SRC + bloque curricular compacto + Nivel fácil + 6 ejercicios en dos columnas.',
            'Página 3: continuación + 4 ejercicios intermedios + 2 retos contextualizados + autoevaluación + pie SRC.'
        ],
        'identity_rules': [
            'A4 vertical.',
            'Mantener encabezado y pie institucionales.',
            'Azul = nivel fácil; verde = nivel intermedio; morado = nivel reto.',
            'Cajas redondeadas, espacios amplios de resolución y cuadrícula tenue.',
            'No convertir la ficha en una hoja de texto: usar frases breves, tarjetas, ejemplos y progresión visual.',
            'La autoevaluación usa acciones concretas del tema.'
        ],
        'required_spec': {
            'title': 'Título de la ficha.',
            'practice_title': 'Título de la página de práctica.',
            'grade': 'Ej.: 2.º o 5.º',
            'curriculum': {
                'competencia': 'Texto de competencia.',
                'capacidades': ['4 capacidades completas'],
                'capacidades_abrev': ['4 capacidades abreviadas para página 2'],
                'desempeno': 'Desempeño precisado.'
            },
            'pages': [
                {'cards': '4 tarjetas', 'operations': '4 bloques', 'keywords': 'hasta 8', 'applications': '2', 'tip': '1'},
                {'subtitle': 'orientación breve', 'exercises': '6 ejercicios'},
                {'reminder': 'recordatorio', 'intermediate': '4 ejercicios', 'challenge': '2 retos', 'self_assessment_rows': '5', 'reinforce': '4', 'feelings': '3'}
            ]
        }
    }


@mcp.tool()
def generate_ficha_src_pdf(spec: dict[str, Any], output_name: str = 'FICHA_SRC.pdf') -> dict:
    """Genera una ficha SRC de tres páginas usando el modelo institucional aprobado."""
    errors = _validate_spec(spec)
    if errors:
        return {
            'ok': False,
            'error': 'La ficha no se generó porque faltan datos necesarios para conservar la plantilla maestra.',
            'details': errors,
        }
    file_id = uuid.uuid4().hex
    safe_name = _safe_pdf_name(output_name)
    path = GENERATED_DIR / f'{file_id}__{safe_name}'
    try:
        render_ficha_pdf(spec, path)
    except Exception as exc:
        return {'ok': False, 'error': str(exc)}
    relative = f'/download/{file_id}'
    return {
        'ok': True,
        'file_id': file_id,
        'filename': safe_name,
        'download_url': f'{PUBLIC_BASE_URL}{relative}' if PUBLIC_BASE_URL else relative,
        'message': 'Ficha SRC generada correctamente con SRC_FICHA_MAESTRA_V1.'
    }


@mcp.tool()
def get_generated_ficha(file_id: str) -> dict:
    """Consulta si una ficha PDF generada continúa disponible."""
    path = _find_generated(file_id)
    if path is None:
        return {'found': False, 'file_id': file_id}
    relative = f'/download/{file_id}'
    original_name = path.name.split('__', 1)[1] if '__' in path.name else path.name
    return {
        'found': True,
        'file_id': file_id,
        'filename': original_name,
        'size_bytes': path.stat().st_size,
        'download_url': f'{PUBLIC_BASE_URL}{relative}' if PUBLIC_BASE_URL else relative,
    }


async def health(request):
    return JSONResponse({'ok': True, 'service': 'SRC Fichas Didácticas', 'version': '0.2.0', 'mcp_endpoint': '/mcp'})


async def home(request):
    return PlainTextResponse('SRC Fichas Didácticas MCP v0.2.0 - endpoint: /mcp')


async def download(request):
    file_id = request.path_params['file_id']
    path = _find_generated(file_id)
    if path is None:
        return PlainTextResponse('Ficha no encontrada o expirada.', status_code=404)
    original_name = path.name.split('__', 1)[1] if '__' in path.name else path.name
    return FileResponse(path, filename=original_name, media_type='application/pdf')


if os.getenv('MCP_DISABLE_DNS_REBINDING', '').lower() in {'1', 'true', 'yes'}:
    security = TransportSecuritySettings(enable_dns_rebinding_protection=False)
else:
    security = None

mcp_app = mcp.streamable_http_app(json_response=True, transport_security=security)


@asynccontextmanager
async def lifespan(app: Starlette) -> AsyncIterator[None]:
    async with mcp.session_manager.run():
        yield


app = Starlette(
    routes=[
        Route('/', home, methods=['GET']),
        Route('/health', health, methods=['GET']),
        Route('/download/{file_id}', download, methods=['GET']),
        Mount('/', app=mcp_app),
    ],
    lifespan=lifespan,
)
