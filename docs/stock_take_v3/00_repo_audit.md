# Phase 0 — Repo Audit (VCL Stock Take V3)

**Date:** 2026-05-10
**Branch:** `claude/audit-stocktake-repo-gtBZ8`
**Scope:** Documentation-only audit of the existing repository. No DocTypes,
business logic, or stock records have been created or modified.

> **Naming note:** the project description refers to the app as
> `vcl_stocktake`, but the repository, Python package, app ID and module path
> are all `vcl_stock_control`. Throughout this document the existing app is
> referred to by its real id (`vcl_stock_control`); "Stock Take V3" is the new
> capability being layered on top. The discrepancy needs an explicit decision
> before Phase 1 (see §6 Risks).

---

## 1. Current App Structure

```
vcl_stock_control/                     <- repo root
├── ACCESS_GUIDE.md                    <- desk + URL routing reference
├── INK_CHEMICAL_ENTRY_PAGE.md         <- website-page reference
├── README.md                          <- short overview
├── VCL_STOCK_CONTROL_REFERENCE.md     <- full field-by-field spec (~28 KB)
├── pyproject.toml                     <- name=vcl_stock_control, py>=3.10
├── requirements.txt
├── setup.py                           <- packages discovered via setuptools
└── vcl_stock_control/                 <- Python/Frappe app package
    ├── __init__.py                    <- __version__ = "1.0.0"
    ├── hooks.py                       <- app metadata, fixtures, after_install
    ├── install.py                     <- seeds 7 default Stock Categories
    ├── modules.txt                    <- Masters / Transactions / Reports
    ├── stock_utils.py                 <- shared validation + UOM helpers
    ├── patches.txt                    <- empty
    ├── patches/                       <- empty package
    ├── api/
    │   └── stock_entry_api.py         <- 3 whitelisted endpoints
    ├── import_templates/              <- 9 CSV seed templates
    ├── masters/doctype/               <- 3 master DocTypes
    ├── transactions/doctype/          <- 6 submittable + 6 child DocTypes
    ├── reports/                       <- 5 script reports
    ├── public/{css,js}/               <- 1 CSS + 1 JS for the website page
    ├── templates/                     <- empty (only __init__.py)
    └── www/                           <- 1 website page (ink-chemical-entry)
```

- Frappe modules registered: **Masters**, **Transactions**, **Reports**.
- Required apps: `frappe`, `erpnext`. Target platform: Frappe / ERPNext v16.
- `hooks.py` exposes: `fixtures` (Stock Category where `is_active=1`),
  `after_install = vcl_stock_control.install.after_install`. No scheduler
  events, doc events, or class overrides are wired.
- `patches.txt` is empty — no historical schema migrations.
- No tests directory, no CI config, no Node/React tooling
  (`package.json`, `vite.config*`, `webpack.config*` all absent).

---

## 2. Existing DocTypes

### 2.1 Masters (module: Masters)

| DocType | Naming | Submittable | Notes |
|---|---|---|---|
| Stock Category | `field:stock_category_name` | No | Quick Entry. Flags `is_item_linked`, `is_manual_only`, `is_active`. Seeded with 7 records on install (Ink, Chemical, Raw Material, Finished Goods, Core, Spare, Fuel). |
| Stock Material Profile | `SMP-.YYYY.-.#####` | No | Manual material master for non-Item stock. Has UOM, dimensions, source, and reorder-level sections. Optional `linked_item` Link to ERPNext Item for future migration. |
| Stock UOM Conversion Rule | `hash` | No | Conversion rules at either Material Profile or Stock Category level (Select `conversion_for`). |

### 2.2 Transactions (module: Transactions)

All six parents are **submittable** (Draft → Submitted → Cancelled) and all
hold a child table named `items`. None of them write to ERPNext stock —
they are pure capture documents.

| Parent DocType | Series | Child Line DocType | Source linkage | Notable extras |
|---|---|---|---|---|
| Ink Chemical Stock Entry | `ICSE-.YYYY.-.#####` | Ink Chemical Stock Entry Line | ERPNext **Item** (`reqd=1`) | `department`, `location` (reqd), `supplier`, `batch_no`, `expiry_date` per line. |
| Raw Material Stock Entry | `RMSE-.YYYY.-.#####` | Raw Material Stock Entry Line | Stock Material Profile **or** `manual_description` | Per-line `colour`, `gsm`, `width_mm`, `length_mm`, `country`, `mill`, `secondary_qty/uom`. Header uses `warehouse_text`. |
| Finished Goods Stock Entry | `FGSE-.YYYY.-.#####` | Finished Goods Stock Entry Line | Profile or manual | Bundle/carton breakdown (`bundle_qty * pieces_per_bundle + carton_qty * pieces_per_carton → calculated_pieces`). Auto-fills `entry_qty` if blank. |
| Core Stock Entry | `CSE-.YYYY.-.#####` | Core Stock Entry Line | Profile or manual | Minimal line set. |
| Spare Stock Entry | `SSE-.YYYY.-.#####` | Spare Stock Entry Line | Profile or manual | Per-line `minimum_level` + computed `reorder_flag`. Header has `department`. |
| Fuel Stock Entry | `FSE-.YYYY.-.#####` | Fuel Stock Entry Line | `fuel_point` **or** profile **or** manual | Custom validator allows fuel_point as the source. |

Common line shape: `default_uom`, `entry_uom`, `entry_qty`,
`conversion_factor` (default 1), `qty_in_default_uom` (read_only),
`notes`. The invariant `qty_in_default_uom = entry_qty × conversion_factor`
is enforced server-side in `stock_utils.validate_stock_lines`.

Permissions across all six parents: System Manager (full + submit/cancel/amend),
Stock Manager (full + submit/cancel/amend, no delete), Stock User
(create/read/write only — no submit).

### 2.3 No other DocTypes

There are **no** Print Format, Web Form, Workspace, Dashboard, Dashboard
Chart, Number Card, Notification, Custom Field, Property Setter, Role,
Server Script, Client Script, Email Template, Workflow, or Document Naming
Rule definitions in this repo.

---

## 3. Pages, Reports, Print Formats, Public Assets, APIs

### 3.1 Reports (5 — all Script Reports, `is_standard: Yes`, module: Reports)

| Report | `ref_doctype` | Roles |
|---|---|---|
| Latest Stock Snapshot | Ink Chemical Stock Entry | System Manager / Stock Manager / Stock User |
| Stock History | Ink Chemical Stock Entry | same |
| Low Stock | Stock Material Profile | same |
| Category Summary | Stock Category | same |
| Stock Variance | Stock Category | same |

`Latest Stock Snapshot` unions all six stock-entry parents/children with
filters for posting_date / location / category, and de-duplicates per
material to surface the "latest" row (ordering by `p.posting_date DESC`,
which is approximate — see §6).

### 3.2 Web pages

- `vcl_stock_control/www/ink-chemical-entry.{py,html}` →
  `/ink-chemical-entry`. Uses `templates/web.html`. Login required
  (Guest is rejected). Renders a vanilla-JS table that posts to
  `vcl_stock_control.api.stock_entry_api.create_ink_chemical_stock_entry`.

### 3.3 Print formats

- **None.** No `.../print_format/` folder anywhere in the repo.

### 3.4 Public assets

- `public/css/ink_chemical_entry.css` (241 lines) — page-scoped styling.
- `public/js/ink_chemical_entry.js` (388 lines) — namespaced as `VCL.*`,
  vanilla JS (no framework). Handles add/remove/renumber rows, item search
  via `frappe.client.get_list`, UOM dropdown population, live conversion,
  and submit.
- These are **not** declared in `hooks.py` as `app_include_*` or
  `web_include_*`; the page-side `.html` is responsible for loading them
  (typical for `www/` pages). Worth re-verifying when V3 introduces a new
  page.

### 3.5 Whitelisted API (module: `vcl_stock_control.api.stock_entry_api`)

| Endpoint | Inputs | Behaviour |
|---|---|---|
| `get_ink_item_details(item_code)` | item code | Returns item_name, stock_uom, list of valid UOMs from `Item.uoms`. |
| `get_item_conversion_factor(item_code, from_uom, to_uom)` | three strings | Wraps `stock_utils._get_item_uom_conversion`; returns 0 if missing. |
| `create_ink_chemical_stock_entry(payload)` | JSON payload | Validates server-side, recomputes conversion factor, creates an `Ink Chemical Stock Entry`, optionally submits. Uses `ignore_permissions=False`. |

A separate whitelisted helper exists in `stock_utils.py`:
`fetch_conversion_factor(from_uom, to_uom, item, material_profile, stock_category)`.

### 3.6 CSV import templates

`vcl_stock_control/import_templates/` contains 9 numbered CSVs covering
each master and each transaction parent — useful as Phase-1 seed/reference
data.

---

## 4. Does a React Frontend Exist?

**No.** Confirmed by:

- No `package.json`, `tsconfig*.json`, `vite.config*`, `webpack.config*`,
  `.babelrc`, or `node_modules/` anywhere.
- No `.jsx` / `.tsx` files; the only JS is one vanilla file
  (`public/js/ink_chemical_entry.js`) that uses `frappe.call` and DOM APIs.
- No bundler outputs in `public/dist/` (folder doesn't exist).
- The single web page is a Jinja template extending `templates/web.html`.

If V3 introduces a React app, it will be the first React surface in the
repo and will need build tooling, asset wiring in `hooks.py`, and a new
mount point.

---

## 5. Recommended Implementation Approach for Stock Take V3

> **Caveat:** the canonical V3 spec lives in Notion
> (`https://www.notion.so/35c8e0265cd5807e8062e841f19d37be`) and was not
> reachable from the audit environment, so the recommendation below is
> based on the existing repo plus the constraints stated by the user
> (no Stock Reconciliation logic, no submission/modification of ERPNext
> stock records, no DocTypes yet). Any V3 detail in Notion that conflicts
> with this should override §5 and be tracked as a Phase-1 follow-up.

Recommended shape:

1. **Treat V3 as an additive layer, not a rewrite.** Keep the six existing
   stock-entry DocTypes and `stock_utils.py` exactly as they are. Build
   Stock Take V3 as a separate workflow that *consumes* qty data and
   produces count documents, without touching ERPNext's
   `Stock Reconciliation` / `Stock Ledger Entry`.

2. **New module `Stock Take V3`** under `vcl_stock_control/stock_take_v3/`
   with its own DocType subfolder. Adding a new module is cheaper and
   clearer than expanding `Transactions`, and gives V3 its own permissions
   surface and report namespace. Register it in `modules.txt` in Phase 1.

3. **Likely DocType set (to be confirmed in Phase 1, not created now):**
   - `Stock Take Session` (submittable) — a count event with date,
     location/department, status, and roles (counter / supervisor).
   - `Stock Take Count Line` (child) — `material_profile` **or** `item`
     **or** `manual_description`, `expected_qty`, `counted_qty`,
     `variance`, `variance_qty`, `notes`. Mirrors the existing line
     UOM conventions (`default_uom`, `entry_uom`, `entry_qty`,
     `conversion_factor`, `qty_in_default_uom`) so `stock_utils` can be
     reused.
   - Optional: `Stock Take Plan` (template) for recurring counts.

4. **Reuse `stock_utils.py` verbatim** (`get_conversion_factor`,
   `calculate_qty_in_default_uom`, `validate_stock_lines`,
   `validate_material_source`). Do not fork the UOM logic.

5. **Reuse `Stock Category`, `Stock Material Profile`, and
   `Stock UOM Conversion Rule`** rather than introducing parallel masters.

6. **Operator UI:**
   - *Lowest-friction option:* extend the existing `www/` pattern with
     vanilla JS — same auth model, no toolchain. Recommended unless V3
     explicitly needs a SPA/offline.
   - *If V3 needs a React SPA:* mount under `www/stock-take/` with a
     thin Jinja shell, ship a built bundle from `public/dist/`, and add
     `web_include_js`/`web_include_css` in `hooks.py`. Build tooling
     (Vite recommended) needs to be agreed and added in Phase 1.

7. **Variance reporting only.** Surface "expected vs counted vs variance"
   via a new Script Report alongside `Latest Stock Snapshot`. The
   "expected" side reads from the existing six stock-entry doctypes;
   it does **not** read or write ERPNext `Bin` / `Stock Ledger Entry`.

8. **Phasing.** Suggested:
   - Phase 0 — this audit.
   - Phase 1 — DocType + module scaffolding (no business logic yet).
   - Phase 2 — server validation, conversion reuse, fixtures.
   - Phase 3 — operator UI (web page).
   - Phase 4 — variance report + permissions polish.
   - Phase 5 — optional ERPNext Item linkage (still no Stock Reco).

---

## 6. Risks and Conflicts with Existing Code

1. **App-name discrepancy (`vcl_stocktake` vs `vcl_stock_control`).**
   The brief refers to `vcl_stocktake`, but the package is
   `vcl_stock_control`. Possible meanings: (a) V3 is a *new* sibling app
   called `vcl_stocktake`; (b) V3 is a *new module* inside
   `vcl_stock_control`; (c) the repo will be renamed. **Decision required
   before Phase 1** — it determines import paths, fixtures, and PR
   ownership. The recommendation in §5 assumes (b).

2. **No tests, no CI.** There is no automated regression coverage on
   `stock_utils.py` or the existing six submit flows, so any V3 change
   that touches shared helpers will need manual smoke testing on a
   bench instance.

3. **`Latest Stock Snapshot` "latest per material" logic.** The dedup is
   `seen.add(material or description)` after `ORDER BY posting_date DESC`,
   ignoring time-of-day and `creation`. Two entries on the same date
   resolve in undefined SQL order. V3 variance reporting must not
   inherit this; pin a deterministic ordering
   (`posting_date DESC, creation DESC, name DESC`).

4. **`Latest Stock Snapshot` swallows exceptions per doctype.** The
   `try/except: pass` block hides schema errors. If V3 adds a new
   stock-entry-like doctype, the snapshot will silently omit it. Either
   widen the `try`/log, or have V3 keep its own report.

5. **`stock_entry_api.create_ink_chemical_stock_entry` recomputes the
   conversion factor server-side.** Good for security; bad if V3 wants
   to record the operator-entered factor verbatim. V3 line writers
   should follow the same recompute pattern unless a deliberate audit
   field is added.

6. **`stock_utils.validate_stock_lines` mutates `row.conversion_factor`
   and `row.qty_in_default_uom` during `validate`.** Any V3 doctype
   reusing it must be a child doctype with those same fieldnames, or
   the helper needs a parameterised refactor.

7. **`fixtures` exports only active `Stock Category` rows.** When V3
   ships, decide whether new V3 categories (e.g. "Stock Take") belong in
   fixtures and whether `install.py` should seed them — the current
   `after_install` is idempotent (`frappe.db.exists` guard).

8. **Permissions model.** "Stock User" has *no submit* on existing
   stock entries. V3 likely needs a counter role that can submit a
   Stock Take Session — either reuse Stock Manager or introduce a new
   `Stock Take User` role. Avoid silently elevating Stock User.

9. **Public assets are not declared in `hooks.py`.** The single existing
   page works because Jinja loads the URLs directly. A V3 SPA must
   declare `web_include_js` / `web_include_css` (or build to a bundle
   that the page imports explicitly), or the assets will only load on
   pages that hard-code them.

10. **No ERPNext stock interaction allowed.** `linked_item` on
    `Stock Material Profile` is described as "for future migration to
    ERP Item" but is currently unused. V3 must not start populating it
    in a way that suggests an ERPNext stock posting will follow, until
    a separate phase explicitly authorises ERPNext stock writes.

---

## 7. Files Likely to be Created or Modified in Phase 1

> "Phase 1" is interpreted as scaffolding the new module and DocTypes
> (no business logic yet). The list below is a preview to align scope —
> nothing in Phase 0 creates any of these files.

### 7.1 Likely **new** files

```
vcl_stock_control/stock_take_v3/__init__.py
vcl_stock_control/stock_take_v3/doctype/__init__.py
vcl_stock_control/stock_take_v3/doctype/stock_take_session/__init__.py
vcl_stock_control/stock_take_v3/doctype/stock_take_session/stock_take_session.json
vcl_stock_control/stock_take_v3/doctype/stock_take_session/stock_take_session.py
vcl_stock_control/stock_take_v3/doctype/stock_take_session/stock_take_session.js
vcl_stock_control/stock_take_v3/doctype/stock_take_count_line/__init__.py
vcl_stock_control/stock_take_v3/doctype/stock_take_count_line/stock_take_count_line.json
vcl_stock_control/stock_take_v3/doctype/stock_take_count_line/stock_take_count_line.py
vcl_stock_control/import_templates/10_stock_take_session.csv          # if seed data is required
docs/stock_take_v3/01_phase1_doctype_spec.md                          # design doc
```

(Optional, only if a Plan/template DocType is in V3 scope:)

```
vcl_stock_control/stock_take_v3/doctype/stock_take_plan/...
```

(Optional, only if V3 ships a React SPA — defer until §5 decision):

```
package.json
vite.config.ts (or equivalent)
src/stock_take/...                 # React source
vcl_stock_control/public/dist/...  # built bundle
vcl_stock_control/www/stock-take.{py,html}
```

### 7.2 Likely **modified** files

| File | Change |
|---|---|
| `vcl_stock_control/modules.txt` | Add `Stock Take V3`. |
| `vcl_stock_control/hooks.py` | Possibly add `fixtures` for the new module; `web_include_js/css` only if a new web page is added. |
| `vcl_stock_control/install.py` | Possibly seed default Stock Take roles/categories (idempotent). |
| `README.md` | Mention Stock Take V3 module in the architecture table. |
| `VCL_STOCK_CONTROL_REFERENCE.md` | Add a Stock Take V3 section once Phase 1 stabilises. |
| `ACCESS_GUIDE.md` | Add desk URLs for new DocTypes. |

### 7.3 Files **not** modified in Phase 0 or Phase 1 (per rules)

- All existing DocType JSON / `.py` files under
  `vcl_stock_control/{masters,transactions,reports}/`.
- `vcl_stock_control/stock_utils.py` (consumed read-only by V3).
- Any ERPNext core DocType (Stock Reconciliation, Stock Ledger Entry,
  Bin, Item, etc.) — strictly out of scope.

---

## Appendix — Quick Inventory Counts

| Artefact | Count |
|---|---:|
| Master DocTypes | 3 |
| Submittable transaction DocTypes | 6 |
| Child line DocTypes | 6 |
| Script Reports | 5 |
| Print Formats | 0 |
| Web Pages (`www/`) | 1 |
| Whitelisted API methods | 4 (3 in `stock_entry_api.py`, 1 in `stock_utils.py`) |
| CSS files | 1 |
| JS files | 1 (vanilla, no framework) |
| React / SPA bundles | 0 |
| Fixtures defined | 1 (Stock Category, active only) |
| Patches | 0 |
| Tests | 0 |
| CI workflows | 0 |
