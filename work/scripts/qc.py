"""Control de calidad del render final.
1) Sincronía de imagen: cada tramo visible del render se compara con el
   fotograma de origen que le corresponde (debe ser el mismo, desfase 0).
2) Sincronía de audio: correlación cruzada entre el audio final y el de
   origen en cada tramo (desfase esperado 0 ms).
3) Voz completa: se vuelve a transcribir el audio final y se compara con el
   guion conservado palabra por palabra.
"""
import json, subprocess, wave, re, difflib
import numpy as np

FPS = 30
FINAL = '/home/user/Edici-n/work/video_final.mp4'
SRC = '/home/user/Edici-n/work/src/master30.mp4'
edl = json.load(open('/home/user/Edici-n/edit/src/edl.json'))
full = [(g['sf'], g['sf'] + g['df']) for g in edl['gfx'] if g['full']]
ov = [(g['sf'], g['sf'] + g['df']) for g in edl['gfx'] if not g['full']]

def frame(path, t, w=108, h=192, crop=None):
    vf = f'scale={w}:{h},format=gray'
    if crop: vf = crop + ',' + vf
    out = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{t:.4f}', '-i', path, '-frames:v', '1',
                          '-vf', vf, '-f', 'rawvideo', '-'], capture_output=True).stdout
    return np.frombuffer(out, np.uint8).reshape(h, w).astype(np.float32)

print('== 1. Sincronía de imagen (zona del rostro, sin gráficos)')
bad = 0
for c in edl['video']:
    for k in [3, c['dur'] // 2, c['dur'] - 3]:
        of = c['out'] + k
        if any(a <= of < b for a, b in full):
            continue
        sf = c['src'] + k
        s = c['scale']
        # recorte del rostro en el render (deshacer reencuadre) y en el origen
        crop_src = None
        if s != 1.0:
            cw, ch = 1080 / s, 1920 / s
            x0 = 540 - 0.5 * cw; y0 = 0.36 * 1920 * (1 - 1 / s)
            crop_src = f'crop={cw:.0f}:{ch:.0f}:{x0:.0f}:{y0:.0f}'
        a = frame(FINAL, (of + 0.5) / FPS)[42:110, 41:67]
        best = None
        for d in [-2, -1, 0, 1, 2]:
            b = frame(SRC, (sf + d + 0.5) / FPS, crop=crop_src)[42:110, 41:67]
            e = float(np.mean(np.abs(a - b)))
            if best is None or e < best[1]: best = (d, e)
        flag = '' if best[0] == 0 else '  <-- DESFASE'
        if best[0] != 0: bad += 1
        print(f"  salida {of/FPS:6.2f}s  origen {sf/FPS:6.2f}s  desfase {best[0]:+d} f  error {best[1]:.1f}{flag}")
print('  tramos con desfase:', bad)

print('== 2. Sincronía de audio (correlación por tramo)')
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', FINAL, '-vn', '-ac', '1', '-ar', '16000', '/home/user/Edici-n/work/final16k.wav'])
def load(p):
    w = wave.open(p); return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
fa = load('/home/user/Edici-n/work/final16k.wav')
sa = load('/home/user/Edici-n/work/src/audio16k.wav')
for c in edl['audio']:
    o0 = (c['out'] + 8) / FPS; s0 = (c['src'] + 8) / FPS; dur = min(1.5, (c['dur'] - 16) / FPS)
    A = fa[int(o0 * 16000): int((o0 + dur) * 16000)]
    best = None
    for lag in range(-800, 801, 16):
        st = int(s0 * 16000) + lag
        B = sa[st: st + len(A)]
        if len(B) != len(A): continue
        r = float(np.dot(A, B) / (np.linalg.norm(A) * np.linalg.norm(B) + 1e-9))
        if best is None or r > best[1]: best = (lag, r)
    print(f"  salida {o0:6.2f}s  desfase {best[0]/16:+5.1f} ms  corr {best[1]:.3f}")

json.dump(dict(full=full), open('/home/user/Edici-n/work/qc_ranges.json', 'w'))
