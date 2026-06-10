# Phase 0 — Repo Audit (Alternate Version)

> **Status:** Parallel audit supplied 2026-06-10. The original Phase 0 audit
> lives at `docs/stock_take_v3/00_repo_audit.md` and was the basis for the
> Phase 1 work committed in `733e04b` (mapping foundation). This file is kept
> for traceability — it was authored against a different branch
> (`codex/new-branch`) and reaches a different §5 / §7 recommendation than
> what was actually built.
>
> **Known divergences from current branch state:**
>
> 1. Header says "branch audited: `codex/new-branch`"; the audit was committed
>    on `claude/audit-stock-control-app-ZFEsG`.
> 2. Date stamped 2026-05-10; merged on 2026-06-10.
> 3. §1 lists three Frappe modules (Masters, Transactions, Reports);
>    `modules.txt` now also includes `Stock Take V3`.
> 4. §5 / §7 recommend a session-based count workflow with
>    `Stock Take Session` + `Stock Take Session Line` DocTypes. Phase 1
>    actually shipped a **mapping-foundation** approach with
>    `VCL Stocktake Mapping Release`, `VCL Stocktake Item Map`, and
>    `VCL Stocktake Mapping Exception` — see `01_mapping_foundation.md`.
> 5. §7 lists existing transaction controllers as "do not modify"; that
>    constraint is still respected by the mapping-foundation work, but the
>    file list itself never materialised.
>
> Sections 1-4 (current app structure, DocTypes, pages/reports/APIs, no
> React) match the repository. Sections 5-7 should be read as a historical
> alternative, not as current guidance.

---

# Stock Take V3 - Phase 0 Repository Audit

Date: 2026-05-10  
Repository branch audited: `codex/new-branch`  
Scope: documentation-only audit for the existing Frappe app in this repository.

> Note: the prompt refers to an existing Frappe app named `vcl_stocktake`, but the repository metadata and package paths identify the app as `vcl_stock_control` / **VCL Stock Control**. This audit uses the repository as the source of truth and calls out this naming mismatch as a Phase 1 risk to resolve before implementation.
>
> The Notion URL supplied for VCL Stock Take V3 was checked from this environment, but the page contents were not accessible without an authenticated Notion session. This audit therefore focuses on repository findings and conservative implementation recommendations.

## 1. Current app structure

### App identity and dependencies

| Area | Current state |
| --- | --- |
| Python package / Frappe app | `vcl_stock_control` |
| App title | `VCL Stock Control` |
| Version | `1.0.0` |
| Required apps | `frappe`, `erpnext` |
| Python requirement | `>=3.10` in `pyproject.toml` |
| Runtime dependency file | `requirements.txt` currently lists `frappe` |
| Modules | `Masters`, `Transactions`, `Reports` |
| Install hook | `after_install = vcl_stock_control.install.after_install` |
| Fixtures | Active `Stock Category` records |
| Patches | Patch files exist but contain no patch entries |

### Directory layout

```text
vcl_stock_control/
├── api/
│   └── stock_entry_api.py
├── import_templates/
│   ├── 01_stock_category.csv
│   ├── 02_stock_material_profile.csv
│   ├── 03_stock_uom_conversion_rule.csv
│   ├── 04_ink_chemical_stock_entry.csv
│   ├── 05_raw_material_stock_entry.csv
│   ├── 06_finished_goods_stock_entry.csv
│   ├── 07_core_stock_entry.csv
│   ├── 08_spare_stock_entry.csv
│   └── 09_fuel_stock_entry.csv
├── masters/
│   └── doctype/
│       ├── stock_category/
│       ├── stock_material_profile/
│       └── stock_uom_conversion_rule/
├── patches/
├── public/
│   ├── css/ink_chemical_entry.css
│   └── js/ink_chemical_entry.js
├── reports/
│   ├── category_summary/
│   ├── latest_stock_snapshot/
│   ├── low_stock/
│   ├── stock_history/
│   └── stock_variance/
├── templates/
├── transactions/
│   └── doctype/
│       ├── core_stock_entry/
│       ├── core_stock_entry_line/
│       ├── finished_goods_stock_entry/
│       ├── finished_goods_stock_entry_line/
│       ├── fuel_stock_entry/
│       ├── fuel_stock_entry_line/
│       ├── ink_chemical_stock_entry/
│       ├── ink_chemical_stock_entry_line/
│       ├── raw_material_stock_entry/
│       ├── raw_material_stock_entry_line/
│       ├── spare_stock_entry/
│       └── spare_stock_entry_line/
├── www/
│   ├── ink-chemical-entry.html
│   └── ink-chemical-entry.py
├── hooks.py
├── install.py
├── modules.txt
├── patches.txt
└── stock_utils.py
```

### Existing design model

The current app is a stock-capture layer, not an ERPNext stock ledger replacement. Existing project documentation states these design rules:

1. Only inks and chemicals link to ERPNext `Item`.
2. Other categories use the custom `Stock Material Profile` master.
3. Quantity normalization is `qty_in_default_uom = entry_qty * conversion_factor`.
4. Transaction DocTypes are submittable.
5. Reports count submitted records only.

The code follows this model with shared validation/conversion helpers in `stock_utils.py`, submittable transaction DocTypes, and script reports that query submitted transaction records.

## 2. Existing DocTypes

There are 15 custom DocTypes: 3 master DocTypes, 6 parent transaction DocTypes, and 6 child-table DocTypes.

### Master DocTypes

| DocType | Path | Purpose / notes | Submittable | Naming |
| --- | --- | --- | --- | --- |
| `Stock Category` | `vcl_stock_control/masters/doctype/stock_category/` | Classifies major stock groups and flags whether a category is item-linked or manual-only. | No | `field:stock_category_name` |
| `Stock Material Profile` | `vcl_stock_control/masters/doctype/stock_material_profile/` | Manual material master for non-Item stock, with optional future `Item` link, UOMs, dimensions, source details, and stock levels. | No | `SMP-.YYYY.-.#####` |
| `Stock UOM Conversion Rule` | `vcl_stock_control/masters/doctype/stock_uom_conversion_rule/` | Manual-stock conversion rules at material-profile or stock-category level. | No | `hash` |

### Transaction parent DocTypes

| DocType | Path | Child table | Series | Submittable | Key header fields |
| --- | --- | --- | --- | --- | --- |
| `Ink Chemical Stock Entry` | `vcl_stock_control/transactions/doctype/ink_chemical_stock_entry/` | `Ink Chemical Stock Entry Line` | `ICSE-.YYYY.-.#####` | Yes | `posting_date`, `department`, `location`, `items`, `remarks` |
| `Raw Material Stock Entry` | `vcl_stock_control/transactions/doctype/raw_material_stock_entry/` | `Raw Material Stock Entry Line` | `RMSE-.YYYY.-.#####` | Yes | `posting_date`, `warehouse_text`, `location`, `items`, `remarks` |
| `Finished Goods Stock Entry` | `vcl_stock_control/transactions/doctype/finished_goods_stock_entry/` | `Finished Goods Stock Entry Line` | `FGSE-.YYYY.-.#####` | Yes | `posting_date`, `location`, `items`, `remarks` |
| `Core Stock Entry` | `vcl_stock_control/transactions/doctype/core_stock_entry/` | `Core Stock Entry Line` | `CSE-.YYYY.-.#####` | Yes | `posting_date`, `location`, `items`, `remarks` |
| `Spare Stock Entry` | `vcl_stock_control/transactions/doctype/spare_stock_entry/` | `Spare Stock Entry Line` | `SSE-.YYYY.-.#####` | Yes | `posting_date`, `location`, `department`, `items`, `remarks` |
| `Fuel Stock Entry` | `vcl_stock_control/transactions/doctype/fuel_stock_entry/` | `Fuel Stock Entry Line` | `FSE-.YYYY.-.#####` | Yes | `posting_date`, `location`, `items`, `remarks` |

### Transaction child DocTypes

| Child DocType | Parent | Material source | Quantity fields | Category-specific fields |
| --- | --- | --- | --- | --- |
| `Ink Chemical Stock Entry Line` | `Ink Chemical Stock Entry` | Required `Item` link | `default_uom`, `entry_uom`, `entry_qty`, `conversion_factor`, `qty_in_default_uom` | `stock_category`, `supplier`, `batch_no`, `expiry_date`, `notes` |
| `Raw Material Stock Entry Line` | `Raw Material Stock Entry` | `Stock Material Profile` or manual description | Same normalized quantity fields | `stock_category`, `colour`, `gsm`, `width_mm`, `length_mm`, `size_text`, `country`, `mill`, `secondary_qty`, `secondary_uom` |
| `Finished Goods Stock Entry Line` | `Finished Goods Stock Entry` | `Stock Material Profile` or manual description | Same normalized quantity fields | `size_text`, `pages`, `ruling_type`, `print_type`, bundle/carton fields, `calculated_pieces` |
| `Core Stock Entry Line` | `Core Stock Entry` | `Stock Material Profile` or manual description | Same normalized quantity fields | `size_text`, `status_note` |
| `Spare Stock Entry Line` | `Spare Stock Entry` | `Stock Material Profile` or manual description | Same normalized quantity fields | `part_no`, `minimum_level`, `reorder_flag` |
| `Fuel Stock Entry Line` | `Fuel Stock Entry` | `fuel_point`, `Stock Material Profile`, or manual description | Same normalized quantity fields | `fuel_point`, `notes` |

### Existing validation and calculations

| Area | Current behavior |
| --- | --- |
| Common stock line validation | Requires lines, UOMs, quantity, non-negative quantities, and calculates `qty_in_default_uom`. |
| Item-linked conversions | Uses ERPNext `Item` UOM Conversion Detail via `_get_item_uom_conversion`. |
| Manual-stock conversions | Uses `Stock UOM Conversion Rule`, preferring material-profile rule before stock-category rule. |
| Source validation | Ink/chemical lines require `Item`; manual categories require `material_profile` or `manual_description`; fuel additionally accepts `fuel_point`. |
| Finished goods | Calculates `calculated_pieces` from bundle/carton fields and can set entry quantity when default UOM is pieces. |
| Spare entries | Sets `reorder_flag` based on `minimum_level` and normalized quantity. |
| Stock ledger impact | No existing code creates ERPNext `Stock Entry`, `Stock Reconciliation`, `Stock Ledger Entry`, or `Bin` updates. |

## 3. Existing pages, reports, print formats, public assets, and APIs

### Website / web pages

| Page | Files | Route | Purpose |
| --- | --- | --- | --- |
| Ink & Chemical Stock Entry | `vcl_stock_control/www/ink-chemical-entry.html`, `vcl_stock_control/www/ink-chemical-entry.py` | `/ink-chemical-entry` | Logged-in operator page for entering item-linked ink/chemical stock. |

The page extends Frappe's `templates/web.html`, renders a dynamic table, loads app JS/CSS assets directly, and rejects guest users in `get_context`.

No Desk `page/` module directory was found.

### Reports

| Report | Type | Ref DocType | Files | Filters / notes |
| --- | --- | --- | --- | --- |
| `Latest Stock Snapshot` | Script Report | `Ink Chemical Stock Entry` | `latest_stock_snapshot.json`, `.js`, `.py` | `posting_date`, `stock_category`, `location`; scans submitted entries across all six transaction types and returns latest record per material/location. |
| `Stock History` | Script Report | `Ink Chemical Stock Entry` | `stock_history.json`, `.js`, `.py` | `from_date`, `to_date`, `stock_category`, `location`; scans submitted entries across all six transaction types. |
| `Low Stock` | Script Report | `Stock Material Profile` | `low_stock.json`, `.js`, `.py` | No JS filters; compares latest captured quantity against material profile thresholds. |
| `Category Summary` | Script Report | `Stock Category` | `category_summary.json`, `.js`, `.py` | No JS filters; aggregates submitted quantities by category. |
| `Stock Variance` | Script Report | `Stock Category` | `stock_variance.json`, `.js`, `.py` | Required previous/current dates plus optional stock category; compares latest snapshots as of two dates. |

All report JSON files grant access to `System Manager`, `Stock Manager`, and `Stock User` roles.

### Print formats

No custom print format directories or print format JSON files were found in the repository.

### Public assets

| Asset | Purpose |
| --- | --- |
| `vcl_stock_control/public/js/ink_chemical_entry.js` | Client-side behavior for `/ink-chemical-entry`: line management, item autocomplete, conversion lookup, payload build, save/submit API call. |
| `vcl_stock_control/public/css/ink_chemical_entry.css` | Website page styling, responsive layout, stock-line table, messages, and actions. |

No bundled React/Vue/Svelte frontend assets or build output were found.

### APIs and whitelisted methods

| Method | File | Purpose | Notes |
| --- | --- | --- | --- |
| `vcl_stock_control.api.stock_entry_api.get_ink_item_details` | `vcl_stock_control/api/stock_entry_api.py` | Fetches ERPNext `Item` details and item UOM conversion rows for the website page. | Whitelisted; requires an item code. |
| `vcl_stock_control.api.stock_entry_api.get_item_conversion_factor` | `vcl_stock_control/api/stock_entry_api.py` | Returns conversion factor for an item/UOM pair. | Whitelisted; delegates to item UOM conversion helper. |
| `vcl_stock_control.api.stock_entry_api.create_ink_chemical_stock_entry` | `vcl_stock_control/api/stock_entry_api.py` | Creates and optionally submits an `Ink Chemical Stock Entry` from website JSON payload. | Whitelisted; recalculates item details/conversions server-side before insert/submit. |
| `vcl_stock_control.stock_utils.fetch_conversion_factor` | `vcl_stock_control/stock_utils.py` | Client-side conversion lookup helper for forms. | Whitelisted; handles item, material-profile, or stock-category conversions. |

The website JavaScript also calls the standard Frappe method `frappe.client.get_list` to search active `Item` records.

## 4. Whether a React frontend already exists

A React frontend does **not** appear to exist in this repository.

Evidence:

- No `package.json`, `vite.config.*`, `yarn.lock`, `pnpm-lock.yaml`, `*.jsx`, or `*.tsx` files were found.
- The only custom frontend is a Frappe website page implemented with Jinja/HTML, plain JavaScript, and CSS.
- `hooks.py` does not define `app_include_js`, `app_include_css`, `web_include_js`, or a Frappe v15/v16 frontend build integration.

## 5. Recommended implementation approach for Stock Take V3

Because the current app is a stock-capture system and does not post ERPNext stock ledger records, Stock Take V3 should be implemented as an additive stock-count workflow first, with ERPNext stock reconciliation kept behind an explicit, reviewed boundary.

### Recommended architecture

1. **Add new V3 DocTypes rather than repurposing existing entry DocTypes.**
   - Keep existing capture forms and reports stable.
   - Create stock-take-specific parent/child DocTypes for sessions, counted lines, review/approval, and reconciliation preparation.

2. **Model physical count workflow separately from ERP posting.**
   - Suggested conceptual flow:
     1. Create a stock take session for company/warehouse/category/date.
     2. Load or generate expected lines from ERPNext items and/or existing manual material profiles, depending on V3 requirements.
     3. Allow counters to capture counted quantity, UOM, batch/serial metadata where required, and comments.
     4. Calculate variance in a review state.
     5. Require manager approval before any ERPNext stock impact.
     6. In a later phase, generate a draft `Stock Reconciliation` only after explicit user action and permission checks.

3. **Preserve the current no-ledger-impact behavior during early phases.**
   - Phase 1 should likely create DocTypes, permissions, basic forms, and possibly reports only.
   - Avoid creating `Stock Reconciliation` logic until V3 workflow, controls, and approval steps are confirmed.

4. **Use Frappe-native UI initially unless V3 explicitly requires React.**
   - There is no React build chain today.
   - Frappe Desk forms, child tables, workflow states, script reports, and optionally a website page can be delivered with lower risk.
   - If operator scanning/mobile UX is a hard V3 requirement, consider a dedicated `www/` page using plain JS first or introduce React only with a deliberate build setup and deployment plan.

5. **Integrate with ERPNext Items/Warehouses carefully.**
   - Existing app only item-links inks and chemicals; V3 stock take may need full ERP stock items, warehouses, batches, serials, or bins.
   - Clarify whether V3 counts ERPNext `Item`/`Warehouse` stock only, custom manual materials only, or both.

6. **Create a clear service boundary before ERP posting.**
   - Put reconciliation-preparation and eventual ERP posting code in a new module such as `vcl_stock_control/stock_take_v3/services/` or `vcl_stock_control/stock_take_v3/api.py`.
   - Keep functions idempotent where possible.
   - Use explicit permission checks and audit fields.

### Suggested Phase 1 deliverable boundary

Phase 1 should likely be limited to:

- New DocTypes and permissions for a draft stock-take session and count lines.
- Basic Desk form usability and client scripts.
- Read-only expected quantity lookup only if clearly required and safe.
- Initial script report(s) for count progress/variance without ERP stock updates.
- No submission to ERPNext `Stock Reconciliation` yet.

## 6. Risks or conflicts with existing code

| Risk / conflict | Why it matters | Recommendation |
| --- | --- | --- |
| App naming mismatch: prompt says `vcl_stocktake`, repo is `vcl_stock_control`. | New module paths, app names, and import paths could be created incorrectly. | Confirm final app/package naming before Phase 1. Prefer using existing `vcl_stock_control` package unless a migration/rename is explicitly required. |
| Existing app is not an ERP stock ledger replacement. | V3 stock take may require ERPNext stock reconciliation, which is a different responsibility and higher-risk. | Keep count capture and reconciliation posting separate; do not post ERP stock records until a later approved phase. |
| Existing transaction reports assume six current transaction DocTypes. | Adding V3 counted quantities to current reports could confuse capture snapshots with stock-take counts. | Build separate V3 reports or explicitly label V3 data; avoid silently mixing data sources. |
| Existing manual material model differs from ERPNext Item/Warehouse model. | V3 may need ERP item stock, warehouse balances, batch/serial handling, or manual stock profiles. | Decide V3 source of truth per category before creating fields. |
| Existing whitelisted API can submit `Ink Chemical Stock Entry`. | New V3 APIs must not accidentally copy submit/post behavior into stock reconciliation. | Default V3 APIs to save draft/count data only; add permission and workflow gates for approval/posting later. |
| No React frontend exists. | Introducing React adds build, deployment, and maintenance work not currently present. | Use Frappe-native UI unless V3 operator UX requires React and the build pipeline is explicitly accepted. |
| Report SQL often catches and suppresses exceptions. | Failures may be hidden, making V3 audit/variance issues difficult to diagnose if this pattern is reused. | Avoid broad silent exception handling in new V3 code; surface errors or log them with context. |
| Import templates and current DocTypes may have overlapping concepts with stock count imports. | Users could confuse stock-entry imports with stock-take count imports. | Use V3-specific naming and documentation for count upload templates. |
| Notion documentation inaccessible in this environment. | Requirements may be incomplete in this audit. | Treat this audit as repo-only; review Notion requirements manually before implementation. |

## 7. Files likely to be created or modified in Phase 1

The exact file list depends on the confirmed V3 data model, but the following are likely if Phase 1 creates a Frappe-native Stock Take V3 foundation.

### Likely new files/directories

```text
docs/stock_take_v3/01_phase_1_design.md
vcl_stock_control/stock_take_v3/__init__.py
vcl_stock_control/stock_take_v3/api.py
vcl_stock_control/stock_take_v3/services/__init__.py
vcl_stock_control/stock_take_v3/services/session_builder.py
vcl_stock_control/stock_take_v3/services/variance.py
vcl_stock_control/stock_take_v3/doctype/__init__.py
vcl_stock_control/stock_take_v3/doctype/stock_take_session/__init__.py
vcl_stock_control/stock_take_v3/doctype/stock_take_session/stock_take_session.json
vcl_stock_control/stock_take_v3/doctype/stock_take_session/stock_take_session.py
vcl_stock_control/stock_take_v3/doctype/stock_take_session/stock_take_session.js
vcl_stock_control/stock_take_v3/doctype/stock_take_session_line/__init__.py
vcl_stock_control/stock_take_v3/doctype/stock_take_session_line/stock_take_session_line.json
vcl_stock_control/stock_take_v3/doctype/stock_take_session_line/stock_take_session_line.py
vcl_stock_control/stock_take_v3/report/stock_take_progress/stock_take_progress.json
vcl_stock_control/stock_take_v3/report/stock_take_progress/stock_take_progress.py
vcl_stock_control/stock_take_v3/report/stock_take_progress/stock_take_progress.js
vcl_stock_control/stock_take_v3/report/stock_take_variance/stock_take_variance.json
vcl_stock_control/stock_take_v3/report/stock_take_variance/stock_take_variance.py
vcl_stock_control/stock_take_v3/report/stock_take_variance/stock_take_variance.js
vcl_stock_control/import_templates/10_stock_take_session_line.csv
```

Possible names may need to follow Frappe module conventions. If the team wants `Stock Take V3` as a first-class module, `vcl_stock_control/modules.txt` would also need a new module entry.

### Likely modified files

| File | Reason |
| --- | --- |
| `vcl_stock_control/modules.txt` | Add a `Stock Take V3` module if V3 is separated from `Transactions` / `Reports`. |
| `vcl_stock_control/hooks.py` | Add fixtures, include assets, permissions hooks, scheduler entries, or web includes only if required. |
| `vcl_stock_control/patches.txt` and/or `vcl_stock_control/patches/patches.txt` | Add data migration/setup patches if Phase 1 needs default roles, workflow states, or seed records. |
| `vcl_stock_control/install.py` | Add safe default V3 setup only if it is required on fresh installs. |
| `README.md`, `ACCESS_GUIDE.md`, `VCL_STOCK_CONTROL_REFERENCE.md` | Document V3 workflow, roles, routes, reports, and setup. |
| `vcl_stock_control/public/js/...` and `vcl_stock_control/public/css/...` | Only if Phase 1 includes a custom operator page instead of Desk forms. |
| `vcl_stock_control/www/...` | Only if Phase 1 includes a web/mobile count page. |

### Files that should not be modified in Phase 1 without explicit approval

| File / area | Reason |
| --- | --- |
| Existing transaction DocType Python controllers | Avoid changing current stock-capture business logic. |
| Existing report SQL | Avoid changing live report semantics before V3 data is established. |
| ERPNext stock posting APIs | V3 should not create or submit `Stock Reconciliation` in Phase 1. |
| Existing import templates 01-09 | Avoid disrupting current imports. Add V3-specific templates instead. |

## Phase 0 conclusion

The repository already contains a stable Frappe app for stock capture across multiple operational categories, with no evidence of a React frontend and no existing ERPNext stock reconciliation posting logic. Stock Take V3 should be added as a separate, controlled stock-count workflow that preserves existing capture behavior and postpones ERPNext stock ledger changes until requirements, approvals, and safety controls are confirmed.
