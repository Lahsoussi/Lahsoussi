#!/usr/bin/env python3
"""Render a floor plan described in JSON (metres) to an inline SVG string.

Coordinate system: x to the right, y downwards, origin at the plot's top-left.
Room boxes are wall-centreline rectangles that tile the plot. Net area shown in
labels is (w - wall) * (h - wall) with wall = 0.20 m average (0.25 outer / 0.10-0.15 inner).

JSON schema (all lengths in metres):
{
  "title": "Étage courant", "plot": {"w": 10, "h": 10, "street": "bottom"},
  "rooms": [{"id": "salon", "name": "Salon marocain", "type": "salon", "x": 0, "y": 0, "w": 4.6, "h": 4.5,
             "furniture": [{"kind": "sedari", ...}]}],
  "doors": [{"x": 2.3, "y": 4.5, "w": 0.9, "dir": "h", "swing": "down-right"}],
  "windows": [{"x": 0.5, "y": 0, "w": 1.6, "dir": "h"}],
  "labels": [{"x":..., "y":..., "text": "..."}],
  "notes": ["..."]
}
"""
import json, math, sys

S = 62.0          # px per metre
M = 78.0          # margin px (room for dimension lines)
WALL_OUT = 0.25
WALL_IN = 0.12

FILL = {
    'salon':   'var(--pl-salon)',
    'sejour':  'var(--pl-salon)',
    'bedroom': 'var(--pl-bed)',
    'kitchen': 'var(--pl-kitchen)',
    'bath':    'var(--pl-wet)',
    'wc':      'var(--pl-wet)',
    'hall':    'var(--pl-hall)',
    'stair':   'var(--pl-stair)',
    'patio':   'var(--pl-patio)',
    'balcony': 'var(--pl-balcony)',
    'terrace': 'var(--pl-balcony)',
    'storage': 'var(--pl-hall)',
    'tech':    'var(--pl-hall)',
    'void':    'none',
}

def px(v):
    return round(v * S + M, 2)

def esc(s):
    return (s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))

def net_area(r):
    w = max(r['w'] - 0.2, 0.1)
    h = max(r['h'] - 0.2, 0.1)
    return w * h

def room_rect(r):
    """Return inner rectangle (x1,y1,x2,y2) in metres inset by half wall thickness."""
    return (r['x'] + 0.1, r['y'] + 0.1, r['x'] + r['w'] - 0.1, r['y'] + r['h'] - 0.1)

# ---------- furniture primitives (all in metres, relative to room inner rect) ----------

def f_rect(x, y, w, h, cls='fn', rx=0.0):
    return f'<rect x="{px(x)}" y="{px(y)}" width="{round(w*S,2)}" height="{round(h*S,2)}" rx="{round(rx*S,2)}" class="{cls}"/>'

def f_line(x1, y1, x2, y2, cls='fn'):
    return f'<line x1="{px(x1)}" y1="{px(y1)}" x2="{px(x2)}" y2="{px(y2)}" class="{cls}"/>'

def f_circle(cx, cy, r, cls='fn'):
    return f'<circle cx="{px(cx)}" cy="{px(cy)}" r="{round(r*S,2)}" class="{cls}"/>'

def furniture(room, item):
    x1, y1, x2, y2 = room_rect(room)
    k = item['kind']
    out = []
    if k == 'sedari':
        # U or L shaped banquettes 0.75 deep along given walls
        d = item.get('depth', 0.75)
        for side in item.get('sides', ['top', 'left', 'right']):
            if side == 'top':
                out.append(f_rect(x1 + 0.05, y1 + 0.05, (x2 - x1) - 0.1, d))
            elif side == 'bottom':
                out.append(f_rect(x1 + 0.05, y2 - d - 0.05, (x2 - x1) - 0.1, d))
            elif side == 'left':
                out.append(f_rect(x1 + 0.05, y1 + 0.05, d, (y2 - y1) - 0.1))
            elif side == 'right':
                out.append(f_rect(x2 - d - 0.05, y1 + 0.05, d, (y2 - y1) - 0.1))
        # low tables
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        out.append(f_rect(cx - 0.6, cy - 0.35, 1.2, 0.7, rx=0.05))
    elif k == 'sofa':
        out.append(f_rect(item['x'] + x1, item['y'] + y1, item.get('w', 2.2), item.get('h', 0.9), rx=0.08))
    elif k == 'table':
        out.append(f_rect(item['x'] + x1, item['y'] + y1, item.get('w', 1.6), item.get('h', 0.9), rx=0.04))
        # chairs
        tx, ty, tw, th = item['x'] + x1, item['y'] + y1, item.get('w', 1.6), item.get('h', 0.9)
        n = item.get('chairs', 4)
        for i in range(n // 2):
            cx = tx + tw * (i + 0.5) / (n // 2) - 0.2
            out.append(f_rect(cx, ty - 0.45, 0.4, 0.4, rx=0.06))
            out.append(f_rect(cx, ty + th + 0.05, 0.4, 0.4, rx=0.06))
    elif k == 'bed':
        w = item.get('w', 1.6); h = item.get('h', 2.0)
        bx, by = item['x'] + x1, item['y'] + y1
        out.append(f_rect(bx, by, w, h, rx=0.04))
        # pillows
        if item.get('head', 'top') == 'top':
            out.append(f_rect(bx + 0.08, by + 0.08, w / 2 - 0.12, 0.45, rx=0.05))
            out.append(f_rect(bx + w / 2 + 0.04, by + 0.08, w / 2 - 0.12, 0.45, rx=0.05))
            out.append(f_line(bx, by + 0.7, bx + w, by + 0.7))
        elif item['head'] == 'left':
            out.append(f_rect(bx + 0.08, by + 0.08, 0.45, h / 2 - 0.12, rx=0.05))
            out.append(f_rect(bx + 0.08, by + h / 2 + 0.04, 0.45, h / 2 - 0.12, rx=0.05))
            out.append(f_line(bx + 0.7, by, bx + 0.7, by + h))
        elif item['head'] == 'right':
            out.append(f_rect(bx + w - 0.53, by + 0.08, 0.45, h / 2 - 0.12, rx=0.05))
            out.append(f_rect(bx + w - 0.53, by + h / 2 + 0.04, 0.45, h / 2 - 0.12, rx=0.05))
            out.append(f_line(bx + w - 0.7, by, bx + w - 0.7, by + h))
        elif item['head'] == 'bottom':
            out.append(f_rect(bx + 0.08, by + h - 0.53, w / 2 - 0.12, 0.45, rx=0.05))
            out.append(f_rect(bx + w / 2 + 0.04, by + h - 0.53, w / 2 - 0.12, 0.45, rx=0.05))
            out.append(f_line(bx, by + h - 0.7, bx + w, by + h - 0.7))
    elif k == 'wardrobe':
        bx, by = item['x'] + x1, item['y'] + y1
        w, h = item.get('w', 1.8), item.get('h', 0.6)
        out.append(f_rect(bx, by, w, h))
        out.append(f_line(bx, by, bx + w, by + h, 'fn-thin'))
        out.append(f_line(bx, by + h, bx + w, by, 'fn-thin'))
    elif k == 'counter':
        bx, by = item['x'] + x1, item['y'] + y1
        w, h = item.get('w', 3.0), item.get('h', 0.6)
        out.append(f_rect(bx, by, w, h))
        # sink + hob
        if w >= h:
            out.append(f_rect(bx + 0.2, by + 0.1, 0.5, h - 0.2, 'fn-thin', rx=0.05))
            out.append(f_circle(bx + w - 0.45, by + h / 2, 0.12, 'fn-thin'))
            out.append(f_circle(bx + w - 0.85, by + h / 2, 0.12, 'fn-thin'))
        else:
            out.append(f_rect(bx + 0.1, by + 0.2, w - 0.2, 0.5, 'fn-thin', rx=0.05))
            out.append(f_circle(bx + w / 2, by + h - 0.45, 0.12, 'fn-thin'))
            out.append(f_circle(bx + w / 2, by + h - 0.85, 0.12, 'fn-thin'))
    elif k == 'fridge':
        out.append(f_rect(item['x'] + x1, item['y'] + y1, 0.7, 0.7))
    elif k == 'wc':
        bx, by = item['x'] + x1, item['y'] + y1
        rot = item.get('rot', 0)
        if rot in (0, 180):
            out.append(f_rect(bx, by, 0.4, 0.2, rx=0.03))
            out.append(f'<ellipse cx="{px(bx+0.2)}" cy="{px(by+0.45)}" rx="{round(0.18*S,2)}" ry="{round(0.25*S,2)}" class="fn"/>')
        else:
            out.append(f_rect(bx, by, 0.2, 0.4, rx=0.03))
            out.append(f'<ellipse cx="{px(bx+0.45)}" cy="{px(by+0.2)}" rx="{round(0.25*S,2)}" ry="{round(0.18*S,2)}" class="fn"/>')
    elif k == 'shower':
        bx, by = item['x'] + x1, item['y'] + y1
        w, h = item.get('w', 0.9), item.get('h', 0.9)
        out.append(f_rect(bx, by, w, h))
        out.append(f_circle(bx + w / 2, by + h / 2, 0.06, 'fn-thin'))
        out.append(f_line(bx, by, bx + w, by + h, 'fn-thin'))
    elif k == 'bathtub':
        bx, by = item['x'] + x1, item['y'] + y1
        w, h = item.get('w', 1.6), item.get('h', 0.7)
        out.append(f_rect(bx, by, w, h, rx=0.1))
        out.append(f_rect(bx + 0.1, by + 0.1, w - 0.2, h - 0.2, 'fn-thin', rx=0.15))
    elif k == 'sink':
        bx, by = item['x'] + x1, item['y'] + y1
        w = item.get('w', 0.6); h = item.get('h', 0.45)
        out.append(f_rect(bx, by, w, h, rx=0.03))
        out.append(f'<ellipse cx="{px(bx+w/2)}" cy="{px(by+h/2)}" rx="{round(0.18*S,2)}" ry="{round(0.13*S,2)}" class="fn-thin"/>')
    elif k == 'washer':
        bx, by = item['x'] + x1, item['y'] + y1
        out.append(f_rect(bx, by, 0.6, 0.6))
        out.append(f_circle(bx + 0.3, by + 0.3, 0.2, 'fn-thin'))
    elif k == 'plant':
        bx, by = item['x'] + x1, item['y'] + y1
        out.append(f_circle(bx, by, item.get('r', 0.45), 'fn-plant'))
        out.append(f_circle(bx, by, item.get('r', 0.45) * 0.55, 'fn-thin'))
    elif k == 'text':
        out.append(f'<text x="{px(item["x"]+x1)}" y="{px(item["y"]+y1)}" class="fn-text">{esc(item["text"])}</text>')
    return out

# ---------- stairs ----------

def stair_straight(room):
    """Straight flight along the left half rising from the front (bottom, large y) to the rear landing;
    gallery on the right half returns to the front for the next flight."""
    x1, y1, x2, y2 = room_rect(room)
    out = []
    w, h = x2 - x1, y2 - y1
    fw = room.get('flight', 1.1)
    landing = room.get('landing', 1.1)
    n = room.get('treads', 16)
    run = h - landing
    t = run / n
    # treads
    for i in range(n + 1):
        yy = y2 - i * t
        out.append(f_line(x1, yy, x1 + fw, yy, 'st'))
    # separation line flight / gallery
    out.append(f_line(x1 + fw, y1 + landing, x1 + fw, y2, 'st-core'))
    # landing edge
    out.append(f_line(x1, y1 + landing, x2, y1 + landing, 'st'))
    # gallery dashed guide
    out.append(f'<line x1="{px(x1+fw+(w-fw)/2)}" y1="{px(y1+landing)}" x2="{px(x1+fw+(w-fw)/2)}" y2="{px(y2-0.2)}" class="arc"/>')
    # arrow up along the flight
    ax = x1 + fw / 2
    out.append(f'<path d="M{px(ax)} {px(y2-0.25)} L{px(ax)} {px(y1+landing+0.15)}" class="st-arrow"/>')
    out.append(f_circle(ax, y2 - 0.25, 0.07, 'st-dot'))
    out.append(f'<polygon points="{px(ax-0.12)},{px(y1+landing+0.4)} {px(ax+0.12)},{px(y1+landing+0.4)} {px(ax)},{px(y1+landing+0.1)}" class="st-head"/>')
    return out

def stair(room):
    """U-shaped two-flight stair with central wall/void. Long axis follows the longer side."""
    if room.get('straight'):
        return stair_straight(room)
    x1, y1, x2, y2 = room_rect(room)
    out = []
    w, h = x2 - x1, y2 - y1
    vertical = h >= w
    n_treads = room.get('treads', 8)
    if vertical:
        fw = (w - 0.1) / 2       # flight width
        landing = room.get('landing', 1.0)
        run = h - landing - 0.9  # departure landing 0.9
        t = run / n_treads
        # left flight (going up towards top), right flight
        for i in range(n_treads + 1):
            yy = y1 + landing + i * t
            out.append(f_line(x1, yy, x1 + fw, yy, 'st'))
            out.append(f_line(x2 - fw, yy, x2, yy, 'st'))
        out.append(f_rect(x1 + fw, y1 + landing, 0.1, run, 'st-core'))
        # arrow: up along left flight then across landing and down the right (we mark "up")
        ax = x1 + fw / 2
        out.append(f'<path d="M{px(ax)} {px(y2-0.3)} L{px(ax)} {px(y1+landing/2)} L{px(x2-fw/2)} {px(y1+landing/2)} L{px(x2-fw/2)} {px(y2-0.3)}" class="st-arrow"/>')
        out.append(f_circle(ax, y2 - 0.3, 0.07, 'st-dot'))
        out.append(f'<polygon points="{px(x2-fw/2-0.12)},{px(y2-0.55)} {px(x2-fw/2+0.12)},{px(y2-0.55)} {px(x2-fw/2)},{px(y2-0.25)}" class="st-head"/>')
    else:
        fh = (h - 0.1) / 2
        landing = room.get('landing', 1.0)
        run = w - landing - 0.9
        t = run / n_treads
        for i in range(n_treads + 1):
            xx = x1 + 0.9 + i * t
            out.append(f_line(xx, y1, xx, y1 + fh, 'st'))
            out.append(f_line(xx, y2 - fh, xx, y2, 'st'))
        out.append(f_rect(x1 + 0.9, y1 + fh, run, 0.1, 'st-core'))
        ay = y2 - fh / 2
        out.append(f'<path d="M{px(x1+0.3)} {px(ay)} L{px(x2-landing/2)} {px(ay)} L{px(x2-landing/2)} {px(y1+fh/2)} L{px(x1+0.3)} {px(y1+fh/2)}" class="st-arrow"/>')
        out.append(f_circle(x1 + 0.3, ay, 0.07, 'st-dot'))
        out.append(f'<polygon points="{px(x1+0.55)},{px(y1+fh/2-0.12)} {px(x1+0.55)},{px(y1+fh/2+0.12)} {px(x1+0.25)},{px(y1+fh/2)}" class="st-head"/>')
    return out

# ---------- doors & windows ----------

def door(d):
    """d: x,y = hinge point on the wall centreline; w = leaf width; dir 'h' (wall horizontal) or 'v';
    swing: for 'h' walls 'down-right','down-left','up-right','up-left'; for 'v' 'right-down','right-up','left-down','left-up'."""
    x, y, w = d['x'], d['y'], d.get('w', 0.8)
    sw = d.get('swing', 'down-right')
    out = []
    if d.get('dir', 'h') == 'h':
        # opening gap in wall
        gx = x if 'right' in sw else x - w
        out.append(f'<rect x="{px(gx)}" y="{px(y-0.14)}" width="{round(w*S,2)}" height="{round(0.28*S,2)}" class="gap"/>')
        sx = 1 if 'right' in sw else -1
        sy = 1 if 'down' in sw else -1
        # leaf: from hinge perpendicular to wall
        out.append(f_line(x, y, x, y + sy * w, 'leaf'))
        # arc from leaf tip to wall point
        large = 0
        sweep = 1 if (sx * sy) > 0 else 0
        out.append(f'<path d="M{px(x)} {px(y+sy*w)} A{round(w*S,2)} {round(w*S,2)} 0 {large} {sweep} {px(x+sx*w)} {px(y)}" class="arc"/>')
    else:
        gy = y if 'down' in sw else y - w
        out.append(f'<rect x="{px(x-0.14)}" y="{px(gy)}" width="{round(0.28*S,2)}" height="{round(w*S,2)}" class="gap"/>')
        sx = 1 if 'right' in sw else -1
        sy = 1 if 'down' in sw else -1
        out.append(f_line(x, y, x + sx * w, y, 'leaf'))
        sweep = 0 if (sx * sy) > 0 else 1
        out.append(f'<path d="M{px(x+sx*w)} {px(y)} A{round(w*S,2)} {round(w*S,2)} 0 0 {sweep} {px(x)} {px(y+sy*w)}" class="arc"/>')
    return out

def opening(o):
    """A plain opening without leaf (arch / passage)."""
    x, y, w = o['x'], o['y'], o['w']
    if o.get('dir', 'h') == 'h':
        return [f'<rect x="{px(x)}" y="{px(y-0.14)}" width="{round(w*S,2)}" height="{round(0.28*S,2)}" class="gap"/>',
                f_line(x, y - 0.14, x, y + 0.14, 'wall-thin'), f_line(x + w, y - 0.14, x + w, y + 0.14, 'wall-thin')]
    return [f'<rect x="{px(x-0.14)}" y="{px(y)}" width="{round(0.28*S,2)}" height="{round(w*S,2)}" class="gap"/>',
            f_line(x - 0.14, y, x + 0.14, y, 'wall-thin'), f_line(x - 0.14, y + w, x + 0.14, y + w, 'wall-thin')]

def window(wd):
    x, y, w = wd['x'], wd['y'], wd['w']
    out = []
    if wd.get('dir', 'h') == 'h':
        out.append(f'<rect x="{px(x)}" y="{px(y-0.14)}" width="{round(w*S,2)}" height="{round(0.28*S,2)}" class="gap"/>')
        for off in (-0.08, 0, 0.08):
            out.append(f_line(x, y + off, x + w, y + off, 'win'))
    else:
        out.append(f'<rect x="{px(x-0.14)}" y="{px(y)}" width="{round(0.28*S,2)}" height="{round(w*S,2)}" class="gap"/>')
        for off in (-0.08, 0, 0.08):
            out.append(f_line(x + off, y, x + off, y + w, 'win'))
    return out

# ---------- dimensions ----------

def dim_h(x1, x2, y, text, cls='dim'):
    out = [f_line(x1, y, x2, y, cls), f_line(x1, y - 0.12, x1, y + 0.12, cls), f_line(x2, y - 0.12, x2, y + 0.12, cls)]
    out.append(f'<text x="{px((x1+x2)/2)}" y="{px(y)-5}" class="dim-t" text-anchor="middle">{esc(text)}</text>')
    return out

def dim_v(y1, y2, x, text, cls='dim'):
    out = [f_line(x, y1, x, y2, cls), f_line(x - 0.12, y1, x + 0.12, y1, cls), f_line(x - 0.12, y2, x + 0.12, y2, cls)]
    out.append(f'<text x="{px(x)-5}" y="{px((y1+y2)/2)}" class="dim-t" text-anchor="middle" transform="rotate(-90 {px(x)-5} {px((y1+y2)/2)})">{esc(text)}</text>')
    return out

def fmt(v):
    return f'{v:.2f}'.rstrip('0').rstrip('.')

# ---------- main ----------

def render(plan, show_furniture=True, show_dims=True, id_prefix='p'):
    P = plan['plot']
    W, H = P['w'], P['h']
    total_w = W * S + 2 * M
    ext_b = max([r['y'] + r['h'] for r in plan['rooms'] if r['type'] == 'balcony'] + [H])
    total_h = ext_b * S + 2 * M + 10
    out = []
    out.append(f'<svg viewBox="0 0 {round(total_w)} {round(total_h)}" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="{id_prefix}-title" class="plan">')
    out.append(f'<title id="{id_prefix}-title">{esc(plan.get("title", "Plan"))}</title>')
    # plot ground
    out.append(f'<rect x="{px(0)}" y="{px(0)}" width="{round(W*S,2)}" height="{round(H*S,2)}" class="plot"/>')
    rooms = plan['rooms']
    # room fills
    for r in rooms:
        x1, y1, x2, y2 = room_rect(r)
        cls = 'room room-' + r['type']
        fill = FILL.get(r['type'], 'var(--pl-hall)')
        extra = ''
        if r['type'] == 'patio':
            extra = f' fill="url(#{id_prefix}-hatch)"'
            out.append(f'<rect x="{px(x1)}" y="{px(y1)}" width="{round((x2-x1)*S,2)}" height="{round((y2-y1)*S,2)}" class="{cls}" style="fill:{fill}"/>')
        out.append(f'<rect x="{px(x1)}" y="{px(y1)}" width="{round((x2-x1)*S,2)}" height="{round((y2-y1)*S,2)}" class="{cls}" style="fill:{fill if not extra else "none"}"{extra}/>')
    # walls: draw each room box outline as thick line; outer boundary thicker
    for r in rooms:
        if r['type'] in ('balcony', 'void'):
            continue
        out.append(f'<rect x="{px(r["x"])}" y="{px(r["y"])}" width="{round(r["w"]*S,2)}" height="{round(r["h"]*S,2)}" class="wall"/>')
    # balcony outline (thin, over the street)
    for r in rooms:
        if r['type'] == 'balcony':
            out.append(f'<rect x="{px(r["x"])}" y="{px(r["y"])}" width="{round(r["w"]*S,2)}" height="{round(r["h"]*S,2)}" class="balc"/>')
    out.append(f'<rect x="{px(0)}" y="{px(0)}" width="{round(W*S,2)}" height="{round(H*S,2)}" class="wall-outer"/>')
    # openings
    for o in plan.get('openings', []):
        out += opening(o)
    for wd in plan.get('windows', []):
        out += window(wd)
    for d in plan.get('doors', []):
        out += door(d)
    # stairs and furniture
    for r in rooms:
        if r['type'] == 'stair':
            out += stair(r)
        if show_furniture:
            for it in r.get('furniture', []):
                out += furniture(r, it)
    # labels
    for r in rooms:
        if r['type'] in ('void',):
            continue
        x1, y1, x2, y2 = room_rect(r)
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        lx = r.get('lx', cx); ly = r.get('ly', cy)
        area = net_area(r)
        name = r['name']
        small = (x2 - x1) < 1.6 or (y2 - y1) < 1.3
        cls = 'lbl-s' if small else 'lbl'
        if r.get('label_area', True) and not (r['type'] in ('balcony',) and small):
            out.append(f'<text x="{px(lx)}" y="{px(ly)-4}" class="{cls}" text-anchor="middle">{esc(name)}</text>')
            out.append(f'<text x="{px(lx)}" y="{px(ly)+11}" class="{cls}-a" text-anchor="middle">{fmt(round(area,1))} m²</text>')
        else:
            out.append(f'<text x="{px(lx)}" y="{px(ly)+4}" class="{cls}" text-anchor="middle">{esc(name)}</text>')
    for lb in plan.get('labels', []):
        out.append(f'<text x="{px(lb["x"])}" y="{px(lb["y"])}" class="{lb.get("cls","note")}" text-anchor="{lb.get("anchor","middle")}">{esc(lb["text"])}</text>')
    # dimensions
    if show_dims:
        out += dim_h(0, W, -0.55, f'{fmt(W)} m')
        out += dim_v(0, H, -0.55, f'{fmt(H)} m')
        for d in plan.get('dims', []):
            if d['dir'] == 'h':
                out += dim_h(d['from'], d['to'], d['at'], d.get('text', fmt(d['to']-d['from']) + ' m'), 'dim2')
            else:
                out += dim_v(d['from'], d['to'], d['at'], d.get('text', fmt(d['to']-d['from']) + ' m'), 'dim2')
    # street label & north
    street = P.get('street', 'bottom')
    ext = max([r['y'] + r['h'] for r in rooms if r['type'] == 'balcony'] + [H])
    if street == 'bottom':
        out.append(f'<text x="{px(W/2)}" y="{px(ext)+34}" class="street" text-anchor="middle">{esc(P.get("street_label", "RUE / STREET"))}</text>')
    else:
        out.append(f'<text x="{px(W/2)}" y="{px(0)-40}" class="street" text-anchor="middle">{esc(P.get("street_label", "RUE / STREET"))}</text>')
    # party wall labels
    for side in P.get('party', ['left', 'right', 'top']):
        if side == 'left':
            out.append(f'<text x="{px(0)+8}" y="{px(H/2)}" class="party" transform="rotate(-90 {px(0)+8} {px(H/2)})" text-anchor="middle">mitoyen</text>')
        if side == 'right':
            out.append(f'<text x="{px(W)-6}" y="{px(H/2)}" class="party" transform="rotate(90 {px(W)-6} {px(H/2)})" text-anchor="middle">mitoyen</text>')
        if side == 'top':
            out.append(f'<text x="{px(W/2)}" y="{px(0)+13}" class="party" text-anchor="middle">mitoyen</text>')
    # hatch pattern defs
    out.insert(1, f'<defs><pattern id="{id_prefix}-hatch" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="8" class="hatch"/></pattern></defs>')
    out.append('</svg>')
    return '\n'.join(out)

def summary(plan):
    rows = []
    tot = 0
    for r in plan['rooms']:
        if r['type'] in ('void', 'stair', 'patio', 'balcony', 'terrace') or not r.get('count', True):
            continue
        a = net_area(r)
        tot += a
        rows.append((r['name'], r['type'], round(a, 1)))
    return rows, round(tot, 1)

def check(plan):
    """Geometry checks: rooms inside plot, no overlaps, tiling coverage."""
    P = plan['plot']; W, H = P['w'], P['h']
    issues = []
    rs = [r for r in plan['rooms'] if r['type'] != 'balcony']
    cover = 0
    for r in rs:
        if r['x'] < -1e-6 or r['y'] < -1e-6 or r['x'] + r['w'] > W + 1e-6 or r['y'] + r['h'] > H + 1e-6:
            issues.append(f"{r['id']} outside plot")
        cover += r['w'] * r['h']
    for i in range(len(rs)):
        for j in range(i + 1, len(rs)):
            a, b = rs[i], rs[j]
            ox = min(a['x'] + a['w'], b['x'] + b['w']) - max(a['x'], b['x'])
            oy = min(a['y'] + a['h'], b['y'] + b['h']) - max(a['y'], b['y'])
            if ox > 1e-6 and oy > 1e-6:
                issues.append(f"{a['id']} overlaps {b['id']} by {ox:.2f}x{oy:.2f}")
    if abs(cover - W * H) > 0.05:
        issues.append(f"coverage {cover:.2f} != plot {W*H:.2f} (gap or double count)")
    return issues

if __name__ == '__main__':
    plan = json.load(open(sys.argv[1]))
    mode = sys.argv[2] if len(sys.argv) > 2 else 'svg'
    if mode == 'check':
        print(json.dumps({'issues': check(plan), 'summary': summary(plan)}, ensure_ascii=False, indent=1))
    else:
        print(render(plan, id_prefix=sys.argv[3] if len(sys.argv) > 3 else 'p'))
