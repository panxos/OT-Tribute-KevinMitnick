#!/usr/bin/env python3
"""Genera screenshots PNG del demo para el README."""
import re
from PIL import Image, ImageDraw, ImageFont

FONT_PATH = "/usr/share/fonts/TTF/DejaVuSansMono.ttf"
FONT_SIZE  = 15
PADDING    = 20
BG         = (13, 17, 23)       # fondo negro azulado
FG         = (201, 209, 217)    # gris claro

ANSI_COLORS = {
    '30': (40,  40,  40),
    '31': (255, 85, 85),
    '32': (80, 200, 120),
    '33': (255, 215, 0),
    '34': (100, 150, 255),
    '35': (200, 100, 255),
    '36': (80, 220, 220),
    '37': (201, 209, 217),
    '90': (100, 110, 120),
    '91': (255, 100, 100),
    '92': (100, 255, 130),
    '93': (255, 230, 80),
    '94': (130, 170, 255),
    '95': (220, 130, 255),
    '96': (100, 240, 240),
    '97': (255, 255, 255),
    '0':  (201, 209, 217),
}

def strip_ansi(text):
    return re.sub(r'\033\[[^m]*m', '', text)

def parse_ansi_spans(text):
    """Retorna lista de (texto, color_rgb, bold)."""
    spans = []
    cur_col = FG
    cur_bold = False
    i = 0
    buf = ""
    cur_col_save = FG
    while i < len(text):
        if text[i] == '\033' and i+1 < len(text) and text[i+1] == '[':
            # flush buf
            if buf:
                spans.append((buf, cur_col, cur_bold))
                buf = ""
            j = i + 2
            while j < len(text) and text[j] != 'm':
                j += 1
            codes = text[i+2:j].split(';')
            for code in codes:
                if code == '0' or code == '':
                    cur_col = FG; cur_bold = False
                elif code == '1':
                    cur_bold = True
                elif code == '2':
                    cur_bold = False
                elif code in ANSI_COLORS:
                    cur_col = ANSI_COLORS[code]
            i = j + 1
        else:
            buf += text[i]
            i += 1
    if buf:
        spans.append((buf, cur_col, cur_bold))
    return spans

def render_screen(lines, outpath, title="", width=900):
    font_reg  = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    font_bold = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    try:
        font_bold = ImageFont.truetype(FONT_PATH.replace('DejaVuSansMono', 'DejaVuSansMono-Bold'), FONT_SIZE)
    except Exception:
        pass

    cw = font_reg.getbbox("M")[2]
    ch = font_reg.getbbox("Mg")[3] + 3

    # strip ansi for height calc
    plain_lines = [strip_ansi(l) for l in lines]
    height = ch * len(lines) + PADDING * 2 + (30 if title else 0)

    img = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(img)

    # título de ventana
    if title:
        draw.rectangle([0, 0, width, 26], fill=(30, 35, 45))
        # 3 dots
        for xi, col in [(14, (255,95,86)), (34, (255,189,46)), (54, (39,201,63))]:
            draw.ellipse([xi-5, 8, xi+5, 18], fill=col)
        draw.text((75, 5), title, font=font_reg, fill=(180, 180, 180))
        y_off = PADDING + 26
    else:
        y_off = PADDING

    for line in lines:
        spans = parse_ansi_spans(line)
        x = PADDING
        for text, color, bold in spans:
            font = font_bold if bold else font_reg
            draw.text((x, y_off), text, font=font, fill=color)
            bx = font.getbbox(text)
            x += bx[2] - bx[0]
        y_off += ch

    img.save(outpath, "PNG", optimize=True)
    print(f"  ✓ {outpath}")


# ─── SCREEN 1: Chapter Menu ──────────────────────────────────────────────────
menu = [
    "",
    "  \033[96m\033[1m" + "  O P E R A C I Ó N   T A K E D O W N".center(70) + "\033[0m",
    "  \033[90m" + "Kevin Mitnick  ·  1963-2023".center(70) + "\033[0m",
    "",
    "\033[32m" + "─"*72 + "\033[0m",
    "",
    "  \033[97m\033[1m" + "[ 0 ]  Historia completa (recomendado)".center(70) + "\033[0m",
    "",
    "  \033[90m  [ 1 ]  Boot Toshiba + Matrix Rain\033[0m",
    "  \033[90m  [ 2 ]  Perfil FBI — Quién es Mitnick\033[0m",
    "  \033[90m  [ 3 ]  El Ataque de Navidad 1994\033[0m",
    "  \033[90m  [ 4 ]  Shimomura descubre el hack\033[0m",
    "  \033[90m  [ 5 ]  Voicemails reales (audios)\033[0m",
    "  \033[90m  [ 6 ]  La llamada grabada — Lottor\033[0m",
    "  \033[90m  [ 7 ]  Ingeniería Social\033[0m",
    "  \033[90m  [ 8 ]  Triangulación celular\033[0m",
    "  \033[90m  [ 9 ]  El Arresto — 15 Feb 1995\033[0m",
    "  \033[90m  [ 10]  Legado + Muerte 2023\033[0m",
    "",
    "\033[32m" + "─"*72 + "\033[0m",
    "",
    "  \033[96m\033[1m  Selección [0-10]: \033[93m_\033[0m",
]
render_screen(menu, "screenshots/01_menu.png", "kevin_mitnick_demo.py — Menú Principal", width=760)

# ─── SCREEN 2: FBI Dossier ───────────────────────────────────────────────────
fbi = [
    "",
    "  \033[91m\033[1m╔" + "═"*68 + "╗\033[0m",
    "  \033[91m\033[1m║" + " ⚠  FUGITIVO ACTIVO — MAXIMA PRIORIDAD — FBI NCIC ".center(68) + "║\033[0m",
    "  \033[91m\033[1m╠" + "═"*68 + "╣\033[0m",
    "  \033[91m\033[1m║\033[0m  \033[90m[foto]\033[0m" + " "*10 + "  \033[93m\033[1mNOMBRE          \033[0m  \033[97mKevin David Mitnick\033[0m" + " "*6 + "\033[91m\033[1m║\033[0m",
    "  \033[91m\033[1m║\033[0m  \033[90m[FBI] \033[0m" + " "*10 + "  \033[93m\033[1mALIAS           \033[0m  \033[97mcondor · The Darkside Hacker\033[0m" + " "*2 + "\033[91m\033[1m║\033[0m",
    "  \033[91m\033[1m║\033[0m  \033[90m[WANT]\033[0m" + " "*10 + "  \033[93m\033[1mNACIMIENTO      \033[0m  \033[97m6 Agosto 1963, Van Nuys CA\033[0m" + " "*3 + "\033[91m\033[1m║\033[0m",
    "  \033[91m\033[1m║\033[0m  \033[90m[STED]\033[0m" + " "*10 + "  \033[93m\033[1mESTADO          \033[0m  \033[91m\033[1mFUGITIVO — 3 años clandestino\033[0m" + " "*1 + "\033[91m\033[1m║\033[0m",
    "  \033[91m\033[1m║\033[0m  \033[90m[PELI]\033[0m" + " "*10 + "  \033[93m\033[1mPELIGROSIDAD    \033[0m  \033[91m\033[1mEXTREMA — Redes militares\033[0m" + " "*4 + "\033[91m\033[1m║\033[0m",
    "  \033[91m\033[1m║\033[0m  \033[90m[GROS]\033[0m" + " "*10 + "  \033[93m\033[1mUBICACIÓN       \033[0m  \033[97mRaleigh, North Carolina\033[0m" + " "*7 + "\033[91m\033[1m║\033[0m",
    "  \033[91m\033[1m║\033[0m  \033[90m      \033[0m" + " "*10 + "  \033[93m\033[1mCARGOS          \033[0m  \033[97mComputer Fraud · Wire Fraud\033[0m" + " "*4 + "\033[91m\033[1m║\033[0m",
    "  \033[91m\033[1m╚" + "═"*68 + "╝\033[0m",
    "",
    "  \033[90m              U.S. MARSHALS WANTED POSTER\033[0m",
]
render_screen(fbi, "screenshots/02_fbi_dossier.png", "kevin_mitnick_demo.py — FBI Dossier", width=860)

# ─── SCREEN 3: Ataque TCP / Terminal ─────────────────────────────────────────
attack = [
    "  \033[32m══ FASE 2: SYN FLOOD — Silenciando osiris ══════════════════════════\033[0m",
    "",
    "  \033[92m$\033[0m \033[97msyn_flood osiris.sdsc.edu 514 25\033[0m",
    "",
    "  \033[90m[01] SYN  172.18.44.12:51234 → osiris:514  seq=0xdeadbeef\033[0m",
    "  \033[90m[02] SYN  172.29.11.88:38901 → osiris:514  seq=0xcafe0001\033[0m",
    "  \033[90m[03] SYN  172.21.200.3:60123 → osiris:514  seq=0xbabe1234\033[0m",
    "  \033[90m[04] SYN  172.16.77.44:14500 → osiris:514  seq=0xfeed4321\033[0m",
    "  \033[90m[05] SYN  172.30.55.99:29911 → osiris:514  seq=0xab120000\033[0m",
    "  \033[90m[06] SYN  172.25.143.7:44001 → osiris:514  seq=0x1234abcd\033[0m",
    "  \033[90m[07] SYN  172.19.88.201:9834 → osiris:514  seq=0xdeadc0de\033[0m",
    "  \033[90m[08] SYN  172.22.111.50:7320 → osiris:514  seq=0x00ff1234\033[0m",
    "  \033[90m[09] SYN  172.28.33.170:5500 → osiris:514  seq=0x77889900\033[0m",
    "  \033[90m[10] SYN  172.17.200.66:1022 → osiris:514  seq=0xaabbccdd\033[0m",
    "",
    "  \033[93m\033[1m[!] Cola SYN de osiris DESBORDADA — ya no puede responder RST\033[0m",
    "  \033[93m[!] osiris está ciego. Ahora podemos suplantar su IP sin ser detectados.\033[0m",
    "",
    "  \033[32m══ FASE 3: TCP ISN PREDICTION — El corazon del ataque ══════════════\033[0m",
]
render_screen(attack, "screenshots/03_syn_flood.png", "kevin_mitnick_demo.py — SYN Flood", width=820)

# ─── SCREEN 4: ISN Diagram ───────────────────────────────────────────────────
isn = [
    "",
    "  \033[93m\033[1m  EL HANDSHAKE CIEGO — paso a paso\033[0m".center(78),
    "  \033[90m  (Mitnick nunca ve los paquetes que recibe osiris — actúa 'a ciegas')\033[0m".center(78),
    "",
    "  \033[96m\033[1m MITNICK            \033[0m  \033[97mSYN (src=osiris) seq=0xdeadbeef  ──────────────►\033[0m  \033[32m\033[1m  x-terminal\033[0m",
    "  \033[90m                      x-terminal recibe SYN creyendo que viene de osiris.\033[0m",
    "",
    "  \033[90m x-terminal         \033[0m  \033[97mSYN-ACK seq=0x3da0c0000  ──────────────►\033[0m  \033[91m\033[1m  osiris (sordo!)\033[0m",
    "  \033[90m                      SYN-ACK va a osiris real — Mitnick NUNCA lo ve.\033[0m",
    "",
    "  \033[93m\033[1m MITNICK (CIEGO)    \033[0m  \033[97mACK ack=0x3da0c0001  ──────────────►\033[0m  \033[92m\033[1m  x-terminal\033[0m",
    "  \033[90m                      Mitnick calcula el ACK sin haberlo visto. Si acierta...\033[0m",
    "",
    "  \033[92m\033[1m x-terminal         \033[0m  \033[97m                  CONEXIÓN ESTABLECIDA  ✓       \033[0m  \033[92m\033[1m  MITNICK=osiris\033[0m",
    "  \033[90m                      x-terminal cree hablar con osiris. El handshake está completo.\033[0m",
    "",
    "  \033[91m\033[1m  El truco: BSD usaba ISN predecible. Mitnick calculó el número exacto.\033[0m".center(78),
    "  \033[91m  Después de esto: este bug fue parchado en TODOS los sistemas Unix.\033[0m".center(78),
]
render_screen(isn, "screenshots/04_isn_diagram.png", "kevin_mitnick_demo.py — ISN Handshake Ciego", width=920)

# ─── SCREEN 5: Triangulación ─────────────────────────────────────────────────
triang = [
    "",
    "\033[92m\033[1m  MAPA DE TRIANGULACIÓN — RALEIGH, NC — 11-14 FEB 1995\033[0m".center(72),
    "",
    "  \033[90m[A] Spring Forest                    [B] Westover Hills\033[0m",
    "  \033[90m -88dBm ●                              ● -74dBm\033[0m",
    "  \033[90m         ╲                           ╱\033[0m",
    "  \033[93m          ╲                         ╱\033[0m",
    "  \033[93m           ╲       Durham Dr        ╱\033[0m",
    "  \033[93m            ╲                      ╱\033[0m",
    "  \033[91m\033[1m             ╲──────►  ★ SURREY HOUSE ◄──╱\033[0m",
    "  \033[91m\033[1m                       Apt 202-D\033[0m",
    "  \033[91m\033[1m                    1 Wayne Hills Dr\033[0m",
    "  \033[93m                           │\033[0m",
    "  \033[90m                          [C] Tryon Rd -65dBm\033[0m",
    "",
    "  \033[90m  ANTENA-A ●── ●── ●──── ANTENA-B ●── ●── ●──── ANTENA-C ●── ●── ●  COBERTURA: 100%\033[0m",
    "",
    "  \033[91m\033[1m★  POSICIÓN EXACTA CONFIRMADA — APT 202-D  ★\033[0m".center(72),
]
render_screen(triang, "screenshots/05_triangulacion.png", "kevin_mitnick_demo.py — Triangulación Celular", width=860)

# ─── SCREEN 6: Arresto ───────────────────────────────────────────────────────
arresto = [
    "",
    "  \033[97m  4 agentes del FBI. Shimomura en el estacionamiento con el receptor.\033[0m",
    "  \033[97m  01:30 AM. El edificio está en silencio.\033[0m",
    "  \033[97m  Suben por las escaleras. Pasillo D. Tercer piso.\033[0m",
    "",
    "  \033[93m  Los agentes se posicionan a cada lado de la puerta 202-D.\033[0m",
    "",
    '  \033[91m  Bowne: "Kevin Mitnick — FBI — ABRA LA PUERTA."\033[0m',
    "  \033[91m  ...\033[0m",
    "  \033[91m  Silencio.\033[0m",
    "  \033[91m  Pasos.\033[0m",
    "  \033[91m  Luz bajo la puerta.\033[0m",
    "",
    "  \033[92m  La puerta se abre.\033[0m",
    '  \033[92m  Mitnick: "Oh no..."\033[0m',
    "",
    "  \033[92m  Kevin David Mitnick — 31 años — queda detenido.\033[0m",
    "  \033[92m  El fugitivo más buscado de América. Capturado.\033[0m",
    "",
    "  \033[91m\033[1m" + "  ██  F U G I T I V O   C A P T U R A D O  ██  ".center(70) + "\033[0m",
]
render_screen(arresto, "screenshots/06_arresto.png", "kevin_mitnick_demo.py — El Arresto", width=820)

# ─── SCREEN 7: FREE KEVIN / Credits ──────────────────────────────────────────
credits_scr = [
    "",
    "\033[96m" + "═"*70 + "\033[0m",
    "",
    "\033[92m\033[1m" + "  O P E R A C I O N   T A K E D O W N".center(70) + "\033[0m",
    "\033[90m" + "  Kevin Mitnick  ·  1963-2023  ·  Demo Educativo".center(70) + "\033[0m",
    "",
    "\033[32m" + "─"*70 + "\033[0m",
    "",
    "\033[93m\033[1m" + "  Presentado por:".center(70) + "\033[0m",
    "",
    "\033[96m\033[1m" + "[ P A N X O Z ]".center(70) + "\033[0m",
    "",
    "\033[97m" + "github.com/panxos".center(70) + "\033[0m",
    "\033[97m" + "linkedin.com/in/faravena".center(70) + "\033[0m",
    "\033[90m" + "soporteinfo.net".center(70) + "\033[0m",
    "",
    "\033[96m" + "═"*70 + "\033[0m",
]
render_screen(credits_scr, "screenshots/07_credits.png", "kevin_mitnick_demo.py — Créditos", width=760)

print("\n  Todos los screenshots generados en screenshots/")
