#!/usr/bin/env python3
"""Genera el logo del proyecto: estilo terminal hacker, ANSI-art, alta calidad."""
import math, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1200, 400
BG   = (10, 12, 18)

FONT = "/usr/share/fonts/TTF/DejaVuSansMono.ttf"
try:
    FONT_BOLD = FONT.replace("DejaVuSansMono.ttf", "DejaVuSansMono-Bold.ttf")
    ImageFont.truetype(FONT_BOLD, 10)
except Exception:
    FONT_BOLD = FONT

GREEN      = (80, 255, 100)
GREEN_DIM  = (30, 100, 40)
RED        = (220, 50, 50)
CYAN       = (60, 220, 220)
YELLOW     = (255, 215, 60)
ORANGE     = (255, 140, 0)
WHITE      = (220, 225, 235)
GRAY       = (70, 80, 90)
DARKGRAY   = (25, 30, 38)

img  = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(img)

# ── 1. Fondo: matriz de caracteres ────────────────────────────────────────────
f_tiny = ImageFont.truetype(FONT, 11)
matrix_chars = "01アイウエオカキクケコサシスセソ10"
random.seed(42)
for col in range(0, W, 14):
    for row in range(0, H, 16):
        ch   = random.choice(matrix_chars)
        alpha = random.randint(8, 35)
        gc   = (0, alpha*2, 0)
        draw.text((col, row), ch, font=f_tiny, fill=gc)

# ── 2. Panel central oscuro ───────────────────────────────────────────────────
panel_x1, panel_y1 = 40, 28
panel_x2, panel_y2 = W - 40, H - 28
draw.rectangle([panel_x1, panel_y1, panel_x2, panel_y2], fill=(12, 15, 22))

# bordes: verde brillante
bw = 2
draw.rectangle([panel_x1, panel_y1, panel_x2, panel_y2], outline=GREEN_DIM, width=bw)
# línea interior cyan
draw.rectangle([panel_x1+6, panel_y1+6, panel_x2-6, panel_y2-6], outline=(0,60,60), width=1)

# ── 3. Barra de título tipo terminal ──────────────────────────────────────────
bar_y2 = panel_y1 + 32
draw.rectangle([panel_x1, panel_y1, panel_x2, bar_y2], fill=(18, 22, 32))
draw.rectangle([panel_x1, panel_y1, panel_x2, bar_y2], outline=GREEN_DIM, width=1)

# dots
for xi, col in [(panel_x1+18, (255,95,86)), (panel_x1+38, (255,189,46)), (panel_x1+58, (39,201,63))]:
    draw.ellipse([xi-7, panel_y1+9, xi+7, panel_y1+23], fill=col)

# título de la barra
f_bar = ImageFont.truetype(FONT, 12)
bar_text = "faravena@h0ruz  ~/OT-Tribute-KevinMitnick  [python3 kevin_mitnick_demo.py]"
draw.text((panel_x1 + 82, panel_y1 + 9), bar_text, font=f_bar, fill=(140, 150, 160))

# ── 4. Texto principal — tres líneas ──────────────────────────────────────────
f_title  = ImageFont.truetype(FONT_BOLD, 58)
f_sub    = ImageFont.truetype(FONT_BOLD, 22)
f_detail = ImageFont.truetype(FONT, 14)

# Sombra roja para el título
title1 = "OPERACIÓN"
title2 = "TAKEDOWN"
cx = W // 2

# --- OPERACIÓN ---
bbox1 = draw.textbbox((0,0), title1, font=f_title)
tw1 = bbox1[2] - bbox1[0]
tx1 = cx - tw1 // 2 - 180
ty1 = panel_y1 + 50

# sombra
draw.text((tx1+3, ty1+3), title1, font=f_title, fill=(80, 0, 0))
# gradiente manual: rojo → naranja en el texto
for i, ch in enumerate(title1):
    bch = draw.textbbox((0,0), title1[:i], font=f_title)
    xoff = bch[2] - bch[0]
    t = i / max(len(title1)-1, 1)
    r = int(RED[0] + (ORANGE[0]-RED[0])*t)
    g = int(RED[1] + (ORANGE[1]-RED[1])*t)
    b = int(RED[2] + (ORANGE[2]-RED[2])*t)
    draw.text((tx1 + xoff, ty1), ch, font=f_title, fill=(r,g,b))

# --- TAKEDOWN ---
bbox2 = draw.textbbox((0,0), title2, font=f_title)
tw2 = bbox2[2] - bbox2[0]
tx2 = cx - tw2 // 2 + 200
ty2 = panel_y1 + 50

draw.text((tx2+3, ty2+3), title2, font=f_title, fill=(0, 60, 0))
for i, ch in enumerate(title2):
    bch = draw.textbbox((0,0), title2[:i], font=f_title)
    xoff = bch[2] - bch[0]
    t = i / max(len(title2)-1, 1)
    r = int(GREEN[0]*(1-t) + CYAN[0]*t)
    g = int(GREEN[1]*(1-t) + CYAN[1]*t)
    b = int(GREEN[2]*(1-t) + CYAN[2]*t)
    draw.text((tx2 + xoff, ty2), ch, font=f_title, fill=(r,g,b))

# separador vertical
sep_x = cx
draw.line([(sep_x, ty1+8), (sep_x, ty1+78)], fill=GRAY, width=2)

# ── 5. Subtítulo ──────────────────────────────────────────────────────────────
sub  = "Kevin David Mitnick  ·  1963–2023  ·  The World's Most Famous Hacker"
bbox = draw.textbbox((0,0), sub, font=f_sub)
stw  = bbox[2] - bbox[0]
draw.text((cx - stw//2 + 1, ty1 + 148), sub, font=f_sub, fill=(20, 20, 20))
draw.text((cx - stw//2, ty1 + 147), sub, font=f_sub, fill=CYAN)

# ── 6. Badge de stats ─────────────────────────────────────────────────────────
badges = [
    ("10 CAPÍTULOS",  GREEN),
    ("AUDIOS REALES", YELLOW),
    ("DATOS HISTÓRICOS", CYAN),
    ("TCP ISN EXPLOIT", RED),
    ("PANXOZ",        ORANGE),
]
bx = panel_x1 + 30
by = panel_y2 - 50
f_badge = ImageFont.truetype(FONT_BOLD, 12)
f_badge_lbl = ImageFont.truetype(FONT, 11)
for label, col in badges:
    bbox_b = draw.textbbox((0,0), f" {label} ", font=f_badge)
    bw2 = bbox_b[2] - bbox_b[0] + 8
    draw.rounded_rectangle([bx, by, bx+bw2, by+22], radius=4, fill=(20,25,32), outline=col, width=1)
    draw.text((bx+4, by+4), f" {label} ", font=f_badge, fill=col)
    bx += bw2 + 10

# ── 7. Prompt parpadeante en esquina ─────────────────────────────────────────
f_prompt = ImageFont.truetype(FONT_BOLD, 14)
prompt   = "  github.com/panxos ▌"
draw.text((panel_x2 - 260, panel_y2 - 46), prompt, font=f_prompt, fill=GREEN)

# ── 8. Líneas de escaneo (scanlines) ─────────────────────────────────────────
scan_layer = Image.new("RGBA", (W, H), (0,0,0,0))
scan_draw  = ImageDraw.Draw(scan_layer)
for y in range(0, H, 4):
    scan_draw.line([(0, y), (W, y)], fill=(0, 0, 0, 18))
img = Image.alpha_composite(img.convert("RGBA"), scan_layer).convert("RGB")

# ── 9. Vignette (oscurecer bordes) ───────────────────────────────────────────
vig = Image.new("RGBA", (W, H), (0,0,0,0))
vd  = ImageDraw.Draw(vig)
for r in range(min(W,H)//2, 0, -1):
    alpha = int(80 * (1 - r / (min(W,H)//2)))
    vd.ellipse([W//2-r, H//2-r, W//2+r, H//2+r], outline=(0,0,0,alpha))
img = Image.alpha_composite(img.convert("RGBA"), vig).convert("RGB")

img.save("screenshots/logo.png", "PNG", optimize=True)
print("  ✓ screenshots/logo.png  (1200×400)")
