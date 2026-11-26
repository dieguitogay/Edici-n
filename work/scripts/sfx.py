"""Diseño sonoro sintetizado para la dramatización del apagón (0–19,7 s).
Todo se genera aquí (sin librerías de sonido externas) y queda muy por debajo
de la voz: cama a unos -32 LUFS y golpes puntuales que no pasan de -18 dBFS."""
import numpy as np, wave

SR = 48000
DUR = 20.2
N = int(SR * DUR)
rng = np.random.default_rng(11)
L = np.zeros(N); Rch = np.zeros(N)
t = np.arange(N) / SR

def band(x, lo, hi):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    g = np.clip((f - lo * 0.8) / (lo * 0.2 + 1e-9), 0, 1) * np.clip((hi * 1.25 - f) / (hi * 0.25), 0, 1)
    return np.fft.irfft(X * g, len(x))

def env(a, b, fa=0.05, fb=0.05):
    e = np.zeros(N); i0, i1 = int(a * SR), int(b * SR)
    e[i0:i1] = 1
    na, nb = int(fa * SR), int(fb * SR)
    if na: e[i0:i0 + na] *= np.linspace(0, 1, na)
    if nb: e[i1 - nb:i1] *= np.linspace(1, 0, nb)
    return e

def add(sig, at, gain_db=0, pan=0.0):
    i = int(at * SR); n = min(len(sig), N - i)
    g = 10 ** (gain_db / 20)
    L[i:i + n] += sig[:n] * g * np.sqrt((1 - pan) / 2) * np.sqrt(2) / np.sqrt(2)
    Rch[i:i + n] += sig[:n] * g * np.sqrt((1 + pan) / 2)

def norm(x):
    return x / (np.max(np.abs(x)) + 1e-12)

# 1. antes del corte: zumbido eléctrico + motor del ventilador
hum = (np.sin(2 * np.pi * 60 * t) + .5 * np.sin(2 * np.pi * 120 * t) + .25 * np.sin(2 * np.pi * 180 * t))
# al cortar la luz el zumbido cae de tono y muere
ph = np.cumsum(np.where(t < 2.30, 60, 60 * np.exp(-(t - 2.30) * 5.5))) / SR
hum2 = np.sin(2 * np.pi * ph) + .5 * np.sin(4 * np.pi * ph)
hume = env(0, 2.30, 0.3, 0) + env(2.30, 2.90, 0, 0.6)
humsig = np.where(t < 2.30, hum, hum2) * hume
add(humsig * 0.5, 0, -30)
noise = rng.normal(0, 1, N)
whir = band(noise, 150, 900)
# modulación de 5 aspas: 6 Hz antes, frenando hasta 0 a los 3,85 s
rate = np.where(t < 2.30, 6.0, np.clip(6.0 * (1 - (t - 2.30) / 1.55), 0, 6))
am = 0.6 + 0.4 * np.sin(2 * np.pi * np.cumsum(rate) / SR)
whire = env(0, 3.9, 0.3, 1.2)
add(norm(whir) * am * whire, 0, -31)

# 2. el apagón: golpe grave + clic
k = np.arange(int(0.45 * SR)) / SR
thunk = np.sin(2 * np.pi * (80 * k - 50 * k * k / 0.9)) * np.exp(-k * 9)
click = band(rng.normal(0, 1, int(0.02 * SR)), 1500, 9000) * np.exp(-np.arange(int(0.02 * SR)) / SR * 300)
add(norm(thunk), 2.29, -19)
add(norm(click), 2.29, -24)
add(norm(click), 2.35, -30); add(norm(click), 2.41, -32)

# 3. ambiente nocturno: tono de sala + grillos (a partir del apagón)
room = band(rng.normal(0, 1, N), 60, 2500)
add(norm(room) * env(2.35, DUR, 0.6, 0.4), 0, -40)
def cricket():
    n = int(0.03 * SR); kk = np.arange(n) / SR
    pulse = np.sin(2 * np.pi * 4700 * kk) * np.sin(np.pi * kk / 0.03) ** 2
    s = np.zeros(int(0.14 * SR))
    for j in range(3): s[int(j * 0.045 * SR):int(j * 0.045 * SR) + n] += pulse
    return s
tt = 2.6
while tt < 19.5:
    add(cricket(), tt, -38 + rng.uniform(-4, 2), pan=rng.uniform(-0.8, 0.8))
    tt += rng.uniform(0.35, 0.9)

# 4. tensión: dron grave que crece hasta el final
dr = (np.sin(2 * np.pi * 43 * t) + .6 * np.sin(2 * np.pi * 86.5 * t + .3) + .25 * np.sin(2 * np.pi * 129 * t))
dre = env(3.8, 19.70, 1.5, 0.02) * np.clip(0.5 + (t - 3.8) / 32, 0, 1)
add(dr * dre * 0.5, 0, -27)

# 5. reloj: tics que aceleran y frenan (6 horas en 1,1 s)
def tick():
    n = int(0.012 * SR); return band(rng.normal(0, 1, n), 2500, 8000) * np.exp(-np.arange(n) / SR * 500)
u = np.linspace(0, 1, 46)
times = 4.98 + 1.1 * np.where(u < .5, 2 * u * u, 1 - (-2 * u + 2) ** 2 / 2)
for x in times: add(norm(tick()), x, -31)

# 6. teléfono: vibración al encender y aviso de alarma
k = np.arange(int(0.09 * SR)) / SR
add(norm(np.sin(2 * np.pi * 160 * k) * np.sin(np.pi * k / 0.09)), 6.21, -27)
for f0, d0 in [(1318.5, 0.0), (1760, 0.11)]:
    k = np.arange(int(0.5 * SR)) / SR
    add(norm(np.sin(2 * np.pi * f0 * k) * np.exp(-k * 9)), 8.55 + d0, -30)

# 7. monitor de bebé: estática y alerta
st = band(rng.normal(0, 1, N), 1800, 6000) * env(9.10, 11.0, 0.05, 0.05)
crk = np.zeros(N)
for x in rng.uniform(9.1, 11.0, 60): crk[int(x * SR)] = rng.uniform(-1, 1)
add(norm(st) * (0.6 + 0.4 * np.sin(2 * np.pi * 3 * t)), 0, -38)
add(norm(band(crk, 800, 7000)), 0, -32)
for x in [10.50, 10.84]:
    k = np.arange(int(0.09 * SR)) / SR
    add(norm(np.sin(2 * np.pi * 2093 * k) * np.sin(np.pi * k / 0.09)), x, -30)

# 8. nevera: sello de la puerta y clic de la linterna
seal = band(rng.normal(0, 1, int(0.25 * SR)), 80, 1200) * np.exp(-np.arange(int(0.25 * SR)) / SR * 18)
add(norm(seal), 11.06, -26)
add(norm(click), 11.62, -27)

# 9. router y laptop
for x in [14.66, 14.74, 14.82, 14.94]: add(norm(click), x, -33)
for f0, d0 in [(659.3, 0), (440, 0.16)]:
    k = np.arange(int(0.45 * SR)) / SR
    add(norm(np.sin(2 * np.pi * f0 * k) * np.exp(-k * 7)), 15.86 + d0, -29)

# 10. exterior: viento + subida hacia el corte al rostro (19,70 s)
wind = band(rng.normal(0, 1, N), 120, 1400) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.35 * t + 1))
add(norm(wind) * env(16.6, 19.70, 0.4, 0.02), 0, -34)
rise = band(rng.normal(0, 1, N), 600, 6000) * np.clip((t - 18.6) / 1.1, 0, 1) ** 2 * (t < 19.70)
add(norm(rise), 0, -31)

out = np.stack([L, Rch], 1) * 2.0   # +6 dB: presente, pero ~19 LU bajo la voz
out *= (t < 19.70)[:, None]          # silencio seco en el corte al rostro
peak = np.max(np.abs(out)); print('pico dBFS', 20 * np.log10(peak))
pcm = (np.clip(out, -1, 1) * 32767).astype('<i2')
w = wave.open('/home/user/Edici-n/edit/public/sfx.wav', 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes(pcm.tobytes()); w.close()
