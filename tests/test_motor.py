from pathlib import Path
import json

from motor_docx import fill_docx

ROOT = Path(__file__).resolve().parents[1]

def test_generate_example(tmp_path):
    data = json.loads((ROOT / 'examples' / 'prueba_datos.json').read_text(encoding='utf-8'))
    out = tmp_path / 'test.docx'
    fill_docx(ROOT / 'templates' / 'MASTER_SRC_TEMPLATE.docx', data, out)
    assert out.exists()
    assert out.stat().st_size > 100_000
