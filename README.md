# VCL Stock Control

Custom Frappe / ERPNext v16 app for factory stock capture and visibility.

## What It Does

Digitises manual stock sheets for:
- **Inks & Chemicals** (linked to ERPNext Item)
- **Raw Materials** (paper, reels, boards, FBB, duplex, bond)
- **Finished Goods** (books, exercise books, pads)
- **Cores** (paper cores)
- **Spares** (bearings, belts, blades)
- **Fuel** (diesel tanks, generators)

This is a stock-capture control layer, not a full ERP stock ledger replacement.

## Architecture

### Masters (3 DocTypes)
| DocType | Purpose |
|---------|---------|
| Stock Category | Classifies stock groups (Ink, Chemical, Raw Material, etc.) |
| Stock Material Profile | Manual material master for non-Item stock |
| Stock UOM Conversion Rule | Conversion rules for Material Profile and Stock Category |

### Transactions (6 Submittable DocTypes)
| DocType | Series | Linkage |
|---------|--------|---------|
| Ink Chemical Stock Entry | ICSE-.YYYY.-.##### | ERPNext Item |
| Raw Material Stock Entry | RMSE-.YYYY.-.##### | Stock Material Profile |
| Finished Goods Stock Entry | FGSE-.YYYY.-.##### | Stock Material Profile |
| Core Stock Entry | CSE-.YYYY.-.##### | Stock Material Profile |
| Spare Stock Entry | SSE-.YYYY.-.##### | Stock Material Profile |
| Fuel Stock Entry | FSE-.YYYY.-.##### | Stock Material Profile |

### Reports (5 Script Reports)
- Latest Stock Snapshot
- Stock History
- Low Stock
- Category Summary
- Stock Variance

### Website Pages
- `/ink-chemical-entry` - Operator-facing entry page for inks and chemicals

## Key Design Rules
1. Only Inks and Chemicals link to ERPNext Item
2. Everything else uses Stock Material Profile
3. All stock lines: `qty_in_default_uom = entry_qty x conversion_factor`
4. All transactions are submittable (Draft > Submitted > Cancelled)
5. Only submitted records count in reports

## Installation

```bash
bench get-app vcl_stock_control
bench install-app vcl_stock_control
bench build
bench restart
```

## Dependencies
- Frappe Framework
- ERPNext

## Detailed Reference
See [VCL_STOCK_CONTROL_REFERENCE.md](VCL_STOCK_CONTROL_REFERENCE.md) for complete field-by-field documentation of every DocType, report, validation, and client script.

## License
MIT
