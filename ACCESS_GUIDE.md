# VCL Stock Control - Access Guide

## Accessing the App

### Desk (Backend)
All DocTypes are accessible via the standard ERPNext Desk interface.

| What | URL Path | Notes |
|------|----------|-------|
| Ink Chemical Stock Entry | `/app/ink-chemical-stock-entry` | List and form view |
| Raw Material Stock Entry | `/app/raw-material-stock-entry` | List and form view |
| Finished Goods Stock Entry | `/app/finished-goods-stock-entry` | List and form view |
| Core Stock Entry | `/app/core-stock-entry` | List and form view |
| Spare Stock Entry | `/app/spare-stock-entry` | List and form view |
| Fuel Stock Entry | `/app/fuel-stock-entry` | List and form view |
| Stock Category | `/app/stock-category` | Master setup |
| Stock Material Profile | `/app/stock-material-profile` | Manual material master |
| Stock UOM Conversion Rule | `/app/stock-uom-conversion-rule` | Conversion rules |

### Website Pages (Operator UI)
| Page | URL | Purpose |
|------|-----|---------|
| Ink Chemical Entry | `/ink-chemical-entry` | Clean operator entry form |

### Reports
Access via Desk sidebar or direct URL:

| Report | How to Access |
|--------|---------------|
| Latest Stock Snapshot | Search > Latest Stock Snapshot |
| Stock History | Search > Stock History |
| Low Stock | Search > Low Stock |
| Category Summary | Search > Category Summary |
| Stock Variance | Search > Stock Variance |

## User Roles

### Stock User
- Can create and save draft entries (all 6 transaction types)
- Can view all stock data and reports
- Can use the website entry page (saves drafts only)
- Cannot submit, cancel, or amend entries

### Stock Manager
- Everything Stock User can do, plus:
- Can submit entries
- Can cancel entries
- Can amend entries
- Can create/edit master records (Categories, Profiles, Conversion Rules)
- Can use website entry page with submit

### System Manager
- Full access to everything
- Can delete records
- Can manage permissions

## Setting Up Users

1. Go to **Setup > User** and create/edit the user
2. Under **Roles**, add one of:
   - `Stock User` (for operators)
   - `Stock Manager` (for supervisors)
3. Ensure they also have `Website User` role for website page access
4. Save

## First-Time Setup

### Step 1: Stock Categories
Already created on install. Verify at `/app/stock-category`:
- Ink, Chemical (item-linked)
- Raw Material, Finished Goods, Core, Spare, Fuel (manual)

### Step 2: Stock Material Profiles
Create profiles for manual stock at `/app/stock-material-profile`.
Or import via Data Import using `import_templates/02_stock_material_profile.csv`.

### Step 3: UOM Conversion Rules
Set up common conversions at `/app/stock-uom-conversion-rule`.
E.g. Bundle > Pcs = 25, Carton > Pcs = 204.

### Step 4: Start Entering Stock
- For inks/chemicals: Use `/ink-chemical-entry` (website) or Desk form
- For other categories: Use Desk forms

## Import Templates
CSV templates are included in `vcl_stock_control/import_templates/`:

| # | File | Import Into |
|---|------|-------------|
| 1 | 01_stock_category.csv | Stock Category |
| 2 | 02_stock_material_profile.csv | Stock Material Profile |
| 3 | 03_stock_uom_conversion_rule.csv | Stock UOM Conversion Rule |
| 4 | 04_ink_chemical_stock_entry.csv | Ink Chemical Stock Entry |
| 5 | 05_raw_material_stock_entry.csv | Raw Material Stock Entry |
| 6 | 06_finished_goods_stock_entry.csv | Finished Goods Stock Entry |
| 7 | 07_core_stock_entry.csv | Core Stock Entry |
| 8 | 08_spare_stock_entry.csv | Spare Stock Entry |
| 9 | 09_fuel_stock_entry.csv | Fuel Stock Entry |

Import using: **Setup > Data Import > New** > Select DocType > Upload CSV.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Page shows "Please log in" | User must be logged in to access website pages |
| Cannot submit entry | User needs Stock Manager role |
| Conversion factor not loading | Check Item has UOM conversions set up in Item master |
| Website page not found | Run `bench build` and `bench restart` after app install |
| Reports show no data | Only submitted entries (docstatus=1) appear in reports |
