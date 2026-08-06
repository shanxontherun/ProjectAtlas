# Creative Engine — Template Format

Templates are data-driven JSON files discovered by the registry from
the `creative/templates/` directory. Each template file declares a
`meta.id` that uniquely identifies it.

## Rules

- One template per file; the id is declared in `meta.id`, not derived
  from the file name.
- Duplicate ids and files without `meta.id` are rejected.
- Templates must contain at least one zone.
- Every zone must stay inside the canvas (platform overrides too).
- Zone names must be unique.
- Templates reference a brand by id instead of hardcoding styling.

## Structure

```
{
  "meta": {
    "id": "home_01",            required, unique
    "version": "1.0.0",         default "1.0.0"
    "platforms": [],            default []
    "description": ""
  },
  "canvas": {
    "width": 1000,              required, > 0
    "height": 1500,             required, > 0
    "background": "#FFFFFF",    hex color, default "#FFFFFF"
    "platform_overrides": {}    optional, free-form
  },
  "brand": "atlas",             optional brand reference
  "data_map": {
    "headline": "pinterest_title"   slot -> content/product field
  },
  "zones": [ ... ],
  "output": {
    "filename_pattern": "{template_id}_{variant}",
    "format": "png",            "png" | "jpeg" | "webp"
    "quality": 95,              1-100, default 95
    "variant": "default"
  }
}
```

## Zones

A zone is a composable layer with a type, bounds, and optional style.

Supported zone types:

- `image`
- `text`
- `rect`
- `badge`
- `rating`
- `price`
- `logo`
- `overlay`
- `gradient`
- `watermark`

Zone object:

```
{
  "name": "headline",              required, unique
  "type": "text",                  required, supported type
  "bounds": {
    "x": 80,                       >= 0
    "y": 80,                       >= 0
    "width": 840,                  > 0
    "height": 160                  > 0
  },
  "style": {                       optional, renderer-specific
    "font_role": "title",
    "color_role": "text"
  },
  "platform_overrides": {},        optional, per-platform bounds
  "visible_if": null               optional, visibility condition
}
```

`style` is free-form data interpreted by renderers in Phase B.
`platform_overrides` maps a platform name to an alternate bounds
object, e.g. `{"instagram": {"x": 40, "y": 40, "width": 400, "height": 100}}`.

## Validation

Templates are validated at load time. Structure and constraint
failures raise `ValidationError` with per-field messages, for example:

```
zones.0.type: Input should be 'image', 'text', 'rect', 'badge', ...
canvas.background: Value error, background must be a hex color ...
Value error, Zone 'a' bounds x=90 y=90 width=50 height=50 exceed canvas
```

Missing/unidentifiable templates raise `TemplateError`. A template
that references a missing brand raises `BrandError`.

## Example

See `creative/templates/pinterest/home_01.json` for a complete
template with headline, product image, rating badge, call to action
and watermark zones.
