"""Construye la edición: recortes, mapa de tiempos, eventos de apoyo,
subtítulos (SRT + JSON) y la lista de edición que consume Remotion.
Todos los tiempos de origen son del master a 30 fps (master30.mp4)."""
import json, math, re
import numpy as np

FPS = 30
SRC = '/home/user/Edici-n/work/src'
OUT = '/home/user/Edici-n/edit'
W = json.load(open(f'{SRC}/words.json'))
rms = np.load(f'{SRC}/rms.npy')  # dB por bloque de 10 ms
TOTAL_SRC_FRAMES = 3108           # se termina en 103,6 s (remate + respiro final)

# ---------------------------------------------------------------- recortes
# [inicio, fin) en fotogramas de origen. Cada uno se verificó contra la
# envolvente de energía: solo aire muerto o la vacilación «Es… un tanque».
REMOVE = [
    (187, 191),    # 00:06  «horas» → «Sabes»       (cambio de ángulo 6,23)
    (331, 354),    # 00:11  silencio tras «llorar»  (ángulo 11,53)
    (613, 619),    # 00:20  «trasnochar» → «El verdadero» (ángulo 20,57)
    (1169, 1178),  # 00:39  «mantenimiento» → «Opción»     (ángulo 39,23)
    (1313, 1319),  # 00:43  «oficinas» → «Te da»           (ángulo 43,93)
    (1582, 1591),  # 00:52  «producir» → «Hogar»           (ángulo 52,97)
    (1683, 1700),  # 00:56  «perfecto» → «Cuenta con»      (ángulo 56,50)
    (1813, 1831),  # 01:00  «nevera» → «iluminación»       (ángulo 60,77)
    (1935, 1942),  # 01:04  «BTU» → «para que duermas»     (ángulo 64,67)
    (2051, 2054),  # 01:08  «equipos» → «Sistema»          (ángulo 68,47)
    (2161, 2165),  # 01:12  «Para» → «quienes»             (ángulo 72,03)
    (2240, 2254),  # 01:14  vacilación «Es … un tanque»    (bajo el apoyo 19,2 kWh)
    (2471, 2479),  # 01:22  «BTU» → «Nevera»               (ángulo 82,50)
    (2619, 2628),  # 01:27  «luz» → «Lo mejor»             (ángulo 87,60, bajo el gráfico solar)
    (2791, 2796),  # 01:33  «futuro» → «Deja»              (ángulo 93,20)
    (2909, 2918),  # 01:37  «mismo» → «Haz clic»           (ángulo 97,10)
]

segments = []
cur = 0
for a, b in REMOVE:
    segments.append([cur, a]); cur = b
segments.append([cur, TOTAL_SRC_FRAMES])

def src2out_f(f):
    """Fotograma de origen → fotograma de salida (si cae en un recorte, se
    lleva al inicio del material siguiente)."""
    removed = 0
    for a, b in REMOVE:
        if f >= b: removed += b - a
        elif f >= a: return a - removed
    return f - removed

def s2o(t):  # segundos de origen → segundos de salida
    return src2out_f(t * FPS) / FPS if False else (src2out_exact(t))

def src2out_exact(t):
    removed = 0.0
    for a, b in REMOVE:
        a_s, b_s = a / FPS, b / FPS
        if t >= b_s: removed += b_s - a_s
        elif t >= a_s: return a_s - removed
    return t - removed

OUT_FRAMES = sum(b - a for a, b in segments)

# --------------------------------------------- reencuadre en saltos de plano
# Encuadres de origen casi idénticos a ambos lados de un corte: se alterna un
# reencuadre fijo (sin animación) para que el salto se lea como cambio de plano.
SHOT_BOUNDS = [0, 187, 346, 454, 617, 749, 915, 1075, 1177, 1318, 1443, 1589,
               1695, 1823, 1940, 2054, 2161, 2475, 2628, 2796, 2913, 99999]
PUNCH = {749: 1.08, 1318: 1.08, 1695: 1.08, 1940: 1.08, 2161: 1.08, 2628: 1.08}
def scale_for(src_f):
    for i in range(len(SHOT_BOUNDS) - 1):
        if SHOT_BOUNDS[i] <= src_f < SHOT_BOUNDS[i + 1]:
            return PUNCH.get(SHOT_BOUNDS[i], 1.0)
    return 1.0

video_clips = []
o = 0
for a, b in segments:
    # partir también en los límites de plano para aplicar el reencuadre
    cuts = [a] + [s for s in SHOT_BOUNDS if a < s < b] + [b]
    for x, y in zip(cuts, cuts[1:]):
        video_clips.append(dict(src=x, out=o + (x - a), dur=y - x, scale=scale_for(x)))
    o += b - a

audio_clips = []
o = 0
H = 3  # asas de 3 fotogramas: fundido cruzado con el ambiente del propio clip
for i, (a, b) in enumerate(segments):
    hin = H if i > 0 else 0
    hout = H if i < len(segments) - 1 else 0
    audio_clips.append(dict(src=a - hin, out=o - hin, dur=(b - a) + hin + hout, fin=hin * 2, fout=hout * 2))
    o += b - a
# el último clip se desvanece 8 fotogramas al final
audio_clips[-1]['fout'] = 8

# ------------------------------------------------ afinado de tiempos de voz
def onset(t0, t1, thr=-22.0):
    for i in range(int(t0 * 100), int(t1 * 100)):
        if i + 3 < len(rms) and rms[i] > thr and rms[i + 1] > thr - 4 and rms[i + 2] > thr - 4:
            return i / 100
    return t0

def offset(t0, t1, thr=-28.0):
    for i in range(int(t1 * 100), int(t0 * 100), -1):
        if i < len(rms) and rms[i] > thr:
            return i / 100 + 0.04
    return t1

def wstart(i):
    w = W[i]; lo = W[i - 1]['e'] if i > 0 else 0
    return onset(max(lo, w['s'] - 0.05), min(w['e'], w['s'] + 0.6))

def wend(i):
    w = W[i]; hi = W[i + 1]['s'] if i + 1 < len(W) else w['e'] + 0.3
    return offset(w['s'], min(hi + 0.4, w['e'] + 0.2))

# ------------------------------------------------------------- subtítulos
# (texto, palabra inicial, palabra final). *palabra* = resalte discreto.
CUES = [
    ("Son las 2 de la mañana,", 0, 5),
    ("otra vez te cortaron la *luz*", 6, 11),
    ("y tu casa ahora se convierte en un *horno*", 12, 20),
    ("durante las próximas 6 horas.", 21, 25),
    ("Sabes que no vas a dormir nada,", 26, 32),
    ("mañana tienes que trabajar temprano", 33, 37),
    ("y tus hijos empiezan a llorar.", 38, 43),
    ("Es la impotencia de ver", 44, 48),
    ("cómo se te daña la comida en la *nevera*.", 49, 57),
    ("Se te cae el *internet*", 58, 62),
    ("a la mitad de un trabajo importante", 63, 69),
    ("y saber que tú y tu familia", 70, 76),
    ("se van a trasnochar.", 77, 80),
    ("El verdadero lujo hoy", 81, 84),
    ("no es un carro del año,", 85, 90),
    ("es la *tranquilidad* de tu familia.", 91, 96),
    ("En *ALK* no te instalamos un equipito barato", 97, 104),
    ("para prender 3 bombillos", 105, 108),
    ("que se te va a dañar en 3 meses.", 109, 117),
    ("Nosotros montamos", 118, 119),
    ("infraestructura eléctrica *profesional*,", 120, 122),
    ("blindada contra picos de voltaje.", 123, 127),
    ("Cero ruido de plantas eléctricas,", 128, 132),
    ("cero humo y cero mantenimiento.", 133, 137),
    ("Opción esencial desde *1.500 dólares*,", 138, 142),
    ("diseñada para casas, apartamentos u oficinas.", 143, 148),
    ("Te da de *5 a 6 horas* de autonomía real", 149, 158),
    ("para mantener activos 2 ventiladores", 159, 163),
    ("y iluminación LED completa,", 164, 167),
    ("televisores y tu internet encendido", 168, 172),
    ("para que nunca dejes de producir.", 173, 178),
    ("Hogar funcional desde *3.100 dólares*,", 179, 184),
    ("el equilibrio perfecto.", 185, 187),
    ("Cuenta con *9,6 kWh* de energía", 188, 194),
    ("para respaldar tu nevera,", 195, 198),
    ("iluminación, internet", 199, 200),
    ("y un aire acondicionado de *12.000 BTU*,", 201, 208),
    ("para que duermas fresco y protejas tus alimentos", 209, 216),
    ("sin turnar los equipos.", 217, 220),
    ("Sistema Elite 6000 desde *5.150 dólares*,", 221, 227),
    ("para quienes no aceptan", 228, 231),
    ("interrupciones en su confort.", 232, 235),
    ("Es un tanque masivo de *19,2 kWh*", 236, 243),
    ("de autonomía real.", 244, 246),
    ("Mantiene encendidos en simultáneo", 247, 250),
    ("2 aires acondicionados de *12.000 BTU*.", 251, 257),
    ("Nevera, freezer, computadora", 258, 260),
    ("y toda tu casa funcionando", 261, 265),
    ("como si nunca se hubiese ido la luz.", 266, 273),
    ("Lo mejor de todo es que toda nuestra ingeniería", 274, 282),
    ("es 100 % escalable", 283, 286),
    ("a *energía solar* en el futuro.", 287, 292),
    ("Deja de sufrir por la red eléctrica", 293, 299),
    ("y toma el control de tu hogar hoy mismo.", 300, 308),
    ("Haz clic abajo,", 309, 311),
    ("agenda una asesoría técnica *sin costo*", 312, 317),
    ("por parte de nuestro equipo de ingenieros", 318, 324),
    ("y deja que nosotros nos encarguemos del resto.", 325, 332),
]
# comprobación: las palabras cubren toda la transcripción, en orden
assert CUES[0][1] == 0 and CUES[-1][2] == len(W) - 1
for (_, _, e1), (_, s2, _) in zip(CUES, CUES[1:]):
    assert s2 == e1 + 1, (e1, s2)

# anclas manuales donde Whisper estiró la palabra sobre una pausa (verificadas
# con la envolvente de energía)
ONSET_FIX = {26: 6.52, 44: 12.05, 81: 20.84, 118: 30.70, 123: 34.06, 128: 35.82,
             138: 39.36, 149: 44.08, 164: 48.20, 179: 53.21, 188: 56.84, 199: 61.18,
             209: 64.82, 221: 68.50, 228: 71.46, 236: 74.52, 247: 78.94, 258: 82.72,
             274: 87.60, 293: 93.30, 309: 97.38}

cues = []
for text, i0, i1 in CUES:
    st = ONSET_FIX.get(i0, wstart(i0))
    en = wend(i1)
    cues.append(dict(text=text, s=st, e=en))
# a la salida: entrar 2 fotogramas antes de la voz, sostener hasta 10 fotogramas
# después o hasta el siguiente subtítulo
out_cues = []
for i, c in enumerate(cues):
    s = src2out_exact(c['s']) - 2 / FPS
    e = src2out_exact(c['e']) + 10 / FPS
    out_cues.append(dict(text=c['text'], s=max(0, s), e=e))
for a, b in zip(out_cues, out_cues[1:]):
    if a['e'] > b['s'] - 1 / FPS: a['e'] = b['s'] - 1 / FPS
out_cues[-1]['e'] = min(out_cues[-1]['e'] + 0.3, OUT_FRAMES / FPS)
for c in out_cues:
    c['sf'] = round(c['s'] * FPS); c['ef'] = round(c['e'] * FPS)

def srt_time(t):
    ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f'{h:02}:{m:02}:{s:02},{ms:03}'

def wrap2(t, maxc=34):
    t = t.replace('*', '')
    if len(t) <= maxc: return t
    words = t.split(' '); best = None
    for k in range(1, len(words)):
        l1, l2 = ' '.join(words[:k]), ' '.join(words[k:])
        sc = max(len(l1), len(l2))
        if best is None or sc < best[0]: best = (sc, l1 + '\n' + l2)
    return best[1]

with open('/home/user/Edici-n/work/subtitulos.srt', 'w', encoding='utf-8') as f:
    for i, c in enumerate(out_cues, 1):
        f.write(f"{i}\n{srt_time(c['sf'] / FPS)} --> {srt_time(c['ef'] / FPS)}\n{wrap2(c['text'])}\n\n")

# --------------------------------------------------------- eventos de apoyo
def T(t):  # segundos de origen → segundos de salida
    return src2out_exact(t)
def F(t):
    return round(T(t) * FPS)

ev = {}
# Apertura dramatizada (Hyperframes): ocupa 0–19,70 s y vuelve al rostro
# 1 fotograma antes de «El verdadero lujo hoy».
ev['drama'] = dict(start=0.0, dur=591 / FPS)
# Infraestructura: corte en L. La imagen pasa al gráfico 9 fotogramas antes
# de que termine «…en 3 meses» y la voz remata sobre el apoyo.
infra_in = T(30.46) - 9 / FPS
infra_out = T(35.8333)
ev['infra'] = dict(start=infra_in, dur=infra_out - infra_in,
                   t_title=T(31.30) - infra_in, t_shield=T(34.06) - infra_in,
                   t_nodes=T(30.70) - infra_in)
# Planes: misma plantilla. Nombre + «Desde» al nombrarlo; datos al decirlos.
def plan(start_src, end_src, name, price, tiles, desde_src):
    s = T(start_src)
    return dict(start=s - 3 / FPS, dur=T(end_src) - s + 3 / FPS, name=name, price=price,
                t_price=T(desde_src) - s + 3 / FPS,
                tiles=[dict(t=T(tt) - s + 3 / FPS, v=v, l=l) for tt, v, l in tiles])
ev['plan1'] = plan(39.36, 52.62, 'Opción esencial', 'USD 1.500',
                   [(44.34, '5–6 h', 'de autonomía')], 39.94)
ev['plan2'] = plan(53.21, 68.22, 'Hogar funcional', 'USD 3.100',
                   [(57.16, '9,6 kWh', 'de energía'), (62.78, '12.000 BTU', 'aire acondicionado')], 53.74)
ev['plan3'] = plan(68.50, 86.83, 'Sistema Elite 6000', 'USD 5.150',
                   [(76.08, '19,2 kWh', 'de autonomía real'), (80.24, '2 aires', 'de 12.000 BTU')], 69.64)
# Apoyos puntuales (columna derecha)
p1s = T(47.00)
ev['uses1'] = dict(start=p1s, dur=T(52.62) - p1s,
                   items=[dict(t=T(47.04) - p1s, icon='fan', label='2 ventiladores'),
                          dict(t=T(48.20) - p1s, icon='bulb', label='Iluminación LED'),
                          dict(t=T(50.10) - p1s, icon='wifi', label='Internet')])
p2s = T(59.80)
ev['uses2'] = dict(start=p2s, dur=T(62.60) - p2s,
                   items=[dict(t=T(59.88) - p2s, icon='fridge', label='Nevera')])
# Elite: corte en L hacia el dato. La imagen cambia 8 fotogramas antes del
# final de «…en su confort»; la voz sigue sobre el apoyo y volvemos al rostro
# justo en «Mantiene» (sincronía labial).
st_in = T(74.46) - 8 / FPS
st_out = T(78.86)
ev['stat'] = dict(start=st_in, dur=st_out - st_in, t_value=T(76.08) - st_in,
                  t_label=T(77.90) - st_in, t_tank=T(75.36) - st_in)
# Solar: corte en L sobre «…se hubiese ido la luz» (10 fotogramas).
so_in = T(87.16) - 10 / FPS
so_out = T(93.2)
ev['solar'] = dict(start=so_in, dur=so_out - so_in, t_system=T(88.62) - so_in,
                   t_scal=T(90.16) - so_in, t_panel=T(91.46) - so_in)
# Invitación
cs = T(98.20)
ev['cta'] = dict(start=cs, dur=OUT_FRAMES / FPS - cs)

for k, v in ev.items():
    v['sf'] = round(v['start'] * FPS)
    v['df'] = round(v['dur'] * FPS)

# Intervalos de pantalla completa (fondo desenfocado bajo el gráfico)
FULL = ['infra', 'stat', 'solar']

edl = dict(fps=FPS, frames=OUT_FRAMES, video=video_clips, audio=audio_clips,
           cues=[dict(text=c['text'], sf=c['sf'], ef=c['ef']) for c in out_cues],
           gfx=[dict(id=k, sf=v['sf'], df=v['df'], full=k in FULL) for k, v in ev.items()])
json.dump(edl, open(f'{OUT}/src/edl.json', 'w'), ensure_ascii=False, indent=1)
json.dump(ev, open('/home/user/Edici-n/work/events.json', 'w'), ensure_ascii=False, indent=1)
print('salida:', OUT_FRAMES, 'fotogramas =', OUT_FRAMES / FPS, 's')
for k, v in ev.items():
    print(f"{k:9s} {v['start']:6.2f}s +{v['dur']:5.2f}s")
for c in out_cues[:8]:
    print(c)
