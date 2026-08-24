from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

from .assets import header_bytes, footer_bytes

PAGE_W, PAGE_H = A4
MM = 72 / 25.4

DARK_GREEN = colors.HexColor('#005B46')
OLIVE = colors.HexColor('#6F8E35')
BLUE = colors.HexColor('#0B5D82')
CYAN = colors.HexColor('#1592B2')
GREEN = colors.HexColor('#3B8F3E')
PURPLE = colors.HexColor('#7B2E91')
ORANGE = colors.HexColor('#D67A31')
RED = colors.HexColor('#D63A2F')
YELLOW = colors.HexColor('#E9AF2B')
GRID = colors.HexColor('#E7EBEE')
LIGHT_BLUE = colors.HexColor('#EAF4F8')
LIGHT_GREEN = colors.HexColor('#EFF8ED')
LIGHT_PURPLE = colors.HexColor('#F6EEF8')
LIGHT_ORANGE = colors.HexColor('#FCF2E9')
TEXT = colors.HexColor('#202529')
MUTED = colors.HexColor('#50606A')

FONT = 'Helvetica'
FONT_BOLD = 'Helvetica-Bold'

HEADER_IMG = ImageReader(header_bytes())
FOOTER_IMG = ImageReader(footer_bytes())


def _fit_font(text: str, max_width: float, start: float, minimum: float = 8) -> float:
    size = start
    while size > minimum and stringWidth(text, FONT_BOLD, size) > max_width:
        size -= 0.5
    return size


def _wrap(text: str, font: str, size: float, max_width: float) -> list[str]:
    words = str(text).split()
    if not words:
        return ['']
    lines: list[str] = []
    cur = words[0]
    for word in words[1:]:
        test = cur + ' ' + word
        if stringWidth(test, font, size) <= max_width:
            cur = test
        else:
            lines.append(cur)
            cur = word
    lines.append(cur)
    return lines


def _draw_wrapped(c: canvas.Canvas, text: str, x: float, y: float, width: float,
                  size: float = 8.5, leading: float | None = None,
                  font: str = FONT, color=TEXT, max_lines: int | None = None) -> float:
    leading = leading or size * 1.25
    c.setFont(font, size)
    c.setFillColor(color)
    lines = _wrap(text, font, size, width)
    if max_lines is not None:
        lines = lines[:max_lines]
    for line in lines:
        c.drawString(x, y, line)
        y -= leading
    return y


def _round_rect(c: canvas.Canvas, x: float, y: float, w: float, h: float,
                stroke, fill=None, radius: float = 5, line_width: float = 1.0):
    c.setLineWidth(line_width)
    c.setStrokeColor(stroke)
    c.setFillColor(fill if fill is not None else colors.white)
    c.roundRect(x, y, w, h, radius, stroke=1, fill=1)


def _draw_matrix(c: canvas.Canvas, matrix: list[list[Any]], x: float, y_center: float,
                 font_size: float = 9, cell_w: float = 16, cell_h: float = 12) -> float:
    rows = max(1, len(matrix))
    cols = max(1, max((len(r) for r in matrix), default=1))
    inner_w = cols * cell_w
    h = rows * cell_h
    top = y_center + h / 2
    bottom = y_center - h / 2
    left = x
    right = x + inner_w + 10
    c.setStrokeColor(TEXT)
    c.setLineWidth(0.8)
    c.line(left + 3, bottom, left, bottom)
    c.line(left, bottom, left, top)
    c.line(left, top, left + 3, top)
    c.line(right - 3, bottom, right, bottom)
    c.line(right, bottom, right, top)
    c.line(right, top, right - 3, top)
    c.setFont(FONT, font_size)
    c.setFillColor(TEXT)
    for i, row in enumerate(matrix):
        for j, value in enumerate(row):
            txt = str(value)
            cx = left + 5 + j * cell_w + cell_w / 2
            cy = top - (i + 0.72) * cell_h
            c.drawCentredString(cx, cy, txt)
    return right - left


def _draw_rich_line(c: canvas.Canvas, runs: list[dict[str, Any]], x: float, y: float,
                    max_width: float, size: float = 9) -> float:
    cur_x = x
    for run in runs:
        kind = run.get('type', 'text')
        if kind == 'matrix':
            width = _draw_matrix(c, run.get('value', [[0]]), cur_x, y + 2, font_size=size)
            cur_x += width + 5
        else:
            txt = str(run.get('text', ''))
            font = FONT_BOLD if run.get('bold') else FONT
            run_size = float(run.get('size', size))
            c.setFont(font, run_size)
            c.setFillColor(run.get('color', TEXT))
            c.drawString(cur_x, y, txt)
            cur_x += stringWidth(txt, font, run_size) + float(run.get('gap', 2))
        if cur_x > x + max_width:
            break
    return cur_x


def draw_institutional_header(c: canvas.Canvas, title: str, grade: str, sections: Iterable[str], year: str = '2026') -> float:
    c.drawImage(HEADER_IMG, 18*MM, PAGE_H - 36*MM, width=150*MM, height=25.6*MM, mask='auto', preserveAspectRatio=True)
    title_y = PAGE_H - 41.5*MM
    title_size = _fit_font(title.upper(), PAGE_W - 36*MM, 20, 12)
    c.setFillColor(DARK_GREEN)
    c.setFont(FONT_BOLD, title_size)
    c.drawCentredString(PAGE_W/2, title_y, title.upper())
    info_y = title_y - 10.5*MM
    c.setFillColor(TEXT)
    c.setFont(FONT_BOLD, 8.5)
    c.drawString(21*MM, info_y, 'Nombre:')
    c.setLineWidth(0.6)
    c.line(42*MM, info_y-1, 83*MM, info_y-1)
    sec_x = 88*MM
    c.drawString(sec_x, info_y, f'Sección: {grade}')
    x = sec_x + 31*MM
    for sec in sections:
        c.rect(x, info_y-3, 4.4*MM, 4.4*MM, stroke=1, fill=0)
        c.drawString(x + 6*MM, info_y, str(sec))
        x += 14*MM
    date_x = 145*MM
    c.drawString(date_x, info_y, 'Fecha:')
    x = date_x + 16*MM
    for i, width in enumerate([10*MM, 10*MM, 16*MM]):
        c.roundRect(x, info_y-3.5, width, 5.8*MM, 1.5, stroke=1, fill=0)
        if i < 2:
            x += width + 3*MM
            c.drawString(x-1.6*MM, info_y, '/')
            x += 2*MM
        else:
            c.setFont(FONT_BOLD, 8)
            c.drawCentredString(x+width/2, info_y-0.4, year)
    return info_y - 8*MM


def draw_curriculum_block(c: canvas.Canvas, y_top: float, spec: dict[str, Any], compact: bool = False) -> float:
    x = 18*MM
    w = PAGE_W - 36*MM
    if compact:
        h = 18*MM
        _round_rect(c, x, y_top-h, w, h, OLIVE, colors.white, 4, 1)
        c.setFillColor(colors.HexColor('#F1F4E8'))
        c.rect(x, y_top-h, 24*MM, h, stroke=0, fill=1)
        c.setFillColor(DARK_GREEN)
        c.setFont(FONT_BOLD, 8.5)
        c.drawString(x+6*MM, y_top-6*MM, 'Competencia:')
        _draw_wrapped(c, spec.get('competencia',''), x+27*MM, y_top-6*MM, w-30*MM, 7.5, 9)
        c.setFont(FONT_BOLD, 7.2)
        c.drawString(x+6*MM, y_top-14*MM, 'Capacidades:')
        caps = spec.get('capacidades_abrev') or []
        cap_text = '   |   '.join(str(s) for s in caps)
        c.setFont(FONT, 7.2)
        c.drawString(x+27*MM, y_top-14*MM, cap_text)
        return y_top-h-4*MM
    h = 38*MM
    _round_rect(c, x, y_top-h, w, h, OLIVE, colors.white, 4, 1)
    label_w = 48*MM
    row_heights = [10*MM, 17*MM, 11*MM]
    labels = ['Competencia:', 'Capacidades:', 'Desempeño\nprecisado:']
    y = y_top
    for idx, rh in enumerate(row_heights):
        y2 = y-rh
        c.setFillColor(colors.HexColor('#F0F3E7'))
        c.rect(x, y2, label_w, rh, stroke=0, fill=1)
        if idx > 0:
            c.setStrokeColor(OLIVE)
            c.line(x, y, x+w, y)
        c.setFillColor(DARK_GREEN)
        c.setFont(FONT_BOLD, 8)
        label = labels[idx]
        if '\n' in label:
            a,b = label.split('\n')
            c.drawString(x+18*MM, y-4.5*MM, a)
            c.drawString(x+18*MM, y-8.3*MM, b)
        else:
            c.drawString(x+18*MM, y-rh/2-1.5, label)
        c.setStrokeColor(OLIVE)
        c.setLineWidth(1.5)
        if idx == 0:
            c.circle(x+9*MM, y-rh/2, 3.6*MM, stroke=1, fill=0)
            c.circle(x+9*MM, y-rh/2, 1.5*MM, stroke=1, fill=0)
        elif idx == 1:
            c.circle(x+9*MM, y-rh/2, 3.1*MM, stroke=1, fill=0)
            off = 4.4*MM
            c.line(x+9*MM, y-rh/2+3.1*MM, x+9*MM, y-rh/2+off)
            c.line(x+9*MM+3.1*MM, y-rh/2, x+9*MM+off, y-rh/2)
            c.line(x+9*MM, y-rh/2-3.1*MM, x+9*MM, y-rh/2-off)
            c.line(x+9*MM-3.1*MM, y-rh/2, x+9*MM-off, y-rh/2)
        else:
            bx = x+5.5*MM
            by = y2+2.2*MM
            for k, bh in enumerate([2.5,4.5,7.0]):
                c.rect(bx+k*3*MM, by, 2*MM, bh*MM, stroke=0, fill=1)
        y = y2
    c.setFillColor(TEXT)
    c.setFont(FONT, 7.5)
    _draw_wrapped(c, spec.get('competencia',''), x+label_w+4*MM, y_top-5.8*MM, w-label_w-7*MM, 7.5, 8.5)
    yy = y_top-row_heights[0]-4.2*MM
    for cap in spec.get('capacidades', [])[:5]:
        c.setFont(FONT, 7.1)
        c.drawString(x+label_w+4*MM, yy, '•')
        yy = _draw_wrapped(c, str(cap), x+label_w+8*MM, yy, w-label_w-11*MM, 7.1, 7.7, max_lines=2)
        yy -= 0.8*MM
    perf_top = y_top-sum(row_heights[:2])-4*MM
    _draw_wrapped(c, spec.get('desempeno',''), x+label_w+4*MM, perf_top, w-label_w-7*MM, 7.2, 8.2, max_lines=3)
    return y_top-h-4*MM


def draw_section_title(c: canvas.Canvas, y_top: float, number: int | str, title: str, color=BLUE) -> float:
    x = 18*MM
    c.setFillColor(color)
    c.circle(x+4.5*MM, y_top-4.5*MM, 4.5*MM, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont(FONT_BOLD, 10)
    c.drawCentredString(x+4.5*MM, y_top-6.2*MM, str(number))
    c.setFillColor(color)
    c.setFont(FONT_BOLD, 10.5)
    c.drawString(x+12*MM, y_top-7*MM, title)
    return y_top-11*MM


def draw_theory_cards(c: canvas.Canvas, y_top: float, cards: list[dict[str, Any]]) -> float:
    x0 = 21*MM
    gap = 3*MM
    count = max(1, len(cards))
    total_w = PAGE_W - 42*MM
    card_w = (total_w - gap*(count-1))/count
    h = 31*MM
    palette = [BLUE, CYAN, GREEN, PURPLE]
    fills = [LIGHT_BLUE, colors.HexColor('#EDF8FA'), LIGHT_GREEN, LIGHT_PURPLE]
    for i, card in enumerate(cards):
        x = x0 + i*(card_w+gap)
        col = palette[i % len(palette)]
        _round_rect(c, x, y_top-h, card_w, h, col, colors.white, 5, 1)
        c.setFillColor(fills[i % len(fills)])
        c.circle(x+card_w/2, y_top-7.5*MM, 4.2*MM, stroke=0, fill=1)
        c.setStrokeColor(col)
        c.setLineWidth(1.2)
        c.circle(x+card_w/2, y_top-7.5*MM, 3*MM, stroke=1, fill=0)
        title = str(card.get('title',''))
        ts = _fit_font(title, card_w-8*MM, 8.4, 6.6)
        c.setFillColor(col)
        c.setFont(FONT_BOLD, ts)
        title_lines = _wrap(title, FONT_BOLD, ts, card_w-8*MM)[:2]
        yy = y_top-14*MM
        for line in title_lines:
            c.drawCentredString(x+card_w/2, yy, line)
            yy -= 3.5*MM
        body = str(card.get('body',''))
        c.setFillColor(TEXT)
        c.setFont(FONT, 6.9)
        body_lines = _wrap(body, FONT, 6.9, card_w-7*MM)[:4]
        yy = y_top-23*MM
        for line in body_lines:
            c.drawCentredString(x+card_w/2, yy, line)
            yy -= 3.2*MM
    return y_top-h-4*MM


def draw_operation_grid(c: canvas.Canvas, y_top: float, ops: list[dict[str, Any]]) -> float:
    x0 = 21*MM
    gap = 3*MM
    total_w = PAGE_W - 42*MM
    col_w = (total_w-gap)/2
    row_h = 35*MM
    palette = [BLUE, GREEN, CYAN, ORANGE]
    for i, op in enumerate(ops[:4]):
        row = i//2
        col = i%2
        x = x0 + col*(col_w+gap)
        y = y_top - (row+1)*row_h - row*gap
        color = palette[i]
        _round_rect(c, x, y, col_w, row_h, color, colors.white, 4, 1)
        c.setFillColor(color)
        c.setFont(FONT_BOLD, 9)
        c.drawString(x+3*MM, y+row_h-5.5*MM, str(op.get('title','')))
        yy = y+row_h-10*MM
        for bullet in op.get('bullets', [])[:2]:
            c.setFillColor(TEXT)
            c.setFont(FONT, 6.8)
            c.drawString(x+4*MM, yy, '•')
            yy = _draw_wrapped(c, str(bullet), x+8*MM, yy, col_w-12*MM, 6.8, 7.4, max_lines=2)
        example = op.get('example')
        if example:
            c.setFillColor(color)
            c.roundRect(x+3*MM, y+5*MM, 16*MM, 5*MM, 1.5, stroke=0, fill=1)
            c.setFillColor(colors.white)
            c.setFont(FONT_BOLD, 6.5)
            c.drawCentredString(x+11*MM, y+6.5*MM, 'Ejemplo:')
            if isinstance(example, list):
                _draw_rich_line(c, example, x+21*MM, y+7*MM, col_w-25*MM, 8)
            else:
                _draw_wrapped(c, str(example), x+21*MM, y+8*MM, col_w-25*MM, 7.3, 8)
    return y_top - 2*row_h - gap - 4*MM


def draw_bottom_three(c: canvas.Canvas, y_top: float, spec: dict[str, Any]) -> float:
    x0 = 21*MM
    gap = 2.5*MM
    total_w = PAGE_W - 42*MM
    widths = [64*MM, 66*MM, total_w-64*MM-66*MM-2*gap]
    titles = ['Palabras clave y pistas', '¿Para qué sirven en la vida real?', 'Consejo']
    colorset = [BLUE, BLUE, DARK_GREEN]
    h = 27*MM
    data = [spec.get('keywords', []), spec.get('applications', []), spec.get('tip','')]
    x = x0
    for i,w in enumerate(widths):
        _round_rect(c, x, y_top-h, w, h, colorset[i], colors.white, 4, 1)
        c.setFillColor(colorset[i])
        c.setFont(FONT_BOLD, 8.5)
        c.drawCentredString(x+w/2, y_top-5*MM, titles[i])
        if i == 0:
            xx = x+4*MM; yy = y_top-12*MM
            for kw in data[i][:8]:
                label = str(kw)
                bw = stringWidth(label, FONT_BOLD, 6.2)+6*MM
                if xx+bw > x+w-4*MM:
                    xx = x+4*MM; yy -= 6.5*MM
                _round_rect(c, xx, yy-4*MM, bw, 5*MM, colors.HexColor('#AFC3CF'), colors.white, 3, 0.7)
                c.setFillColor(MUTED); c.setFont(FONT_BOLD,6.2); c.drawCentredString(xx+bw/2, yy-2.3*MM, label)
                xx += bw+2*MM
        elif i == 1:
            yy = y_top-12*MM
            for app in data[i][:2]:
                _round_rect(c, x+3*MM, yy-8*MM, w-6*MM, 9*MM, colors.HexColor('#BFD9E2'), colors.HexColor('#F9FCFD'), 3, .6)
                _draw_wrapped(c, str(app), x+6*MM, yy-2.5*MM, w-12*MM, 6.2, 6.7, max_lines=2)
                yy -= 10.5*MM
        else:
            _draw_wrapped(c, str(data[i]), x+5*MM, y_top-11*MM, w-10*MM, 6.7, 7.3, max_lines=5)
        x += w+gap
    return y_top-h-3*MM


def draw_level_banner(c: canvas.Canvas, y_top: float, label: str, subtitle: str, color) -> float:
    x = 18*MM; w = PAGE_W - 36*MM; h = 9.5*MM
    _round_rect(c, x, y_top-h, w, h, color, colors.white, 3, 1)
    tag_w = 54*MM
    c.setFillColor(color); c.roundRect(x, y_top-h, tag_w, h, 3, stroke=0, fill=1)
    c.setFillColor(colors.white); c.setFont(FONT_BOLD, 10)
    c.drawString(x+8*MM, y_top-6.3*MM, label)
    c.setFillColor(color); c.setFont(FONT_BOLD, 7.7)
    c.drawString(x+tag_w+4*MM, y_top-6.2*MM, subtitle)
    return y_top-h-4*MM


def draw_grid(c: canvas.Canvas, x: float, y: float, w: float, h: float, spacing: float = 5*MM):
    c.setStrokeColor(GRID); c.setLineWidth(0.35)
    xx=x
    while xx <= x+w+0.1:
        c.line(xx,y,xx,y+h); xx+=spacing
    yy=y
    while yy <= y+h+0.1:
        c.line(x,yy,x+w,yy); yy+=spacing


def draw_exercise(c: canvas.Canvas, ex: dict[str, Any], x: float, y: float, w: float, h: float,
                  color=BLUE, challenge: bool = False):
    _round_rect(c, x, y, w, h, color, colors.white, 4, 1)
    c.setFillColor(color); c.roundRect(x+3*MM, y+h-10*MM, 8*MM, 8*MM, 3, stroke=0, fill=1)
    c.setFillColor(colors.white); c.setFont(FONT_BOLD, 10)
    c.drawCentredString(x+7*MM, y+h-7.5*MM, str(ex.get('number','')))
    cap = str(ex.get('capability',''))
    if cap:
        pill_w = max(18*MM, stringWidth('Cap.: '+cap, FONT_BOLD, 6.5)+5*MM)
        c.setFillColor(colors.HexColor('#F5F8F9')); c.setStrokeColor(color)
        c.roundRect(x+13*MM, y+h-9*MM, pill_w, 6*MM, 2, stroke=1, fill=1)
        c.setFillColor(color); c.setFont(FONT_BOLD, 6.5)
        c.drawCentredString(x+13*MM+pill_w/2, y+h-7.1*MM, 'Cap.: '+cap)
    yy = y+h-16*MM
    for rich in ex.get('prompt_lines', []):
        _draw_rich_line(c, rich, x+5*MM, yy, w-10*MM, 8.5)
        yy -= 8*MM
    prompt = ex.get('prompt')
    if prompt:
        yy = _draw_wrapped(c, str(prompt), x+5*MM, yy, w-10*MM, 8, 9.2, max_lines=5)
    space = ex.get('answer_space','blank')
    space_y = y+5*MM
    space_h = max(10*MM, yy-space_y-2*MM)
    if space == 'grid':
        draw_grid(c, x+5*MM, space_y, w-10*MM, space_h, 4.8*MM)
    elif space == 'lines':
        c.setStrokeColor(colors.HexColor('#AAB3B8')); c.setLineWidth(.6)
        lyy = space_y+space_h-3*MM
        while lyy>space_y+1*MM:
            c.line(x+6*MM, lyy, x+w-6*MM, lyy); lyy -= 7*MM
    elif space == 'split_grid':
        mid = x+w/2
        c.setFillColor(MUTED); c.setFont(FONT_BOLD,7)
        c.drawString(x+5*MM, space_y+space_h-3*MM, 'A =')
        c.drawString(mid+3*MM, space_y+space_h-3*MM, 'B =')
        draw_grid(c, x+5*MM, space_y, w/2-9*MM, space_h-6*MM, 4.8*MM)
        draw_grid(c, mid+3*MM, space_y, w/2-8*MM, space_h-6*MM, 4.8*MM)


def draw_practice_two_columns(c: canvas.Canvas, y_top: float, exercises: list[dict[str, Any]], color=BLUE) -> float:
    x0=18*MM; gap=3*MM; total_w=PAGE_W-36*MM; col_w=(total_w-gap)/2
    bottom = 31*MM
    avail = y_top-bottom
    rows = max(1, (len(exercises)+1)//2)
    row_gap = 3*MM
    row_h = (avail - (rows-1)*row_gap)/rows
    for i,ex in enumerate(exercises):
        row=i//2; col=i%2
        x=x0+col*(col_w+gap)
        y=y_top-(row+1)*row_h-row*row_gap
        draw_exercise(c, ex, x,y,col_w,row_h,color)
    return bottom


def draw_intermediate_challenge(c: canvas.Canvas, y_top: float, intermediate: list[dict[str, Any]], challenge: list[dict[str, Any]]) -> float:
    x0=5*MM; gap=3*MM; total_w=PAGE_W-10*MM; left_w=102*MM; right_w=total_w-left_w-gap
    bottom=96*MM
    c.setFillColor(GREEN); c.roundRect(x0+28*MM, y_top-8*MM, 52*MM, 7*MM, 3, stroke=0, fill=1)
    c.setFillColor(colors.white); c.setFont(FONT_BOLD,9); c.drawCentredString(x0+54*MM,y_top-6*MM,'NIVEL INTERMEDIO')
    rx=x0+left_w+gap
    c.setFillColor(PURPLE); c.roundRect(rx+18*MM, y_top-8*MM, 48*MM, 7*MM, 3, stroke=0, fill=1)
    c.setFillColor(colors.white); c.drawCentredString(rx+42*MM,y_top-6*MM,'NIVEL RETO')
    content_top=y_top-12*MM
    ih=(content_top-bottom-3*3*MM)/max(1,len(intermediate))
    for i,ex in enumerate(intermediate):
        y=content_top-(i+1)*ih-i*3*MM
        draw_exercise(c,ex,x0,y,left_w,ih,GREEN)
    ch=(content_top-bottom-3*MM)/max(1,len(challenge))
    for i,ex in enumerate(challenge):
        y=content_top-(i+1)*ch-i*3*MM
        draw_exercise(c,ex,rx,y,right_w,ch,PURPLE,True)
    return bottom


def draw_self_assessment(c: canvas.Canvas, y_top: float, rows: list[str], reinforce: list[str], feelings: list[str]) -> float:
    x=8*MM; w=PAGE_W-16*MM
    h=54*MM
    y=y_top-h
    _round_rect(c,x,y,w,h,BLUE,colors.white,3,1)
    row_h=7*MM
    label_w=85*MM
    col_w=(w-label_w)/3
    c.setFillColor(colors.HexColor('#F3F7F9')); c.rect(x,y+h-row_h,w,row_h,stroke=0,fill=1)
    c.setFillColor(BLUE); c.setFont(FONT_BOLD,8.5); c.drawString(x+7*MM,y+h-5*MM,'AUTOEVALUACIÓN')
    for j,(lab,col) in enumerate([('Siempre',GREEN),('A veces',YELLOW),('Necesito reforzar',RED)]):
        c.setFillColor(col); c.setFont(FONT_BOLD,7.5); c.drawCentredString(x+label_w+col_w*(j+.5),y+h-5*MM,lab)
    cur_y=y+h-row_h
    item_h=5.6*MM
    c.setStrokeColor(colors.HexColor('#A7BCC8')); c.setLineWidth(.5)
    for r in rows[:5]:
        cur_y-=item_h
        c.line(x,cur_y,x+w,cur_y)
        c.setFillColor(TEXT); c.setFont(FONT,6.7); c.drawString(x+7*MM,cur_y+1.7*MM,r)
        for j in range(3):
            bx=x+label_w+col_w*j+col_w/2-2*MM
            by=cur_y+1.2*MM
            c.rect(bx,by,4*MM,4*MM,stroke=1,fill=0)
    for j in range(4):
        xx=x+label_w+col_w*j
        c.line(xx,cur_y,xx,y+h)
    cur_y-=6.7*MM
    c.setFillColor(BLUE); c.setFont(FONT_BOLD,7.3); c.drawString(x+4*MM,cur_y+2.1*MM,'Necesito reforzar más:')
    xx=x+53*MM
    c.setFillColor(TEXT); c.setFont(FONT,6.7)
    for item in reinforce[:4]:
        c.rect(xx,cur_y+1.3*MM,3.5*MM,3.5*MM,stroke=1,fill=0); c.drawString(xx+5*MM,cur_y+2.1*MM,item); xx += 32*MM
    cur_y-=6.7*MM
    c.setFillColor(BLUE); c.setFont(FONT_BOLD,7.3); c.drawString(x+4*MM,cur_y+2.1*MM,'Hoy siento que:')
    xx=x+43*MM
    c.setFillColor(TEXT); c.setFont(FONT,6.7)
    for item in feelings[:3]:
        c.rect(xx,cur_y+1.3*MM,3.5*MM,3.5*MM,stroke=1,fill=0); c.drawString(xx+5*MM,cur_y+2.1*MM,item); xx += 42*MM
    return y-2*MM


def draw_footer(c: canvas.Canvas):
    c.drawImage(FOOTER_IMG, 4*MM, 5*MM, width=202*MM, height=24.2*MM, mask='auto', preserveAspectRatio=True)


def generate_ficha_pdf(spec: dict[str, Any], output_path: str | Path) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(output_path), pagesize=A4)
    c.setTitle(spec.get('title','Ficha SRC'))
    grade = str(spec.get('grade',''))
    sections = spec.get('sections',['A','B'])
    year = str(spec.get('year','2026'))
    curriculum = spec.get('curriculum',{})
    pages = spec.get('pages',[])
    for page in pages:
        kind = page.get('kind','practice_easy')
        title = page.get('title') or spec.get('title','FICHA DE MATEMÁTICA')
        if kind == 'practice_levels' and page.get('continuation_only', True):
            y = PAGE_H - 8*MM
        else:
            y = draw_institutional_header(c,title,grade,sections,year)
            y = draw_curriculum_block(c,y,curriculum,compact=page.get('compact_curriculum', kind!='theory'))
        if kind == 'theory':
            y = draw_section_title(c,y,1,page.get('section1_title','¿Qué debo observar primero?'),BLUE)
            y = draw_theory_cards(c,y,page.get('cards',[]))
            y = draw_section_title(c,y,2,page.get('section2_title','Conceptos y procedimientos'),BLUE)
            y = draw_operation_grid(c,y,page.get('operations',[]))
            draw_bottom_three(c,y,page)
        elif kind == 'practice_easy':
            y = draw_level_banner(c,y,page.get('level_label','Nivel fácil'),page.get('subtitle','Reconoce el tipo de procedimiento y verifica tus datos antes de empezar.'),BLUE)
            draw_practice_two_columns(c,y,page.get('exercises',[]),BLUE)
        elif kind == 'practice_levels':
            band_h=8*MM
            c.setFillColor(DARK_GREEN); c.roundRect(4*MM,y-band_h,PAGE_W-8*MM,band_h,3,stroke=0,fill=1)
            c.setFillColor(colors.white); c.setFont(FONT_BOLD,9)
            c.drawCentredString(PAGE_W/2,y-5.5*MM,page.get('continuation_title','Continuación - Nivel intermedio y reto'))
            y-=12*MM
            if page.get('reminder'):
                _round_rect(c,7*MM,y-9*MM,PAGE_W-14*MM,9*MM,colors.HexColor('#A7BCC8'),colors.white,3,.8)
                c.setFillColor(GREEN); c.circle(14*MM,y-4.5*MM,2.7*MM,stroke=1,fill=0)
                _draw_wrapped(c,page['reminder'],20*MM,y-6*MM,PAGE_W-30*MM,7.1,8)
                y-=13*MM
            bottom = draw_intermediate_challenge(c,y,page.get('intermediate',[]),page.get('challenge',[]))
            draw_self_assessment(c,bottom-2*MM,page.get('self_assessment_rows',[]),page.get('reinforce',[]),page.get('feelings',[]))
        else:
            raise ValueError(f'Unsupported page kind: {kind}')
        draw_footer(c)
        c.showPage()
    c.save()
    return output_path
