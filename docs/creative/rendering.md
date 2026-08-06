# Creative Engine — Rendering

The Rendering Engine (Phase B) turns a template, brand profile, AI
content, and a product image into a finished platform-ready image.

## Architecture

Rendering is split into three pure, stateless modules:

| Module | Responsibility | Draws text? |
| ------ | -------------- | ----------- |
| `composer.py` | Canvas, background, image placement, rects, overlays, gradients, stars | No |
| `typography.py` | Font resolution, wrapping, measurement, alignment, auto-fit | No |
| `rendering.py` | Orchestration, content binding, color/role resolution, output | Yes (via typography layout) |

This split keeps each concern independently testable:

- The **Composer** knows nothing about text or fonts.
- The **Typography Engine** only produces layouts (positions and
  sizes); it never touches an image.
- The **Rendering Engine** is the only place that calls `ImageDraw`
  to place text, because it owns the final draw surface.

## Pipeline

```
TemplateRegistry.load(id)
        │  (Template + resolved BrandProfile)
        ▼
content + product_image
        ▼
create_canvas(width, height, background)
        ▼
for each zone (in template order):
        │
        ├─ text/price/badge ──► typography.layout_text ──► draw text
        ├─ image             ──► composer.place_image (cover/contain/stretch)
        ├─ rating            ──► composer.draw_stars + typography for number
        ├─ logo              ──► composer.place_image (brand asset)
        ├─ watermark         ──► typography + brand watermark settings
        ├─ rect              ──► composer.draw_rect
        ├─ overlay           ──► composer.draw_overlay
        └─ gradient          ──► composer.draw_gradient
        ▼
save to output_dir / {filename_pattern}.{ext}
```

Zones render in template order, so later zones draw on top of earlier
ones. The template author controls stacking order.

## Content Binding

A zone's text/rating value comes from the `data_map`:

```json
{ "data_map": { "headline": "pinterest_title" } }
```

A zone named `headline` reads `content["pinterest_title"]`. Zones
without a `data_map` entry look up their own name. Image zones always
use the `product_image` argument.

## Zone Styles

Zones carry presentation values in `style`:

| Key | Applies to | Meaning |
| --- | ---------- | ------- |
| `font_role` | text zones | Brand font role (`title`, `body`, `badge`) |
| `color_role` | most zones | Brand palette role (`text`, `muted`, `primary`, `accent`) |
| `font_size` | text zones | Fixed size in px; omitted means auto-fit |
| `align` | text zones | `left`, `center`, `right` |
| `valign` | text zones | `top`, `middle`, `bottom` |
| `line_spacing` | text zones | Multiplier on measured line height |
| `fit` | image zones | `cover`, `contain`, `stretch` |
| `color` | any zone | Direct hex override of `color_role` |
| `text` | watermark | Direct watermark text override |
| `bottom_color` | gradient | Bottom hex of vertical gradient |
| `radius` | rect | Rounded corner radius |

## Fonts

`FontResolver` looks for a font file by stem (`Inter-Bold.ttf`,
`Inter-Regular.otf`) in `creative/assets/fonts/`, falling back to
Pillow's bundled default font. Font roles come from the brand profile
(`brand.fonts`), so switching brands changes typography without
touching the template.

## Determinism

Rendering is deterministic: the same template, content, product
image, and output settings always produce byte-identical files. The
smoke test in `tests/test_creative_rendering.py` asserts this with
SHA-256 comparisons.

## Output

Output follows `template.output`:

- `filename_pattern` — `{template_id}_{variant}` by default.
- `format` — `png`, `jpeg`, or `webp`.
- `quality` — JPEG/WebP quality (1-100).

Files are written to `creative/generated/` (or an `output_dir`
override). The engine writes image files only — no database, queue,
or metadata persistence.
