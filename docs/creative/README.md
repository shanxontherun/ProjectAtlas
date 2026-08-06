# Creative Engine — Overview

The Creative Engine generates platform-ready creative assets for
Atlas products. This document covers the Phase A foundation (the
data-driven template system, brand profiles, and the registry) and
the Phase B rendering pipeline built on top of it.

## Goals

- Templates and brands are data, not code.
- Templates reference brands instead of hardcoding styling.
- Invalid templates or brands fail immediately with clear errors.
- The engine is platform-independent; platforms are later added as
  profiles without touching templates or code.
- Rendering is stateless and deterministic for a given set of inputs.

## Directory Layout

```
creative/
  __init__.py
  exceptions.py      # Domain exception hierarchy
  _io.py             # Internal JSON read + error formatting helpers
  models.py          # Pydantic contracts (Template, Zone, BrandProfile)
  brands.py          # BrandProfileLoader
  registry.py        # TemplateRegistry
  typography.py      # Phase B: text layout (wrap, align, auto-fit)
  composer.py        # Phase B: raster composition (canvas, images, shapes)
  rendering.py       # Phase B: RenderingEngine (orchestration + output)
  templates/
    pinterest/
      home_01.json   # Basic product pin template
      home_02.json   # Full-featured pin (logo, subtitle, price)
  assets/
    brands/
      atlas.json     # Example brand profile
    fonts/           # Bundled fonts (Phase B)
    logos/
    palettes/
    overlays/
  generated/         # Rendered image output (created on demand)
```

## Public API

The registry is the primary entry point for loading templates:

```python
from creative.registry import TemplateRegistry

registry = TemplateRegistry()

templates = registry.discover()      # list of template ids
template = registry.load("home_01")  # validated Template + resolved brand
brand = registry.get_brand("atlas")  # validated BrandProfile
```

The rendering engine turns a template plus content into an image:

```python
from pathlib import Path
from creative.rendering import RenderingEngine

engine = RenderingEngine()

result = engine.render(
    "home_01",
    {
        "pinterest_title": "Modern kitchen knives set",
        "pinterest_description": "16 piece stainless steel set",
        "rating": 4.8,
        "price": "$49.99",
        "cta": "Shop now",
    },
    product_image=Path("creative/assets/test.jpg"),
)

print(result.path)  # creative/generated/home_01_default.png
```

## Error Handling

All Creative Engine errors inherit from `CreativeError`.

- `TemplateError` — template missing, unreadable, or unidentifiable.
- `BrandError` — brand missing, unreadable, or id/filename mismatch.
- `ValidationError` — template or brand found but violates its schema;
  carries a list of human-readable field errors in `.errors`.
- `RenderError` — a zone cannot be rendered (missing content, unknown
  font/color role, unloadable image) or the output cannot be written.

## Reference

- [Template Format](template-format.md)
- [Brand Format](brand-format.md)
- [Rendering](rendering.md)
