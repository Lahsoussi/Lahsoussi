#!/usr/bin/env python3
"""Parametric street elevation (façade) of the R+2 building as inline SVG.

Config (metres):
{
 "width": 10, "levels": [{"name":"RDC","h":3.2},{"name":"1er","h":3.0},{"name":"2e","h":3.0}],
 "parapet": 1.1, "bulkhead": {"x":0,"w":2.4,"h":2.6},
 "bays": [ {"level":0,"kind":"door","x":0.6,"w":1.2,"h":2.4},
           {"level":0,"kind":"window","x":3.0,"w":2.6,"h":1.4,"sill":1.0},
           {"level":1,"kind":"balcony","x":2.4,"w":7.6,"depth":1.0},
           {"level":1,"kind":"glazing","x":3.0,"w":3.0,"h":2.3,"sill":0.1}, ... ],
 "claustra": [{"level":1,"x":7.0,"w":2.6,"h":2.4}]   # decorative screen panels on balcony fronts
}
"""
import json, sys

S = 62.0
M = 100.0

def px(v):
    return round(v * S + M, 2)

def render(cfg, id_prefix='e'):
    W = cfg['width']
    levels = cfg['levels']
    H = sum(l['h'] for l in levels)
    parapet = cfg.get('parapet', 1.1)
    bulk = cfg.get('bulkhead')
    top = H + parapet + (bulk['h'] if bulk else 0)
    ground_y = top  # y grows downward; ground line at y = top (in metres from top)
    def Y(z):  # z = height above ground -> px y
        return px(top - z)
    total_w = W * S + 2 * M
    total_h = top * S + 2 * M
    out = [f'<svg viewBox="0 0 {round(total_w)} {round(total_h)}" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="{id_prefix}-t" class="elev">',
           f'<title id="{id_prefix}-t">{cfg.get("title","Façade sur rue")}</title>']
    # ground / neighbours hint
    out.append(f'<line x1="{px(-0.9)}" y1="{Y(0)}" x2="{px(W+0.9)}" y2="{Y(0)}" class="ground"/>')
    out.append(f'<rect x="{px(-0.9)}" y="{Y(H+0.6)}" width="{round(0.9*S,2)}" height="{round((H+0.6)*S,2)}" class="neigh"/>')
    out.append(f'<rect x="{px(W)}" y="{Y(H+0.3)}" width="{round(0.9*S,2)}" height="{round((H+0.3)*S,2)}" class="neigh"/>')
    # main body
    out.append(f'<rect x="{px(0)}" y="{Y(H+parapet)}" width="{round(W*S,2)}" height="{round((H+parapet)*S,2)}" class="body"/>')
    # material bands (ground floor stone plinth)
    plinth = cfg.get('plinth', 0)
    if plinth:
        out.append(f'<rect x="{px(0)}" y="{Y(plinth)}" width="{round(W*S,2)}" height="{round(plinth*S,2)}" class="plinth"/>')
    for band in cfg.get('bands', []):
        out.append(f'<rect x="{px(band["x"])}" y="{Y(band["z"]+band["h"])}" width="{round(band["w"]*S,2)}" height="{round(band["h"]*S,2)}" class="{band.get("cls","band")}"/>')
    # bulkhead (stair head on roof)
    if bulk:
        out.append(f'<rect x="{px(bulk["x"])}" y="{Y(H+bulk["h"])}" width="{round(bulk["w"]*S,2)}" height="{round(bulk["h"]*S,2)}" class="body"/>')
        out.append(f'<rect x="{px(bulk["x"]+0.3)}" y="{Y(H+bulk["h"]-0.6)}" width="{round((bulk["w"]-0.6)*S,2)}" height="{round(0.5*S,2)}" class="glass"/>')
    # parapet line
    out.append(f'<line x1="{px(0)}" y1="{Y(H)}" x2="{px(W)}" y2="{Y(H)}" class="joint"/>')
    out.append(f'<line x1="{px(0)}" y1="{Y(H+parapet)}" x2="{px(W)}" y2="{Y(H+parapet)}" class="edge"/>')
    # slab lines
    z = 0
    for i, l in enumerate(levels):
        z += l['h']
        if i < len(levels) - 1:
            out.append(f'<line x1="{px(0)}" y1="{Y(z)}" x2="{px(W)}" y2="{Y(z)}" class="joint"/>')
    # level base heights
    base = []
    z = 0
    for l in levels:
        base.append(z); z += l['h']
    # balconies first (behind railings but in front of wall)
    for b in cfg.get('bays', []):
        if b['kind'] != 'balcony':
            continue
        z0 = base[b['level']]
        # slab
        out.append(f'<rect x="{px(b["x"])}" y="{Y(z0+0.18)}" width="{round(b["w"]*S,2)}" height="{round(0.18*S,2)}" class="slab"/>')
        # railing / claustra
        rh = b.get('rail', 1.05)
        cls = 'claustra' if b.get('screen') else 'rail'
        out.append(f'<rect x="{px(b["x"])}" y="{Y(z0+0.18+rh)}" width="{round(b["w"]*S,2)}" height="{round(rh*S,2)}" class="{cls}"/>')
        if b.get('screen'):
            # perforated pattern hint: grid of small diamonds
            n = int(b['w'] / 0.28)
            m = int(rh / 0.28)
            for i in range(n):
                for j in range(m):
                    cx = b['x'] + 0.14 + i * (b['w'] - 0.28) / max(n - 1, 1)
                    cz = z0 + 0.18 + 0.14 + j * (rh - 0.28) / max(m - 1, 1)
                    out.append(f'<rect x="{px(cx)-3.6}" y="{Y(cz)-3.6}" width="7.2" height="7.2" transform="rotate(45 {px(cx)} {Y(cz)})" class="perf"/>')
        else:
            n = int(b['w'] / 0.12)
            for i in range(n + 1):
                x = b['x'] + i * b['w'] / n
                out.append(f'<line x1="{px(x)}" y1="{Y(z0+0.18)}" x2="{px(x)}" y2="{Y(z0+0.18+rh)}" class="bar"/>')
            out.append(f'<line x1="{px(b["x"])}" y1="{Y(z0+0.18+rh)}" x2="{px(b["x"]+b["w"])}" y2="{Y(z0+0.18+rh)}" class="handrail"/>')
    # openings
    for b in cfg.get('bays', []):
        k = b['kind']
        z0 = base[b['level']]
        if k == 'door':
            out.append(f'<rect x="{px(b["x"])}" y="{Y(z0+b["h"])}" width="{round(b["w"]*S,2)}" height="{round(b["h"]*S,2)}" class="door"/>')
            # vertical slats
            n = int(b['w'] / 0.15)
            for i in range(1, n):
                x = b['x'] + i * b['w'] / n
                out.append(f'<line x1="{px(x)}" y1="{Y(z0+b["h"]-0.1)}" x2="{px(x)}" y2="{Y(z0+0.1)}" class="slat"/>')
        elif k in ('window', 'glazing'):
            sill = b.get('sill', 1.0)
            out.append(f'<rect x="{px(b["x"])}" y="{Y(z0+sill+b["h"])}" width="{round(b["w"]*S,2)}" height="{round(b["h"]*S,2)}" class="frame"/>')
            out.append(f'<rect x="{px(b["x"]+0.06)}" y="{Y(z0+sill+b["h"]-0.06)}" width="{round((b["w"]-0.12)*S,2)}" height="{round((b["h"]-0.12)*S,2)}" class="glass"/>')
            panes = b.get('panes', 2)
            for i in range(1, panes):
                x = b['x'] + i * b['w'] / panes
                out.append(f'<line x1="{px(x)}" y1="{Y(z0+sill+b["h"])}" x2="{px(x)}" y2="{Y(z0+sill)}" class="mullion"/>')
            if b.get('arch'):
                r = b['w'] / 2
                out.append(f'<path d="M{px(b["x"]-0.1)} {Y(z0+sill+b["h"])} A{round(r*S,2)} {round(r*S,2)} 0 0 1 {px(b["x"]+b["w"]+0.1)} {Y(z0+sill+b["h"])}" class="archline"/>')
        elif k == 'screen':
            out.append(f'<rect x="{px(b["x"])}" y="{Y(z0+b.get("sill",0)+b["h"])}" width="{round(b["w"]*S,2)}" height="{round(b["h"]*S,2)}" class="claustra"/>')
            n = int(b['w'] / 0.28); m = int(b['h'] / 0.28)
            for i in range(n):
                for j in range(m):
                    cx = b['x'] + 0.14 + i * (b['w'] - 0.28) / max(n - 1, 1)
                    cz = z0 + b.get('sill', 0) + 0.14 + j * (b['h'] - 0.28) / max(m - 1, 1)
                    out.append(f'<rect x="{px(cx)-3.6}" y="{Y(cz)-3.6}" width="7.2" height="7.2" transform="rotate(45 {px(cx)} {Y(cz)})" class="perf"/>')
        elif k == 'vent':
            out.append(f'<rect x="{px(b["x"])}" y="{Y(z0+b.get("sill",2.2)+b["h"])}" width="{round(b["w"]*S,2)}" height="{round(b["h"]*S,2)}" class="frame"/>')
    # level labels on the left
    for i, l in enumerate(levels):
        zc = base[i] + l['h'] / 2
        out.append(f'<text x="6" y="{Y(zc)+4}" class="lvl" text-anchor="start">{l["name"]}</text>')
        out.append(f'<text x="6" y="{Y(zc)+16}" class="lvl-a" text-anchor="start">{l.get("note","")}</text>')
    out.append(f'<text x="6" y="{Y(H+parapet/2)+4}" class="lvl" text-anchor="start">Terrasse</text>')
    # height dimension on right
    out.append(f'<line x1="{px(W+1.2)}" y1="{Y(0)}" x2="{px(W+1.2)}" y2="{Y(H+parapet)}" class="dim"/>')
    out.append(f'<line x1="{px(W+1.05)}" y1="{Y(0)}" x2="{px(W+1.35)}" y2="{Y(0)}" class="dim"/>')
    out.append(f'<line x1="{px(W+1.05)}" y1="{Y(H+parapet)}" x2="{px(W+1.35)}" y2="{Y(H+parapet)}" class="dim"/>')
    out.append(f'<text x="{px(W+1.2)+12}" y="{Y((H+parapet)/2)}" class="dim-t" transform="rotate(90 {px(W+1.2)+12} {Y((H+parapet)/2)})" text-anchor="middle">{H+parapet:.2f} m à l\'acrotère</text>')
    out.append(f'<text x="{px(W/2)}" y="{Y(0)+28}" class="street" text-anchor="middle">{cfg.get("street_label","RUE")}</text>')
    out.append('</svg>')
    return '\n'.join(out)

if __name__ == '__main__':
    cfg = json.load(open(sys.argv[1]))
    print(render(cfg, sys.argv[2] if len(sys.argv) > 2 else 'e'))
