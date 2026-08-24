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

from .generator_pdf import generate_ficha_pdf as render_ficha_pdf

BASE_DIR = Path(__file__).resolve().parent
GENERATED_DIR = Path(os.getenv('FICHAS_GENERATED_DIR', str(BASE_DIR / 'generated')))
GENERATED_DIR.mkdir(parents=True, exist_ok=True)
PUBLIC_BASE_URL = os.getenv('PUBLIC_BASE_URL', '').rstrip('/')

mcp = MCPServer(
    'SRC Fichas Didácticas',
    version='0.1.0',
    instructions=(
        'Genera fichas didácticas de Matemática en PDF con la identidad visual SRC definida por la plantilla maestra. '
        'Conserva el encabezado institucional, el pie con el lema y logos, la jerarquía visual, los niveles de dificultad, '
        'los espacios de respuesta y la autoevaluación. No rediseñes la identidad institucional. '
        'Adapta el contenido interno al tema, grado y propósito, priorizando explicación visual, progresión de dificultad '
        'y espacios de trabajo adecuados al tipo de ejercicio.'
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
    allowed = {'theory', 'practice_easy', 'practice_levels'}
    for i, page in enumerate(pages, 1):
        kind = page.get('kind')
        if kind not in allowed:
            errors.append(f'pages[{i}].kind inválido: {kind!r}')
    return errors


@mcp.tool()
def get_ficha_template_info() -> dict:
    """Devuelve la estructura y reglas de la plantilla maestra de FICHAS SRC. No genera archivos."""
    return {
        'template': 'SRC_FICHA_MAESTRA_V1',
        'version': '0.1.0',
        'output': 'PDF A4 vertical',
        'identity': {
            'header': 'Logo y nombre institucional de Santa Rita de Casia; título grande; nombre, sección y fecha.',
            'footer': 'Lema “Anuncien a Cristo donde puedan”, iconografía institucional, Educar, Agustinos Recoletos y línea multicolor.',
            'fixed_rule': 'Encabezado y pie son componentes de identidad; no deben rediseñarse entre fichas.'
        },
        'curriculum': {
            'full': ['competencia', 'capacidades', 'desempeno'],
            'compact': ['competencia', 'capacidades_abrev']
        },
        'page_kinds': {
            'theory': 'Página visual de teoría: tarjetas, reglas breves, ejemplos, palabras clave, aplicación y consejo.',
            'practice_easy': 'Práctica de nivel fácil en dos columnas, con 6 ejercicios y espacios de respuesta adaptados.',
            'practice_levels': 'Continuación sin encabezado institucional repetido: nivel intermedio, nivel reto y autoevaluación.'
        },
        'answer_spaces': ['grid', 'lines', 'blank', 'split_grid'],
        'math_runs': {
            'text': {'type': 'text', 'text': 'Si A = '},
            'matrix': {'type': 'matrix', 'value': [[1, 2], [3, 4]]}
        },
        'difficulty_colors': {
            'facil': 'azul',
            'intermedio': 'verde',
            'reto': 'morado'
        },
        'design_rules': [
            'Poco texto corrido: fragmentar la explicación en tarjetas, reglas y ejemplos.',
            'Mantener alto contraste, cajas redondeadas y jerarquía visual clara.',
            'Usar cuadrícula para cálculo, líneas para explicación y espacio libre para procedimientos extensos.',
            'Las preguntas avanzan de reconocimiento y procedimiento hacia aplicación, razonamiento e interpretación.',
            'La autoevaluación debe usar acciones concretas del tema, no frases genéricas.',
            'No escribir “DUA” en la ficha; aplicar accesibilidad visual y progresión sin nombrarla.'
        ],
        'required_top_level_fields': ['title', 'grade', 'curriculum', 'pages']
    }


@mcp.tool()
def generate_ficha_src_pdf(spec: dict[str, Any], output_name: str = 'FICHA_SRC.pdf') -> dict:
    """Genera una ficha SRC en PDF usando la plantilla visual institucional y un spec estructurado."""
    errors = _validate_spec(spec)
    if errors:
        return {'ok': False, 'error': 'La ficha no se generó porque el spec está incompleto o es inválido.', 'details': errors}

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
        'message': 'Ficha SRC generada correctamente en PDF.'
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
    return JSONResponse({'ok': True, 'service': 'SRC Fichas Didácticas', 'version': '0.1.0', 'mcp_endpoint': '/mcp'})


async def home(request):
    return PlainTextResponse('SRC Fichas Didácticas MCP v0.1.0 - endpoint: /mcp')


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
