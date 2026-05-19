#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
#  OPERACIÓN TAKEDOWN — Kevin Mitnick  ·  1963-2023
#  Demo espectacular para niños de 12 años  ·  Datos históricos reales
#  Fuentes: takedown.com · Ghost in the Wires · USA v. Mitnick #95-181M
# ─────────────────────────────────────────────────────────────────────────────
import sys, time, random, math, struct, subprocess, threading, shutil, os, argparse

# ══════════════════════════════════════════════════════════════════════════════
#  CLI FLAGS
# ══════════════════════════════════════════════════════════════════════════════
_ap = argparse.ArgumentParser(description="Operación Takedown — Kevin Mitnick Demo")
_ap.add_argument('--fast',     action='store_true', help='Velocidad x2 (presentación rápida)')
_ap.add_argument('--no-audio', action='store_true', help='Sin audio (proyector sin sonido)')
_ap.add_argument('--chapter',  type=int, default=0, metavar='N',
                 help='Saltar directo al capítulo N (1-9)')
ARGS = _ap.parse_args()

SPEED    = 0.5 if ARGS.fast else 1.0
NO_AUDIO = ARGS.no_audio

# ══════════════════════════════════════════════════════════════════════════════
#  TERMINAL
# ══════════════════════════════════════════════════════════════════════════════
def W(): return shutil.get_terminal_size((80,24)).columns
def H(): return shutil.get_terminal_size((80,24)).lines
def cls(): sys.stdout.write("\033[2J\033[H"); sys.stdout.flush()
def goto(r,c): sys.stdout.write(f"\033[{r};{c}H"); sys.stdout.flush()
def hide_cursor(): sys.stdout.write("\033[?25l"); sys.stdout.flush()
def show_cursor(): sys.stdout.write("\033[?25h"); sys.stdout.flush()
def p(s): time.sleep(s * SPEED)

# ══════════════════════════════════════════════════════════════════════════════
#  COLORES
# ══════════════════════════════════════════════════════════════════════════════
G  ="\033[92m"; Y  ="\033[93m"; R  ="\033[91m"; C  ="\033[96m"
WC ="\033[97m"; DG ="\033[32m"; GR ="\033[90m"; M  ="\033[95m"
B  ="\033[94m"; X  ="\033[0m";  BD ="\033[1m";  DM ="\033[2m"

# ══════════════════════════════════════════════════════════════════════════════
#  MOTOR DE SONIDO  (paplay --raw · PipeWire compatible)
# ══════════════════════════════════════════════════════════════════════════════
SR = 44100
def _s(v): return max(-32767,min(32767,int(v)))
def _pcm(s): return b''.join(struct.pack('<h',_s(x)) for x in s)
def _tone(hz,dur,vol=0.4):
    return [vol*32767*math.sin(2*math.pi*hz*i/SR) for i in range(int(SR*dur))]
def _sweep(f0,f1,dur,vol=0.35):
    n=int(SR*dur)
    return [vol*32767*math.sin(2*math.pi*(f0+(f1-f0)*i/n)*i/SR) for i in range(n)]
def _noise(dur,vol=0.18):
    return [vol*32767*(random.random()*2-1) for _ in range(int(SR*dur))]
def _mix(*tt):
    L=max(len(t) for t in tt)
    return [sum(t[i] if i<len(t) else 0 for t in tt)/len(tt) for i in range(L)]
def _cat(*tt):
    o=[]
    for t in tt: o.extend(t)
    return o

import queue as _q
_audio_q = _q.Queue()

_paplay_missing = False   # se setea una sola vez si paplay no está instalado

def _audio_worker():
    global _paplay_missing, NO_AUDIO
    _cmd = ['paplay','--raw','--format=s16le','--rate=44100','--channels=1','/dev/stdin']
    while True:
        raw, done = _audio_q.get()
        try:
            proc = subprocess.Popen(_cmd, stdin=subprocess.PIPE,
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            proc.communicate(raw)
        except FileNotFoundError:
            if not _paplay_missing:
                _paplay_missing = True
                NO_AUDIO = True   # desactivar audio para no reintentar en cada sample
        except Exception:
            pass
        finally:
            if done: done.set()
            _audio_q.task_done()

threading.Thread(target=_audio_worker, daemon=True).start()

def _play(samps, bg=True):
    if NO_AUDIO:
        return
    raw = _pcm(samps)
    done = threading.Event() if not bg else None
    _audio_q.put((raw, done))
    if not bg:
        done.wait()

# Resolución portable de rutas:
# 1. realpath resuelve symlinks → si ~/kevin_mitnick_demo.py es symlink al repo, funciona
# 2. Fallback al directorio de trabajo actual (útil si se ejecuta con python3 ./kevin...)
# 3. Nunca hardcodeamos rutas de usuario
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
if not os.path.isdir(os.path.join(SCRIPT_DIR, "audio")):
    _cwd = os.getcwd()
    if os.path.isdir(os.path.join(_cwd, "audio")):
        SCRIPT_DIR = _cwd

AUDIO_VM  = os.path.join(SCRIPT_DIR, "audio", "voicemail")
AUDIO_LOT = os.path.join(SCRIPT_DIR, "audio", "lottor")

import select, tty, termios

def play_wav(path):
    if NO_AUDIO or not os.path.exists(path):
        return
    _audio_q.join()
    subprocess.run(['paplay', path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def play_wav_skippable(path):
    """Reproduce WAV; el usuario puede saltar con ENTER mientras suena."""
    if NO_AUDIO or not os.path.exists(path):
        if NO_AUDIO:
            print(GR + "  [ ♪ AUDIO — modo sin sonido activo ]" + X)
        return
    _audio_q.join()
    proc = subprocess.Popen(['paplay', path],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    sys.stdout.write(GR + "  [ Reproduciendo... ENTER para saltar ] " + X)
    sys.stdout.flush()
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        while proc.poll() is None:
            if select.select([sys.stdin], [], [], 0.1)[0]:
                sys.stdin.read(1)
                break
    except Exception:
        pass
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    if proc.poll() is None:
        proc.terminate(); proc.wait()
    print()

import wave as _wave

def _wav_duration(path):
    """Duración en segundos de un archivo WAV."""
    try:
        with _wave.open(path) as w:
            return w.getnframes() / w.getframerate()
    except Exception:
        return 0.0

def play_wav_with_subs(path, subs):
    """Reproduce WAV y muestra subtítulos sincronizados mientras suena.

    subs: lista de (col_key, texto_eng, texto_esp)
    La transcripción se distribuye uniformemente a lo largo de la duración real.
    ENTER salta el audio + subtítulos restantes.
    """
    if NO_AUDIO:
        print(GR + "  [ ♪ AUDIO — modo sin sonido activo ]" + X)
        for col_key, eng, esp in subs:
            col = (R+BD if col_key=='R' else M+BD if col_key=='M' else
                   GR+DM if col_key=='GR' else WC+BD)
            print(f"  {col}{eng}{X}")
            print(f"  {GR}  → {esp}{X}")
            print()
        return

    if not os.path.exists(path):
        # Sin WAV — mostrar transcripción sola con delay
        for col_key, eng, esp in subs:
            col = (R+BD if col_key=='R' else M+BD if col_key=='M' else
                   GR+DM if col_key=='GR' else WC+BD)
            print(f"  {col}{eng}{X}")
            print(f"  {GR}  → {esp}{X}")
            print()
            p(1.2)
        return

    dur = _wav_duration(path)
    n   = max(len(subs), 1)
    # Reservar 15% inicial (intro del mensaje) antes del primer subtítulo
    start_delay = dur * 0.12
    interval    = (dur * 0.78) / n   # repartir el 78% restante entre líneas

    _audio_q.join()
    proc    = None
    old     = None
    skipped = False
    try:
        proc = subprocess.Popen(['paplay', path],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        fd  = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        tty.setcbreak(fd)
        print(GR + "  [ Reproduciendo... ENTER para saltar ]" + X)
        print()

        # Pausa inicial (intro del mensaje)
        t0 = time.time()
        while time.time() - t0 < start_delay and proc.poll() is None:
            if select.select([sys.stdin], [], [], 0.05)[0]:
                sys.stdin.read(1); skipped = True; break

        # Mostrar cada línea sincronizada
        for col_key, eng, esp in subs:
            if skipped or proc.poll() is not None:
                break
            col = (R+BD if col_key=='R' else M+BD if col_key=='M' else
                   GR+DM if col_key=='GR' else WC+BD)
            sys.stdout.write(f"  {col}{eng}{X}\n")
            sys.stdout.write(f"  {GR}  → {esp}{X}\n\n")
            sys.stdout.flush()

            t0 = time.time()
            while time.time() - t0 < interval and proc.poll() is None:
                if select.select([sys.stdin], [], [], 0.05)[0]:
                    sys.stdin.read(1); skipped = True; break

        # Esperar fin del audio si no fue saltado
        if not skipped:
            while proc.poll() is None:
                if select.select([sys.stdin], [], [], 0.1)[0]:
                    sys.stdin.read(1); break

    except Exception:
        pass
    finally:
        if old is not None:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
        if proc is not None and proc.poll() is None:
            proc.terminate(); proc.wait()
    print()

_DF={'1':(697,1209),'2':(697,1336),'3':(697,1477),'4':(770,1209),
     '5':(770,1336),'6':(770,1477),'7':(852,1209),'8':(852,1336),
     '9':(852,1477),'0':(941,1336),'*':(941,1209),'#':(941,1477)}

def snd_beep(hz=880,dur=0.12,vol=0.45,bg=True):
    _play(_tone(hz,dur,vol),bg)
def snd_speak(text, pitch=30, speed=120, voice='en', bg=False):
    """TTS via espeak-ng — pitch bajo = voz grave/amenazante."""
    if NO_AUDIO:
        return
    cmd = ['espeak-ng', '-v', voice, '-s', str(speed), '-p', str(pitch), text]
    def go():
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if bg: threading.Thread(target=go, daemon=True).start()
    else: go()
def snd_beeps(seq,bg=False):
    d=[]
    for hz,dur in seq: d=_cat(d,_tone(hz,dur,0.4),[0]*int(SR*0.04))
    _play(d,bg)
def snd_static(dur=0.5,bg=False): _play(_noise(dur,0.22),bg)
def snd_click(): _play(_cat(_noise(0.012,0.25),[0]*int(SR*0.055)))
def snd_clicks(n=6):
    d=[]
    for _ in range(n): d=_cat(d,_noise(0.013,0.28),[0]*int(SR*0.06))
    _play(d)
def snd_alert(bg=True): _play(_cat(_tone(1400,0.13,0.5),_tone(700,0.2,0.5)),bg)
def snd_success(bg=False):
    _play(_cat(_tone(660,0.09),_tone(880,0.09),_tone(1100,0.16)),bg)
def snd_alarm(bg=False):
    d=[]
    for _ in range(6): d=_cat(d,_sweep(350,1100,0.2,0.6),_sweep(1100,350,0.2,0.6))
    _play(d,bg)
def snd_crt(bg=False):
    _play(_cat(_noise(0.35,0.28),_tone(220,0.08,0.2),_tone(440,0.14,0.4)),bg)
def snd_ring(n=2, bg=False):
    """Timbre telefónico real: 440+480Hz — patrón USA (largo-pausa)."""
    def _ring_pulse():
        # Un timbre = 440Hz+480Hz mezclados por 1.2s
        return _mix(_tone(440,1.2,0.55), _tone(480,1.2,0.55))
    d = []
    for _ in range(n):
        d = _cat(d, _ring_pulse(), [0]*int(SR*0.8))
    _play(d, bg)

def snd_am(bg=False):
    """Contestador automático real: 3 bips largos y fuertes."""
    silence = [0]*int(SR*0.18)
    d = _cat(
        _tone(1400, 0.25, 0.7), silence,
        _tone(1400, 0.25, 0.7), silence,
        _tone(1400, 0.55, 0.7),
    )
    _play(d, bg)

def snd_dial(num, bg=False):
    """DTMF real — tones largos y fuertes para que se escuchen bien."""
    d = []
    for c in num:
        if c in _DF:
            f1, f2 = _DF[c]
            tone = _mix(_tone(f1, 0.18, 0.7), _tone(f2, 0.18, 0.7))
            d = _cat(d, tone, [0]*int(SR*0.09))
    _play(d, bg)
def snd_modem(bg=False):
    d=_cat(_tone(350,0.3,0.3),_tone(440,0.3,0.3),
           _sweep(300,1200,0.5,0.4),
           _mix(_tone(1200,0.4,0.3),_noise(0.4,0.12)),
           _sweep(1200,2400,0.6,0.4),
           _mix(_tone(2400,0.3,0.35),_noise(0.3,0.1)),
           _sweep(2400,1200,0.3,0.3),
           _mix(_tone(1200,0.2,0.25),_noise(0.2,0.08)),
           _tone(2400,0.3,0.22))
    _play(d,bg)
def snd_data(dur=1.0):
    t,d=0.0,[]
    while t<dur:
        hz=1200+1200*math.sin(2*math.pi*11*t)
        d.append(0.28*32767*math.sin(2*math.pi*hz*t))
        t+=1/SR
    _play(d)
def snd_dramatic(bg=False):
    d=_cat(_tone(220,0.4,0.5),_tone(196,0.4,0.4),_tone(165,0.6,0.3))
    _play(d,bg)
def snd_heartbeat(n=4,bg=False):
    d=[]
    for _ in range(n):
        d=_cat(d,_tone(80,0.08,0.6),_tone(80,0.06,0.4),[0]*int(SR*0.55))
    _play(d,bg)

def snd_tension_crescendo(dur=8.0, bg=False):
    """Sweep de tensión creciente — sube de 80Hz a 1800Hz en dur segundos."""
    samples = []
    steps = 40
    step_dur = dur / steps
    for i in range(steps):
        t = i / steps
        hz = 80 + (1800 - 80) * (t ** 1.8)
        vol = 0.18 + 0.42 * t
        pulse = _mix(_sweep(hz, hz * 1.015, step_dur, vol),
                     _noise(step_dur, vol * 0.08))
        samples.extend(pulse)
    _play(samples, bg)

def snd_keyclick(bg=True):
    """Click mecánico de teclado: transiente de ruido corto + tono suave."""
    click = _cat(_noise(0.006, 0.55), _tone(3200, 0.004, 0.12), [0]*int(SR*0.022))
    _play(click, bg)

def render_photo(path, w_chars=36, h_chars=18, label="", col=GR):
    """Muestra imagen como ANSI art centrada en el terminal. Silencioso si no existe."""
    if not os.path.exists(path):
        return
    try:
        res = subprocess.run(
            ['chafa', '--format', 'ansi', '--size', f'{w_chars}x{h_chars}', path],
            capture_output=True, text=True
        )
        if res.returncode != 0:
            return
        tw = W()
        pad = max(0, (tw - w_chars) // 2)
        indent = " " * pad
        for line in res.stdout.split('\n'):
            if line:
                print(indent + line)
        if label:
            print(col + label.center(tw) + X)
    except FileNotFoundError:
        pass

# ══════════════════════════════════════════════════════════════════════════════
#  EFECTOS VISUALES
# ══════════════════════════════════════════════════════════════════════════════
MATRIX_CHARS = "01234567890abcdefABCDEF!@#$%^&*|/\\:.-+=<>[]{}?~"

def matrix_rain(duration=3.5, overlay_text=None):
    """Lluvia matricial estilo película."""
    hide_cursor(); cls()
    cols = W(); rows = H()
    drops = [random.randint(-rows, 0) for _ in range(cols)]
    trail = [' '] * (cols * rows)
    end = time.time() + duration
    frame = 0
    while time.time() < end:
        sys.stdout.write("\033[H")
        for r in range(rows - 1):
            line = ""
            for c in range(cols):
                ch = random.choice(MATRIX_CHARS)
                rel = drops[c] - r
                if rel == 0:
                    line += WC + BD + ch + X
                elif 0 < rel <= 4:
                    line += G + BD + ch + X
                elif 0 < rel <= 10:
                    line += DG + ch + X
                elif 0 < rel <= 18:
                    line += GR + DM + random.choice("01 ") + X
                else:
                    line += " "
            sys.stdout.write(line + "\n")
        sys.stdout.flush()
        for c in range(cols):
            if drops[c] > rows + random.randint(5, 20):
                drops[c] = random.randint(-rows, 0)
            drops[c] += 1
        if overlay_text and frame > 20:
            mid = rows // 2
            for i, line in enumerate(overlay_text):
                padded = line.center(cols)
                sys.stdout.write(f"\033[{mid+i};1H" + G + BD + padded + X)
        sys.stdout.flush()
        frame += 1
        p(0.055)
    show_cursor()

def spinner(label, duration=2.0, col=G):
    """Spinner estilo hacker."""
    frames = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]
    end = time.time() + duration
    i = 0
    while time.time() < end:
        sys.stdout.write(f"\r  {col}{frames[i%len(frames)]}{X}  {col}{label}{X}   ")
        sys.stdout.flush(); p(0.1); i += 1
    sys.stdout.write(f"\r  {G}✔{X}  {G}{BD}{label}{X}   \n")
    sys.stdout.flush()

def scrolling_logs(lines, speed=0.04):
    """Logs scrollando rápido — efecto impresionante."""
    for line in lines:
        print(GR + "  " + line + X)
        p(speed + random.uniform(0,0.02))

def typ(text, delay=0.024, col="", nl=True):
    for ch in text:
        sys.stdout.write(col+ch+X); sys.stdout.flush(); p(delay)
    if nl: print()

def tln(text, delay=0.045, col=""):
    for ch in text:
        sys.stdout.write(col+ch+X); sys.stdout.flush(); p(delay)

def blink(text, n=5, col=R):
    for _ in range(n):
        sys.stdout.write(col+BD+text+X+"\r"); sys.stdout.flush(); p(0.36)
        sys.stdout.write(" "*min(len(text),W()-1)+"\r"); sys.stdout.flush(); p(0.23)
    print(col+BD+text+X)

def noise_line(n=3):
    ch="0123456789ABCDEFabcdef╠╬░▒▓!@#$%^&*><|∑∆"
    for _ in range(n):
        print(GR+"".join(random.choice(ch) for _ in range(W()-1))+X); p(0.05)

def hr(ch="─",col=DG): print(col+ch*W()+X)
def HR(ch="═",col=Y):  print(col+BD+ch*W()+X)

import re as _re
_ANSI = _re.compile(r'\033\[[0-9;]*m')
def _vlen(s): return len(_ANSI.sub('', s))

def box_top(col=G):
    w = W(); print(col+"  ┌"+"─"*(w-4)+"┐"+X)
def box_bot(col=G):
    w = W(); print(col+"  └"+"─"*(w-4)+"┘"+X)
def box_row(content="", col=G):
    print(col+"  │"+X+"  "+content+X)

def chapter_title(num, title, subtitle=""):
    """Entrada dramática de capítulo."""
    cls()
    hide_cursor()
    snd_beeps([(220+num*40, 0.08),(440+num*40,0.08),(660+num*40,0.12)])
    p(0.3)
    w = W()
    # Líneas que crecen
    for i in range(1, w//2+1, 3):
        sys.stdout.write("\r" + Y+BD + ("═"*i).center(w) + X)
        sys.stdout.flush(); p(0.01)
    print()
    print()
    print(GR+DM + f"  CAPÍTULO {num}".center(w) + X)
    print()
    print(G+BD + f"  {title}".center(w) + X)
    if subtitle:
        print(WC + f"  {subtitle}".center(w) + X)
    print()
    # Líneas que crecen hacia abajo
    for i in range(1, w//2+1, 3):
        sys.stdout.write("\r" + Y+BD + ("═"*i).center(w) + X)
        sys.stdout.flush(); p(0.01)
    print()
    show_cursor()
    p(1.2)

def countdown(n=5, label="INICIANDO EN"):
    for i in range(n, 0, -1):
        col = R if i <= 2 else Y if i <= 3 else G
        sys.stdout.write(f"\r  {col}{BD}[ {label} {i} ]{X}   ")
        sys.stdout.flush()
        snd_beep(440 + (n-i)*100, 0.07, 0.5)
        p(0.9)
    sys.stdout.write(f"\r  {R}{BD}[ AHORA ]{X}            \n")
    sys.stdout.flush()
    snd_beep(1100, 0.2, 0.7)
    p(0.3)

def big_text(lines, col=G):
    """Texto grande centrado con entrada dramática."""
    w = W()
    print()
    for line in lines:
        print(col+BD + line.center(w) + X)
    print()

def glitch_screen(duration=2.2):
    """Efecto de glitch: pantalla se corrompe visualmente antes de un evento crítico."""
    hide_cursor()
    w = W(); h = H()
    GLITCH = "▓░█▒▀▄▌▐■□▪▫◘◙♦♣♠◄►▲▼±≡≈∞∂∑∏"
    end = time.time() + duration
    intensity = 0.0
    while time.time() < end:
        intensity = min(1.0, intensity + 0.08)
        sys.stdout.write("\033[H")
        for r in range(h - 1):
            line = ""
            for c in range(w):
                if random.random() < intensity * 0.65:
                    ch = random.choice(GLITCH)
                    col = random.choice([R, Y, GR, WC, R+BD])
                    line += col + ch + X
                else:
                    line += " "
            sys.stdout.write(line + "\n")
        sys.stdout.flush()
        if not NO_AUDIO and random.random() < 0.4:
            _play(_cat(_noise(0.025, 0.35), [0]*int(SR*0.02)), bg=True)
        p(0.055)
    show_cursor()

def hexdump_scroll(label="capturando trafico", lines=16, delay=0.07):
    """Hexdump animado de tráfico de red falso."""
    print(GR + f"  [{label}]" + X)
    offset = random.randint(0x0000, 0x0200)
    for i in range(lines):
        hexpart = " ".join(f"{random.randint(0,255):02x}" for _ in range(16))
        ascpart = "".join(chr(random.randint(0x20,0x7e)) if random.random()>0.4 else '.' for _ in range(16))
        addr = offset + i * 16
        print(GR + f"  {addr:08x}  {hexpart}  |{ascpart}|" + X)
        p(delay)

def alert_screen(text, col=R, n=5):
    """Pantalla de alerta a pantalla completa."""
    cls()
    h = H(); w = W()
    mid = h // 2 - 2
    hide_cursor()
    for _ in range(n):
        cls()
        print("\n" * mid)
        print(col+BD + ("█"*w))
        print(text.center(w))
        print(text.center(w))
        print(("█"*w) + X)
        sys.stdout.flush()
        snd_beep(800, 0.12, 0.6)
        p(0.3)
        cls()
        p(0.2)
    show_cursor()

def prm(host="$", col=G): tln(f"\n  {host} ", 0.04, col)
def cmd(c, delay=0.05):
    for ch in c:
        sys.stdout.write(WC + ch + X)
        sys.stdout.flush()
        snd_keyclick()
        p(delay + random.uniform(-0.01, 0.015))
    print()

def ask_skip(label="audio"):
    """Retorna True si el usuario quiere saltar el audio."""
    ans = input(C+BD + f"  [ ENTER = escuchar {label}  |  s = saltar ] " + X).strip().lower()
    return ans.startswith('s')

def bar(label, w=None, speed=0.038, col=G):
    bw = w or max(10, W()-len(label)-12)
    sys.stdout.write(f"  {col}{label} [{X}"); sys.stdout.flush()
    for _ in range(bw):
        p(speed+random.uniform(0,0.012))
        sys.stdout.write(G+"█"+X); sys.stdout.flush()
    sys.stdout.write(G+"] "+WC+BD+"OK\n"+X); sys.stdout.flush()

# ══════════════════════════════════════════════════════════════════════════════
#  BIOS + CONEXIÓN DESDE LA MÁQUINA DE KEVIN
# ══════════════════════════════════════════════════════════════════════════════
def cap_toshiba():
    """Simula el boot del Toshiba T1960CS de Mitnick y la conexión desde Raleigh."""
    hide_cursor(); cls()
    w = W()
    amber = "\033[33m"   # color ámbar BIOS antiguo

    # BIOS POST
    bios_lines = [
        "",
        "Award Software International, Inc.  BIOS v4.51PG",
        "Copyright (C) 1984-1994, Award Software International, Inc.",
        "",
        "Toshiba Satellite T1960CS  BIOS v1.30  486DX2/66MHz",
        "",
        "Testing Memory: ",
    ]
    for line in bios_lines:
        if "Testing" in line:
            sys.stdout.write(amber + "  " + line); sys.stdout.flush()
        else:
            print(amber + "  " + line)
        p(0.12)

    # memory count
    for kb in range(0, 8193, 512):
        sys.stdout.write(f"\r{amber}  Testing Memory: {kb}K   "); sys.stdout.flush()
        p(0.04)
    print(f"\r{amber}  Testing Memory: 8192K OK   " + X)
    p(0.3)

    post = [
        "",
        "  Detecting IDE Master Drive... TOSHIBA MK1924FCV  203MB  OK",
        "  Detecting IDE Slave Drive ...  None",
        "  Floppy Disk Drive A: 1.44MB  OK",
        "  Serial Port COM1: 3F8h  IRQ4  OK",
        "  Internal Modem  COM2: 2F8h  IRQ3  OK",
        "  PCMCIA Slot: GTE Cellular Ready   OK",
        "",
        "  Press DEL to enter setup...",
        "",
    ]
    for l in post:
        print(amber + l + X); p(0.1)

    p(0.5)
    snd_beep(800, 0.05, 0.3)

    # Boot Linux
    print(DG + "  Loading Linux..." + X); p(0.4)
    boot = [
        "Linux 1.2.13 #1 Thu Aug 15 12:04:33 EDT 1994 (i486)",
        "Calibrating delay loop..  ok - 66.24 BogoMIPS",
        "Memory: 7524k/8192k available",
        "hda: TOSHIBA MK1924FCV, 203MB w/0kB Cache",
        "com2: GTE Cellular PCMCIA 14400 baud  OK",
        "",
    ]
    for l in boot:
        print(GR + "  " + l + X); p(0.08)

    p(0.3)
    print(GR + "  login: " + X, end=""); sys.stdout.flush(); p(0.4)
    typ("condor", 0.09, WC); p(0.2)
    print(GR + "  password: " + X, end=""); sys.stdout.flush(); p(0.3)
    typ("••••••••", 0.07, GR); p(0.3)
    print()
    print(GR + '  Last login: Wed Feb  8 23:47 1995 from localhost' + X)
    print(WC + '  Linux 1.2.13  "condor@darkside" — Raleigh, NC' + X)
    print()
    p(0.5)

    # Conexión modem
    HR("─", DG)
    print(DG + BD + "  CONEXIÓN VÍA MÓDEM CELULAR — GTE Cellular / Raleigh NC" + X)
    HR("─", DG)
    print()

    tln("  condor@darkside:~$ ", 0.04, G); cmd("cu -l /dev/com2 -s 14400"); p(0.3)
    print()

    modem_seq = [
        ("AT",          "OK"),
        ("ATZ",         "OK"),
        ("ATE0V1",      "OK"),
        ("ATM1L2",      "OK"),
        ("ATDT*99***1#",""),
    ]
    for cmd_at, resp in modem_seq:
        tln("  ", 0.01, GR); typ(cmd_at, 0.07, WC)
        if resp:
            p(0.15); print(GR + "  " + resp + X)
        p(0.12)

    print(); sys.stdout.flush()
    snd_modem(bg=False)
    print()

    connect_seq = [
        "RING",
        "CONNECT 14400/ARQ/V42",
        "",
        "GTE Cellular Data Network — Raleigh, NC",
        "PPP Authentication...",
    ]
    for l in connect_seq:
        print(GR + "  " + l + X); p(0.25)

    spinner("Negociando PPP / LCP...", 1.5, G)
    spinner("Autenticando CHAP...", 1.2, G)
    snd_success()
    print()
    print(G + BD + "  PPP link established." + X)
    print(G + "  Local  IP : 205.215.0.47" + X)
    print(G + "  Remote IP : 205.215.0.1  (GTE Cellular Gateway, Raleigh NC)" + X)
    print(G + "  MTU       : 1500  MRU: 1500  Speed: 14400 bps" + X)
    print()
    p(0.5)
    print(Y + BD + "  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" + X)
    print(Y + BD + "  Conectado como: condor" + X)
    print(Y + BD + "  Desde:          Surrey House Apt 202-D, Raleigh NC 27612" + X)
    print(Y + BD + "  IP asignada:    205.215.0.47  (GTE Cellular)" + X)
    print(Y + BD + "  Fecha:          14 Febrero 1995  —  11:42 PM EST" + X)
    print(Y + BD + "  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" + X)
    print()
    p(0.6)

    # Salto a Netcom
    tln("  condor@darkside:~$ ", 0.04, G); cmd("telnet netcom-rtp1.netcom.com"); p(0.4)
    snd_data(0.6)
    print()
    print(GR + "  Trying 192.100.81.101..." + X); p(0.3)
    print(GR + "  Connected to netcom-rtp1.netcom.com" + X); p(0.2)
    print(GR + "  Escape character is '^]'." + X); p(0.2)
    print()
    print(C + "  NETCOM On-line Communication Services" + X)
    print(GR + "  login: " + X, end=""); sys.stdout.flush()
    typ("gkremen", 0.08, WC); p(0.2)
    print(GR + "  password: " + X, end=""); sys.stdout.flush()
    typ("•••••••", 0.07, GR)
    print()
    p(0.4)
    snd_alert()
    print(G + BD + "  Last login: Mon Feb 13 23:11 1995 from NETCOM-rtp1" + X)
    print(GR + "  netcom-rtp1%  _" + X)
    print()
    p(0.8)
    print(R + BD + "  Lo que Mitnick no sabe:".center(w) + X)
    print(R + "  Shimomura lleva 5 días en Raleigh. Esta noche da su última ubicación al FBI.".center(w) + X)
    print(R + "  Está analizando cada conexión de gkremen en tiempo real.".center(w) + X)
    print()
    p(1.5)
    show_cursor()
    input(C + BD + "\n  [ ENTER → Comienza la historia ] " + X)

# ══════════════════════════════════════════════════════════════════════════════
#  THE WELL — DONDE TODO CONVERGE
# ══════════════════════════════════════════════════════════════════════════════
def cap_the_well():
    chapter_title(7, "THE WELL", "23 Enero 1995 — San Francisco — El error que lo delató")
    cls()

    typ("  The WELL — Whole Earth 'Lectronic Link.", 0.022, WC)
    typ("  Una de las primeras comunidades online del mundo. San Francisco, 1985.", 0.022, WC)
    typ("  Intelectuales, periodistas, hackers, hippies digitales.", 0.022, WC)
    print()
    p(0.6)
    typ("  Mitnick la usó como vault: guardó ahí los archivos robados.", 0.022, Y)
    typ("  Era discreta, confiable. Nadie sospechaba.", 0.022, Y)
    print()
    p(0.5)

    HR("─", C)
    print(C + BD + "  23 ENERO 1995 — UN USUARIO REPORTA ALGO EXTRAÑO" + X)
    HR("─", C)
    print()
    p(0.4)

    well_log = [
        "  The WELL — syslog — 1995-01-23",
        "",
        "  Jan 23 09:14  login: bruce (bruce@well.com) ttyp3",
        "  Jan 23 09:17  WARNING: disk quota exceeded for user 'jslit'",
        "  Jan 23 09:17  jslit home dir: 6.2 GB (quota: 100 MB) ← ANOMALÍA",
        "",
        "  Admin: 'jslit' reporta no haber subido nada.",
        "  Alguien más está usando su cuenta.",
        "",
    ]
    for l in well_log:
        print(GR + l + X); p(0.15)

    p(0.4)
    spinner("Analizando directorio /home/jslit...", 2.0, Y)
    print()

    files = [
        ("-rw-r--r--  1 jslit  users   1.2G  Jan 20 03:11  shimomura-tools.tar.gz"),
        ("-rw-r--r--  1 jslit  users   892M  Jan 18 02:44  netcom-captures.tar.gz"),
        ("-rw-r--r--  1 jslit  users   445M  Jan 22 01:33  nokia-src.tar.gz"),
        ("-rw-r--r--  1 jslit  users   331M  Jan 21 04:21  motorola-rf.tar.gz"),
        ("-rw-r--r--  1 jslit  users   218M  Jan 19 03:59  sun-solaris-src.tar.gz"),
        ("-rw-r--r--  1 jslit  users   178M  Jan 17 02:10  fujitsu-nets.tar.gz"),
        ("-rw-r--r--  1 jslit  users    44M  Jan 22 05:01  sdsc-sniffer-logs.gz"),
        ("-rw-r--r--  1 jslit  users    12M  Jan 15 01:22  cc-numbers-20k.txt.gz"),
    ]
    print(WC + "  Contenido encontrado en /home/jslit:" + X)
    print()
    for f in files:
        col = R + BD if any(x in f for x in ["shimomura", "netcom-cap", "cc-num"]) else Y
        print(f"  {col}{f}{X}")
        p(0.22)
        snd_beep(440, 0.04)

    print()
    p(0.5)
    snd_alert()
    print(R + BD + "  Los archivos de Shimomura. Los logs de Netcom. +20,000 tarjetas." + X)
    print(R + BD + "  Todo el archivo digital de los crímenes de Mitnick, en un solo lugar." + X)
    print()
    p(0.6)

    print(WC + "  The WELL llama al FBI. El FBI llama a Shimomura." + X)
    print(WC + "  Shimomura analiza los logs de acceso a The WELL." + X)
    print()
    p(0.5)

    access_log = [
        "  well-access.log:",
        "",
        "  1995-01-15  02:44  LOGIN jslit  from: netcom22.netcom.com",
        "  1995-01-17  01:33  LOGIN jslit  from: netcom-rtp1.netcom.com",
        "  1995-01-18  03:11  LOGIN jslit  from: teal.csn.org → netcom22",
        "  1995-01-19  04:01  LOGIN jslit  from: netcom-rtp1.netcom.com",
        "  1995-01-21  02:22  LOGIN jslit  from: netcom-rtp2.netcom.com",
        "  1995-01-22  05:00  LOGIN jslit  from: netcom-rtp1.netcom.com",
        "",
        "  PATRÓN: accesos desde NETCOM-rtp1 y rtp2 (Research Triangle Park, NC)",
    ]
    for l in access_log:
        col = R + BD if "rtp" in l.lower() else GR
        print(col + l + X); p(0.18)

    print()
    p(0.5)
    snd_success()
    print(G + BD + "  RTP = Research Triangle Park — Raleigh, North Carolina." + X)
    print(G + "  El usuario es 'gkremen' en Netcom. Patrón de conexión idéntico." + X)
    print(G + "  Shimomura ya tiene la ciudad. Solo falta la dirección exacta." + X)
    print()
    p(0.8)
    typ("  9 Febrero 1995: Shimomura compra un pasaje a Raleigh.", 0.022, R)
    typ("  El tiempo de Mitnick se acaba.", 0.022, R)
    print()
    p(1.2)
    input(C + BD + "\n  [ ENTER → La triangulación ] " + X)

# ══════════════════════════════════════════════════════════════════════════════
#  FREE KEVIN — EL MOVIMIENTO
# ══════════════════════════════════════════════════════════════════════════════
def cap_free_kevin():
    chapter_title(11, "FREE KEVIN", "El movimiento que cambió la historia de internet")
    cls()

    w = W()
    snd_dramatic()
    p(0.5)

    typ("  15 Febrero 1995. La noticia explota en la comunidad hacker:", 0.022, WC)
    typ("  Kevin Mitnick fue arrestado.", 0.022, WC)
    typ("  La comunidad entra en shock. Luego, en acción.", 0.022, Y)
    print()
    p(0.8)

    HR("═", R)
    print(R + BD + "  LO QUE NADIE CONTABA: EL TRATO INJUSTO" + X)
    HR("═", R)
    print()

    injusticias = [
        ("8 meses en celda de aislamiento", "Sin juicio. Sin condena. Esperando."),
        ("'Puede iniciar una guerra nuclear'", "El fiscal convenció al juez de que Mitnick\n"
         "                                     podía activar armas nucleares silbando\n"
         "                                     en un teléfono público. Sin ninguna prueba."),
        ("3 años sin juicio", "Más tiempo detenido que la condena final."),
        ("Sin fianza", "Por 'peligro para las comunicaciones nacionales'."),
        ("No podía ver el expediente", "Sus abogados no podían revelarle el caso."),
        ("Acceso negado al baño en traslados", "Trato degradante documentado por su abogada."),
    ]
    for titulo, desc in injusticias:
        print(f"  {R + BD}● {titulo}{X}")
        for linea in desc.split("\n"):
            print(f"  {GR}  {linea}{X}")
        print(); p(0.5)

    p(0.5)
    input(C + BD + "  [ ENTER → El movimiento ] " + X)
    cls()

    HR("═", G)
    print(G + BD + "  LA RESPUESTA DE LA COMUNIDAD HACKER" + X)
    HR("═", G)
    print()

    print(C + BD + "  Emmanuel Goldstein — Eric Corley" + X)
    print(WC + "  Fundador de 2600: The Hacker Quarterly" + X)
    print(GR + "  La revista más influyente de la cultura hacker" + X)
    print()
    p(0.5)
    typ('  "Kevin no merece este trato. Ningún hacker merece esto."', 0.022, Y)
    typ("  — Emmanuel Goldstein, entrevista 1995", 0.022, GR)
    print()
    p(0.7)

    acciones = [
        ("Feb 1995",  G,  "freekevin.com lanzado — el primer sitio activista de internet"),
        ("Mar 1995",  G,  "Pegatinas 'FREE KEVIN' aparecen en conferencias DEF CON y CCC"),
        ("May 1995",  Y,  "2600 Magazine dedica número completo al caso Mitnick"),
        ("Ago 1995",  Y,  "Protesta en Los Angeles — 200 hackers frente al tribunal federal"),
        ("1996",      Y,  "John Perry Barlow (EFF) escribe sobre los derechos digitales"),
        ("1997",      C,  "EFF — Electronic Frontier Foundation — toma el caso"),
        ("1998",      C,  "Congresistas reciben peticiones con 20,000 firmas"),
        ("Ene 1999",  G,  "Mitnick acepta plea deal — reconoce 5 cargos para salir"),
        ("Ene 2000",  G,  "Libre. El movimiento ganó. 5 años después del arresto."),
        ("2001",      G,  "El caso se estudia en leyes de EE.UU. — reforma al Computer Fraud Act"),
    ]

    print(WC + BD + f"  {'FECHA':<12}  {'EVENTO'}" + X)
    print(GR + "  " + "─" * (w - 4) + X)
    for fecha, col, evento in acciones:
        print(f"  {Y + BD}{fecha:<12}{X}  {col}{evento}{X}")
        p(0.3)

    print()
    p(0.8)
    HR("─", Y)
    print(Y + BD + "  EL MITO DE LA GUERRA NUCLEAR — Desacreditado" + X)
    HR("─", Y)
    print()
    typ("  El fiscal argumentó que Mitnick podía —desde un teléfono público—", 0.022, WC)
    typ("  'marcar números y causar un caos nacional'.", 0.022, WC)
    typ("  Que podía 'iniciar una guerra nuclear con un silbido'.", 0.022, WC)
    print()
    p(0.4)
    typ("  Esto era FALSO. Ningún experto técnico lo avaló.", 0.022, R)
    typ("  Pero el juez lo creyó. Mitnick pasó 8 meses en confinamiento solitario.", 0.022, R)
    typ("  Un caso de ignorancia tecnológica convertida en crueldad judicial.", 0.022, R)
    print()
    p(0.8)

    big_text([
        "Su crimen fue ser demasiado bueno",
        "en algo que nadie entendía.",
        "",
        "— Comunidad hacker, 1996",
    ], Y)

    p(1.5)
    input(C + BD + "\n  [ ENTER → Su legado ] " + X)

# ══════════════════════════════════════════════════════════════════════════════
#  FREE KEVIN — BANNER ÉPICO FINAL
# ══════════════════════════════════════════════════════════════════════════════
FREE_KEVIN_ART = [
    " ███████╗██████╗ ███████╗███████╗    ██╗  ██╗███████╗██╗   ██╗██╗███╗   ██╗",
    " ██╔════╝██╔══██╗██╔════╝██╔════╝    ██║ ██╔╝██╔════╝██║   ██║██║████╗  ██║",
    " █████╗  ██████╔╝█████╗  █████╗      █████╔╝ █████╗  ██║   ██║██║██╔██╗ ██║",
    " ██╔══╝  ██╔══██╗██╔══╝  ██╔══╝      ██╔═██╗ ██╔══╝  ╚██╗ ██╔╝██║██║╚██╗██║",
    " ██║     ██║  ██║███████╗███████╗    ██║  ██╗███████╗  ╚████╔╝ ██║██║ ╚████║",
    " ╚═╝     ╚═╝  ╚═╝╚══════╝╚══════╝    ╚═╝  ╚═╝╚══════╝   ╚═══╝  ╚═╝╚═╝  ╚═══╝",
]

def free_kevin_finale():
    matrix_rain(3.5)
    cls()
    w = W(); h = H()
    hide_cursor()
    snd_alarm(bg=True)
    p(0.3)

    # Aparece línea a línea con color rojo parpadeante
    mid = max(2, (h - len(FREE_KEVIN_ART) - 10) // 2)
    print("\n" * mid)
    colors = [R, R+BD, Y+BD, G+BD, C+BD, WC+BD]
    for i, line in enumerate(FREE_KEVIN_ART):
        col = colors[i % len(colors)]
        centered = line.center(w)
        print(col + centered + X)
        snd_beep(300 + i * 120, 0.08, 0.6)
        p(0.18)

    print()
    p(0.5)

    subtexts = [
        ("Kevin David Mitnick  ·  1963–2023", WC + BD),
        ("El hacker más buscado de América — liberado, rehabilitado, legendario.", WC),
        ("", ""),
        ('"The art of invisibility is knowing when to be seen."', Y),
        ("                                          — Kevin Mitnick", GR),
        ("", ""),
        ("★  freekevin.com  ·  2600.com  ·  mitnicksecurity.com  ★", DG),
    ]
    for txt, col in subtexts:
        print(col + txt.center(w) + X)
        p(0.35)

    print()
    p(1.0)

    # Pulso de colores sobre el banner — 3 veces
    for flash in range(3):
        for fc in [R+BD, Y+BD, G+BD, C+BD, WC+BD, M+BD]:
            goto(mid + 1, 1)
            for line in FREE_KEVIN_ART:
                sys.stdout.write(fc + line.center(w) + X + "\n")
            sys.stdout.flush()
            p(0.12)
    p(0.5)

    # Últimos sonidos de cierre
    snd_beeps([(440,0.12),(660,0.12),(880,0.15),(1100,0.20)], bg=False)
    p(0.5)
    show_cursor()
    print()
    print(GR + DM + "  [ Demo completado — Presiona Enter ]".center(w) + X)
    input()

# ══════════════════════════════════════════════════════════════════════════════
#  BANNER SAS  (Sprint Switched Access Services A0344462 — película Takedown 2000)
# ══════════════════════════════════════════════════════════════════════════════
SAS = [
    "         SSSSS           AAAAA           SSSSS",
    "       SSSSSSS          AAAAAAA        SSSSSSS",
    "      SSS  SSS         AAA  AAA       SSS  SSS",
    "      SSSSS            AAA  AAA       SSSSS   ",
    "      SSSSS            AAAAAAAAA      SSSSS   ",
    "       SSSSS           AAAAAAAAA       SSSSS  ",
    "         SSS           AAA  AAA          SSS  ",
    "      SSS  SSS  %%     AAA  AAA  %%   SSS  SSS  %%",
    "      SSSSSSS   %%     AAA  AAA  %%   SSSSSSS   %%",
    "       SSSSS    %%     AAA  AAA  %%    SSSSS    %%",
]

def scale_art(art, sx=2, sy=2):
    """Escala ASCII art: sx multiplicador ancho, sy multiplicador alto."""
    out = []
    for line in art:
        scaled = "".join(ch * sx for ch in line)
        for _ in range(sy):
            out.append(scaled)
    return out

# ══════════════════════════════════════════════════════════════════════════════
#  ESCENA 0 — APERTURA ÉPICA
# ══════════════════════════════════════════════════════════════════════════════
def escena_boot():
    hide_cursor()
    matrix_rain(4.0, overlay_text=[
        "[ O P E R A C I O N   T A K E D O W N ]",
        "",
        "Kevin Mitnick — El Hacker mas Buscado de America",
        "1994 - 1995",
    ])
    p(0.5)
    cls()
    snd_static(0.5)
    noise_line(4)
    p(0.2)
    cls()
    p(0.3)
    snd_crt()

    w = W()
    sx = 2 if w >= 100 else 1
    sas_big = scale_art(SAS, sx=sx, sy=2)
    print()
    for i, linea in enumerate(sas_big):
        linea_c = linea.center(w)
        centrada = linea_c.replace("%%", Y+BD+"%%"+X+GR+DM)
        orig_i = i // 2
        if orig_i < 4 and (i % 2 == 0):
            snd_beep(180+orig_i*60, 0.04, 0.12)
        print(GR+DM + centrada + X)
        p(0.03)

    print()
    for txt in ["SWITCHED ACCESS SERVICES", "A0344462  ISSUE 2",
                "RELEASE NOTES — SPRINT COMMUNICATIONS CO.",
                "","[ Dramatizacion — Pelicula Takedown, 2000 ]"]:
        col = GR+DM if "[" in txt else Y+BD if txt else ""
        print(col + txt.center(w) + X if txt else "")
        p(0.25)

    print()
    snd_beeps([(440,0.08),(880,0.12)])
    p(0.5)

    # Cursor CRT parpadeante
    for _ in range(8):
        sys.stdout.write(G+"█"+X+"\r"); sys.stdout.flush(); p(0.3)
        sys.stdout.write("  \r"); sys.stdout.flush(); p(0.22)
    print()
    show_cursor()
    p(0.4)
    print()
    print(C+BD + "  Presiona ENTER para comenzar".center(w) + X)
    input()

# ══════════════════════════════════════════════════════════════════════════════
#  CAP 1 — KEVIN MITNICK: EL FUGITIVO
# ══════════════════════════════════════════════════════════════════════════════
def cap_perfil():
    chapter_title(1, "EL HOMBRE MÁS BUSCADO", "Kevin Mitnick — El Fugitivo Digital")
    cls()
    snd_heartbeat(3)

    # Simulación de búsqueda en base de datos FBI
    print(R+BD + "  ┌" + "─"*(W()-4) + "┐" + X)
    print(R+BD + "  │" + " FBI NATIONAL CRIME INFORMATION CENTER — FUGITIVE SEARCH ".center(W()-4) + "│" + X)
    print(R+BD + "  └" + "─"*(W()-4) + "┘" + X)
    print()
    p(0.4)

    spinner("Buscando en base de datos federal...", 2.5, R)
    p(0.3)
    snd_alert()

    w = W()
    # Cargar foto
    PHOTO_W = 34
    photo_lines = []
    photo_path = os.path.join(SCRIPT_DIR, "mitnick.jpg")
    if os.path.exists(photo_path):
        try:
            res = subprocess.run(
                ['chafa', '--format', 'ansi', '--size', f'{PHOTO_W}x20', photo_path],
                capture_output=True, text=True
            )
            if res.returncode == 0:
                photo_lines = [l for l in res.stdout.split('\n') if l]
        except FileNotFoundError:
            pass

    datos = [
        ("NOMBRE",       "Kevin David Mitnick"),
        ("ALIAS",        "condor · The Darkside Hacker · gkremen"),
        ("NACIMIENTO",   "6 Agosto 1963, Van Nuys, California"),
        ("ESTATURA",     "1.87 m  Cabello oscuro  Lentes"),
        ("ESTADO",       "FUGITIVO — 3 anos en clandestinidad"),
        ("PELIGROSIDAD", "EXTREMA — Redes militares comprometidas"),
        ("UBICACION",    "Raleigh, North Carolina — Dic 1994"),
        ("",             ""),
        ("CARGOS",       "Computer Fraud · Wire Fraud · Theft Trade Secrets"),
        ("RECOMPENSA",   "Se solicita informacion — FBI Field Office"),
    ]

    # ╔ header ╗ (ancho completo)
    print()
    print(R+BD + "  ╔" + "═"*(w-4) + "╗" + X)
    print(R+BD + "  ║" + " ⚠  FUGITIVO ACTIVO — MAXIMA PRIORIDAD — FBI NCIC ".center(w-4) + "║" + X)
    print(R+BD + "  ╠" + "═"*(w-4) + "╣" + X)

    # Dos columnas: foto izquierda | datos derecha
    # Layout visual por fila:
    #   "  ║" (3) + "  " (2) + photo (PHOTO_W) + "  " (2) + data_visual + "║" (1) = w
    # → data_visual = w - 3 - 2 - PHOTO_W - 2 - 1 = w - PHOTO_W - 8
    DATA_VIS = w - PHOTO_W - 8

    total_rows = max(len(photo_lines), len(datos))
    for i in range(total_rows):
        ph = photo_lines[i] if i < len(photo_lines) else " " * PHOTO_W
        if i < len(datos):
            k, v = datos[i]
            if k == "":
                data_str = " " * DATA_VIS
            else:
                content_vis = 2 + 16 + 2 + len(v)
                pad = max(0, DATA_VIS - content_vis)
                data_str = f"  {Y}{BD}{k:<16}{X}  {WC}{v}" + " " * pad
        else:
            data_str = " " * DATA_VIS
        print(R+"  ║"+X + "  " + ph + "  " + data_str + R+"║"+X)
        p(0.09)

    # Fila titulo foto + separador
    foto_label = "U.S. MARSHALS WANTED POSTER".center(PHOTO_W+4)
    print(R+BD + "  ╠" + "═"*(w-4) + "╣" + X)
    print(R+BD + "  ║" + foto_label + " CASO: USA v. Mitnick  CR-95-0132-RMT".ljust(w-4-len(foto_label)) + "║" + X)
    print(R+BD + "  ╚" + "═"*(w-4) + "╝" + X)
    p(0.8)

    print()
    typ("  Kevin Mitnick no era un criminal cualquiera.", 0.025, WC)
    typ("  Era alguien que podía entrar a CUALQUIER sistema... con una llamada.", 0.025, WC)
    print()
    p(0.5)

    hitos = [
        ("12 años", G,  "Engaña al conductor del bus de L.A. para viajar gratis — primer hack"),
        ("13 años", G,  "Aprende phone phreaking — llama gratis a cualquier parte del mundo"),
        ("16 años", Y,  "Entra al sistema ARPANET del Pentágono — primer gran sistema"),
        ("17 años", Y,  "Primer arresto — acceso a DEC VMS. Probation."),
        ("25 años", Y,  "Viola probation. Entra a Motorola, Nokia, Sun. Fugitivo."),
        ("28 años", R,  "FBI lo persigue. Cambia de ciudad cada mes. Sigue hackeando."),
        ("31 años", R,  "Diciembre 1994 — El mayor error de su vida: ataca a Shimomura."),
    ]

    print()
    for edad, col, hecho in hitos:
        print(f"  {col}{BD}[{edad:<8}]{X}  {WC}{hecho}{X}")
        p(0.3)

    print()
    p(0.8)
    HR("─",G)
    print()
    typ("  Lo que no sabía Mitnick:", 0.025, WC)
    typ("  Tsutomu Shimomura no era un investigador cualquiera.", 0.025, WC)
    typ("  Era el mejor experto en seguridad de redes de los Estados Unidos.", 0.025, R)
    print()
    p(1.2)
    input(C+BD + "\n  [ ENTER → El ataque de Navidad ] " + X)

# ══════════════════════════════════════════════════════════════════════════════
#  CAP 2 — EL ATAQUE DE NAVIDAD
# ══════════════════════════════════════════════════════════════════════════════
def cap_ataque():
    chapter_title(2, "EL ATAQUE DE NAVIDAD", "25 Diciembre 1994 — 14:09 PST")

    cls()
    w = W()
    print(Y+BD + "  25 de Diciembre de 1994. Nochebuena.".center(w) + X)
    print(WC + "  Shimomura está esquiando en Lake Tahoe.".center(w) + X)
    print(WC + "  Sus computadoras en San Diego están solas.".center(w) + X)
    print()
    p(0.8)
    print(R+BD + "  A las 2:09 PM... alguien lanza un ataque nunca visto antes.".center(w) + X)
    print(R+BD + "  IP Spoofing + TCP Sequence Number Prediction.".center(w) + X)
    print(R+BD + "  Teóricamente posible desde 1985. Nunca ejecutado en la realidad.".center(w) + X)
    print()
    p(1.0)

    # Topología de la red objetivo
    HR("─",G)
    print(G+BD + "  TOPOLOGÍA DE RED — SDSC (San Diego Supercomputer Center)" + X)
    HR("─",G)
    print()

    topo_rows = [
        "",
        "    [INTERNET]",
        "        │",
        "        ▼",
        "   ┌─────────────┐  RSH TRUST  ┌─────────────┐",
        "   │   "+Y+"osiris"+G+"    │ ◄────────── │ "+C+"x-terminal"+G+" │  (Shimomura's WS)",
        "   │ sdsc.edu    │             │  sdsc.edu   │",
        "   └─────────────┘             └─────────────┘",
        "          │",
        "          │ RSH TRUST",
        "          ▼",
        "   ┌─────────────┐             ┌─────────────┐",
        "   │  "+R+BD+"rimmon"+G+"    │ ── NFS ───► │    ariel    │",
        "   │ sdsc.edu    │             │  sdsc.edu   │",
        "   └─────────────┘             └─────────────┘",
        "",
        "   "+R+BD+"OBJETIVO"+G+": entrar como root en "+R+BD+"rimmon"+G+" spoofando "+Y+"osiris"+G,
    ]
    box_top(G)
    for row in topo_rows:
        box_row(G + row, G); p(0.05)
    box_bot(G)

    p(0.8)
    print()
    input(C + "  [ ENTER → Ver el hack en tiempo real ] " + X)

    cls()
    HR("─",G)
    print(G+BD + "  TERMINAL — Mitnick@darkside  |  25 Dic 1994  14:09 PST" + X)
    HR("─",G)
    print()
    p(0.5)

    # FASE 1: Reconocimiento
    print(DG + "\n  ══ FASE 1: RECONOCIMIENTO ══════════════════════════════════════════\n" + X)
    prm(); cmd("finger -l @rimmon.sdsc.edu")
    for l in ["[rimmon.sdsc.edu]",
              "Login: tsutomu           Name: Tsutomu Shimomura",
              "Last login Sat Dec 24 11:43 (PST) on ttyp2 from x-terminal",
              "No unread mail."]:
        print(GR+"  "+l+X); p(0.1)

    prm(); cmd("rpcinfo -p rimmon.sdsc.edu")
    for s in ["  portmapper 100000/tcp/111","  mountd 100005/udp/765",
              "  nfs     100003/udp/2049","  status  100024/tcp/705"]:
        print(GR+s+X); p(0.09)

    prm(); cmd("showmount -e rimmon.sdsc.edu")
    print(GR+"  /home/tsutomu   osiris.sdsc.edu"+X)
    print(GR+"  /scratch        (everyone)"+X)
    p(0.5)
    snd_beep(660,0.08)
    print(DG+"\n  # osiris tiene acceso NFS al home de Shimomura. Perfecto."+X)
    print(DG+"  # rimmon confía en osiris via rsh sin password. El vector de ataque está listo."+X)
    p(0.8)

    # FASE 2: SYN Flood
    print(DG + "\n  ══ FASE 2: SYN FLOOD — Silenciando osiris ═══════════════════════════\n" + X)
    prm(); cmd("syn_flood osiris.sdsc.edu 514 25")
    p(0.3)
    snd_data(1.5)
    print()
    for i in range(10):
        src=f"172.{random.randint(16,31)}.{random.randint(1,254)}.{random.randint(2,253)}"
        seq=random.randint(0x10000000,0xffffffff)
        print(GR+f"  [{i+1:02d}] SYN  {src}:{random.randint(10000,65000)} → osiris:514  seq={seq:#010x}"+X)
        p(0.1)
    print()
    snd_alert()
    print(Y+BD+"  [!] Cola SYN de osiris DESBORDADA — ya no puede responder RST"+X)
    print(Y+"  [!] osiris está ciego. Ahora podemos suplantar su IP sin ser detectados."+X)
    p(0.8)

    # FASE 3: Predicción ISN
    print(DG + "\n  ══ FASE 3: TCP ISN PREDICTION — El corazon del ataque ══════════════\n" + X)
    input(C + "  [ ENTER → Ver como funciona la prediccion ISN ] " + X)
    cls()

    print(Y+BD + "  LA VULNERABILIDAD — Robert T. Morris, 1985" + X)
    print(GR + "  Paper: 'A Weakness in the 4.2BSD UNIX TCP/IP Software'" + X)
    print(GR + "  Publicado 10 años antes. Nunca nadie lo habia ejecutado en produccion." + X)
    print()
    p(0.5)

    print(WC + "  El problema central de TCP/IP en BSD (SunOS es derivado de BSD):" + X)
    print()
    print(Y + "  Para establecer una conexion TCP, ambos lados hacen un 'handshake' de 3 pasos:" + X)
    print()
    box_top(C)
    box_row(C + "  Cliente  →  SYN (seq=X)          →  Servidor", C)
    box_row(C + "  Cliente  ←  SYN-ACK (seq=Y, ack=X+1)  ←  Servidor", C)
    box_row(C + "  Cliente  →  ACK (ack=Y+1)         →  Servidor", C)
    box_row(C + "", C)
    box_row(C + "  Y = ISN (Initial Sequence Number) generado por el servidor", C)
    box_row(C + "  Para completar el handshake, el cliente DEBE conocer Y (para enviar Y+1)", C)
    box_bot(C)
    print()
    p(0.8)

    print(R+BD + "  EL BUG: En BSD 4.2, el ISN NO era aleatorio." + X)
    print(WC + "  El kernel incrementaba un contador global exactamente:" + X)
    print(Y+BD + "    +128,000  cada segundo  (constante del sistema)" + X)
    print(Y+BD + "    +64,000   por cada nueva conexion TCP creada" + X)
    print()
    print(WC + "  En SunOS 4.1.3 (rimmon/x-terminal): incremento medido = 0x20000 (131,072)" + X)
    print(WC + "  por cada medio segundo aproximadamente." + X)
    print()
    p(0.6)

    print(G+BD + "  LA TECNICA DE MITNICK — 3 pasos:" + X)
    print()
    print(G + "  1. MEDIR: Enviar SYNs a x-terminal y medir los ISN que responde" + X)
    print(G + "  2. CALCULAR: Predecir el ISN que asignara a la proxima conexion" + X)
    print(G + "  3. RESPONDER CIEGO: Enviar ACK con el valor predicho sin ver el SYN-ACK" + X)
    print()
    p(0.5)

    print(DG + "  --- Por que 'ciego'? ---" + X)
    print(WC + "  Cuando Mitnick spoofeaba desde osiris, x-terminal enviaba el SYN-ACK" + X)
    print(WC + "  a osiris (IP real). Mitnick nunca veia ese paquete." + X)
    print(WC + "  Pero si calculaba el ISN correctamente, su ACK forjado completaba" + X)
    print(WC + "  el handshake. x-terminal no podia distinguirlo de osiris real." + X)
    print()
    p(0.8)

    print(Y+BD + "  MUESTREO en vivo — probe_isn mide el patron:" + X)
    print()
    prm(); cmd("probe_isn x-terminal.sdsc.edu 513 6")
    p(0.3); snd_data(0.5)
    base = 0x3DA00000
    for i in range(6):
        isn = base + i*0x20000 + random.randint(0, 0x200)
        delta = "" if i == 0 else f"  delta=+{0x20000:#06x}"
        print(GR+f"  [{i+1}] SYN→513  SYN-ACK rcv  ISN={isn:#010x}{delta}"+X)
        p(0.22)
    print()
    snd_success()
    print(G+BD + "  [+] PATRON CONFIRMADO: ISN sube exactamente +0x00020000 por conexion" + X)
    print(G + "  [+] El proximo ISN sera: ~0x" + format(base + 6*0x20000, '08X') + " (±margen de timing)" + X)
    print(G + "  [+] Enviamos SYN desde osiris, calculamos Y, enviamos ACK(Y+1) ciego." + X)
    p(0.8)

    # Diagrama animado del handshake spoofado
    input(C + "  [ ENTER → Ver el handshake imposible en diagrama ] " + X)
    cls()
    w = W()
    pred_isn = base + 7*0x20000
    print()
    print(Y+BD + "  EL HANDSHAKE CIEGO — paso a paso".center(w) + X)
    print(GR + "  (Mitnick nunca ve los paquetes que recibe osiris — actúa 'a ciegas')".center(w) + X)
    print()
    steps = [
        (C,  " MITNICK           ",  "SYN (src=osiris) seq=0xdeadbeef  ──────────────►",  "  x-terminal",  DG,
              "   x-terminal recibe SYN creyendo que viene de osiris."),
        (GR, " x-terminal        ",  "SYN-ACK seq="+format(pred_isn,'#010x')+"  ──────────────►",  "  osiris (sordo!)",  R,
              "   SYN-ACK va a osiris real — Mitnick NUNCA lo ve."),
        (Y,  " MITNICK (CIEGO)   ",  "ACK ack="+format(pred_isn+1,'#010x')+"  ──────────────►",  "  x-terminal",  G,
              "   Mitnick calcula el ACK sin haberlo visto. Si acierta..."),
        (G,  " x-terminal        ",  "                  CONEXIÓN ESTABLECIDA  ✓       ",  "  MITNICK=osiris", G,
              "   x-terminal cree hablar con osiris. El handshake está completo."),
    ]
    col_left = 22; col_arrow = 50
    for i, (lc, left, arrow, right, rc, note) in enumerate(steps):
        p(0.3)
        snd_beep(440 + i*120, 0.06, 0.3)
        print(f"  {lc+BD}{left}{X}  {WC}{arrow}{X}  {rc+BD}{right}{X}")
        p(0.15)
        print(GR + f"  {'':22}{note}" + X)
        print()
        p(0.5)
    p(0.4)
    print(R+BD + "  El truco: BSD usaba ISN predecible. Mitnick calculó el número exacto.".center(w) + X)
    print(R    + "  Después de esto: este bug fue parchado en TODOS los sistemas Unix.".center(w) + X)
    p(1.0)

    # FASE 4: El exploit
    print(DG + "\n  ══ FASE 4: IP SPOOFING — El ataque ═════════════════════════════════\n" + X)
    prm(); cmd("rsh_spoof -src osiris.sdsc.edu -dst x-terminal.sdsc.edu \\")
    prm(); cmd("         -isn 0x3da0ff02 -cmd 'rsh -l root rimmon echo \"++ ++\" >>/.rhosts'")
    p(0.5)
    bar("  Forjando cabecera IP          ", speed=0.06, col=Y)
    bar("  Calculando TCP checksum       ", speed=0.055, col=Y)
    bar("  Inyectando paquete           ", speed=0.06, col=G)
    p(0.3)
    snd_success()
    print(G+BD+"\n  [+] x-terminal acepta el paquete falso (cree que es osiris)"+X)
    print(G+"  [+] Ejecuta: rsh -l root rimmon 'echo ++ >> /.rhosts'"+X)
    print(G+"  [+] rimmon ahora permite acceso root SIN PASSWORD desde cualquier IP"+X)
    p(1.0)

    # FASE 5: Dentro del sistema
    print(DG + "\n  ══ FASE 5: DENTRO DEL SISTEMA DE SHIMOMURA ════════════════════════\n" + X)
    prm(); cmd("rsh -l root rimmon.sdsc.edu")
    p(0.4); snd_modem()
    print()
    print(G+BD+"  rimmon# "+X,end=""); p(0.5); print()

    cmds_post = [
        ("id",               "uid=0(root) gid=0(root) groups=0(root)"),
        ("uname -a",         "SunOS rimmon.sdsc.edu 4.1.3_U1 2 sun4c sparc SUNW,Sun_4_60"),
        ("uptime",           " 2:18pm  up 12 days, 4:03,  1 user,  load average: 0.05"),
        ("cat /etc/passwd",  "root:x:0:0:System Administrator:/:/bin/csh\ntsutomu:x:1001:100:Tsutomu Shimomura:/home/tsutomu:/bin/csh"),
        ("ls /home/tsutomu", ".cshrc  .login  .rhosts  bin  etc  lib  src  security-tools"),
        ("cat /home/tsutomu/.rhosts", "x-terminal.sdsc.edu  tsutomu\nrimmon.sdsc.edu  root"),
    ]
    for c, out in cmds_post:
        tln("  rimmon# ", 0.04, G); cmd(c, 0.055); p(0.2)
        for ol in out.split("\n"): print(GR+"  "+ol+X)
        p(0.3)

    p(0.5)
    # Instalar backdoor — datos REALES del análisis forense
    print(DG+"\n  # 14:21 — Instalando backdoor telnet sniffer + módulo kernel"+X)
    print(DG+"  # (Tiempos exactos: análisis forense Shimomura — takedown.com)"+X)
    print()

    tln("  rimmon# ",0.04,G); cmd("uudecode </tmp/.xdata && gunzip /tmp/telnet.gz")
    bar("  Transfiriendo herramientas    ", speed=0.05, col=Y)

    tln("  rimmon# ",0.04,G); cmd("cc -O -o /tmp/.telnet /tmp/telnet.c")
    p(0.3)
    spinner("Compilando telnet sniffer... (19 segundos según análisis forense)", 2.5, Y)

    tln("  rimmon# ",0.04,G); cmd("cc -O -o /tmp/tap /tmp/tap.c && modload /tmp/tap")
    spinner("Compilando y cargando módulo kernel...", 2.0, Y)

    tln("  rimmon# ",0.04,G); cmd("mknod /dev/tap c 11 0 && chmod 0777 /dev/tap")
    p(0.2)
    print(G+"  crwxrwxrwx  1 root  wheel  11, 0  Dec 25 14:37  /dev/tap"+X)
    p(0.3)
    snd_success()
    print(G+BD+"\n  [+] /dev/tap activo — TODO lo que pase por rimmon queda grabado"+X)
    print(G+"  [+] Propagando a ariel.sdsc.edu..."+X)
    p(0.5)
    bar("  Instalando en ariel.sdsc.edu  ", speed=0.045, col=G)

    tln("  rimmon# ",0.04,G); cmd("touch -t 199412231200 /tmp/.telnet /tmp/tap /dev/tap")
    print(GR+"  Timestamps camuflados: Dec 23 12:00 — antes del ataque"+X)
    p(0.3)
    tln("  rimmon# ",0.04,G); cmd("exit")
    print(GR+"  Connection to rimmon.sdsc.edu closed."+X)
    p(3.0)
    glitch_screen(2.2)
    alert_screen("  ⚡  SISTEMA DE SHIMOMURA COMPROMETIDO  ⚡  ", R, 3)
    cls()
    print()
    big_text([
        "ATAQUE COMPLETADO",
        "Duración total: 59 minutos",
        "Sistemas: rimmon · x-terminal · ariel",
        "Backdoors instaladas. Nadie lo sabe... todavía.",
    ], G)
    p(2.0)
    input(C+BD + "\n  [ ENTER → Shimomura descubre el ataque ] " + X)

# ══════════════════════════════════════════════════════════════════════════════
#  CAP 3 — SHIMOMURA RESPONDE
# ══════════════════════════════════════════════════════════════════════════════
def cap_shimomura():
    chapter_title(3, "SHIMOMURA DESCUBRE EL ATAQUE", "26-28 Diciembre 1994 — San Diego")
    cls()

    typ("  Andrew Gross llama a Shimomura a Lake Tahoe:", 0.022, WC)
    typ('  "Tsutomu... hay algo muy raro en los logs de rimmon."', 0.022, Y)
    print()
    typ("  Shimomura corta las vacaciones. Regresa a San Diego.", 0.022, WC)
    typ("  Tres días analizando cada inode, cada timestamp, cada paquete.", 0.022, WC)
    print()
    p(0.8)

    HR("─",C)
    print(C+BD+"  ANÁLISIS FORENSE — Fuente real: state-analysis.html (takedown.com)" + X)
    HR("─",C)
    print()

    print(WC+BD+f"  {'HORA PST':<10}  {'SISTEMA':<16}  {'QUÉ PASÓ (DATOS REALES)'}"+X)
    print(GR+"  "+"─"*(W()-4)+X)

    forense = [
        ("13:50","rimmon","finger @rimmon @osiris — reconocimiento inicial"),
        ("14:09","x-terminal","SYN flood desde server.internet.com — puerto 514 saturado"),
        ("14:09","osiris","25 paquetes SYN sin RST — cola desbordada, cegado"),
        ("14:18","rimmon","rsh LOGIN COMO ROOT — IP origen: osiris (¡SPOOFADA!)"),
        ("14:19","rimmon","uname · id · file · head · netstat · cat /etc/passwd"),
        ("14:21","rimmon","uudecode data.uu → telnet.gz descomprimido"),
        ("14:21","rimmon","cc -O telnet.c → compilado en exactamente 19 segundos"),
        ("14:37","rimmon","cc -O tap.c → módulo kernel compilado"),
        ("14:37","rimmon","modload tap → MÓDULO CARGADO EN KERNEL SunOS"),
        ("14:37","rimmon","mknod /dev/tap crwxrwxrwx — backdoor ACTIVA"),
        ("14:40","ariel","MISMO PATRÓN — propagación lateral automática"),
        ("14:51","ariel","touch timestamps — intento de borrar huellas"),
        ("15:08","rimmon","Sesión cerrada. Atacante desaparece."),
    ]
    for hora, host, evento in forense:
        col = R if any(w in evento for w in ["SPOOFADA","MÓDULO","backdoor","MISMO","CARGADO"]) else GR
        print(f"  {Y}{hora}{X}  {C}{host:<16}{X}  {col}{evento}{X}")
        p(0.18)
        if "MÓDULO" in evento or "SPOOFADA" in evento: snd_beep(440,0.05)

    print()
    p(0.8)
    spinner("Shimomura reconstruye el ataque paso a paso...", 3.0, C)
    print()
    print(GR + "  [Reproduciendo tráfico capturado por /dev/tap — rimmon.sdsc.edu]" + X)
    p(0.3)
    hexdump_scroll("tcpdump -r rimmon-tap.pcap | head", lines=12, delay=0.06)
    print()
    snd_alert()
    print(R+BD+"  ¡Es IP Spoofing + TCP ISN Prediction ejecutado en la vida real!"+X)
    print(WC+"  Solo se había teorizado en 1985. NADIE lo había hecho antes en producción."+X)
    print()
    p(0.8)
    typ("  1 Enero 1995: Shimomura presenta el exploit en la conferencia CMAD.", 0.022, Y)
    typ("  15 Enero 1995: New York Times publica el ataque en primera plana.", 0.022, Y)
    typ("  El FBI activa recursos. El mundo queda en shock.", 0.022, R)
    print()
    p(1.0)
    input(C+BD+"\n  [ ENTER → Los mensajes de voz ] "+X)

# ══════════════════════════════════════════════════════════════════════════════
#  CAP 4 — VOICEMAILS REALES
# ══════════════════════════════════════════════════════════════════════════════
def cap_voicemail():
    chapter_title(4, "LOS MENSAJES DE VOZ", "Dic 1994 — Feb 1995 — Audios REALES de takedown.com")
    cls()

    print(GR+DM+"  Fuente: takedown.com/evidence/voicemail/ — 6 mensajes reales en el contestador de Shimomura"+X)
    print(GR+DM+"  Autoría debatida — publicado como evidencia oficial del caso federal."+X)
    print()
    p(0.6)

    mensajes = [
        ("1", "27 Dic 1994  4:33 PM", "th1.wav",
         [('WC', '"Damn you."',                    '"Maldito seas."'),
          ('WC', '"My technique is the best. My boss is the best. Damn you."',
                 '"Mi técnica es la mejor. Mi jefe es el mejor. Maldito seas."'),
          ('WC', '"I know rdist technique, I know sendmail technique,"',
                 '"Conozco la técnica rdist, conozco la técnica sendmail,"'),
          ('WC', '"and my style is much better. Damn you."',
                 '"y mi estilo es mucho mejor. Maldito."'),
          ('WC', '"Don\'t you know who I am?"',   '"¿No sabes quién soy?"'),
          ('WC', '"Me, and my friends, we\'ll kill you."',
                 '"Yo y mis amigos te vamos a destruir."'),
          ('M',  '[2ª voz] "Hey boss, your kung fu\'s really good."',
                 '[2ª voz] "Oye jefe, tu kung fu es muy bueno."'),
          ('WC', '"That\'s right. My style is the best."',
                 '"Así es. Mi estilo es el mejor."')]),
        ("2", "30 Dic 1994  2:35 PM", "th2.wav",
         [('GR', '[Ruidos extraños — taunt de artes marciales]', '[Ruidos extraños]'),
          ('WC', '"You, your security technique will be defeated."',
                 '"Tu técnica de seguridad será derrotada."'),
          ('WC', '"Your technique is no good."', '"Tu técnica no sirve."')]),
        ("3", "5 Ene 1995  12:28 PM", "th3.wav",
         [('GR', '[Música inquietante — sin palabras]', '[Música inquietante — sin palabras]')]),
        ("4", "4 Feb 1995  9:52 AM", "th4.wav",
         [('WC', '"Ahh Tsutomu, my learn-ed disciple."',
                 '"Ahh Tsutomu, mi ilustrado discípulo."'),
          ('WC', '"I see you put my voice for Newsweek, you put it on the net."',
                 '"Veo que pusiste mi voz en Newsweek, y en la red."'),
          ('WC', '"Don\'t you know that my kung fu is the best?"',
                 '"¿No sabes que mi kung fu es el mejor?"'),
          ('WC', '"Have I not taught you, grasshopper? You must learn from the master."',
                 '"¿Acaso no te enseñé, saltamontes? Debes aprender del maestro."'),
          ('WC', '"I know tiger claw style. I know crane technique. I know crazy monkey technique."',
                 '"Conozco el estilo de garra de tigre. Conozco la grulla. Conozco el mono loco."'),
          ('WC', '"And I also know rdist and sendmail."',
                 '"Y también conozco rdist y sendmail."'),
          ('WC', '"I\'m very disappointed, my son."', '"Estoy muy decepcionado, hijo mío."')]),
        ("5", "15 Feb 1995  6:52 AM ← DÍA DEL ARRESTO", "th5.wav",
         [('R',  '[MISMO DÍA DEL ARRESTO — 5 horas después — ¿quién llama?]',
                 '[MISMO DÍA DEL ARRESTO — intento desesperado de desvincularse]'),
          ('WC', '"Hi, it is I again, Tsutomu, my son."',
                 '"Hola, soy yo de nuevo, Tsutomu, hijo mío."'),
          ('WC', '"All these phone calls making reference to kung fu movies?"',
                 '"Todas estas llamadas haciendo referencia a películas de kung fu..."'),
          ('WC', '"Nothing to do with any computer thing whatsoever."',
                 '"No tienen nada que ver con computadoras."'),
          ('R',  '"I see now that this is getting too big, way too big."',
                 '"Veo que esto se está poniendo muy grande, demasiado grande."'),
          ('R',  '"I want to tell you, my son, these have nothing to do with Mitnick, hacking, anything."',
                 '"Te digo, hijo, esto no tiene nada que ver con Mitnick, hacking, nada."')]),
        ("6", "15 Feb 1995  7:23 PM ← TRAS EL ARRESTO", "th6.wav",
         [('R',  '[12 horas después del arresto — ¿quién sigue llamando?]',
                 '[12 horas después del arresto — la voz no para]'),
          ('WC', '"Tsutomu, my friend. I just want to reiterate, it is big joke."',
                 '"Tsutomu, amigo. Solo quiero reiterar, es una broma grande."'),
          ('R',  '"You tell me, do not send them to come and get me."',
                 '"Te digo, no los mandes a venir por mí."'),
          ('R',  '"No, do not fly out to come and get me. I\'m not worth it."',
                 '"No, no vueles para venir a buscarme. No vale la pena."'),
          ('WC', '"Just make fun of kung fu movies. That is it. Thank you."',
                 '"Solo hacer burla de películas de kung fu. Eso es todo. Gracias."')]),
    ]

    for num, fecha, wavfile, lineas in mensajes:
        cls() if num != "1" else None
        print()
        hr("─", Y)
        col_hdr = R+BD if "ARRESTO" in fecha else Y+BD
        print(col_hdr + f"  ▶ MENSAJE #{num} — {fecha}" + X)
        hr("─", Y)
        print()

        wav_path = os.path.join(AUDIO_VM, wavfile)
        if os.path.exists(wav_path):
            print(G+BD+"  🔊 AUDIO REAL — takedown.com  [ ENTER para saltar ]" + X)
            p(0.4)
            play_wav_with_subs(wav_path, lineas)
        else:
            # Sin WAV — mostrar transcripción con delay y bip de contestador
            snd_am(bg=False)
            p(0.3)
            for col_key, eng, esp in lineas:
                col = (R+BD if col_key=='R' else M+BD if col_key=='M' else
                       GR+DM if col_key=='GR' else WC+BD)
                print(f"  {col}{eng}{X}")
                print(f"  {GR}  → {esp}{X}")
                print()
                p(0.8)
        p(0.3)

        if num in ("5","6"):
            print()
            print(R + BD + "  ⚠️  Este mensaje fue enviado el día del arresto.".center(W()) + X)
            if num == "6":
                print(R + "  Mitnick fue arrestado a la 1:30 AM. Este mensaje es de las 7 PM.".center(W()) + X)
                print(R + "  La voz de las grabaciones NUNCA fue atribuida oficialmente.".center(W()) + X)

        p(0.5)
        if num != "6":
            input(C + BD + f"\n  [ ENTER → Mensaje #{int(num)+1} ] " + X)

    print()
    p(0.8)
    typ("  Shimomura archivó todo. Junto con los logs de Netcom y el análisis forense,", 0.022, DG)
    typ("  estos audios fueron presentados como evidencia en el juicio federal.", 0.022, DG)
    print()
    typ("  Quien sea que llamó... se confiaba demasiado.", 0.022, R)
    typ("  Y confiarse es siempre el error fatal.", 0.022, R)
    print()
    p(1.2)
    input(C+BD+"\n  [ ENTER → La llamada grabada con Mark Lottor ] "+X)

# ══════════════════════════════════════════════════════════════════════════════
#  CAP 5 — LA LLAMADA GRABADA — KEVIN HABLA DE SHIMOMURA
# ══════════════════════════════════════════════════════════════════════════════
def cap_lottor():
    chapter_title(5, "LA LLAMADA GRABADA", "Kevin Mitnick habla de Shimomura — sin saber que lo cazan")
    cls()

    typ("  Mark Lottor — investigador de Network Wizards, San Francisco.", 0.022, WC)
    typ("  Mitnick hackeó sus sistemas. Luego... lo llamó por teléfono.", 0.022, WC)
    typ("  La llamada fue grabada. Es evidencia oficial del caso federal.", 0.022, Y)
    print()
    p(0.5)

    print(R+BD+"  LO QUE HACE ESTA GRABACIÓN ÚNICA:".center(W())+X)
    print(WC+"  Kevin menciona a Shimomura POR NOMBRE.".center(W())+X)
    print(WC+"  Lo llama 'un mago'. No sabe que Shimomura ya está en Raleigh buscándolo.".center(W())+X)
    print()
    p(1.0)

    # 10 segmentos — combinamos en bloques de 2-3
    segs = [
        ("1-2", "seg1.wav",
         [("Kevin:", "I'm not going to pass it around. I just was interested to see how you did it.",
                     "No lo voy a distribuir. Solo me interesaba ver cómo lo hiciste."),
          ("Kevin:", "You're a hacker and I'm a hacker. No harm intended, I wasn't gonna wipe your system.",
                     "Tú eres un hacker y yo soy un hacker. Sin mala intención, no iba a borrar tu sistema.")]),
        ("3",   "seg3.wav",
         [("Mark:", "How did you possibly get my new passwords?",
                    "¿Cómo conseguiste mis nuevas contraseñas?"),
          ("Kevin:", "Heh. I can always get it again, if I wanted to.",
                     "Heh. Siempre puedo conseguirlas de nuevo, si quisiera."),
          ("Kevin:", "I can just keep coming back. I can get it again. That's the funny thing.",
                     "Puedo seguir volviendo. Puedo conseguirlas de nuevo. Eso es lo gracioso.")]),
        ("6",   "seg6.wav",
         [("Kevin:", "I did a lot of research on you before I came after you.",
                     "Investigué mucho sobre ti antes de ir a por ti."),
          ("Kevin:", "I know your mother's name, and your dad's name...",
                     "Conozco el nombre de tu madre, y el de tu padre..."),
          ("Mark:", "Were you trying to look for passwords?",
                    "¿Intentabas buscar contraseñas?"),
          ("Kevin:", "No, no, I just thought I'd get a profile. Do my homework.",
                     "No, no. Solo quería hacer un perfil. Hacer mi tarea.")]),
        ("7-8", "seg7.wav",
         [("Kevin:", "I guess you know Tsutomu Shimomura?",
                     "Supongo que conoces a Tsutomu Shimomura, ¿verdad?"),
          ("Kevin:", "Yeah, yeah. He's a pretty good hacker himself. Can break into systems.",
                     "Sí, sí. Él mismo es bastante buen hacker. Puede entrar a sistemas."),
          ("Kevin:", "The guy's a wizard. He should work for your company, Network Wizards.",
                     "El tipo es un mago. Debería trabajar en tu empresa, Network Wizards."),
          ("Mark:", "He has better things to do.",
                    "Él tiene cosas mejores que hacer.")]),
        ("10",  "seg10.wav",
         [("Kevin:", "I'd even be willing, for a reasonable price, to purchase your code from you.",
                     "Incluso estaría dispuesto, por un precio razonable, a comprarte el código."),
          ("Mark:", "What would you do with it?",
                    "¿Qué harías con él?"),
          ("Kevin:", "Oh, hack it myself!",
                     "¡Oh, hackearlo yo mismo!")]),
    ]

    for seg_id, wavfile, dialogo in segs:
        print()
        hr("─", C)
        print(C+BD+f"  ▶ SEGMENTO {seg_id}"+X)
        hr("─", C)
        print()

        # Transcripción primero
        for who, eng, esp in dialogo:
            col = Y+BD if "Kevin" in who else G
            print(f"  {col}{who:<8}{X}  {WC}{eng}{X}")
            print(f"  {GR}          → {esp}{X}")
            print()
            p(0.3)

        # Destacar el momento Shimomura antes del audio
        if "7-8" in seg_id:
            p(0.3)
            blink("  ★  Kevin llama 'mago' a Shimomura. Shimomura está en Raleigh buscándolo.  ★", 3, R)

        print()
        wav_path = os.path.join(AUDIO_LOT, wavfile)
        if os.path.exists(wav_path):
            print(G+BD+"  🔊 AUDIO REAL de la llamada grabada"+X)
            p(0.3)
            play_wav_skippable(wav_path)
        else:
            snd_data(0.8)

    print()
    p(0.8)
    snd_dramatic()
    print()
    big_text([
        "Kevin habló. Mencionó a Shimomura.",
        "Llamó a su cazador 'un mago'.",
        "",
        "Todo quedó grabado.",
    ], R)
    p(2.0)
    input(C+BD+"\n  [ ENTER → Ingeniería Social ] "+X)

# ══════════════════════════════════════════════════════════════════════════════
#  CAP 5 — INGENIERÍA SOCIAL EN ACCIÓN
# ══════════════════════════════════════════════════════════════════════════════
def cap_social():
    chapter_title(5, "EL ARMA SECRETA", "Ingeniería Social — La técnica más poderosa")
    cls()

    big_text([
        '"90% del hacking es ingeniería social."',
        "",
        "— Kevin Mitnick",
    ], Y)
    p(1.5)

    HR("─",Y)
    print(Y+BD+"  LLAMADA SIMULADA — Cómo Mitnick obtuvo acceso a Nokia, Helsinki (1994)" + X)
    print(GR+"  Basado en 'Ghost in the Wires' cap. 20 — Mitnick llamo haciendose pasar por empleado interno" + X)
    HR("─",Y)
    print()
    p(0.5)

    if not NO_AUDIO and not ask_skip("DTMF + timbre simulado"):
        snd_dial("358981234567")
        p(0.4)
        print(GR+"  [Marcando: +358-9-812-34567  Nokia HQ, Helsinki, Finlandia]"+X)
        print(GR+"  [Tono de llamada — DTMF sintetizado]"+X)
        snd_ring(2, bg=False)
    p(0.5)

    dialogo = [
        (G,  "  Nokia: Good afternoon, Nokia Corporation."),
        (GR, "        → Nokia, buenas tardes."),
        (Y,  '  KM:   "Hi, this is Dave Williams from network operations in Los Angeles."'),
        (GR, '        → "Hola, habla Dave Williams de operaciones de red en Los Ángeles."'),
        (Y,  '  KM:   "I\'m having trouble connecting to the internal auth server from remote."'),
        (GR, '        → "Tengo problemas para conectarme al servidor interno de autenticación."'),
        (G,  "  Nokia: Let me transfer you to tier 2 support..."),
        (GR, "        → Le transfiero a soporte nivel 2..."),
        (GR, "  [30 minutos después — 3 transferencias — 2 historias falsas más tarde]"),
        (R,  "  Tech:  Your temp credentials are: nk94$xv2@fi — server: auth.nokia.fi"),
        (GR, "        → Tus credenciales temporales son: nk94$xv2@fi — servidor: auth.nokia.fi"),
        (Y,  '  KM:   "Perfect, thanks a lot!" [Cuelga]'),
        (GR, '        → "Perfecto, muchas gracias." [Cuelga]'),
    ]
    for col, txt in dialogo:
        if txt.startswith("  ["):
            print(); print(DM+txt+X); print()
        else:
            typ(txt, 0.022, col)
        p(0.3)

    print()
    p(0.6)
    snd_success()
    print(G+BD+"  Así de simple. Sin exploits. Sin código. Solo una llamada de 30 minutos."+X)
    print()
    p(0.5)

    HR("─",C)
    print(C+BD+"  SISTEMAS REALES COMPROMETIDOS — En orden cronológico"+X)
    HR("─",C)
    print()

    # Cronológico, con detalle de cada ataque
    sistemas = [
        ("1988", "DEC / Digital Equipment Corp.",
         "Primer gran hack documentado. Mitnick (25 años) entra al sistema\n"
         "  VMS de DEC en Nashua, NH. Roba el código fuente completo del\n"
         "  sistema operativo VAX/VMS — valorado en $1M USD. Es detectado,\n"
         "  arrestado y condenado a 1 año de prisión federal.",
         "Técnico: exploit en VMS + ingeniería social a empleados DEC"),
        ("1988", "DoD — ARPAnet / MITRE Corp.",
         "Desde una terminal de la USC (University of Southern California)\n"
         "  entra a sistemas del Departamento de Defensa. Navega por ARPAnet\n"
         "  (precursor de internet) accediendo a sistemas militares.\n"
         "  Tenía 25 años. Nunca se hizo pública la magnitud del acceso.",
         "Técnico: explotación de confianza entre nodos ARPAnet"),
        ("1992", "Pacific Bell — RBOC",
         "Fugitivo desde ese año, entra a los sistemas internos de Pacific Bell\n"
         "  (filial de AT&T, California). Accede al sistema COSMOS — base de datos\n"
         "  de configuración de líneas telefónicas de todo el estado.\n"
         "  Usa estos accesos para clonar números celulares y navegar gratis.",
         "Técnico + Ing. Social: se hizo pasar por técnico de Pacific Bell"),
        ("1992", "Netcom — ISP San José",
         "Penetra el servidor de autenticación de Netcom, uno de los mayores\n"
         "  ISPs de California. Crea la cuenta 'gkremen' y roba credenciales\n"
         "  de +20,000 usuarios, incluyendo números de tarjeta de crédito.\n"
         "  Usa Netcom como plataforma de salto a otros sistemas.",
         "Técnico: ataque al sistema de autenticación + sniffer de red"),
        ("1993", "Novell Inc.",
         "Entra a los sistemas de desarrollo de Novell en Provo, Utah.\n"
         "  Roba el código fuente de NetWare — el sistema operativo de red\n"
         "  más usado en redes corporativas de la época.\n"
         "  Valorado en decenas de millones de dólares.",
         "Técnico: explotación de acceso remoto + ing. social a helpdesk"),
        ("1993", "Sun Microsystems",
         "Entra a los servidores de Sun en Mountain View, California.\n"
         "  Roba código fuente de Solaris (SunOS 5.x) — el Unix más usado\n"
         "  en universidades y centros de investigación.\n"
         "  El código le permite encontrar vulnerabilidades 0-day.",
         "Técnico: exploit + ing. social a administradores de red"),
        ("1994", "Motorola Inc.",
         "Entra a los sistemas de I+D de Motorola en Schaumburg, Illinois.\n"
         "  Obtiene código fuente del firmware de radios celulares MicroTAC.\n"
         "  Esto le permite entender cómo clonar frecuencias celulares\n"
         "  para hacer llamadas y conectarse a internet gratis.",
         "Combinado: explotación técnica + llamadas de ingeniería social"),
        ("1994", "Nokia — Helsinki, Finlandia",
         "Entra a los sistemas de Nokia Corporation en Helsinki.\n"
         "  Roba código fuente del sistema operativo de los teléfonos Nokia\n"
         "  de la serie 2100 — los más vendidos en Europa ese año.\n"
         "  Todo esto mediante UNA SOLA llamada telefónica como 'Dave Williams'.",
         "Ingeniería Social pura: 30 minutos, 3 transfers, credenciales obtenidas"),
        ("1994", "Fujitsu Ltd.",
         "Entra a sistemas de Fujitsu en Japón/EE.UU.\n"
         "  Obtiene software propietario de redes de telecomunicaciones.\n"
         "  Usado para entender la infraestructura de las operadoras.",
         "Ingeniería Social + explotación de acceso remoto"),
        ("1994", "SDSC — Shimomura (Fatal Error)",
         "25 Diciembre 1994. Ataca el SDSC (San Diego Supercomputer Center).\n"
         "  Los servidores personales de Tsutomu Shimomura — experto de seguridad.\n"
         "  Roba 20,000 archivos: herramientas de seguridad, investigaciones,\n"
         "  software militar. Es el ataque más sofisticado de su carrera.\n"
         "  Y el más costoso: Shimomura lo perseguirá hasta atraparlo.",
         "TCP ISN Prediction + IP Spoofing — jamás ejecutado antes en la vida real"),
    ]

    total = len(sistemas)
    for idx, (año, empresa, detalle, metodo) in enumerate(sistemas, 1):
        cls()
        w = W()
        print()
        HR("═", R)
        print(R+BD + f"  SISTEMA {idx}/{total} — {año}".center(w) + X)
        print(Y+BD + f"  {empresa}".center(w) + X)
        HR("═", R)
        print()
        for linea in detalle.split("\n"):
            print(WC + "  " + linea.strip() + X)
            p(0.05)
        print()
        print(C+BD + "  Método:" + X)
        print(DG + "  " + metodo + X)
        print()
        snd_beep(440 + idx * 30, 0.07)
        p(0.3)
        if idx < total:
            input(C+BD + f"\n  [ ENTER → Sistema {idx+1}/{total} ] " + X)
        else:
            input(C+BD + "\n  [ ENTER → El rastro hasta Raleigh ] " + X)

# ══════════════════════════════════════════════════════════════════════════════
#  CAP 6 — RASTREANDO AL FUGITIVO
# ══════════════════════════════════════════════════════════════════════════════
def cap_tracking():
    chapter_title(6, "LA CACERÍA", "Shimomura sigue el rastro — Enero/Febrero 1995")
    cls()

    typ("  23 Enero 1995: Un usuario de The Well (BBS de San Francisco) reporta", 0.022, WC)
    typ("  archivos sospechosos en su directorio. Son los archivos de Shimomura.", 0.022, WC)
    typ("  La cuenta fue penetrada desde Netcom — usuario: gkremen.", 0.022, Y)
    print()
    p(0.8)

    # Mapa de conexiones
    HR("─",G)
    print(G+BD+"  RUTA REAL DE MITNICK — Raleigh NC → Múltiples Sistemas"+X)
    HR("─",G)
    print()

    mapa_rows = [
        ("",    Y+"[Apartamento 202-D — Surrey House — Raleigh, NC]"+G),
        ("",    "         │  Celular Sprint clonado  (IMSI robado)"),
        ("",    "         ▼"),
        ("",    Y+"[Torres Sprint RTP — Research Triangle Park, NC]"+G),
        ("",    "         │  PPP dialup anónimo"),
        ("",    "         ▼"),
        ("",    Y+"[NETCOM-rtp1 / NETCOM-rtp2]"+G+"  ──►  cuenta: "+R+BD+"gkremen"+G),
        ("",    "         │              (alias de Kevin Mitnick)"),
        ("",    "         ├──────────────────────────┬──────────────────────"),
        ("",    "         ▼                          ▼"),
        ("",    Y+"[teal.csn.org]"+G+" ──► "+Y+"[escape.com]"+G+"       "+Y+"[The Well BBS]"+G+"  "+R+BD+"(archivos)"+G),
        ("",    "                          │"),
        ("",    "                          ▼"),
        ("",    "          "+R+BD+"[Nokia · Motorola · Sun · SDSC]"+G),
    ]
    box_top(G)
    for _, content in mapa_rows:
        box_row(G + content + G, G); p(0.06)
    box_bot(G)

    print()
    p(0.6)
    HR("─",DG)
    print(DG+"  LOGS REALES DE NETCOM — gkremen (Mitnick) — Fuente: takedown.com"+X)
    HR("─",DG)
    print()
    print(WC+BD+f"  {'HOST':<14} {'USER':<10} {'TTY':<8} {'DESDE':<22} {'LOGIN':<15} {'DUR'}"+X)
    print(GR+"  "+"─"*(W()-4)+X)
    logs=[
        ("netcom22",    "gkremen","ttyp0","teal.csn.org",    "Feb  4 21:53","00:25"),
        ("netcom-rtp1", "gkremen","ttyr1","NETCOM-rtp1",     "Feb 11 03:21","01:23"),
        ("netcom-rtp1", "gkremen","ttys5","escape.com",      "Feb 13 22:01","01:37"),
        ("netcom2",     "gkremen","ttyqe","NETCOM-min2",     "Feb 13 17:47","00:25"),
        ("netcom-rtp2", "gkremen","ttyqf","NETCOM-rtp2",     "Feb 14 00:47","01:24"),
        ("netcom-rtp1", "gkremen","ttyr3","NETCOM-rtp1",     "Feb 14 23:11","00:52"),
    ]
    for e in logs:
        print(GR+f"  {e[0]:<14} {e[1]:<10} {e[2]:<8} {e[3]:<22} {e[4]:<15} {e[5]}"+X)
        p(0.2)

    print()
    p(0.5)
    print(Y+"  Patrón claro: todos los accesos desde Raleigh-Durham (RTP)."+X)
    print(Y+"  9 Febrero: Shimomura confirma. El fugitivo está en Raleigh, North Carolina."+X)
    print(Y+"  Compra un pasaje de avión."+X)
    p(1.2)
    input(C+BD+"\n  [ ENTER → La triangulación ] "+X)

# ══════════════════════════════════════════════════════════════════════════════
#  CAP 7 — TRIANGULACIÓN CELULAR
# ══════════════════════════════════════════════════════════════════════════════
def cap_triangulacion():
    chapter_title(7, "LA SEÑAL", "Triangulación Celular — 11-14 Febrero 1995")
    cls()

    typ("  Shimomura llega a Raleigh. Un ingeniero de Sprint Cellular lo ayuda.", 0.022, WC)
    typ("  Usan equipo TSCM — Technical Surveillance Countermeasures.", 0.022, WC)
    typ("  Recorren la ciudad en auto con una antena de dirección.", 0.022, WC)
    typ("  Miden la intensidad de la señal del celular de Mitnick.", 0.022, WC)
    print()
    p(0.8)

    HR("─",G)
    print(G+BD+"  INTENSIDAD SEÑAL CELULAR — 919-861-0116  (celular de Mitnick)"+X)
    HR("─",G)
    print()

    zonas=[
        (-88,"Spring Forest Rd",      "░░░░░░░░░░░░░░░░░░░░","Señal muy débil"),
        (-81,"Wake Forest Rd",        "▒▒▒░░░░░░░░░░░░░░░░░",""),
        (-74,"Westover Hills Pkwy",   "▒▒▒▒▒▒░░░░░░░░░░░░░░","Zona general: ~5km"),
        (-65,"Durham Dr",             "▒▒▒▒▒▒▒▒▒▒░░░░░░░░░░","Barrio localizado: ~2km"),
        (-55,"Duraleigh Rd",          "▒▒▒▒▒▒▒▒▒▒▒▒▒▒░░░░░░","Edificio residencial: ~500m"),
        (-43,"Surrey House Apartments","▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒█","◄ OBJETIVO — 1 Wayne Hills Dr"),
    ]

    for dbm, lugar, barra, nota in zonas:
        col = R+BD if "OBJETIVO" in nota else G if dbm>-55 else Y if dbm>-70 else GR
        nota_str = f"  {R+BD}{nota}{X}" if nota else ""
        sys.stdout.write(f"\r  {col}{lugar:<26}{X}  {WC}{dbm:+d} dBm{X}  {col}{barra}{X}{nota_str}\n")
        sys.stdout.flush()
        hz_sig = 250 + abs(dbm)*6
        snd_beep(hz_sig, 0.08, 0.5)
        p(0.7)

    print()
    p(0.5)
    snd_alarm()
    print()
    blink(f"  ★  SEÑAL MÁXIMA: Surrey House Apartments — Apt 202-D  ★  ".center(W()), 4, R)
    print()

    # Mapa ASCII de Raleigh — animado con señales irradiando
    p(0.5)
    print()
    print(G+BD + "  MAPA DE TRIANGULACIÓN — RALEIGH, NC — 11-14 FEB 1995".center(W()) + X)
    print()
    map_base = [
        "         N",
        "         ↑",
        "  [A] Spring Forest                    [B] Westover Hills",
        "   -88dBm ●                              ● -74dBm",
        "            ╲                           ╱",
        "             ╲                         ╱",
        "              ╲       Durham Dr        ╱",
        "               ╲                     ╱",
        "                ╲                   ╱",
        "                 ╲    ┌─────────┐  ╱",
        "                  ╲   │ ★ 202D │ ╱   ← Surrey House Apts",
        "                   ╲  │ -43dBm │╱      1 Wayne Hills Dr",
        "                    ╲ └─────────┘",
        "                     ╲╱",
        "                      ● [C] Tryon Rd",
        "                      -65dBm",
        "                      ↓",
        "                      S",
    ]
    # Fase 1: mostrar mapa con señales débiles (gris)
    for row in map_base:
        print(GR + "  " + row + X)
        p(0.04)
    p(0.8)

    # Fase 2: animar señales irradiando de cada torre hacia el objetivo
    ring_chars = ["·", "·", "◦", "◦", "○", "○", "●"]
    print()
    print(Y+BD + "  [TRIANGULANDO SEÑAL 919-861-0116...]".center(W()) + X)
    p(0.4)
    for step, ch in enumerate(ring_chars):
        col = GR if step < 3 else Y if step < 5 else R+BD
        print(f"\r  {col}  ANTENA-A {ch}{'·'*step} ──── ANTENA-B {ch}{'·'*step} ──── ANTENA-C {ch}{'·'*step}  COBERTURA: {step*14+2}%{X}",
              end="", flush=True)
        snd_beep(300 + step*80, 0.07, 0.35)
        p(0.35)
    print()
    p(0.4)

    # Fase 3: resultado — objetivo iluminado
    print()
    print(R+BD + "         N".center(W()) + X)
    print(R+BD + "         ↑".center(W()) + X)
    print()
    print(Y + "  [A] ●──────────────────────────────────● [B]".center(W()) + X)
    print(Y + "        ╲                               ╱".center(W()) + X)
    print(Y + "         ╲                             ╱".center(W()) + X)
    print(Y + "          ╲                           ╱".center(W()) + X)
    print(R+BD + "           ╲──────►  ★ SURREY HOUSE ◄──╱".center(W()) + X)
    print(R+BD + "                      Apt 202-D".center(W()) + X)
    print(R+BD + "                   1 Wayne Hills Dr".center(W()) + X)
    print(Y + "                          │".center(W()) + X)
    print(Y + "                         [C]".center(W()) + X)
    print()
    snd_alarm()
    blink("  ★  POSICIÓN EXACTA CONFIRMADA — APT 202-D  ★  ".center(W()), 3, R)

    print()
    p(0.8)
    typ("  14 Febrero: Shimomura camina los pasillos del edificio con el receptor.", 0.022, WC)
    typ("  La señal explota en el ala D, piso 2. Apartamento 202-D.", 0.022, WC)
    typ("  Llama al agente del FBI John Bowne. Le da la dirección exacta.", 0.022, R)
    p(1.5)
    input(C+BD+"\n  [ ENTER → El arresto ] "+X)

# ══════════════════════════════════════════════════════════════════════════════
#  CAP 8 — EL ARRESTO
# ══════════════════════════════════════════════════════════════════════════════
def cap_arresto():
    chapter_title(8, "FIN DE LA FUGA", "15 Febrero 1995 — 01:30 AM — Raleigh, NC")

    cls()
    snd_tension_crescendo(7.0, bg=True)
    snd_heartbeat(4)

    lineas=[
        (WC, "  4 agentes del FBI. Shimomura en el estacionamiento con el receptor."),
        (WC, "  01:30 AM. El edificio está en silencio."),
        (WC, "  Suben por las escaleras. Pasillo D. Tercer piso."),
        ("",""),
        (Y,  "  Los agentes se posicionan a cada lado de la puerta 202-D."),
        ("",""),
        (R,  '  Bowne: "Kevin Mitnick — FBI — ABRA LA PUERTA."'),
        (R,  "  ..."),
        (R,  "  Silencio."),
        (R,  "  Pasos."),
        (R,  "  Luz bajo la puerta."),
        ("",""),
        (G,  "  La puerta se abre."),
        (G,  '  Mitnick: "Oh no..."'),
        ("",""),
        (G,  "  Kevin David Mitnick — 31 años — queda detenido."),
        (G,  "  El fugitivo más buscado de América. Capturado."),
    ]
    for col, txt in lineas:
        if not txt: print(); p(0.45); continue
        typ(txt, 0.022, col); p(0.22)

    print()
    p(0.8)
    glitch_screen(1.5)
    snd_alarm()
    print()
    blink(("  ██  F U G I T I V O   C A P T U R A D O  ██  ").center(W()), 6, R)
    print()
    render_photo(os.path.join(SCRIPT_DIR, "mitnick.jpg"), w_chars=32, h_chars=14,
                 label="Kevin Mitnick — Booking Photo — 15 Feb 1995 — Raleigh NC", col=R)
    print()
    p(1.0)

    HR("─",C)
    print(C+BD+"  EVIDENCIA EN EL APARTAMENTO 202-D"+X)
    HR("─",C)
    print()
    evidencia=[
        ("PowerBook 520",      "Laptop con módem celular — herramienta principal"),
        ("2 celulares clonados","IMSI/ESN robados de terceros"),
        ("+20,000 números CC", "Tarjetas de crédito robadas de Netcom"),
        ("Diskettes con tools", "Sniffers, exploits, scripts de hacking"),
        ("Notas manuscritas",   "Passwords, extensiones internas, nombres de empleados"),
        ("Hardware de RF",      "Para clonar frecuencias celulares"),
    ]
    for item, desc in evidencia:
        print(f"  {R}[✗]{X}  {Y+BD}{item:<26}{X}  {WC}{desc}{X}")
        p(0.3); snd_beep(440,0.05)

    print()
    p(0.6)
    HR("─",R)
    print(R+BD+"  CARGOS FEDERALES — USA v. Mitnick — Caso No. CR-95-0132-RMT"+X)
    HR("─",R)
    print()
    cargos=[
        ("18 U.S.C. § 1030","Computer Fraud and Abuse — acceso no autorizado"),
        ("18 U.S.C. § 1343","Wire Fraud — fraude electrónico"),
        ("18 U.S.C. § 2511","Interception of Electronic Communications"),
        ("18 U.S.C. § 1029","Access Device Fraud — +20k tarjetas robadas"),
        ("18 U.S.C. § 1832","Theft of Trade Secrets — Nokia, Motorola"),
    ]
    for cod, desc in cargos:
        print(f"  {R+BD}{cod:<22}{X}  {WC}{desc}{X}")
        p(0.3)

    print()
    p(0.8)
    print(Y+"  Condena: 46 meses federales + 22 meses detención previa ≈ 5 años total."+X)
    print(Y+"  Liberado: 21 enero 2000. Prohibición de usar internet: 3 años más."+X)
    p(1.5)
    input(C+BD+"\n  [ ENTER → La vida después ] "+X)

# ══════════════════════════════════════════════════════════════════════════════
#  CAP 9 — LIBRE Y LEGENDARIO + LA MUERTE
# ══════════════════════════════════════════════════════════════════════════════
def cap_legado():
    chapter_title(9, "DE FUGITIVO A LEYENDA", "2000 → 16 Julio 2023")
    cls()

    typ("  21 Enero 2000: Sale de prisión. No puede tocar una computadora.", 0.022, WC)
    typ("  El hacker más famoso del mundo... sin internet.", 0.022, WC)
    print()
    p(0.6)

    timeline=[
        ("2000", G,  "Sale libre. Prohibición de usar dispositivos con módem o internet."),
        ("2000", Y,  "Apela la restricción — \"Me impide ganarme la vida\". La gana."),
        ("2002", G,  "Publica 'The Art of Deception' — bestseller. La biblia de ing. social."),
        ("2003", G,  "Funda Mitnick Security Consulting LLC — pentesting profesional."),
        ("2005", G,  "Publica 'The Art of Intrusion' — casos reales de intrusiones."),
        ("2011", G,  "Publica 'Ghost in the Wires' — su autobiografía completa."),
        ("2011", Y,  "DEF CON y Black Hat: habla ante miles. Ovaciones de pie."),
        ("2014", G,  "El FBI — que lo persiguió — contrata a su empresa para tests."),
        ("2017", G,  "Publica 'The Art of Invisibility' — guía de privacidad total."),
        ("2019", Y,  "KnowBe4 lo nombra Chief Hacking Officer."),
        ("2022", G,  "Fortra negocia comprar Mitnick Security Consulting."),
        ("Mar 2023", R, "Diagnóstico: cáncer de páncreas estadio 4."),
        ("Jul 2023", R, "16 de julio — muere en Las Vegas, Nevada. 59 años."),
    ]

    # Timeline horizontal animada
    w = W()
    # Eje de años: 1963..2023
    y0, y1 = 1963, 2023
    bar_w = min(w - 10, 90)
    def yr_to_x(yr):
        return int((yr - y0) / (y1 - y0) * (bar_w - 1))

    hitos = [
        (1963, R,   "NAC"),
        (1981, Y,   "HACK"),
        (1988, Y,   "DEC"),
        (1993, R,   "FUGA"),
        (1995, R,   "PRESO"),
        (2000, G,   "LIBRE"),
        (2003, G,   "SEC"),
        (2011, G,   "LIBRO"),
        (2023, GR,  "†"),
    ]
    # Períodos de color de fondo
    periodos = [
        (1963, 1981, GR),   # infancia
        (1981, 1995, Y),    # hacking activo
        (1995, 2000, R),    # prisión
        (2000, 2023, G),    # post-prisión
    ]

    print()
    print(WC+BD + "  LÍNEA DE TIEMPO — KEVIN MITNICK  1963-2023".center(w) + X)
    print()
    p(0.3)

    # Construir eje
    axis = [" "] * bar_w
    for (a, b, col) in periodos:
        xa, xb = yr_to_x(a), yr_to_x(b)
        for x in range(xa, min(xb, bar_w)):
            axis[x] = "─"
    # Marcar hitos
    hito_cols = {}
    for yr, col, lbl in hitos:
        x = yr_to_x(yr)
        if 0 <= x < bar_w:
            axis[x] = "┼"
            hito_cols[x] = (col, lbl, yr)

    # Imprimir eje coloreado carácter a carácter con delay
    sys.stdout.write("  ")
    for x, ch in enumerate(axis):
        if x in hito_cols:
            col, lbl, yr = hito_cols[x]
            sys.stdout.write(col + BD + "█" + X)
        else:
            # color del período
            pcol = GR
            for (a, b, c) in periodos:
                if yr_to_x(a) <= x < yr_to_x(b):
                    pcol = c
                    break
            sys.stdout.write(pcol + ch + X)
        sys.stdout.flush()
        p(0.012)
    print()

    # Etiquetas debajo
    label_line = [" "] * bar_w
    for yr, col, lbl in hitos:
        x = yr_to_x(yr)
        s = f"{yr}"
        for j, ch in enumerate(s):
            if 0 <= x + j < bar_w:
                label_line[x + j] = ch
    sys.stdout.write("  ")
    x_pos = 0
    for yr, col, lbl in sorted(hitos, key=lambda h: h[0]):
        x = yr_to_x(yr)
        sys.stdout.write(" " * max(0, x - x_pos))
        sys.stdout.write(col + BD + str(yr) + X)
        x_pos = x + len(str(yr))
    print()

    # Leyendas de hitos
    print()
    for yr, col, lbl in hitos:
        desc = next((ev for a, c, ev in timeline if str(yr) in a), "")
        if desc:
            print(f"  {col+BD}{yr:<8}{X}  {col}{desc[:70]}{X}")
            p(0.18)
            if "muere" in desc.lower() or "†" in lbl:
                snd_beep(220, 0.5, 0.3)

    print()
    p(1.0)
    HR("─",GR)
    print()

    # Muerte — pantalla de tributo
    snd_dramatic()
    p(0.5)
    cls()
    w = W()
    print()
    print(GR+DM + ("─"*w) + X)
    print()
    print(WC+BD + "  Kevin David Mitnick".center(w) + X)
    print()
    print(GR + "  6 agosto 1963  —  16 julio 2023".center(w) + X)
    print(GR + "  Las Vegas, Nevada".center(w) + X)
    print()
    print(GR+DM + ("─"*w) + X)
    print()
    render_photo(os.path.join(SCRIPT_DIR, "late.jpg"), w_chars=36, h_chars=16,
                 label="Kevin Mitnick — Campus Party México 2010 — Consultor de Seguridad", col=GR)
    print()
    p(1.5)

    tributos=[
        ("Jeff Moss — Creador de DEF CON",
         '"Kevin fue una leyenda. Mostró que cualquier sistema puede caer."'),
        ("Kevin Poulsen — Hacker / Periodista",
         '"Éramos de la misma era. Kevin llegó más alto y pagó más que todos."'),
        ("Comunidad ciberseguridad global",
         "#RIPMitnick trending en 40 países por 24 horas continuas."),
        ("FBI",
         "Reconoció sus contribuciones a la ciberseguridad tras su liberación."),
        ("KnowBe4 / Fortra",
         '"Kevin transformó la industria. De perseguido... a protector."'),
    ]
    HR("─",Y)
    print(Y+BD+"  TRIBUTOS DE LA COMUNIDAD"+X)
    HR("─",Y)
    print()
    for quien, msg in tributos:
        print(f"  {C+BD}{quien}{X}")
        print(f"  {GR}{msg}{X}")
        print(); p(0.5)

    p(0.8)
    input(C+BD+"\n  [ ENTER → El legado que dejó ] "+X)

# ══════════════════════════════════════════════════════════════════════════════
#  FINAL — LEGADO Y LECCIÓN
# ══════════════════════════════════════════════════════════════════════════════
def cap_final():
    cls()
    matrix_rain(2.0)
    cls()
    snd_beeps([(660,0.1),(880,0.1),(1100,0.2)])
    p(0.3)

    w = W()
    print(G+BD+"""
  ██╗     ███████╗ ██████╗  █████╗  ██████╗██╗   ██╗
  ██║     ██╔════╝██╔════╝ ██╔══██╗██╔════╝╚██╗ ██╔╝
  ██║     █████╗  ██║  ███╗███████║██║      ╚████╔╝
  ██║     ██╔══╝  ██║   ██║██╔══██║██║       ╚██╔╝
  ███████╗███████╗╚██████╔╝██║  ██║╚██████╗   ██║
  ╚══════╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝ ╚═════╝   ╚═╝""" + X)
    print()
    print(C+BD + "  Kevin David Mitnick  ·  1963 - 2023".center(w) + X)
    print(GR    + "  'condor'  ·  El hacker que cambió el mundo".center(w) + X)
    print()
    HR()

    print()
    print(WC+BD+"  ¿QUÉ APRENDEMOS?"+X)
    print()

    lecciones=[
        ("TCP/IP (1994)", "ISN predecible → hoy RFC 6528 lo hace aleatorio (2012)"),
        ("rsh/rlogin",    "Confianza por IP → hoy: SSH con Ed25519 criptográfico"),
        ("Ing. Social",   "Sigue siendo el ataque #1 — ninguna tecnología lo detiene"),
        ("Pentest",       "Industria de $5B/año — nació en parte gracias a Mitnick"),
        ("Factor humano", "El eslabón más débil de la seguridad no es la máquina"),
        ("Hoy (2026)",    "Los ataques de Mitnick están en todos los cursos de ciberseguridad"),
    ]
    for tec, desc in lecciones:
        print(f"  {G+BD}{tec:<18}{X}  {WC}{desc}{X}")
        p(0.25)

    print()
    HR()
    print()
    print(Y+BD + '  "La ingeniería social pasa por alto toda la tecnología'.center(w) + X)
    print(Y+BD + '   y apunta directamente al eslabón más débil:'.center(w) + X)
    print(Y+BD + '   el ser humano."'.center(w) + X)
    print(GR    + '                             — Kevin Mitnick'.center(w) + X)
    print()
    HR()
    print()
    print(WC+BD+"  SUS LIBROS — Lectura obligatoria en ciberseguridad"+X)
    print()
    libros=[
        ("'The Art of Deception'",    "2002","La biblia de la ingeniería social"),
        ("'The Art of Intrusion'",    "2005","Casos reales de los mejores hacks"),
        ("'Ghost in the Wires'",      "2011","Su autobiografía — la historia completa"),
        ("'The Art of Invisibility'", "2017","Privacidad total en la era digital"),
    ]
    for l,a,d in libros:
        print(f"  {C}{l:<34}{X} {Y}({a}){X}  {GR}{d}{X}")
        p(0.2)

    print()
    HR()
    print()
    print(DG+"  Fuentes verificadas:"+X)
    for f in [
        "takedown.com/evidence — logs forenses y voicemails reales de Shimomura",
        "Shimomura — 'IP Spoofing Demystified' — CMAD Conference, Enero 1995",
        "Mitnick — 'Ghost in the Wires', Little, Brown & Co., 2011",
        "Expediente: USA v. Mitnick, CR-95-0132-RMT (C.D. Cal. 1995)",
        "RFC 6528 — Defending Against Sequence Number Attacks, Feb 2012",
    ]:
        print(GR+"  · "+f+X); p(0.15)

    print()
    print(GR+DM+"  ★ Demo educativo — historia real, presentación dramatizada."+X)
    print(GR+DM+"  ★ El acceso no autorizado a sistemas es delito federal."+X)
    print(GR+DM+"  ★ El verdadero mensaje: aprende a defender, no a atacar."+X)
    print()
    snd_beep(880,0.12,bg=False); p(0.15); snd_beep(1100,0.2,bg=False)

# ══════════════════════════════════════════════════════════════════════════════
#  CRÉDITOS — PANXOZ
# ══════════════════════════════════════════════════════════════════════════════
def cap_credits():
    cls()
    w = W()
    hide_cursor()
    snd_beeps([(440,0.07),(660,0.07),(880,0.1),(1100,0.14)])
    p(0.3)
    print()
    print(C+BD + ("═"*w) + X)
    print()
    print(G+BD + "  O P E R A C I O N   T A K E D O W N".center(w) + X)
    print(GR    + "  Kevin Mitnick  ·  1963-2023  ·  Demo Educativo".center(w) + X)
    print()
    print(DG + ("─"*w) + X)
    print()
    print(Y+BD  + "  Presentado por:".center(w) + X)
    print()
    print(C+BD  + "[ P A N X O Z ]".center(w) + X)
    print()
    print(WC    + "github.com/panxos".center(w) + X)
    print(WC    + "linkedin.com/in/faravena".center(w) + X)
    print(GR    + "soporteinfo.net".center(w) + X)
    print()
    print(C+BD + ("═"*w) + X)
    print()
    show_cursor()
    p(3.0)

# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════
CHAPTERS = [
    (1,  "Boot Toshiba + Matrix",       [lambda: cap_toshiba(), lambda: escena_boot()]),
    (2,  "Perfil FBI — Quién es Mitnick", [lambda: cap_perfil()]),
    (3,  "El Ataque de Navidad 1994",   [lambda: cap_ataque()]),
    (4,  "Shimomura descubre el hack",  [lambda: cap_shimomura()]),
    (5,  "Voicemails reales (audios)",  [lambda: cap_voicemail()]),
    (6,  "La llamada grabada — Lottor", [lambda: cap_lottor()]),
    (7,  "Ingeniería Social",           [lambda: cap_social(), lambda: cap_tracking(), lambda: cap_the_well()]),
    (8,  "Triangulación celular",       [lambda: cap_triangulacion()]),
    (9,  "El Arresto — 15 Feb 1995",    [lambda: cap_arresto()]),
    (10, "Legado + Muerte 2023",        [lambda: cap_free_kevin(), lambda: cap_legado(), lambda: cap_final(), lambda: free_kevin_finale()]),
]

def chapter_menu():
    """Menú de capítulos. Retorna el índice de inicio en CHAPTERS."""
    if ARGS.chapter > 0:
        for i, (num, _, _) in enumerate(CHAPTERS):
            if num == ARGS.chapter:
                return i
        return 0
    cls()
    w = W()
    print()
    print(C+BD + "  O P E R A C I Ó N   T A K E D O W N".center(w) + X)
    print(GR   + "  Kevin Mitnick  ·  1963-2023".center(w) + X)
    print()
    print(DG + ("─"*w) + X)
    print()
    print(WC+BD + "  [ 0 ]  Historia completa (recomendado)".center(w) + X)
    print()
    for num, title, _ in CHAPTERS:
        print(GR + f"  [ {num:<2} ]  {title}".center(w) + X)
    print()
    print(DG + ("─"*w) + X)
    print()
    if NO_AUDIO:
        print(Y + "  [MODO SIN AUDIO ACTIVO]".center(w) + X)
    if ARGS.fast:
        print(Y + "  [MODO RÁPIDO x2 ACTIVO]".center(w) + X)
    print()
    ans = input(C+BD + "  Selección [0-10]: " + X).strip()
    if ans == "0" or ans == "":
        return 0
    try:
        n = int(ans)
        for i, (num, _, _) in enumerate(CHAPTERS):
            if num == n:
                return i
    except ValueError:
        pass
    return 0

def main():
    try:
        cap_credits()
        start_idx = chapter_menu()
        for i, (_, _, fns) in enumerate(CHAPTERS):
            if i < start_idx:
                continue
            for fn in fns:
                fn()
        cap_credits()
    except KeyboardInterrupt:
        show_cursor()
        print(R+"\n\n  [!] Interrumpido.\n"+X)
        sys.exit(0)

def asset_check():
    """Verifica assets críticos y avisa si faltan. No bloquea la demo."""
    checks = [
        (os.path.join(SCRIPT_DIR, "mitnick.jpg"),       "Foto FBI dossier"),
        (os.path.join(SCRIPT_DIR, "late.jpg"),           "Foto legado"),
        (os.path.join(AUDIO_VM,   "th1.wav"),            "Voicemail #1"),
        (os.path.join(AUDIO_VM,   "th3.wav"),            "Voicemail #3"),
        (os.path.join(AUDIO_LOT,  "seg1.wav"),           "Llamada Lottor seg1"),
    ]
    missing = [(label, path) for path, label in checks if not os.path.exists(path)]
    if missing:
        print(Y+BD + "\n  [ASSETS FALTANTES — estas funciones usarán fallback]" + X)
        for label, path in missing:
            print(GR + f"    ✗  {label:<28}  {path}" + X)
        print()
        p(1.5)

if __name__=="__main__":
    asset_check()
    main()
