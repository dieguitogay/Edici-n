"""Genera un proyecto de Hyperframes por gráfico de apoyo (HTML + GSAP) con
los tiempos ya calculados sobre la edición final. Cada uno se renderiza a
MOV ProRes 4444 con transparencia y Remotion lo coloca en la línea de tiempo."""
import json, os, shutil, sys

EV = json.load(open('/home/user/Edici-n/work/events.json'))
BASE = '/home/user/Edici-n/edit/hf'
ASSETS = f'{BASE}/gfx'
OUT = f'{BASE}/out'

HEAD = """<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="base.css"><style>{css}</style>
<script src="gsap.min.js"></script><script src="icons.js"></script></head><body>
<div id="root" class="root" data-composition-id="root" data-width="1080" data-height="1920" data-fps="30" data-start="0" data-duration="{dur:.3f}">
{body}
</div>
<script>
document.querySelectorAll('[data-icon]').forEach(e=>{{e.innerHTML=ICONS[e.dataset.icon]}});
const tl=gsap.timeline({{paused:true}});
{js}
tl.set({{}},{{}},{dur:.3f});
window.__timelines={{root:tl}};
</script></body></html>"""

COMMON_CSS = """
.panel{position:absolute;background:var(--navy);border:1px solid rgba(255,255,255,.10);border-radius:22px;box-shadow:0 10px 40px rgba(0,0,0,.28)}
.muted{color:var(--muted)}
"""

def ease_in(sel, t, x=0, y=14, d=0.32):
    return f'tl.fromTo("{sel}",{{opacity:0,x:{x},y:{y}}},{{opacity:1,x:0,y:0,duration:{d},ease:"power2.out"}},{t:.3f});'

def ease_out(sel, t, d=0.22):
    return f'tl.to("{sel}",{{opacity:0,duration:{d},ease:"power1.in"}},{max(t, 0):.3f});'

def write(name, dur, body, css, js):
    d = f'{OUT}/{name}'
    os.makedirs(d, exist_ok=True)
    for f in ['gsap.min.js', 'icons.js', 'base.css', 'logo_alk.png']:
        shutil.copy(f'{ASSETS}/{f}', d)
    open(f'{d}/index.html', 'w').write(HEAD.format(css=COMMON_CSS + css, body=body, js='\n'.join(js), dur=dur))

# ---------------------------------------------------------------- apagón
def blackout(e):
    css = """.badge{position:absolute;left:64px;display:flex;align-items:center;gap:16px;padding:16px 26px 16px 18px;opacity:0}
.badge .ico{width:48px;height:48px;position:relative;color:var(--white)}
.badge .ico::after{content:"";position:absolute;left:-4px;right:-4px;top:50%;height:4px;border-radius:2px;background:#ff8a5c;transform:rotate(-40deg)}
.badge .t{font-size:32px;font-weight:600}.badge .s{font-size:22px;font-weight:500;color:var(--muted);letter-spacing:.06em;text-transform:uppercase}"""
    body, js = [], []
    for i, it in enumerate(e['items']):
        body.append(f'<div class="panel badge" id="b{i}" style="top:{232 + i * 108}px"><span class="ico" data-icon="{it["icon"]}"></span><div><div class="s">Sin luz</div><div class="t">{it["label"]}</div></div></div>')
        js.append(ease_in(f'#b{i}', it['t'], x=-18, y=0))
    js.append(ease_out('.badge', e['dur'] - 0.25))
    write('blackout', e['dur'], '\n'.join(body), css, js)

# ---------------------------------------------------- tarjeta de plan (x3)
def plan(name, e):
    css = """.card{left:64px;top:214px;padding:24px 34px 26px;min-width:540px;opacity:0}
.card .n{font-size:44px;font-weight:600;letter-spacing:-.01em;line-height:1.1}
.card .p{display:flex;align-items:baseline;gap:14px;margin-top:10px;opacity:0}
.card .d{font-size:30px;font-weight:500;color:var(--muted)}
.card .v{font-size:70px;font-weight:700;letter-spacing:-.02em;line-height:1}
.card .bar{position:absolute;left:0;top:26px;bottom:26px;width:5px;border-radius:3px;background:var(--amber)}
.tile{position:absolute;left:64px;min-width:300px;white-space:nowrap;padding:16px 28px 18px 28px;opacity:0}
.tile .tv{font-size:50px;font-weight:700;letter-spacing:-.02em;line-height:1.05}
.tile .tl{font-size:24px;font-weight:500;color:var(--muted);margin-top:4px}
.tile::before{content:"";position:absolute;left:0;top:18px;bottom:18px;width:4px;border-radius:2px;background:var(--blue2)}"""
    body = [f'<div class="panel card" id="card"><span class="bar"></span><div class="n">{e["name"]}</div>'
            f'<div class="p" id="price"><span class="d">Desde</span><span class="v">{e["price"]}</span></div></div>']
    js = [ease_in('#card', 0.0), ease_in('#price', max(e['t_price'], 0.25), y=8, d=0.28)]
    for i, t in enumerate(e['tiles']):
        body.append(f'<div class="panel tile" id="t{i}" style="top:{428 + i * 148}px"><div class="tv">{t["v"]}</div><div class="tl">{t["l"]}</div></div>')
        js.append(ease_in(f'#t{i}', t['t'] - 0.03, x=-18, y=0))
    js.append(ease_out('.card,.tile', e['dur'] - 0.25))
    write(name, e['dur'], '\n'.join(body), css, js)

# --------------------------------------------- apoyos puntuales (derecha)
def uses(name, e):
    css = """.pill{position:absolute;right:64px;display:flex;align-items:center;gap:14px;padding:14px 26px 14px 18px;border-radius:999px;opacity:0}
.pill .ico{width:42px;height:42px;color:var(--amber)}.pill span.l{font-size:30px;font-weight:600}"""
    body, js = [], []
    for i, it in enumerate(e['items']):
        body.append(f'<div class="panel pill" id="u{i}" style="top:{470 + i * 92}px"><span class="ico" data-icon="{it["icon"]}"></span><span class="l">{it["label"]}</span></div>')
        js.append(ease_in(f'#u{i}', it['t'] - 0.03, x=18, y=0))
    js.append(ease_out('.pill', e['dur'] - 0.25))
    write(name, e['dur'], '\n'.join(body), css, js)

# ---------------------------------------------- infraestructura (completa)
def infra(e):
    css = """.title{position:absolute;left:80px;right:80px;top:300px;text-align:center;font-size:58px;font-weight:700;letter-spacing:-.02em;line-height:1.08;opacity:0}
.title em{font-style:normal;color:var(--amber)}
.node{position:absolute;left:190px;width:700px;display:flex;align-items:center;gap:26px;padding:26px 34px;opacity:0}
.node .ico{width:64px;height:64px}.node .h{font-size:36px;font-weight:700}.node .s{font-size:25px;color:var(--muted);margin-top:4px}
.node.core{background:linear-gradient(135deg,#2a44d8,#1a2b93);border-color:rgba(255,255,255,.28)}
.link{position:absolute;left:538px;width:4px;height:74px;border-radius:2px;background:var(--amber);transform-origin:top;transform:scaleY(0)}
.shield{position:absolute;left:190px;width:700px;top:1108px;display:flex;align-items:center;justify-content:center;gap:16px;padding:18px 28px;border-radius:999px;background:rgba(255,196,107,.16);border:1px solid rgba(255,196,107,.55);opacity:0}
.shield .ico{width:46px;height:46px;color:var(--amber)}.shield span.l{font-size:31px;font-weight:600}"""
    body = """<div class="title" id="title">Infraestructura eléctrica <em>profesional</em></div>
<div class="panel node" id="n0" style="top:480px"><span class="ico" data-icon="grid"></span><div><div class="h">Red eléctrica</div><div class="s">Cuando se va la luz…</div></div></div>
<div class="link" id="l0" style="top:620px"></div>
<div class="panel node core" id="n1" style="top:706px"><span class="ico" data-icon="battery"></span><div><div class="h">Respaldo ALK</div><div class="s" style="color:rgba(255,244,230,.85)">Inversor + baterías</div></div></div>
<div class="link" id="l1" style="top:846px"></div>
<div class="panel node" id="n2" style="top:932px"><span class="ico" data-icon="home"></span><div><div class="h">Tu hogar</div><div class="s">…sigue funcionando</div></div></div>
<div class="shield" id="sh"><span class="ico" data-icon="shield"></span><span class="l">Blindada contra picos de voltaje</span></div>"""
    t0 = 0.0
    js = [ease_in('#n0', t0 + 0.02, y=18),
          f'tl.to("#l0",{{scaleY:1,duration:.25,ease:"power1.out"}},{t0 + 0.22:.3f});',
          ease_in('#n1', t0 + 0.38, y=18),
          f'tl.to("#l1",{{scaleY:1,duration:.25,ease:"power1.out"}},{t0 + 0.58:.3f});',
          ease_in('#n2', t0 + 0.74, y=18),
          ease_in('#title', e['t_title'] - 0.05, y=12, d=0.35),
          ease_in('#sh', e['t_shield'] - 0.04, y=12)]
    write('infra', e['dur'], body, css, js)

# ---------------------------------------------- 19,2 kWh (completa)
def stat(e):
    css = """.k{position:absolute;left:0;right:0;top:420px;text-align:center;font-size:30px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);opacity:0}
.tank{position:absolute;left:390px;top:500px;width:300px;height:170px;border:5px solid var(--white);border-radius:26px;opacity:0}
.tank::after{content:"";position:absolute;right:-22px;top:50px;width:14px;height:60px;border-radius:0 8px 8px 0;background:var(--white)}
.fill{position:absolute;left:10px;top:10px;bottom:10px;width:0;border-radius:16px;background:linear-gradient(90deg,#5b74ff,#ffc46b)}
.val{position:absolute;left:0;right:0;top:730px;text-align:center;font-size:170px;font-weight:700;letter-spacing:-.04em;line-height:1;opacity:0}
.val small{font-size:80px;font-weight:600;letter-spacing:-.01em;margin-left:14px}
.lab{position:absolute;left:0;right:0;top:930px;text-align:center;font-size:44px;font-weight:600;color:var(--amber);opacity:0}"""
    body = """<div class="k" id="k">Sistema Elite 6000</div>
<div class="tank" id="tank"><div class="fill" id="fill"></div></div>
<div class="val" id="val"><span id="num">19,2</span><small>kWh</small></div>
<div class="lab" id="lab">de autonomía real</div>"""
    js = [ease_in('#k', 0.02, y=10), ease_in('#tank', 0.10, y=14),
          f'tl.to("#fill",{{width:"260px",duration:1.6,ease:"power1.inOut"}},{max(e["t_tank"] - 0.1, 0.3):.3f});',
          ease_in('#val', e['t_value'] - 0.05, y=16, d=0.3),
          ease_in('#lab', e['t_label'] - 0.05, y=10)]
    write('stat', e['dur'], body, css, js)

# ------------------------------------------------- energía solar (completa)
def solar(e):
    css = """.box{position:absolute;left:290px;top:860px;width:500px;display:flex;align-items:center;gap:24px;padding:28px 34px;opacity:0;background:linear-gradient(135deg,#2a44d8,#1a2b93)!important}
.box .ico{width:66px;height:66px}.box .h{font-size:38px;font-weight:700}.box .s{font-size:25px;color:rgba(255,244,230,.85);margin-top:4px}
.sun{position:absolute;left:290px;top:430px;width:500px;display:flex;align-items:center;gap:24px;padding:28px 34px;opacity:0;border:2px dashed rgba(255,196,107,.8)!important;background:rgba(9,17,52,.72)!important}
.sun .ico{width:66px;height:66px;color:var(--amber)}.sun .h{font-size:38px;font-weight:700}.sun .s{font-size:25px;color:var(--muted);margin-top:4px}
.dash{position:absolute;left:538px;top:600px;width:4px;height:250px;background:repeating-linear-gradient(to bottom,var(--amber) 0 14px,transparent 14px 26px);transform-origin:bottom;transform:scaleY(0)}
.tag{position:absolute;left:0;right:0;top:300px;text-align:center;font-size:56px;font-weight:700;letter-spacing:-.02em;opacity:0}
.tag em{font-style:normal;color:var(--amber)}"""
    body = """<div class="tag" id="tag"><em>100 %</em> escalable</div>
<div class="panel sun" id="sun"><span class="ico" data-icon="panel"></span><div><div class="h">Energía solar</div><div class="s">Ampliación a futuro</div></div></div>
<div class="dash" id="dash"></div>
<div class="panel box" id="box"><span class="ico" data-icon="battery"></span><div><div class="h">Tu sistema ALK</div><div class="s">Inversor + baterías</div></div></div>"""
    js = [ease_in('#box', 0.02, y=16),
          ease_in('#tag', e['t_scal'] - 0.05, y=10),
          f'tl.to("#dash",{{scaleY:1,duration:.35,ease:"power1.out"}},{e["t_panel"] - 0.15:.3f});',
          ease_in('#sun', e['t_panel'] + 0.1, y=-16)]
    write('solar', e['dur'], body, css, js)

# ------------------------------------------------------------- invitación
def cta(e):
    css = """.cta{position:absolute;left:64px;right:64px;top:214px;display:flex;align-items:center;gap:28px;padding:26px 34px;border-radius:24px;background:var(--white);color:#0d1640;box-shadow:0 10px 40px rgba(0,0,0,.28);opacity:0}
.cta img{width:150px;flex:none}.cta .h{font-size:40px;font-weight:700;letter-spacing:-.015em;line-height:1.12}
.cta .h b{color:#2a44d8;font-weight:700}.cta .s{display:flex;align-items:center;gap:10px;font-size:26px;font-weight:600;color:#2a44d8;margin-top:8px}
.cta .s .ico{width:30px;height:30px}"""
    body = """<div class="cta" id="cta"><img src="logo_alk.png" alt="ALK"><div><div class="h">Agenda una asesoría técnica <b style="white-space:nowrap">sin costo</b></div><div class="s"><span class="ico" data-icon="cal"></span>Con nuestro equipo de ingenieros</div></div></div>"""
    js = [ease_in('#cta', 0.0, y=14, d=0.35)]
    write('cta', e['dur'], body, css, js)

blackout(EV['blackout']); infra(EV['infra']); stat(EV['stat']); solar(EV['solar']); cta(EV['cta'])
for k in ['plan1', 'plan2', 'plan3']: plan(k, EV[k])
uses('uses1', EV['uses1']); uses('uses2', EV['uses2'])
print('ok', sorted(os.listdir(OUT)))
