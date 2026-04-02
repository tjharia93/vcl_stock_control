# VCL Stock Control App - Complete Reference

**App Name:** vcl_stock_control
**App Title:** VCL Stock Control
**Platform:** Frappe / ERPNext v16
**Required Apps:** frappe, erpnext

---

## 1. App Overview

Stock-capture app for factory stock visibility. Covers inks, chemicals, raw materials, finished goods, cores, spares, and fuel. This is NOT a full ERP stock ledger replacement - it is a structured operational stock capture layer.

**Modules:** Masters, Transactions, Reports

**Key Design Rules:**
- Only Inks and Chemicals link to ERPNext Item
- Everything else uses Stock Material Profile (manual master)
- All stock lines use the same quantity formula: `qty_in_default_uom = entry_qty x conversion_factor`
- All transaction doctypes are submittable (Draft > Submitted > Cancelled)
- Only submitted records count in reports

---

## 2. Master DocTypes

---

### 2.1 Stock Category

**Purpose:** Classify stock into major operational groups.
**Naming:** Field-based (`stock_category_name`)
**Submittable:** No
**Quick Entry:** Yes

#### Fields

| # | Field Name | Field Type | Required | Default | Read Only | Notes |
|---|-----------|-----------|----------|---------|-----------|-------|
| 1 | stock_category_name | Data | Yes | - | No | Unique. Used as document name |
| 2 | is_item_linked | Check | No | 0 | No | Set for Ink/Chemical only |
| 3 | is_manual_only | Check | No | 0 | No | Set for non-Item categories |
| 4 | is_active | Check | No | 1 | No | Active flag |
| 5 | notes | Small Text | No | - | No | Optional notes |

#### Permissions

| Role | Read | Write | Create | Delete | Report |
|------|------|-------|--------|--------|--------|
| System Manager | Yes | Yes | Yes | Yes | Yes |
| Stock Manager | Yes | Yes | Yes | No | Yes |
| Stock User | Yes | No | No | No | Yes |

#### Server Validation
- Cannot be both Item Linked AND Manual Only at the same time

#### Default Records (created on install)
Ink (item-linked), Chemical (item-linked), Raw Material (manual), Finished Goods (manual), Core (manual), Spare (manual), Fuel (manual)

---

### 2.2 Stock Material Profile

**Purpose:** Manual material master for stock categories not yet ready in Item master. Bridge between paper-based reality and future ERP itemisation.
**Naming:** Series `SMP-.YYYY.-.#####`
**Submittable:** No
**Title Field:** material_profile_name

#### Fields

| # | Field Name | Field Type | Required | Default | Read Only | Notes |
|---|-----------|-----------|----------|---------|-----------|-------|
| 1 | naming_series | Select | Yes | SMP-.YYYY.-.##### | No | |
| 2 | material_profile_name | Data | Yes | - | No | Main display name |
| 3 | material_profile_code | Data | No | - | No | Optional human code |
| 4 | stock_category | Link > Stock Category | Yes | - | No | |
| 5 | linked_item | Link > Item | No | - | No | Future migration to ERP Item |
| 6 | is_active | Check | No | 1 | No | |
| 7 | description | Small Text | No | - | No | |
| 8 | default_uom | Link > UOM | Yes | - | No | Main UOM for this material |
| 9 | base_uom | Link > UOM | No | - | No | Optional if different |
| 10 | pack_uom | Link > UOM | No | - | No | |
| 11 | pack_size | Float | No | - | No | |
| 12 | colour | Data | No | - | No | Used for raw materials |
| 13 | gsm | Float | No | - | No | Paper weight |
| 14 | size_text | Data | No | - | No | E.g. 13x79, A5 SL BP |
| 15 | width_mm | Float | No | - | No | |
| 16 | length_mm | Float | No | - | No | |
| 17 | height_mm | Float | No | - | No | |
| 18 | country | Data | No | - | No | Origin country |
| 19 | mill | Data | No | - | No | Paper mill source |
| 20 | part_no | Data | No | - | No | For bearings/spares |
| 21 | fuel_point_type | Data | No | - | No | For fuel entries |
| 22 | minimum_level | Float | No | - | No | For low stock alerts |
| 23 | reorder_level | Float | No | - | No | |
| 24 | notes | Small Text | No | - | No | |

#### Sections (collapsible)
- Dimensions & Properties (colour, gsm, size_text, width, length, height)
- Source & Part Info (country, mill, part_no, fuel_point_type)
- Stock Levels (minimum_level, reorder_level)

#### Permissions

| Role | Read | Write | Create | Delete | Report |
|------|------|-------|--------|--------|--------|
| System Manager | Yes | Yes | Yes | Yes | Yes |
| Stock Manager | Yes | Yes | Yes | No | Yes |
| Stock User | Yes | No | No | No | Yes |

#### Server Validation
- If linked_item is set, validates that the Item exists in ERPNext

#### Search Fields
material_profile_name, stock_category, colour, gsm, size_text

---

### 2.3 Stock UOM Conversion Rule

**Purpose:** Store conversion rules for manual stock (Material Profile and Stock Category level). Item-linked stock uses ERPNext Item's built-in UOM Conversion Detail table instead.
**Naming:** Random hash
**Submittable:** No

#### Fields

| # | Field Name | Field Type | Required | Default | Read Only | Depends On | Notes |
|---|-----------|-----------|----------|---------|-----------|------------|-------|
| 1 | conversion_for | Select | Yes | - | No | - | Options: Material Profile, Stock Category |
| 2 | material_profile | Link > Stock Material Profile | Conditional | - | No | conversion_for = Material Profile | |
| 3 | stock_category | Link > Stock Category | Conditional | - | No | conversion_for = Stock Category | |
| 4 | from_uom | Link > UOM | Yes | - | No | - | |
| 5 | to_uom | Link > UOM | Yes | - | No | - | |
| 6 | conversion_factor | Float | Yes | - | No | - | Must be > 0 |
| 7 | is_active | Check | No | 1 | No | - | |
| 8 | notes | Small Text | No | - | No | - | |

#### Permissions

| Role | Read | Write | Create | Delete | Report |
|------|------|-------|--------|--------|--------|
| System Manager | Yes | Yes | Yes | Yes | Yes |
| Stock Manager | Yes | Yes | Yes | No | Yes |
| Stock User | Yes | No | No | No | Yes |

#### Server Validations
- from_uom and to_uom cannot be the same
- conversion_factor must be > 0
- Material Profile required when conversion_for = Material Profile
- Stock Category required when conversion_for = Stock Category

---

## 3. Transaction DocTypes

All transaction doctypes share:
- **Submittable:** Yes (Draft > Submitted > Cancelled)
- **Amend:** Yes (cancel and amend)
- **Header fields:** naming_series, posting_date, location, remarks
- **Child table field name:** items
- **Common quantity fields on every line:** default_uom, entry_uom, entry_qty, conversion_factor, qty_in_default_uom

**Permissions (same for all 6):**

| Role | Read | Write | Create | Submit | Cancel | Amend | Delete | Report |
|------|------|-------|--------|--------|--------|-------|--------|--------|
| System Manager | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Stock Manager | Yes | Yes | Yes | Yes | Yes | Yes | No | Yes |
| Stock User | Yes | Yes | Yes | No | No | No | No | No |

---

### 3.1 Ink Chemical Stock Entry

**Purpose:** Capture stock for inks and chemicals linked to ERP Item.
**Naming Series:** `ICSE-.YYYY.-.#####`
**Linkage:** Directly linked to ERPNext Item

#### Header Fields

| # | Field Name | Field Type | Required | Default | Notes |
|---|-----------|-----------|----------|---------|-------|
| 1 | naming_series | Select | Yes | ICSE-.YYYY.-.##### | |
| 2 | posting_date | Date | Yes | Today | |
| 3 | department | Data | No | - | |
| 4 | location | Data | Yes | - | |
| 5 | amended_from | Link > Ink Chemical Stock Entry | No | - | Read only, auto |
| 6 | items | Table > Ink Chemical Stock Entry Line | Yes | - | Child table |
| 7 | remarks | Small Text | No | - | |

#### Child Table: Ink Chemical Stock Entry Line

| # | Field Name | Field Type | Required | Default | Read Only | Notes |
|---|-----------|-----------|----------|---------|-----------|-------|
| 1 | item | Link > Item | Yes | - | No | ERPNext Item link |
| 2 | item_name | Data | No | - | Yes | Fetched from Item |
| 3 | stock_category | Link > Stock Category | No | - | No | |
| 4 | default_uom | Link > UOM | Yes | - | Yes | Pulled from Item.stock_uom |
| 5 | entry_uom | Link > UOM | Yes | - | No | User selects (filtered to Item UOMs) |
| 6 | entry_qty | Float | Yes | - | No | User enters |
| 7 | conversion_factor | Float | No | 1 | No | Auto from Item UOM table |
| 8 | qty_in_default_uom | Float | No | - | Yes | Calculated: entry_qty x factor |
| 9 | supplier | Data | No | - | No | |
| 10 | batch_no | Data | No | - | No | |
| 11 | expiry_date | Date | No | - | No | |
| 12 | notes | Small Text | No | - | No | |

#### Client Script Behaviour
- **On Item selected:** Fetches full Item doc via `frappe.client.get`. Sets item_name, default_uom (from stock_uom). Caches Item's UOM table. Filters Entry UOM dropdown to only show UOMs configured on that Item.
- **On Entry UOM changed:** Looks up conversion_factor from cached Item UOM table. If entry_uom = default_uom, sets factor = 1. If UOM not found on Item, shows warning message.
- **On Entry Qty changed:** Calculates qty_in_default_uom = entry_qty x conversion_factor
- **On Conversion Factor changed:** Recalculates qty_in_default_uom

#### Server Validations
- Item is mandatory on every line
- default_uom, entry_uom, entry_qty mandatory
- entry_qty cannot be negative
- If entry_uom != default_uom and no conversion factor: looks up ERPNext Item UOM table, then throws error if not found
- qty_in_default_uom auto-calculated before save
- At least one child row required

---

### 3.2 Raw Material Stock Entry

**Purpose:** Capture raw material stock - paper, reels, boards, chipboard, duplex, FBB, bond, cover board etc.
**Naming Series:** `RMSE-.YYYY.-.#####`
**Linkage:** Manual via Stock Material Profile

#### Header Fields

| # | Field Name | Field Type | Required | Default | Notes |
|---|-----------|-----------|----------|---------|-------|
| 1 | naming_series | Select | Yes | RMSE-.YYYY.-.##### | |
| 2 | posting_date | Date | Yes | Today | |
| 3 | warehouse_text | Data | Yes | - | Go Down / Warehouse name |
| 4 | location | Data | No | - | |
| 5 | amended_from | Link > Raw Material Stock Entry | No | - | Read only |
| 6 | items | Table > Raw Material Stock Entry Line | Yes | - | |
| 7 | remarks | Small Text | No | - | |

#### Child Table: Raw Material Stock Entry Line

| # | Field Name | Field Type | Required | Default | Read Only | Notes |
|---|-----------|-----------|----------|---------|-----------|-------|
| 1 | material_profile | Link > Stock Material Profile | No | - | No | Preferred |
| 2 | manual_description | Data | No | - | No | Fallback if no profile |
| 3 | stock_category | Link > Stock Category | No | - | No | |
| 4 | colour | Data | No | - | No | Auto from profile |
| 5 | gsm | Float | No | - | No | Auto from profile |
| 6 | width_mm | Float | No | - | No | Auto from profile |
| 7 | length_mm | Float | No | - | No | Auto from profile |
| 8 | size_text | Data | No | - | No | Auto from profile |
| 9 | country | Data | No | - | No | Auto from profile |
| 10 | mill | Data | No | - | No | Auto from profile |
| 11 | default_uom | Link > UOM | Yes | - | No | Auto from profile |
| 12 | entry_uom | Link > UOM | Yes | - | No | |
| 13 | entry_qty | Float | Yes | - | No | |
| 14 | conversion_factor | Float | No | 1 | No | |
| 15 | qty_in_default_uom | Float | No | - | Yes | Calculated |
| 16 | secondary_qty | Float | No | - | No | Optional secondary measure |
| 17 | secondary_uom | Link > UOM | No | - | No | |
| 18 | notes | Small Text | No | - | No | |

#### Client Script Behaviour
- **On Material Profile selected:** Fetches default_uom, stock_category, colour, gsm, size_text, width_mm, length_mm, country, mill from the profile
- **On Entry UOM changed:** Calls `vcl_stock_control.stock_utils.fetch_conversion_factor` with material_profile and stock_category
- **On Entry Qty / Conversion Factor changed:** Calculates qty_in_default_uom

#### Server Validations
- Either material_profile OR manual_description must be filled per line
- Standard quantity validations (UOM, qty, conversion factor)

---

### 3.3 Finished Goods Stock Entry

**Purpose:** Capture finished goods stock snapshots - books, exercise books, pads etc.
**Naming Series:** `FGSE-.YYYY.-.#####`
**Linkage:** Manual via Stock Material Profile

#### Header Fields

| # | Field Name | Field Type | Required | Default | Notes |
|---|-----------|-----------|----------|---------|-------|
| 1 | naming_series | Select | Yes | FGSE-.YYYY.-.##### | |
| 2 | posting_date | Date | Yes | Today | |
| 3 | location | Data | Yes | - | |
| 4 | amended_from | Link > Finished Goods Stock Entry | No | - | Read only |
| 5 | items | Table > Finished Goods Stock Entry Line | Yes | - | |
| 6 | remarks | Small Text | No | - | |

#### Child Table: Finished Goods Stock Entry Line

| # | Field Name | Field Type | Required | Default | Read Only | Notes |
|---|-----------|-----------|----------|---------|-----------|-------|
| 1 | material_profile | Link > Stock Material Profile | No | - | No | |
| 2 | manual_description | Data | No | - | No | |
| 3 | size_text | Data | No | - | No | E.g. A5, A4 |
| 4 | pages | Int | No | - | No | |
| 5 | ruling_type | Data | No | - | No | Single Line, Square, Ruled |
| 6 | print_type | Data | No | - | No | Plain, Printed, NCR |
| 7 | bundle_qty | Float | No | - | No | Number of bundles |
| 8 | pieces_per_bundle | Float | No | 25 | No | Default 25 |
| 9 | carton_qty | Float | No | - | No | Number of cartons |
| 10 | pieces_per_carton | Float | No | - | No | |
| 11 | calculated_pieces | Float | No | - | Yes | Auto: (bundles x pcs) + (cartons x pcs) |
| 12 | default_uom | Link > UOM | Yes | - | No | Usually Pcs |
| 13 | entry_uom | Link > UOM | Yes | - | No | |
| 14 | entry_qty | Float | Yes | - | No | Manual or auto from helpers |
| 15 | conversion_factor | Float | No | 1 | No | |
| 16 | qty_in_default_uom | Float | No | - | Yes | Calculated |
| 17 | notes | Small Text | No | - | No | |

#### Client Script Behaviour
- **On Material Profile selected:** Fetches default_uom, size_text
- **On bundle_qty / pieces_per_bundle / carton_qty / pieces_per_carton changed:** Calculates calculated_pieces. If entry_qty is 0, auto-fills entry_qty with calculated_pieces and sets entry_uom = default_uom, factor = 1
- **On Entry UOM / Qty / Factor changed:** Standard qty_in_default_uom calculation

#### Server Validations
- Either material_profile OR manual_description required
- Before validation: calculates pieces from bundle/carton helpers. If entry_qty is 0 and calculated pieces > 0, auto-sets entry_qty
- Standard quantity validations

---

### 3.4 Core Stock Entry

**Purpose:** Track stock position for cores.
**Naming Series:** `CSE-.YYYY.-.#####`
**Linkage:** Manual via Stock Material Profile

#### Header Fields

| # | Field Name | Field Type | Required | Default | Notes |
|---|-----------|-----------|----------|---------|-------|
| 1 | naming_series | Select | Yes | CSE-.YYYY.-.##### | |
| 2 | posting_date | Date | Yes | Today | |
| 3 | location | Data | Yes | - | |
| 4 | amended_from | Link > Core Stock Entry | No | - | Read only |
| 5 | items | Table > Core Stock Entry Line | Yes | - | |
| 6 | remarks | Small Text | No | - | |

#### Child Table: Core Stock Entry Line

| # | Field Name | Field Type | Required | Default | Read Only | Notes |
|---|-----------|-----------|----------|---------|-----------|-------|
| 1 | material_profile | Link > Stock Material Profile | No | - | No | |
| 2 | manual_description | Data | No | - | No | |
| 3 | size_text | Data | No | - | No | Important for core size (13x79) |
| 4 | default_uom | Link > UOM | Yes | - | No | Usually Nos |
| 5 | entry_uom | Link > UOM | Yes | - | No | |
| 6 | entry_qty | Float | Yes | - | No | |
| 7 | conversion_factor | Float | No | 1 | No | |
| 8 | qty_in_default_uom | Float | No | - | Yes | Calculated |
| 9 | status_note | Data | No | - | No | E.g. Good, Some damaged |
| 10 | notes | Small Text | No | - | No | |

#### Client Script Behaviour
- **On Material Profile selected:** Fetches default_uom, size_text
- **On Entry UOM / Qty / Factor changed:** Standard calculation

#### Server Validations
- Either material_profile OR manual_description required
- Standard quantity validations

---

### 3.5 Spare Stock Entry

**Purpose:** Track manual spare stock - bearings, belts, blades, parts.
**Naming Series:** `SSE-.YYYY.-.#####`
**Linkage:** Manual via Stock Material Profile

#### Header Fields

| # | Field Name | Field Type | Required | Default | Notes |
|---|-----------|-----------|----------|---------|-------|
| 1 | naming_series | Select | Yes | SSE-.YYYY.-.##### | |
| 2 | posting_date | Date | Yes | Today | |
| 3 | location | Data | Yes | - | |
| 4 | department | Data | No | - | |
| 5 | amended_from | Link > Spare Stock Entry | No | - | Read only |
| 6 | items | Table > Spare Stock Entry Line | Yes | - | |
| 7 | remarks | Small Text | No | - | |

#### Child Table: Spare Stock Entry Line

| # | Field Name | Field Type | Required | Default | Read Only | Notes |
|---|-----------|-----------|----------|---------|-----------|-------|
| 1 | material_profile | Link > Stock Material Profile | No | - | No | |
| 2 | part_no | Data | No | - | No | Auto from profile |
| 3 | manual_description | Data | No | - | No | |
| 4 | default_uom | Link > UOM | Yes | - | No | Usually Nos |
| 5 | entry_uom | Link > UOM | Yes | - | No | |
| 6 | entry_qty | Float | Yes | - | No | |
| 7 | conversion_factor | Float | No | 1 | No | Usually 1 |
| 8 | qty_in_default_uom | Float | No | - | Yes | Calculated |
| 9 | minimum_level | Float | No | - | No | Auto from profile |
| 10 | reorder_flag | Check | No | 0 | Yes | Auto: 1 if qty < minimum_level |
| 11 | notes | Small Text | No | - | No | |

#### Client Script Behaviour
- **On Material Profile selected:** Fetches default_uom, part_no, minimum_level
- **On Entry Qty / Factor changed:** Calculates qty_in_default_uom. Auto-sets reorder_flag = 1 if qty < minimum_level

#### Server Validations
- Either material_profile OR manual_description required
- Standard quantity validations
- After validation: sets reorder_flag = 1 if qty_in_default_uom < minimum_level

---

### 3.6 Fuel Stock Entry

**Purpose:** Capture daily or periodic fuel balances.
**Naming Series:** `FSE-.YYYY.-.#####`
**Linkage:** Manual

#### Header Fields

| # | Field Name | Field Type | Required | Default | Notes |
|---|-----------|-----------|----------|---------|-------|
| 1 | naming_series | Select | Yes | FSE-.YYYY.-.##### | |
| 2 | posting_date | Date | Yes | Today | |
| 3 | location | Data | Yes | - | |
| 4 | amended_from | Link > Fuel Stock Entry | No | - | Read only |
| 5 | items | Table > Fuel Stock Entry Line | Yes | - | |
| 6 | remarks | Small Text | No | - | |

#### Child Table: Fuel Stock Entry Line

| # | Field Name | Field Type | Required | Default | Read Only | Notes |
|---|-----------|-----------|----------|---------|-----------|-------|
| 1 | fuel_point | Data | No | - | No | E.g. Fuel Tank, Generator, Vimal Bahati |
| 2 | material_profile | Link > Stock Material Profile | No | - | No | |
| 3 | manual_description | Data | No | - | No | |
| 4 | default_uom | Link > UOM | Yes | - | No | Usually Litre |
| 5 | entry_uom | Link > UOM | Yes | - | No | |
| 6 | entry_qty | Float | Yes | - | No | |
| 7 | conversion_factor | Float | No | 1 | No | |
| 8 | qty_in_default_uom | Float | No | - | Yes | Calculated |
| 9 | notes | Small Text | No | - | No | |

#### Client Script Behaviour
- **On Material Profile selected:** Fetches default_uom
- **On Entry UOM / Qty / Factor changed:** Standard calculation

#### Server Validations
- At least one of fuel_point, material_profile, or manual_description required per line
- Standard quantity validations

---

## 4. Shared Conversion Engine (stock_utils.py)

**File:** `vcl_stock_control/stock_utils.py`

### Conversion Factor Lookup Priority

For **Item-linked entries** (Ink/Chemical):
1. ERPNext Item's built-in UOM Conversion Detail table (`_get_item_uom_conversion`)
   - Case 1: entry_uom in table, to_uom is stock_uom -> direct factor
   - Case 2: from_uom is stock_uom, to_uom in table -> inverse (1/factor)
   - Case 3: Neither is stock_uom -> cross-convert via stock_uom (from_factor / to_factor)

For **manual entries** (all other doctypes):
1. Stock UOM Conversion Rule at Material Profile level
2. Stock UOM Conversion Rule at Stock Category level

### Functions

| Function | Purpose | Whitelisted |
|----------|---------|-------------|
| `_get_item_uom_conversion(item, from_uom, to_uom)` | Reads ERPNext Item UOM table | No (internal) |
| `get_conversion_factor(from_uom, to_uom, item, material_profile, stock_category)` | Main lookup with priority chain | No (internal) |
| `calculate_qty_in_default_uom(entry_qty, conversion_factor)` | Simple multiplication | No (internal) |
| `validate_stock_lines(doc, items_field)` | Validates all lines on a stock entry | No (internal) |
| `validate_material_source(row, require_item)` | Checks item/profile/description exists | No (internal) |
| `fetch_conversion_factor(from_uom, to_uom, item, material_profile, stock_category)` | Client-callable API | Yes |

### Common Line Validation (validate_stock_lines)

Applied to all 6 transaction doctypes on validate:
1. At least one child row required
2. Each line must have: default_uom, entry_uom, entry_qty
3. entry_qty cannot be negative
4. If entry_uom != default_uom and no conversion_factor: auto-lookup, throw if not found
5. If entry_uom == default_uom: set conversion_factor = 1
6. Calculate qty_in_default_uom = entry_qty x conversion_factor
7. qty_in_default_uom cannot be negative

---

## 5. Reports

All reports are Script Reports. All read submitted entries only (docstatus = 1).

---

### 5.1 Latest Stock Snapshot

**Purpose:** Show latest submitted stock balance per material across all categories.

#### Filters

| Field Name | Label | Type | Default |
|-----------|-------|------|---------|
| posting_date | As On Date | Date | Today |
| stock_category | Stock Category | Link > Stock Category | - |
| location | Location | Data | - |

#### Output Columns

| Column | Type | Width |
|--------|------|-------|
| Category | Data | 120 |
| Source Type | Data | 100 |
| Material / Item | Data | 250 |
| Description | Data | 200 |
| Default UOM | Data | 100 |
| Qty in Default UOM | Float | 140 |
| Posting Date | Date | 110 |
| Entry Reference | Data | 180 |
| Location | Data | 120 |

#### Logic
Queries all 6 transaction doctypes. For each, joins parent + child, filters by docstatus=1 and optional filters. Groups by material, takes latest entry per material.

---

### 5.2 Stock History

**Purpose:** Show balance history over time by date range.

#### Filters

| Field Name | Label | Type | Default |
|-----------|-------|------|---------|
| from_date | From Date | Date | 1 month ago |
| to_date | To Date | Date | Today |
| stock_category | Stock Category | Link > Stock Category | - |
| location | Location | Data | - |

#### Output Columns

| Column | Type | Width |
|--------|------|-------|
| Posting Date | Date | 110 |
| Entry Reference | Data | 180 |
| Category | Data | 120 |
| Material / Item | Data | 250 |
| Default UOM | Data | 100 |
| Qty in Default UOM | Float | 140 |
| Location | Data | 120 |

#### Logic
Queries all 6 transaction doctypes within date range. Returns all submitted entries sorted by posting_date ascending.

---

### 5.3 Low Stock

**Purpose:** Show materials below minimum/reorder level.

#### Filters
None.

#### Output Columns

| Column | Type | Width |
|--------|------|-------|
| Category | Data | 120 |
| Material / Item | Data | 250 |
| Default UOM | Data | 100 |
| Latest Qty | Float | 120 |
| Minimum Level | Float | 120 |
| Reorder Flag | Check | 100 |
| Entry Reference | Data | 180 |
| Posting Date | Date | 110 |

#### Logic
1. Checks Spare Stock Entry lines where qty_in_default_uom < minimum_level
2. Checks Stock Material Profiles with minimum_level set, then finds latest entry across Raw Material, Finished Goods, Core, Fuel doctypes and flags if below level

---

### 5.4 Category Summary

**Purpose:** Summarise stock totals by category and UOM.

#### Filters
None.

#### Output Columns

| Column | Type | Width |
|--------|------|-------|
| Category | Data | 150 |
| Default UOM | Data | 100 |
| Material Count | Int | 120 |
| Total Qty in Default UOM | Float | 180 |

#### Logic
Queries all 6 doctypes. For each category, takes latest entry per material, then sums by (category, UOM). Does not sum unlike UOMs together.

---

### 5.5 Stock Variance

**Purpose:** Compare stock between two dates to spot unusual drops, missing items, counting errors.

#### Filters

| Field Name | Label | Type | Required | Default |
|-----------|-------|------|----------|---------|
| previous_date | Previous Date | Date | Yes | 1 month ago |
| current_date | Current Date | Date | Yes | Today |
| stock_category | Stock Category | Link > Stock Category | No | - |

#### Output Columns

| Column | Type | Width |
|--------|------|-------|
| Category | Data | 120 |
| Material / Item | Data | 250 |
| Default UOM | Data | 100 |
| Previous Qty | Float | 120 |
| Previous Date | Date | 110 |
| Current Qty | Float | 120 |
| Current Date | Date | 110 |
| Variance | Float | 120 |
| Variance % | Percent | 110 |

#### Logic
Takes snapshot at previous_date and current_date. For each material, gets latest submitted entry on or before each date. Calculates variance = current - previous, variance% = variance/previous x 100.

---

## 6. Installation & Configuration

### hooks.py
- **required_apps:** frappe, erpnext
- **after_install:** Creates default Stock Category records
- **fixtures:** Stock Category (active records)

### install.py
Creates 7 default Stock Category records on install:
- Ink (item-linked)
- Chemical (item-linked)
- Raw Material (manual)
- Finished Goods (manual)
- Core (manual)
- Spare (manual)
- Fuel (manual)

---

## 7. Naming Series Summary

| DocType | Series | Example |
|---------|--------|---------|
| Stock Material Profile | SMP-.YYYY.-.##### | SMP-2026-00001 |
| Ink Chemical Stock Entry | ICSE-.YYYY.-.##### | ICSE-2026-00001 |
| Raw Material Stock Entry | RMSE-.YYYY.-.##### | RMSE-2026-00001 |
| Finished Goods Stock Entry | FGSE-.YYYY.-.##### | FGSE-2026-00001 |
| Core Stock Entry | CSE-.YYYY.-.##### | CSE-2026-00001 |
| Spare Stock Entry | SSE-.YYYY.-.##### | SSE-2026-00001 |
| Fuel Stock Entry | FSE-.YYYY.-.##### | FSE-2026-00001 |

Stock Category uses field-based naming (stock_category_name).
Stock UOM Conversion Rule uses random hash.

---

## 8. Permissions Summary

| Role | Masters (R/W/C) | Transactions (R/W/C/Submit/Cancel) |
|------|----------------|-----------------------------------|
| System Manager | Read, Write, Create, Delete | Read, Write, Create, Submit, Cancel, Amend, Delete |
| Stock Manager | Read, Write, Create | Read, Write, Create, Submit, Cancel, Amend |
| Stock User | Read only | Read, Write, Create |

Stock Users can create drafts but cannot submit or cancel.

---

## 9. Import Templates

Located in `vcl_stock_control/import_templates/`. Import in this order:

| # | File | DocType | Notes |
|---|------|---------|-------|
| 1 | 01_stock_category.csv | Stock Category | Do first |
| 2 | 02_stock_material_profile.csv | Stock Material Profile | Needs categories |
| 3 | 03_stock_uom_conversion_rule.csv | Stock UOM Conversion Rule | Needs profiles |
| 4 | 04_ink_chemical_stock_entry.csv | Ink Chemical Stock Entry | Needs Items in ERPNext |
| 5 | 05_raw_material_stock_entry.csv | Raw Material Stock Entry | Needs profiles |
| 6 | 06_finished_goods_stock_entry.csv | Finished Goods Stock Entry | Needs profiles |
| 7 | 07_core_stock_entry.csv | Core Stock Entry | Needs profiles |
| 8 | 08_spare_stock_entry.csv | Spare Stock Entry | Needs profiles |
| 9 | 09_fuel_stock_entry.csv | Fuel Stock Entry | Needs profiles |

Transaction CSVs use `~items:fieldname` prefix for child table columns (Frappe Data Import format).

---

## 10. File Structure

```
vcl_stock_control/
  setup.py
  requirements.txt
  pyproject.toml
  VCL_STOCK_CONTROL_REFERENCE.md
  vcl_stock_control/
    __init__.py
    hooks.py
    install.py
    modules.txt
    patches.txt
    stock_utils.py
    masters/
      doctype/
        stock_category/
        stock_material_profile/
        stock_uom_conversion_rule/
    transactions/
      doctype/
        ink_chemical_stock_entry/       (+ _line child)
        raw_material_stock_entry/       (+ _line child)
        finished_goods_stock_entry/     (+ _line child)
        core_stock_entry/               (+ _line child)
        spare_stock_entry/              (+ _line child)
        fuel_stock_entry/               (+ _line child)
    reports/
      latest_stock_snapshot/
      stock_history/
      low_stock/
      category_summary/
      stock_variance/
    import_templates/
      01-09 CSV files
```

---

*End of Reference Document*
