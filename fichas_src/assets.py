from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ASSET_DIR = BASE_DIR / 'assets_data'


def _read_chunks(prefix: str) -> bytes:
    parts = sorted(ASSET_DIR.glob(f'{prefix}_*.txt'))
    if not parts:
        raise FileNotFoundError(f'No se encontraron recursos institucionales: {prefix}')
    encoded = ''.join(p.read_text(encoding='ascii').strip() for p in parts)
    return base64.b64decode(encoded)


def header_bytes() -> BytesIO:
    return BytesIO(_read_chunks('header'))


def footer_bytes() -> BytesIO:
    return BytesIO(_read_chunks('footer'))
