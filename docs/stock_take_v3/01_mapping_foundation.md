# Phase 1 — Stock Take V3 Mapping Foundation

**Date:** 2026-05-10
**App:** `vcl_stock_control` (no rename; no new app)
**New module:** `Stock Take V3` (`vcl_stock_control/stock_take_v3/`)
**Branch:** `claude/audit-stocktake-repo-gtBZ8`

> No ERPNext stock records are created, posted, or modified by anything
> in this phase. No Stock Reconciliation, no Stock Entry, no Stock Ledger
> Entry, no Bin updates. No existing DocTypes are altered.

---

## 1. Purpose

Stock Take V3 moves VCL from manual paper count sheets to a controlled,
mapped stocktake workflow. **Mapping is the foundation of the project:
if the mapping is wrong, every later phase is wrong.**

Phase 1 introduces the mapping control layer that pins each physical
stocktake sheet row to:

- an ERPNext **Item**,
- an ERPNext **Warehouse** plus the human-friendly godown / warehouse
  label as it appears on the physical sheet,
- the **Count UOM** the operator will use,
- the **ERPNext Stock UOM** that the Item lives in,
- a **Conversion Rule** (and the inputs that rule needs),
- a **Print Section / Sequence** for the printed sheet,
- a **Release Version** the mapping belongs to,
- a **Mapping Status** that gates downstream phases.

Phase 1 is deliberately not building: capture sessions, print packs, the
capture UI, variance review, or any ERPNext stock posting.

---

## 2. Business rules

1. The mapping table is built and approved **before** print packs and
   counts.
2. Every row that will appear on a print sheet must reach
   `mapping_status = Approved for Print` before downstream phases can
   use it.
3. A mapping can only be approved when it is active and fully
   populated (see §6).
4. When the Count UOM differs from the ERPNext Stock UOM, a Conversion
   Rule must be chosen and its required inputs supplied.
5. Releases group mappings for a print pack. Locked releases are
   frozen — they can only be moved to Cancelled.
6. Physical findings that have no mapping are not silently lost; they
   are logged as `VCL Stocktake Mapping Exception` records and resolved
   before the next release.
7. Phase 1 stores conversion inputs only. No conversion math is run on
   stock quantities anywhere in Phase 1.

---

## 3. DocTypes created

| Name | Submittable | Naming | Purpose |
|---|---|---|---|
| `VCL Stocktake Item Map` | No | `STM-.YYYY.-.#####` | One row per print-sheet line; binds it to ERPNext Item, Warehouse, UOMs, and conversion inputs. |
| `VCL Stocktake Mapping Release` | No | `field:release_version` (the version string is the doc name) | Versioned release wrapper used to gate print packs. |
| `VCL Stocktake Mapping Exception` | No | `STX-.YYYY.-.#####` | Records physical findings that do not match an approved mapping. |

Module path:

```
vcl_stock_control/stock_take_v3/
├── __init__.py
└── doctype/
    ├── __init__.py
    ├── vcl_stocktake_item_map/
    │   ├── __init__.py
    │   ├── vcl_stocktake_item_map.json
    │   ├── vcl_stocktake_item_map.py     <- validate(): approval gate
    │   └── vcl_stocktake_item_map.js     <- conversion-field visibility
    ├── vcl_stocktake_mapping_release/
    │   ├── __init__.py
    │   ├── vcl_stocktake_mapping_release.json
    │   └── vcl_stocktake_mapping_release.py   <- validate(): locked transition
    └── vcl_stocktake_mapping_exception/
        ├── __init__.py
        ├── vcl_stocktake_mapping_exception.json
        └── vcl_stocktake_mapping_exception.py <- validate(): mapped-resolution rule
```

`modules.txt` is updated to register the new `Stock Take V3` module.

---

## 4. Field descriptions

### 4.1 VCL Stocktake Item Map

| Field | Type | Required | Notes |
|---|---|---|---|
| `naming_series` | Select | Yes | `STM-.YYYY.-.#####` |
| `display_row_label` | Data | Yes | Title field; appears on the printed sheet. |
| `area` | Select | (req. for approval) | `Brown Paper`, `Labels`, `NCR`, `Inks & Chemicals`. |
| `section` | Data | No | Sub-section within the area. |
| `active` | Check | Default 1; (req. for approval) | Toggles whether the row is in use. |
| `release_version` | Link → VCL Stocktake Mapping Release | No (recommended) | Which release this mapping belongs to. |
| `mapping_status` | Select | Yes | Default `Draft`. Workflow gate. |
| `erpnext_item` | Link → Item | (req. for approval) | The ERPNext Item. |
| `erpnext_item_name` | Data, read-only | — | Auto-fetched from `Item.item_name`. |
| `godown_warehouse_label` | Data | No | Free-text label exactly as on the physical sheet. |
| `erpnext_warehouse` | Link → Warehouse | (req. for approval) | ERPNext Warehouse this row counts against. |
| `count_uom` | Link → UOM | (req. for approval) | UOM used on the count sheet. |
| `erpnext_stock_uom` | Link → UOM | (req. for approval) | Item's stock UOM. |
| `conversion_rule` | Select | No (req. when UOMs differ) | `None`, `Fixed Factor`, `Reel to SQM`, `Reel to KG`, `Manual Confirmed`, `Pack Size`. |
| `conversion_factor` | Float | Conditional | Required for `Fixed Factor` and `Pack Size`. |
| `width_mm` | Float | Conditional | Required for `Reel to SQM`. |
| `standard_length_m` | Float | Conditional | Required for `Reel to SQM`. |
| `avg_weight_kg` | Float | Conditional | Required for `Reel to KG`. |
| `print_sequence` | Int | (req. for approval, > 0) | Controls row order on the print sheet. |
| `reviewed_by` | Link → User | No | Set when the row is reviewed. |
| `reviewed_on` | Datetime | No | |
| `notes` | Small Text | No | |

### 4.2 VCL Stocktake Mapping Release

| Field | Type | Required | Notes |
|---|---|---|---|
| `release_version` | Data, unique, autoname | Yes | Document name = this string, e.g. `2026-Q2-R1`. |
| `release_date` | Date | Yes | Default today. |
| `status` | Select | Yes | `Draft`, `Under Review`, `Approved`, `Locked`, `Cancelled`. |
| `areas_included` | Small Text | No | Comma-separated areas covered. |
| `approved_by` | Link → User | No | Filled when status reaches `Approved`. |
| `approved_on` | Datetime | No | |
| `remarks` | Small Text | No | |

### 4.3 VCL Stocktake Mapping Exception

| Field | Type | Required | Notes |
|---|---|---|---|
| `naming_series` | Select | Yes | `STX-.YYYY.-.#####` |
| `area` | Select | No | Same options as Item Map. |
| `description` | Small Text | Yes | What was found. Title field. |
| `godown_warehouse_label` | Data | No | Physical location. |
| `count_qty` | Float | No | |
| `count_uom` | Link → UOM | No | |
| `possible_erpnext_item` | Link → Item | No | Suggested match. |
| `resolution_status` | Select | Yes | Default `Open`. |
| `resolution_notes` | Small Text | No | |
| `resolved_by` | Link → User | No | |
| `resolved_on` | Datetime | No | |
| `linked_item_map` | Link → VCL Stocktake Item Map | Conditional | Required when `resolution_status = Mapped`. |

---

## 5. Status flows

### 5.1 Item Map mapping_status

```
Draft
  ├─→ Needs ERPNext Item
  ├─→ Needs Warehouse
  ├─→ Needs UOM
  ├─→ Needs Conversion Rule
  ├─→ Ready for Review
  │       └─→ Approved for Print   (gated by §6 approval rules)
  ├─→ Excluded
  └─→ Inactive
```

Movement between non-`Approved for Print` states is unrestricted in
Phase 1. The hard gate is the transition into `Approved for Print`.

### 5.2 Release status

```
Draft → Under Review → Approved → Locked
                              ↘
                               Cancelled   (terminal)
Locked → only Cancelled
```

### 5.3 Mapping Exception resolution_status

```
Open
  ├─→ Existing ERPNext Item Found
  ├─→ New ERPNext Item Required
  ├─→ Duplicate
  ├─→ Not Relevant
  ├─→ Mapped              (requires linked_item_map)
  └─→ Closed
```

---

## 6. Validation rules

All validations are enforced in Python controllers (`validate()`), with
explicit error messages and no broad `except` blocks. The client script
only toggles field visibility — it never silences a server validation.

### 6.1 `VCLStocktakeItemMap.validate` — approval gate

When `mapping_status == "Approved for Print"`:

- `active` must be checked.
- `erpnext_item` must be set.
- `erpnext_warehouse` must be set.
- `count_uom` must be set.
- `erpnext_stock_uom` must be set.
- `area` must be set.
- `print_sequence` must be a positive integer (`> 0`).
- If `count_uom != erpnext_stock_uom`, `conversion_rule` must be set
  and not `None`.
- Conversion-rule prerequisites:
  - `Fixed Factor` → `conversion_factor > 0`.
  - `Reel to SQM` → both `width_mm` and `standard_length_m` are set.
  - `Reel to KG` → `avg_weight_kg` is set.
  - `Pack Size` → `conversion_factor > 0`.
  - `None`, `Manual Confirmed` → no additional inputs required.

Draft / Needs* / Ready for Review / Excluded / Inactive rows save
freely with whatever data is present, so users can build them in
stages without fighting save errors.

### 6.2 `VCLStocktakeMappingRelease.validate` — Locked transition

If the previous status was `Locked`, the new status must be either
`Locked` (no-op) or `Cancelled`. Any other transition out of `Locked`
is rejected with an explicit message.

### 6.3 `VCLStocktakeMappingException.validate` — Mapped resolution

If `resolution_status == "Mapped"`, `linked_item_map` must reference an
existing `VCL Stocktake Item Map`. Otherwise the save is rejected.

### 6.4 Client script (`vcl_stocktake_item_map.js`)

- Hides `conversion_factor` unless rule is `Fixed Factor` or `Pack Size`.
- Hides the reel-inputs section unless rule is `Reel to SQM` or
  `Reel to KG`.
- Marks the right subset of fields as required on the form (mirrors
  the server validation; the server is still the source of truth).

---

## 7. User steps

### 7.1 Stock User (read-only in Phase 1)

1. Open Desk → global search → e.g. "VCL Stocktake Item Map".
2. Browse the list, filter by `area`, `release_version`, or
   `mapping_status`.
3. Open a row to inspect detail.

### 7.2 Stock Manager (build and approve mappings)

1. Create a `VCL Stocktake Mapping Release` (status `Draft`):
   - Fill `release_version` (e.g. `2026-Q2-R1`).
   - Set `release_date` and the `areas_included` list.
2. For each printable row, create a `VCL Stocktake Item Map`:
   - Fill `display_row_label`, `area`, optionally `section`.
   - Pick `erpnext_item` — the item name auto-fetches.
   - Fill `godown_warehouse_label` (free text) and link
     `erpnext_warehouse`.
   - Fill `count_uom` and `erpnext_stock_uom`.
   - Choose `conversion_rule` and fill the inputs the rule needs
     (the form hides the others).
   - Set `print_sequence` (positive integer).
   - Link `release_version` to your release.
   - Walk `mapping_status` from `Draft` → `Ready for Review` →
     `Approved for Print`.
3. When the release is fully populated, move the release's status to
   `Approved`, then to `Locked` when no further edits are expected.

### 7.3 Anyone reconciling exceptions

1. Create a `VCL Stocktake Mapping Exception` for each unmapped finding.
2. Resolve it via the status flow; when resolving as `Mapped`, set
   `linked_item_map` to the relevant Item Map row.

---

## 8. Admin steps

System Manager:

1. Pull the branch and run:
   ```
   bench --site <site> migrate
   bench --site <site> clear-cache
   bench restart
   ```
2. Confirm the new `Stock Take V3` module appears under Settings →
   Modules.
3. Confirm the three new DocTypes are listed in global search.
4. Confirm role permissions match §11.

The new DocTypes are accessible at:

| DocType | Desk URL |
|---|---|
| VCL Stocktake Item Map | `/app/vcl-stocktake-item-map` |
| VCL Stocktake Mapping Release | `/app/vcl-stocktake-mapping-release` |
| VCL Stocktake Mapping Exception | `/app/vcl-stocktake-mapping-exception` |

No new Workspace JSON is shipped in Phase 1 (see §11).

---

## 9. UAT steps

Performed against a non-production bench by a Stock Manager.

1. **Create a Draft mapping row**
   - New `VCL Stocktake Item Map` with only `display_row_label = "Test
     Row"` and `mapping_status = Draft`.
   - **Expected:** saves with no error.
2. **Try approving without ERPNext Item**
   - On the row from step 1, set `mapping_status = Approved for Print`
     and save.
   - **Expected:** validation blocks and the error lists at least
     `ERPNext Item` among the missing items.
3. **Try approving without Warehouse**
   - Link an Item, retry `Approved for Print`.
   - **Expected:** validation blocks with `ERPNext Warehouse` in the
     missing list.
4. **Try approving with mismatched Count UOM / Stock UOM and no
   conversion rule**
   - Fill all approval prerequisites, set `count_uom = Bottle`,
     `erpnext_stock_uom = Millilitre`, `conversion_rule = None`,
     try `Approved for Print`.
   - **Expected:** validation blocks with "Count UOM ... differs from
     ERPNext Stock UOM ... a Conversion Rule must be set for
     approval."
5. **Approve a valid Inks & Chemicals mapping**
   - `area = Inks & Chemicals`, `erpnext_item` set, warehouse set,
     `count_uom = erpnext_stock_uom` (same UOM, no conversion needed),
     `print_sequence = 10`, `active` checked.
   - **Expected:** saves with `mapping_status = Approved for Print`.
6. **Approve a valid Labels reel-to-sqm mapping**
   - `area = Labels`, `count_uom = Reel`, `erpnext_stock_uom = SQM`,
     `conversion_rule = Reel to SQM`, `width_mm = 1000`,
     `standard_length_m = 500`.
   - **Expected:** saves with `mapping_status = Approved for Print`.
   - Edit the same row, blank `width_mm`, retry approval.
   - **Expected:** validation blocks asking for Width (mm) and
     Standard Length (m).
7. **Approve a valid NCR reel-to-kg mapping**
   - `area = NCR`, `count_uom = Reel`, `erpnext_stock_uom = Kg`,
     `conversion_rule = Reel to KG`, `avg_weight_kg = 25`.
   - **Expected:** saves with `mapping_status = Approved for Print`.
8. **Create a mapping exception**
   - New `VCL Stocktake Mapping Exception` with
     `description = "Found 5 reels unlabelled"`,
     `area = Brown Paper`, `resolution_status = Open`.
   - **Expected:** saves with no error.
9. **Resolve exception as Mapped**
   - Open the exception, set `resolution_status = Mapped` without
     `linked_item_map`, save.
   - **Expected:** validation blocks with "Linked Item Map is
     required when Resolution Status is 'Mapped'."
   - Set `linked_item_map` to an approved Item Map row, save.
   - **Expected:** saves with no error.

---

## 10. OAT steps

1. **Clean migrate**
   - `bench --site <site> migrate` succeeds on a fresh pull.
   - Running it a second time is idempotent (no errors, no duplicate
     metadata).
2. **Module discovery**
   - `Stock Take V3` appears in Settings → Modules.
   - The three DocTypes appear in the global search.
3. **DocTypes visible to the correct roles**
   - Stock User: read-only access to all three DocTypes.
   - Stock Manager: read/write/create on all three; delete only via
     System Manager.
   - System Manager: full access.
4. **No regression to existing stock-entry DocTypes**
   - Open one of each existing stock-entry doctype (Ink Chemical, Raw
     Material, Finished Goods, Core, Spare, Fuel), edit a draft, save.
   - **Expected:** no new errors.
5. **No Stock Reconciliation is created**
   - After full UAT run, check Stock Reconciliation list: 0 new rows.
6. **No stock ledger records are changed**
   - Run a sanity SQL on `tabStock Ledger Entry` / `tabBin` against a
     pre-test snapshot:
     ```
     SELECT COUNT(*) FROM `tabStock Ledger Entry`;
     SELECT COUNT(*) FROM `tabBin`;
     ```
     **Expected:** counts identical before and after the UAT run.
7. **Permissions documented**
   - See §11 below.
8. **Rollback documented**
   - See §11 Rollback notes.

---

## 11. Known limitations

- **No print-pack output.** Phase 1 stores conversion inputs but does
  not produce printed sheets; Phase 2 will.
- **No conversion math runs against stock.** Conversion fields are
  declarative only.
- **No bulk import template ships in this phase.** Mappings can be
  loaded via Frappe's built-in Data Import once the DocType is
  installed; a curated CSV template can be added in a later phase
  alongside the existing `import_templates/` files.
- **No Workspace / Dashboard.** Users open mappings via global search
  or the URLs in §8.
- **`areas_included` is plain text.** A structured child-table model
  can replace it later if reporting needs it.
- **Mid-state conversion checks are deferred.** The conversion-rule
  prerequisites only fire when the user moves to `Approved for Print`.
  Drafts can be partial. The form's client script masks irrelevant
  fields to keep this clear.
- **No automated tests yet.** The whole `vcl_stock_control` app has no
  test suite (see Phase 0 audit). Phase 1 ships UAT/OAT instead.

### Permissions matrix

| Role | VCL Stocktake Item Map | VCL Stocktake Mapping Release | VCL Stocktake Mapping Exception |
|---|---|---|---|
| System Manager | full (create, read, write, delete, report, export, print, email, share) | same | same |
| Stock Manager | create, read, write, report | create, read, write, report | create, read, write, report |
| Stock User | read, report | read, report | read, report |

### Rollback notes

If Phase 1 needs to be rolled back, the steps are:

1. `git revert` the Phase 1 commits on this branch (or revert the
   merge commit on the integration branch).
2. On the affected bench, drop the three DocTypes from the database
   (Desk → DocType List → delete `VCL Stocktake Item Map`, `VCL
   Stocktake Mapping Release`, `VCL Stocktake Mapping Exception`).
3. Remove the `Stock Take V3` line from `vcl_stock_control/modules.txt`
   (the revert above will already do this).
4. `bench --site <site> migrate` to settle DocType metadata.
5. `bench restart`.

No ERPNext core data is touched by Phase 1, so no `Stock Ledger
Entry`, `Bin`, or `Stock Reconciliation` rollback is needed.

---

## 12. Next phase dependency

Phase 2 (Print Pack Generation, **not implemented in this branch**)
depends on:

- At least one `VCL Stocktake Mapping Release` in status `Approved` or
  `Locked`.
- All `VCL Stocktake Item Map` rows for that release in
  `mapping_status = Approved for Print`.

Phase 2 will **read** from these DocTypes and generate printable count
sheets. It will not mutate mapping rows and will not post stock. The
mapping records produced in Phase 1 are the contract for every later
phase, so the bar to approve a mapping is intentionally strict.

Phase 3+ (count capture, variance review, exception reconciliation)
will continue to read from this mapping layer. None of the later phases
in the current roadmap write to ERPNext stock ledgers either — see the
Phase 0 audit (`docs/stock_take_v3/00_repo_audit.md`) for the constraint
log.
