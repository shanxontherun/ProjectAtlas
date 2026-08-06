# Atlas Technical Debt Register

Known technical debt items, each with a recommended fix and the
locations affected. Entries are not automatically resolved.

---

## TD-001 — `research_products.asin` column drift

### Status

Open.

### Summary

Migration `sql/008_update_research_products_status.sql` rebuilt the
`research_products` table and dropped the `asin` column, but the
repository and worker layers still read and write `asin` against that
table. Any code path touching `research_products.asin` fails at
runtime with `OperationalError: table research_products has no column
named asin` (or `KeyError: 'asin'`).

### Recommended fix

Restore the column with a new forward-only migration (e.g.
`sql/013_add_research_products_asin.sql`):

```sql
PRAGMA foreign_keys = ON;

ALTER TABLE research_products
ADD COLUMN asin TEXT;

CREATE INDEX IF NOT EXISTS idx_research_products_asin
    ON research_products (asin);
```

Then consolidate the two divergent `insert_research_product()`
implementations:

- `services/database.py` — schema-matching insert (no `asin`).
- `services/research_products.py` — insert that expects `asin`.

Prefer keeping the repository in `services/research_products.py` and
deleting the duplicate in `services/database.py`, so all callers share
one implementation that matches the actual table schema.

### Locations affected

| Location | Effect |
|---|---|
| `sql/008_update_research_products_status.sql` | Root cause: rebuilt table without `asin`. |
| `services/research_products.py::insert_research_product()` | `INSERT` includes `asin` column -> runtime failure. |
| `services/research_products.py::fetch_product_by_asin()` | `SELECT ... WHERE asin=?` -> runtime failure. |
| `services/image_service.py::fetch_products_pending_images()` | `SELECT asin` -> runtime failure. |
| `services/image_downloader.py::download_product_image()` | Reads `product["asin"]` (lines 60, 147) -> `KeyError`. |
| `workers/discovery_worker.py` | Calls `fetch_product_by_asin()` and `insert_research_product(asin=...)` (lines 80, 92). |
| `workers/image_worker.py` | Logs `product["asin"]` from `research_products` rows (line 77). |
| `services/ai_prompts.py::build_product_prompt()` | Reads `product["asin"]` (line 44); lower severity because this prompt builder is not used by the AI worker pipeline. |

### Not affected

- `sql/005_create_product_registry.sql` — `product_registry.asin` still exists.
- `services/database.py::create_product_registry_entry()` — writes `product_registry.asin`.
- `models/amazon_product.py` — in-memory parser model, not a DB row.
- `tests/test_parser.py` — reads `product.asin` from the parser model.
