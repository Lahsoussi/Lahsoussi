# Floor-plan JSON format (read fully before designing)

All lengths in metres, two decimals max, snapped to a 0.1 m grid. Origin = top-left of the plot.
x grows to the right, y grows DOWNWARD. `plot.street` says which edge is the street:
with `"street": "bottom"` the street is at y = plot.h, so the façade rooms have the largest y.
The other three edges are party walls (mitoyen): NO windows may open on them.

Room boxes are WALL-CENTRELINE rectangles and must TILE THE PLOT EXACTLY (sum of w*h = plot area,
no overlaps, no gaps). The renderer insets each box by 0.10 m to draw the room and reports
net area = (w-0.2)*(h-0.2). Wall thickness is therefore modelled as 0.20 m everywhere; that is
close enough to 0.25 outer / 0.10-0.15 inner for sales plans.

A `balcony` room is the only box allowed OUTSIDE the plot (it projects over the street, y >= plot.h
when street is bottom). It is excluded from the tiling check.

```json
{
  "title": "Étage courant (1er et 2e)",
  "plot": {"w": 10, "h": 10, "street": "bottom", "street_label": "RUE", "party": ["left","right","top"]},
  "rooms": [
    {"id": "stair", "name": "Escalier", "type": "stair", "x": 0, "y": 5.8, "w": 2.4, "h": 4.2, "treads": 8, "landing": 1.0},
    {"id": "salon", "name": "Salon marocain", "type": "salon", "x": 2.4, "y": 5.8, "w": 4.3, "h": 4.2,
     "furniture": [{"kind": "sedari", "sides": ["left","bottom","right"]}]},
    {"id": "balc", "name": "Balcon", "type": "balcony", "x": 2.4, "y": 10, "w": 7.6, "h": 1.0}
  ],
  "windows": [{"x": 3.0, "y": 10, "w": 3.0, "dir": "h"}],
  "openings": [{"x": 3.6, "y": 4.6, "w": 2.0, "dir": "h"}],
  "doors": [{"x": 1.0, "y": 5.8, "w": 0.9, "dir": "h", "swing": "up-right"}],
  "dims": [{"dir": "h", "from": 0, "to": 2.4, "at": 10.35}],
  "labels": [{"x": 5, "y": 9.7, "text": "note", "anchor": "middle"}]
}
```

## Room `type` values (drives colour + legend)
`salon` (salon marocain), `sejour` (European living / dining), `bedroom`, `kitchen`, `bath` (salle de bain),
`wc`, `hall` (hall / dégagement / entrée), `stair` (shared staircase cage), `patio` (open-air courtyard / puits de lumière,
no roof), `balcony`, `terrace`, `storage` (débarras / placard / buanderie), `tech` (gaine / local compteurs).

Optional per room: `"lx"`, `"ly"` (label position), `"label_area": false` (name only), `"count": false`
(exclude from the habitable-area total).

## Furniture kinds (coordinates are relative to the room's INNER top-left corner, i.e. after the 0.10 inset)
- `{"kind":"sedari","sides":["top","left","right"],"depth":0.75}` U/L banquettes along the named inner walls + low table
- `{"kind":"sofa","x":..,"y":..,"w":2.2,"h":0.9}`
- `{"kind":"table","x":..,"y":..,"w":1.6,"h":0.9,"chairs":6}`
- `{"kind":"bed","x":..,"y":..,"w":1.6,"h":2.0,"head":"top|bottom|left|right"}` (w is across the bed when head is top/bottom; for head left/right give w = length, h = width)
- `{"kind":"wardrobe","x":..,"y":..,"w":1.8,"h":0.6}`
- `{"kind":"counter","x":..,"y":..,"w":3.0,"h":0.6}` (kitchen run; if h > w it is drawn vertical)
- `{"kind":"fridge","x":..,"y":..}` 0.7 x 0.7
- `{"kind":"wc","x":..,"y":..,"rot":0|90}` (0 = tank against the top wall)
- `{"kind":"shower","x":..,"y":..,"w":0.9,"h":0.9}`, `{"kind":"bathtub","x":..,"y":..,"w":1.6,"h":0.7}`
- `{"kind":"sink","x":..,"y":..,"w":0.6,"h":0.45}`, `{"kind":"washer","x":..,"y":..}` 0.6 x 0.6
- `{"kind":"plant","x":..,"y":..,"r":0.45}`, `{"kind":"text","x":..,"y":..,"text":"..."}`

## Doors
`x,y` = hinge point ON the wall centreline. `dir` = orientation of the wall ("h" horizontal wall, "v" vertical wall).
`swing` for a horizontal wall: `down-right`, `down-left`, `up-right`, `up-left` (first word = side of the wall the
leaf swings into, second = direction from the hinge along the wall). For a vertical wall: `right-down`, `right-up`,
`left-down`, `left-up`. Interior doors 0.8 m, bathroom/WC 0.7 m, apartment entrance 0.9-1.0 m, street door 1.2 m.
Use `openings` (no leaf) for arches and wide passages, e.g. salon to séjour.

## Windows
`x,y` = start of the window along the wall centreline, `w` its width, `dir` the wall orientation. Windows only on the
street façade or onto a `patio`/courtyard box. Give every habitable room (salon, séjour, bedroom, kitchen) at least
one window of >= 1/8 of its floor area (glass area) or 1.0 m² minimum; bathrooms and WC need a window on a patio/courette
or a ventilation duct (`tech` box) — say which.

## Stairs
Shared cage, U-shaped two-flight stair, minimum clear width 1.00 m per flight for a 3-dwelling building (ideally 1.10),
floor-to-floor 3.00 m (3.20 m at ground floor if you choose) → 17-18 risers of 16.7-17.6 cm, treads 27-28 cm.
A comfortable cage is 2.30-2.50 m wide x 4.20-4.60 m long including the arrival landing. Give `treads` = risers per
flight (8 or 9) and `landing` = intermediate landing depth. The stair continues to the roof terrace.

## Deliverables per design
1. `typical.json` — 1st and 2nd floor apartment (identical).
2. `ground.json` — ground floor: same apartment adapted to the street entrance and stair arrival (the shared entrance
   hall / corridor eats into it; show meter cupboard `tech`; ground floor may skip the balcony and instead show a
   private terrace/cour if you have one).
3. `roof.json` — roof terrace: stair bulkhead (`stair` box), three private laundry rooms or one shared buanderie
   (`storage`), water tanks / solar heaters zone (`tech`), rest as `terrace`.
4. `rationale.md` — 250-500 words: concept, zoning, light/ventilation strategy, why it sells, known compromises.

Validate: `python3 /tmp/claude-0/-home-user-Lahsoussi/8fc2e335-fdba-5748-aa30-2c85f35f604c/scratchpad/planrender.py typical.json check`
must print `"issues": []`. Render to look at it:
`python3 .../planrender.py typical.json svg > typical.svg`, wrap in the preview CSS from `.../preview.html`
(copy its `<style>` block, append the svg) and screenshot with
`cd <scratchpad> && node shot.mjs <relative html> <png> 800`, then Read the png and fix what looks wrong.
