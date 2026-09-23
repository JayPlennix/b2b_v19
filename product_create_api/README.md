# Product API (JDE)

Lets JD Edwards (JDE) create and update products, stock, lots, packagings and customer price lists in Odoo automatically through an API.

## Business Purpose
Transmed's product catalogue, stock and customer prices are maintained in JD
Edwards. Without this module the eCommerce and inventory teams would have to
re-create every item in Odoo, keep stock quantities in step by hand, and set up
each customer's special prices twice. This module lets JDE send new and changed
items, stock levels and customer price lists straight to Odoo. The B2B shop
therefore always shows the current catalogue, availability and each customer's
own prices. In Saudi Arabia (KSA), stock is recorded per lot with its expiry
date, so short-dated goods can be tracked.

## Key Features
- New items created in JDE appear in Odoo automatically, with category, website category, brand, unit, taxes and country of origin.
- Changes in JDE (description, price, cost, category, availability settings, active/inactive) update the existing product.
- Stock quantities sent by JDE are recorded in the matching Odoo warehouse location.
- For KSA, stock is recorded by lot with its expiry date.
- JDE packages (for example BOX of 12, or CARTON of 10 boxes) become product packagings that can be chosen when selling.
- Customer-specific price lists with dated fixed prices are created or updated, and assigned to the customer and their contacts.
- Missing product categories and website categories are created automatically under the right parent.
- JDE product details (family, item type, brand, supplier, storage, temperature) are shown on a **Transmed-b2b** tab on the product.

## How It Works (User Flow)
1. JDE logs in to Odoo with a dedicated user.
2. JDE sends a batch of items. Items that do not exist yet in Odoo (matched on the JDE item number) are created. For items that already exist, only the stock quantity (or, for KSA, the lot) is updated.
3. JDE sends item changes. Each existing item is updated, including its packagings and, when provided, its stock quantity or lot and expiry date.
4. JDE sends customer price lists. Odoo creates the price list if needed, adds or updates the dated prices per item, and assigns the price list to the customer and their contacts.
5. The eCommerce team sees the result in **Website → eCommerce → Products** and on the **Transmed-b2b** product tab.

## Dependencies
| Module | Why it is needed |
|--------|------------------|
| base, web | Core framework and the web session used by JDE. |
| crm | Kept from the original module for the sales setup it expects. |
| account | Customer taxes on products. |
| stock | Stock locations, quantities and lots. |
| stock_delivery | Country of origin on products. |
| product_expiry | Expiry dates on KSA lots. |
| website, website_sale | Website categories, publishing and website price lists. |
| website_sale_stock | Availability display and out-of-stock ordering settings. |
| customer_create_api | Company **Source** code and the JDE customer number used to assign price lists. |
| custom_saleorder_management | Product brands. |

## Configuration
1. Set the **Source** code on each company (provided by `customer_create_api`).
2. Make sure the stock locations JDE sends exist in Odoo with the same full name (for example `WH/Stock`) for the right company.
3. Make sure the units JDE sends (for example `Units`, `kg`) exist in Odoo with the same name.
4. Enable **Units of Measure & Packagings** (Inventory or Sales settings) so packagings can be chosen on sales orders.
5. Give the JDE integration user rights to create products, pricelists and stock.

## Technical Notes
- **Endpoints** (`type='jsonrpc'`, `auth='user'`): `POST /api/product` and `PUT /api/product` take a batch in `data[]` and match on `jde_product_id`, including archived products. `POST /api/product-pricelist` takes a batch in `data[]` and matches partners on `b2b_customer_id`.
- **Inherited models:**
  - `product.template` gets the JDE fields, and `categ_id` is kept required with the first category as default.
  - `product.category` gets `company_id`.
  - `product.pricelist` gets `F4101_timestamp`, `F4106_timestamp` and `timestamp_jde`.
  - `uom.uom` gets `jde_package_name`.
- **Packagings:** Odoo 19 removed `product.packaging`. Each JDE package becomes a `uom.uom` with `relative_uom_id` set to the product's unit and `relative_factor` set to the package quantity. A package with a secondary package is created relative to that package's unit instead. The unit is linked in `product.template.uom_ids`, and an existing unit with the same package name, reference and factor is reused. On every sync the product's whole JDE packaging chain is rebuilt, so packages defined on top of a changed package follow it, as the computed quantity did in 17.0 (BOX 12 → 6 makes CARTON = 10 × BOX go from 120 to 60). Packages not in the payload are kept. The JDE `package_type` is no longer stored, because v19 packaging units have no package type.
- **Soft dependency:** `res.company.is_ksa` / `is_jordan` come from `custom_website`, which depends on this module. They are read only when the field exists; otherwise the company is treated as non-KSA.
- **Views:** a Transmed-b2b page on the product form, the JDE product name under the product options, company on product categories, and the JDE timestamps on the pricelist form.
- **Security:** no new models, so no access rules. API calls run with the rights of the authenticated JDE user.
- **Migrated from 17.0 to 19.0:**
  - Routes changed from `type='json'` to `type='jsonrpc'`.
  - `detailed_type='product'` became `type='consu'` + `is_storable=True`, and `uom_po_id` was removed (purchase unit no longer exists).
  - `product.packaging` and its views were replaced by UoM packagings (see above).
  - The pricelist fields moved next to the pricelist settings, because the `pricelist_config` page no longer exists.
  - `categ_id` is now extended instead of redefined, so core attributes such as tracking are kept.
  - `Command` helpers replaced tuple commands.
  - Previously implicit dependencies are now declared: `product_expiry`, `website_sale_stock`, `stock_delivery`, `customer_create_api`. The unused security CSV was removed.
- **Bugs fixed during migration** (all present in 17.0):
  - Receiving stock for an existing KSA lot crashed (`lot` referenced before assignment). The existing lot is now reused.
  - A newly created website category or product category was passed as a record instead of an id, which broke product creation when the category did not exist yet.
  - Product create/update and pricelist creation now run inside a database savepoint, so a failed item no longer leaves half-created data behind.

---
Developed and maintained by **Plennix Technologies** — https://www.plennix.com
