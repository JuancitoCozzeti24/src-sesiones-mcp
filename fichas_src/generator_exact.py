from __future__ import annotations

from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth

from .assets import header_bytes, footer_bytes

PW, PH = A4
MM = 72 / 25.4

DG = colors.HexColor('#005B46')
BLUE = colors.HexColor('#0B5D82')
CYAN = colors.HexColor('#1391AE')
GREEN = colors.HexColor('#3D8D3B')
PURPLE = colors.HexColor('#7D2B91')
ORANGE = colors.HexColor('#E96A17')
OLIVE = colors.HexColor('#6E8A36')
TEXT = colors.HexColor('#151515')
GRID = colors.HexColor('#E0E5E8')
LIGHT = colors.HexColor('#F7FAFB')
F = 'Helvetica'
FB = 'Helvetica-Bold'


class Ctx:
    def __init__(self, c: canvas.Canvas, w: float, h: float):
        self.c = c
        self.w = w
        self.h = h

    def x(self, p: float) -> float:
        return p * PW / self.w

    def y(self, p: float) -> float:
        return PH - p * PH / self.h

    def wv(self, p: float) -> float:
        return p * PW / self.w

    def hv(self, p: float) -> float:
        return p * PH / self.h


def rr(ctx: Ctx, x1, y1, x2, y2, stroke, fill=colors.white, r=10, lw=1):
    c = ctx.c
    c.setStrokeColor(stroke)
    c.setFillColor(fill)
    c.setLineWidth(lw)
    c.roundRect(ctx.x(x1), ctx.y(y2), ctx.wv(x2 - x1), ctx.hv(y2 - y1), r, stroke=1, fill=1)


def line(ctx: Ctx, x1, y1, x2, y2, col, lw=1):
    c = ctx.c
    c.setStrokeColor(col)
    c.setLineWidth(lw)
    c.line(ctx.x(x1), ctx.y(y1), ctx.x(x2), ctx.y(y2))


def txt(ctx: Ctx, s, x, y, size=8, font=F, col=TEXT):
    c = ctx.c
    c.setFillColor(col)
    c.setFont(font, size)
    c.drawString(ctx.x(x), ctx.y(y), str(s))


def center(ctx: Ctx, s, x1, x2, y, size=8, font=F, col=TEXT):
    c = ctx.c
    c.setFillColor(col)
    c.setFont(font, size)
    c.drawCentredString((ctx.x(x1) + ctx.x(x2)) / 2, ctx.y(y), str(s))


def wrap(text, font, size, maxw):
    words = str(text).split()
    res = []
    cur = ''
    for word in words:
        test = (cur + ' ' + word).strip()
        if not cur or stringWidth(test, font, size) <= maxw:
            cur = test
        else:
            res.append(cur)
            cur = word
    if cur:
        res.append(cur)
    return res or ['']


def paragraph(ctx: Ctx, s, x, y, w, size=8, font=F, col=TEXT, lead=None, max_lines=None, cent=False):
    lead = lead or size * 1.22
    lines = wrap(s, font, size, ctx.wv(w))
    if max_lines:
        lines = lines[:max_lines]
    for part in lines:
        if cent:
            center(ctx, part, x, x + w, y, size, font, col)
        else:
            txt(ctx, part, x, y, size, font, col)
        y += lead * ctx.h / PH
    return y


def circle_num(ctx: Ctx, n, cx, cy, col, rad=20):
    c = ctx.c
    c.setFillColor(col)
    c.circle(ctx.x(cx), ctx.y(cy), ctx.wv(rad), stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont(FB, 12)
    c.drawCentredString(ctx.x(cx), ctx.y(cy + 5), str(n))


def simple_icon(ctx: Ctx, kind, cx, cy, col):
    c = ctx.c
    c.setStrokeColor(col)
    c.setFillColor(col)
    if kind == 'target':
        for r in (13, 8, 3):
            c.circle(ctx.x(cx), ctx.y(cy), ctx.wv(r), stroke=1, fill=0)
        line(ctx, cx + 9, cy - 9, cx + 18, cy - 18, col, 2)
    elif kind == 'head':
        c.circle(ctx.x(cx - 2), ctx.y(cy), ctx.wv(11), stroke=0, fill=1)
        c.setFillColor(OLIVE)
        c.circle(ctx.x(cx + 2), ctx.y(cy - 2), ctx.wv(4), stroke=0, fill=1)
    elif kind == 'bars':
        for i, h in enumerate((8, 14, 22)):
            c.rect(ctx.x(cx - 11 + i * 9), ctx.y(cy + h / 2), ctx.wv(6), ctx.hv(h), stroke=0, fill=1)
        line(ctx, cx - 12, cy - 10, cx + 14, cy - 26, col, 2)
    elif kind == 'grid':
        c.setFillColor(colors.white)
        c.setStrokeColor(col)
        for i in range(3):
            for j in range(3):
                c.rect(ctx.x(cx - 14 + j * 10), ctx.y(cy + 14 - i * 10), ctx.wv(7), ctx.hv(7), stroke=1, fill=0)
    elif kind == 'pin':
        c.circle(ctx.x(cx), ctx.y(cy - 3), ctx.wv(10), stroke=0, fill=1)
        c.setFillColor(colors.white)
        c.circle(ctx.x(cx), ctx.y(cy - 3), ctx.wv(4), stroke=0, fill=1)
        c.setFillColor(col)
        p = c.beginPath()
        p.moveTo(ctx.x(cx - 7), ctx.y(cy + 5))
        p.lineTo(ctx.x(cx), ctx.y(cy + 20))
        p.lineTo(ctx.x(cx + 7), ctx.y(cy + 5))
        p.close()
        c.drawPath(p, stroke=0, fill=1)
    elif kind == 'puzzle':
        c.roundRect(ctx.x(cx - 13), ctx.y(cy + 13), ctx.wv(25), ctx.hv(25), 2, stroke=0, fill=1)
        c.setFillColor(colors.white)
        c.circle(ctx.x(cx), ctx.y(cy - 13), ctx.wv(4), stroke=0, fill=1)
        c.circle(ctx.x(cx + 13), ctx.y(cy), ctx.wv(4), stroke=0, fill=1)
    elif kind == 'bulb':
        c.setFillColor(colors.white)
        c.setStrokeColor(col)
        c.setLineWidth(2)
        c.circle(ctx.x(cx), ctx.y(cy), ctx.wv(15), stroke=1, fill=0)
        line(ctx, cx - 8, cy + 15, cx + 8, cy + 15, col, 2)


def draw_header(ctx: Ctx, header, title, grade, practice=False):
    c = ctx.c
    c.drawImage(header, 7 * MM, PH - 26 * MM, width=111 * MM, height=18.5 * MM, preserveAspectRatio=True, mask='auto')
    center(ctx, title.upper(), 145, 955, 147 if not practice else 157, 23 if not practice else 18.5, FB, DG)

    row_y = 190 if not practice else 207
    box_y = 197 if not practice else 216
    txt(ctx, 'Nombre:', 52, row_y, 9.2, FB)
    line(ctx, 122, row_y + 3, 380, row_y + 3, colors.black, .6)

    txt(ctx, 'Sección:', 408 if not practice else 430, row_y, 8.8, FB)
    txt(ctx, grade, 488 if not practice else 510, row_y, 8.8, FB)
    if practice:
        section_boxes = [(540, 'A'), (607, 'B')]
    else:
        section_boxes = [(515, 'A'), (583, 'B')]
    for x, label in section_boxes:
        c.setStrokeColor(colors.black)
        c.rect(ctx.x(x), ctx.y(box_y), ctx.wv(20), ctx.hv(20), stroke=1, fill=0)
        txt(ctx, label, x + 27, row_y, 9, FB)

    txt(ctx, 'Fecha:', 681 if not practice else 704, row_y, 9.2, FB)
    date_boxes = [(744, 52), (821, 52), (891, 60)] if not practice else [(770, 52), (844, 52), (914, 60)]
    for x, w in date_boxes:
        c.setStrokeColor(colors.HexColor('#666666'))
        c.roundRect(ctx.x(x), ctx.y(box_y + 1), ctx.wv(w), ctx.hv(23), 3, stroke=1, fill=0)
    slash1 = 801 if not practice else 828
    slash2 = 876 if not practice else 902
    txt(ctx, '/', slash1, row_y, 9, FB)
    txt(ctx, '/', slash2, row_y, 9, FB)
    year_x1, year_x2 = (891, 951) if not practice else (914, 974)
    center(ctx, '2026', year_x1, year_x2, row_y, 8.8, FB)


def curricular_full(ctx: Ctx, cur):
    x1, x2 = 52, 997
    y1, y2 = 209, 408
    rr(ctx, x1, y1, x2, y2, OLIVE, colors.white, 7, 1)
    left = 320
    line(ctx, left, y1, left, y2, OLIVE, .8)
    line(ctx, x1, 250, x2, 250, OLIVE, .8)
    line(ctx, x1, 342, x2, 342, OLIVE, .8)
    for ya, yb in ((209, 250), (250, 342), (342, 408)):
        ctx.c.setFillColor(colors.HexColor('#EFF2E8'))
        ctx.c.rect(ctx.x(137), ctx.y(yb), ctx.wv(left - 137), ctx.hv(yb - ya), stroke=0, fill=1)
        ctx.c.setFillColor(OLIVE)
        ctx.c.rect(ctx.x(52), ctx.y(yb), ctx.wv(85), ctx.hv(yb - ya), stroke=0, fill=1)
    simple_icon(ctx, 'target', 95, 230, colors.white)
    simple_icon(ctx, 'head', 95, 293, colors.white)
    simple_icon(ctx, 'bars', 95, 374, colors.white)
    txt(ctx, 'Competencia:', 164, 233, 9, FB, DG)
    txt(ctx, 'Capacidades:', 164, 294, 9, FB, DG)
    txt(ctx, 'Desempeño', 164, 368, 9, FB, DG)
    txt(ctx, 'precisado:', 164, 386, 9, FB, DG)
    paragraph(ctx, cur['competencia'], 340, 236, 620, 8.7, max_lines=2)
    y = 270
    for cap in cur.get('capacidades', [])[:4]:
        txt(ctx, '•', 341, y, 8)
        paragraph(ctx, cap, 358, y, 608, 7.9, max_lines=2)
        y += 21
    paragraph(ctx, cur['desempeno'], 340, 363, 620, 8.2, max_lines=3)


def curricular_compact(ctx: Ctx, cur):
    rr(ctx, 48, 234, 974, 337, OLIVE, colors.white, 7, 1)
    line(ctx, 48, 281, 974, 281, OLIVE, .8)
    ctx.c.setFillColor(OLIVE)
    ctx.c.rect(ctx.x(48), ctx.y(281), ctx.wv(72), ctx.hv(47), stroke=0, fill=1)
    simple_icon(ctx, 'target', 84, 257, colors.white)
    txt(ctx, 'Competencia:', 138, 261, 8.6, FB, DG)
    paragraph(ctx, cur['competencia'], 255, 261, 700, 8.1, max_lines=2)
    txt(ctx, 'Capacidades:', 68, 313, 7.8, FB, DG)
    paragraph(ctx, '   |   '.join(cur.get('capacidades_abrev', [])), 168, 313, 795, 7, max_lines=2)


def footer(ctx: Ctx, footer_img):
    ctx.c.drawImage(footer_img, 4 * MM, 5 * MM, width=202 * MM, height=24.2 * MM, preserveAspectRatio=True, mask='auto')


def static_page1(ctx: Ctx):
    rr(ctx, 48, 420, 998, 646, BLUE, colors.white, 8, 1)
    circle_num(ctx, 1, 71, 442, BLUE, 20)
    cards = [
        (65, 472, 283, 632, BLUE, 'grid'),
        (303, 472, 491, 632, CYAN, 'pin'),
        (511, 472, 721, 632, GREEN, 'puzzle'),
        (742, 472, 976, 632, PURPLE, 'grid'),
    ]
    for x1, y1, x2, y2, col, icon in cards:
        rr(ctx, x1, y1, x2, y2, col, colors.white, 7, .8)
        simple_icon(ctx, icon, x1 + 32, y1 + 39, col)
    for x, col in ((284, BLUE), (492, CYAN), (722, GREEN)):
        line(ctx, x, 551, x + 17, 551, col, 3)
        p = ctx.c.beginPath()
        p.moveTo(ctx.x(x + 17), ctx.y(545))
        p.lineTo(ctx.x(x + 29), ctx.y(551))
        p.lineTo(ctx.x(x + 17), ctx.y(557))
        p.close()
        ctx.c.setFillColor(col)
        ctx.c.drawPath(p, stroke=0, fill=1)

    rr(ctx, 48, 655, 998, 1152, BLUE, colors.white, 8, 1)
    circle_num(ctx, 2, 72, 677, BLUE, 20)
    for x1, y1, x2, y2, col in (
        (65, 694, 495, 884, BLUE),
        (507, 694, 977, 884, GREEN),
        (65, 891, 495, 1147, CYAN),
        (507, 891, 977, 1147, ORANGE),
    ):
        rr(ctx, x1, y1, x2, y2, col, colors.white, 7, .8)

    rr(ctx, 48, 1157, 383, 1330, BLUE, colors.white, 6, .8)
    circle_num(ctx, 3, 72, 1179, BLUE, 18)
    txt(ctx, 'Palabras clave y pistas', 101, 1185, 9.5, FB, BLUE)

    rr(ctx, 388, 1157, 751, 1330, BLUE, colors.white, 6, .8)
    circle_num(ctx, 4, 412, 1179, BLUE, 18)
    txt(ctx, '¿Para qué sirven en la vida real?', 440, 1185, 9.5, FB, BLUE)

    rr(ctx, 758, 1157, 998, 1330, GREEN, colors.HexColor('#F3F8EF'), 6, .8)
    ctx.c.setFillColor(DG)
    ctx.c.rect(ctx.x(758), ctx.y(1190), ctx.wv(240), ctx.hv(33), stroke=0, fill=1)
    center(ctx, 'Consejo', 758, 998, 1183, 10, FB, colors.white)
    simple_icon(ctx, 'bulb', 800, 1250, GREEN)


def static_page2(ctx: Ctx):
    rr(ctx, 48, 360, 974, 400, BLUE, colors.white, 7, 1)
    ctx.c.setFillColor(BLUE)
    ctx.c.roundRect(ctx.x(48), ctx.y(400), ctx.wv(280), ctx.hv(40), 7, stroke=0, fill=1)
    simple_icon(ctx, 'bars', 82, 380, colors.white)
    txt(ctx, 'Nivel fácil', 108, 388, 11, FB, colors.white)
    boxes = [
        (48, 410, 502, 709), (519, 410, 974, 709),
        (48, 721, 502, 1018), (519, 721, 974, 1018),
        (48, 1028, 502, 1306), (519, 1028, 974, 1306),
    ]
    for i, (x1, y1, x2, y2) in enumerate(boxes, 1):
        rr(ctx, x1, y1, x2, y2, BLUE, colors.white, 7, 1)
        circle_num(ctx, i, x1 + 28, y1 + 25, BLUE, 15)


def grid(ctx: Ctx, x1, y1, x2, y2, step=24):
    x = x1
    while x <= x2:
        line(ctx, x, y1, x, y2, GRID, .35)
        x += step
    y = y1
    while y <= y2:
        line(ctx, x1, y, x2, y, GRID, .35)
        y += step


def response_spaces(ctx: Ctx):
    for rect in ((72, 546, 477, 686), (543, 546, 949, 686), (72, 839, 477, 1003), (543, 839, 949, 1003)):
        grid(ctx, *rect)
    grid(ctx, 67, 1190, 242, 1287)
    grid(ctx, 275, 1190, 477, 1287)
    txt(ctx, 'A =', 67, 1181, 8.5)
    txt(ctx, 'B =', 275, 1181, 8.5)
    for y in (1162, 1195, 1228, 1261):
        line(ctx, 552, y, 955, y, colors.HexColor('#7E858A'), .55)


def static_page3(ctx: Ctx):
    rr(ctx, 8, 17, 1047, 51, DG, DG, 8, 0)
    center(ctx, 'Continuación - Nivel intermedio y reto', 8, 1047, 42, 12, FB, colors.white)
    rr(ctx, 15, 52, 1040, 96, BLUE, colors.white, 5, .8)
    ctx.c.setStrokeColor(GREEN)
    ctx.c.circle(ctx.x(55), ctx.y(74), ctx.wv(12), stroke=1, fill=0)
    txt(ctx, '✓', 47, 79, 12, FB, GREEN)

    rr(ctx, 14, 123, 505, 988, GREEN, colors.white, 7, .8)
    rr(ctx, 518, 123, 1007, 988, PURPLE, colors.white, 7, .8)
    for y in (363, 597, 809):
        line(ctx, 14, y, 505, y, GREEN, .8)
    line(ctx, 518, 661, 1007, 661, PURPLE, .8)

    ctx.c.setFillColor(GREEN)
    ctx.c.roundRect(ctx.x(158), ctx.y(141), ctx.wv(225), ctx.hv(34), 7, stroke=0, fill=1)
    center(ctx, '●  NIVEL INTERMEDIO', 158, 383, 133, 10, FB, colors.white)
    ctx.c.setFillColor(PURPLE)
    ctx.c.roundRect(ctx.x(629), ctx.y(141), ctx.wv(252), ctx.hv(34), 7, stroke=0, fill=1)
    center(ctx, '▲  NIVEL RETO', 629, 881, 133, 10, FB, colors.white)

    for n, cy in ((7, 172), (8, 397), (9, 630), (10, 844)):
        circle_num(ctx, n, 44, cy, GREEN, 20)
    for n, cy in ((11, 172), (12, 700)):
        circle_num(ctx, n, 548, cy, PURPLE, 20)

    x1, x2 = 42, 979
    y1, y2 = 1008, 1328
    rr(ctx, x1, y1, x2, y2, BLUE, colors.white, 5, .8)
    for y in (1045, 1082, 1119, 1157, 1195, 1234, 1278):
        line(ctx, x1, y, x2, y, BLUE, .65)
    for x in (428, 613, 795):
        line(ctx, x, 1008, x, 1234, BLUE, .65)
    txt(ctx, 'AUTOEVALUACIÓN', 140, 1033, 9.3, FB, BLUE)
    txt(ctx, 'Siempre', 487, 1033, 8.6, FB, GREEN)
    txt(ctx, 'A veces', 677, 1033, 8.6, FB, colors.HexColor('#E8A821'))
    txt(ctx, 'Necesito reforzar', 815, 1033, 8.6, FB, colors.HexColor('#D6302F'))
    for cy in (1063, 1100, 1138, 1176, 1214):
        for cx in (520, 703, 886):
            ctx.c.setStrokeColor(colors.HexColor('#888888'))
            ctx.c.rect(ctx.x(cx - 10), ctx.y(cy + 10), ctx.wv(20), ctx.hv(20), stroke=1, fill=0)


def page1(ctx: Ctx, spec, p):
    draw_header(ctx, spec['_header'], spec['title'], spec.get('grade', '2.º'))
    curricular_full(ctx, spec['curriculum'])
    static_page1(ctx)
    txt(ctx, p.get('section1_title', '¿Qué debo observar primero?'), 102, 453, 12, FB, BLUE)
    cfg = [(130, 520, 140, BLUE), (374, 514, 105, CYAN), (594, 520, 118, GREEN), (816, 520, 145, PURPLE)]
    body_cfg = [(112, 566, 165), (329, 562, 150), (524, 565, 188), (754, 562, 213)]
    for i, card in enumerate(p.get('cards', [])[:4]):
        x, y, w, col = cfg[i]
        paragraph(ctx, card.get('title', ''), x, y, w, 8.5, FB, col, max_lines=2, cent=True)
        bx, by, bw = body_cfg[i]
        paragraph(ctx, card.get('body', ''), bx, by, bw, 7.3, max_lines=5, cent=True)

    txt(ctx, 'Operaciones básicas', 101, 682, 11, FB, BLUE)
    boxes = [(78, 714, BLUE), (524, 714, GREEN), (78, 910, CYAN), (524, 910, ORANGE)]
    for i, op in enumerate(p.get('operations', [])[:4]):
        x, y, col = boxes[i]
        txt(ctx, op.get('title', ''), x, y, 10, FB, col)
        yy = y + 28
        for bullet in op.get('bullets', [])[:2]:
            txt(ctx, '•', x + 12, yy, 7.3)
            paragraph(ctx, bullet, x + 26, yy, 360, 7.3, max_lines=2)
            yy += 18
        label_y = 774 if i < 2 else 976
        ctx.c.setFillColor(col)
        ctx.c.roundRect(ctx.x(x), ctx.y(label_y + 18), ctx.wv(65), ctx.hv(18), 3, stroke=0, fill=1)
        center(ctx, 'Ejemplo:', x, x + 65, label_y + 7, 6.8, FB, colors.white)
        ex_y1, ex_y2 = ((805, 870) if i < 2 else (1030, 1128))
        rr(ctx, x + 14, ex_y1, x + 394, ex_y2, colors.HexColor('#B8CDD6'), LIGHT, 5, .5)
        ex_y = 822 if i < 2 else 1048
        for j, item in enumerate(op.get('example_lines', [])[:3]):
            paragraph(ctx, item, x + 28, ex_y + j * 28, 350, 7.5, max_lines=2)

    xx, yy = 75, 1218
    for kw in p.get('keywords', [])[:8]:
        bw = max(55, min(130, 25 + len(str(kw)) * 6.5))
        rr(ctx, xx, yy, xx + bw, yy + 22, colors.HexColor('#9DB4C2'), colors.white, 5, .5)
        center(ctx, kw, xx, xx + bw, yy + 15, 6.3, FB, BLUE)
        xx += bw + 10
        if xx > 330:
            xx = 87
            yy += 42
    apps = p.get('applications', [])
    if apps:
        paragraph(ctx, apps[0], 488, 1218, 245, 7, FB, CYAN, max_lines=4)
    if len(apps) > 1:
        paragraph(ctx, apps[1], 488, 1280, 245, 7, FB, GREEN, max_lines=4)
    paragraph(ctx, p.get('tip', ''), 846, 1220, 130, 7, max_lines=7, cent=True)
    footer(ctx, spec['_footer'])


def page2(ctx: Ctx, spec, p):
    draw_header(ctx, spec['_header'], spec.get('practice_title', 'PRÁCTICA DE AULA - ' + spec['title']), spec.get('grade', '2.º'), True)
    curricular_compact(ctx, spec['curriculum'])
    static_page2(ctx)
    paragraph(ctx, p.get('subtitle', ''), 345, 385, 610, 8, FB, BLUE, max_lines=1)
    response_spaces(ctx)
    positions = [(106, 445, 360), (575, 445, 370), (106, 757, 360), (575, 757, 370), (106, 1068, 360), (575, 1068, 370)]
    for i, ex in enumerate(p.get('exercises', [])[:6]):
        x, y, w = positions[i]
        txt(ctx, 'Cap.: ' + str(ex.get('capability', '')), x, y, 8, FB, BLUE)
        paragraph(ctx, ex.get('prompt', ''), x, y + 42, w, 8.3, max_lines=4)
    footer(ctx, spec['_footer'])


def page3(ctx: Ctx, spec, p):
    static_page3(ctx)
    paragraph(ctx, p.get('reminder', ''), 82, 78, 900, 8, max_lines=1)
    positions = [(73, 177, 420), (73, 405, 420), (73, 630, 420), (73, 846, 420)]
    for i, ex in enumerate(p.get('intermediate', [])[:4]):
        x, y, w = positions[i]
        rr(ctx, x, y - 18, x + 90, y + 9, GREEN, colors.HexColor('#EFF8ED'), 4, .7)
        txt(ctx, 'Cap.: ' + str(ex.get('capability', '')), x + 7, y, 7.7, FB, GREEN)
        paragraph(ctx, ex.get('prompt', ''), x + 100, y, w - 100, 8, max_lines=5)

    challenge_positions = [(583, 177, 395), (583, 707, 395)]
    for i, ex in enumerate(p.get('challenge', [])[:2]):
        x, y, w = challenge_positions[i]
        rr(ctx, x, y - 18, x + 115, y + 9, PURPLE, colors.HexColor('#F6EEF8'), 4, .7)
        txt(ctx, 'Cap.: ' + str(ex.get('capability', '')), x + 7, y, 7.7, FB, PURPLE)
        py = y + 45
        paragraph(ctx, ex.get('prompt', ''), x, py, w, 8, max_lines=8)
        sub_y = [py + 120, py + 285] if i == 0 else [py + 105, py + 190]
        for j, (sub, sy) in enumerate(zip(ex.get('subquestions', [])[:2], sub_y)):
            txt(ctx, chr(97 + j) + ')', x, sy, 8.7, FB, PURPLE)
            paragraph(ctx, sub, x + 28, sy, w - 28, 8, max_lines=3)

    rows = p.get('self_assessment_rows', [])
    for label, y in zip(rows[:5], (1067, 1104, 1142, 1179, 1217)):
        paragraph(ctx, label, 120, y, 300, 7.4, max_lines=1)

    txt(ctx, 'Necesito reforzar más:', 63, 1259, 8, FB, BLUE)
    x = 275
    for item in p.get('reinforce', [])[:4]:
        ctx.c.setStrokeColor(colors.HexColor('#777777'))
        ctx.c.rect(ctx.x(x), ctx.y(1269), ctx.wv(18), ctx.hv(18), stroke=1, fill=0)
        paragraph(ctx, item, x + 28, 1261, 125, 7.3, max_lines=1)
        x += 160

    txt(ctx, 'Hoy siento que:', 63, 1307, 8, FB, BLUE)
    x = 230
    for item in p.get('feelings', [])[:3]:
        ctx.c.setStrokeColor(colors.HexColor('#777777'))
        ctx.c.rect(ctx.x(x), ctx.y(1317), ctx.wv(18), ctx.hv(18), stroke=1, fill=0)
        paragraph(ctx, item, x + 28, 1308, 155, 7.3, max_lines=1)
        x += 195
    footer(ctx, spec['_footer'])


def generate_ficha_pdf(spec: dict, output_path: str | Path) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(output_path), pagesize=A4)
    c.setTitle(spec.get('title', 'Ficha SRC'))
    enriched = dict(spec)
    enriched['_header'] = ImageReader(header_bytes())
    enriched['_footer'] = ImageReader(footer_bytes())
    pages = enriched.get('pages', [])
    if len(pages) != 3:
        raise ValueError('SRC_FICHA_MAESTRA_V1 requiere exactamente 3 páginas: teoría, práctica fácil y niveles intermedio/reto.')
    for idx, (w, h) in enumerate(((1086, 1448), (1086, 1448), (1055, 1491))):
        ctx = Ctx(c, w, h)
        (page1, page2, page3)[idx](ctx, enriched, pages[idx])
        c.showPage()
    c.save()
    return output_path
