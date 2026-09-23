# TM Update Products

Updates the customer-facing product names in bulk from an Excel file, matched on the JD Edwards item number.

## Business Purpose
Marketing maintains the product names customers read on the web shop in a
spreadsheet, for hundreds of products at a time. Typing them into Odoo one by
one is slow and error-prone. This module imports the spreadsheet: each row is
matched to a product by its JD Edwards item number, and the customer-facing name
is updated. It reports how many products were updated and which item numbers were
not found, so the file can be corrected.

## Key Features
- Bulk update of the customer-facing product name from an Excel file.
- Products matched on their JDE item number, so no Odoo ids are needed in the file.
- A summary of what was updated, and which item numbers are unknown.

## How It Works (User Flow)
1. Prepare an Excel file with the columns **jde_product_id** and **New Description**.
2. Go to **Inventory → Configuration → Update Products**, upload the file and click **Update Products**.
3. Odoo reports how many products were updated and lists the item numbers it could not find.

## Dependencies
| Module | Why it is needed |
|--------|------------------|
| product, stock | Products and the Inventory configuration menu. |
| tm_website_product_name | The customer-facing product name that is updated. |
| product_create_api | The JDE item number used to match the rows. |

## Configuration
No configuration required. The menu is available to administrators.

## Technical Notes
- **Model:** the `product.update.wizard` transient model reads the file with `openpyxl` (a standard Odoo dependency) and writes `product.template.actual_name`.
- **Security:** the wizard is limited to administrators (`base.group_system`); in 17.0 every internal user could run it.
- **Migrated from 17.0 to 19.0:** no API changes were needed.
- **Bug fixed during migration:** in 17.0 the `openpyxl` import was commented out, so every upload failed with "Error reading file: name 'openpyxl' is not defined"; the wizard never worked. The import is restored, real errors are no longer swallowed as file errors, and the result message now reports unknown item numbers.
- **Original module** by Acespritech Solutions Pvt. Ltd.; Odoo 19.0 migration by Plennix Technologies.

---
Original module by **Acespritech Solutions Pvt. Ltd.** — Odoo 19.0 migration developed and maintained by **Plennix Technologies** — https://www.plennix.com
