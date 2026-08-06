# Creative Engine — Brand Format

Brand profiles are data-driven JSON files that let one template render
under many brands without hardcoding styling. Profiles live in
`creative/assets/brands/`.

## Rules

- One profile per file, named `<brand_id>.json`.
- The declared `id` must match the file name.
- Every palette color must be a hex color (`#RRGGBB`).
- Font roles must map to non-empty font names.

## Structure

```
{
  "id": "atlas",                 required, matches file name
  "name": "Atlas Affiliate",     optional
  "palette": {
    "primary": "#C21F3A",        hex colors, optional
    "accent": "#F7B32B",
    "background": "#FFFFFF",
    "text": "#222222",
    "muted": "#666666"
  },
  "fonts": {
    "title": "Inter-Bold",       role -> font name, optional
    "body": "Inter-Regular",
    "badge": "Inter-SemiBold"
  },
  "logo": "logos/atlas.png",     optional asset path
  "watermark": {                 optional, free-form
    "text": "@atlas_pins",
    "position": "bottom-right"
  },
  "overlays": {                  optional, free-form
    "scrim_color": "#000000",
    "scrim_opacity": 0.35
  }
}
```

## Usage

Templates reference a brand by id:

```
"brand": "atlas"
```

When the registry loads a template that references a brand, it
resolves the brand profile and attaches it to
`Template.brand_profile`, so renderers never look up brand data
themselves.

## Validation

- Missing or unreadable profiles raise `BrandError`.
- A profile whose `id` does not match its file name raises
  `BrandError`.
- Schema or constraint violations (e.g. a non-hex palette color)
  raise `ValidationError` with per-field messages.

## Example

See `creative/assets/brands/atlas.json` for a complete profile.
