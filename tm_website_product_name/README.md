# Website Product Name Edit

Shows a customer-facing product name on the web shop, and tells customers what they already have in their cart per unit.

## Business Purpose
Products are named for internal and JD Edwards use, which is not what customers
should read in the shop. This module adds a separate customer-facing name, used
on the product page and in the shop whenever it is filled in, while the internal
name stays untouched for staff and for JDE. On the product page it also tells
customers what they already have in their cart for that product, split per unit,
so they do not order the same goods twice.

## Key Features
- Customer-facing product name, shown on the product page and the shop tiles.
- The internal name stays unchanged for staff, reports and JDE.
- "You already added ... in your cart" split per unit of measure (for example 2 boxes and 5 units).

## How It Works (User Flow)
1. A manager fills in **Actual Name** on the product (visible to administrators).
2. Customers see that name in the shop and on the product page; staff keep seeing the internal name everywhere else.
3. When a customer opens a product that is already in their cart, the stock message lists the quantity per unit.

## Dependencies
| Module | Why it is needed |
|--------|------------------|
| product, website_sale | Products and the shop. |
| website_sale_stock | The availability message on the product page. |

## Configuration
Fill in **Actual Name** on the products that need a different name in the shop. Products without one keep their normal name. The name can also be imported in bulk with the TM Update Products module.

## Technical Notes
- **Model:** `product.template.actual_name`; `product.product._get_cart_lines()` groups the customer's cart lines of that product per unit, and `_get_additionnal_combination_info` adds them to the product data as `cart_lines`.
- **Templates:** the product page title (`website_sale.product_title`) and the shop tile title use the customer-facing name when set; the stock availability template is extended to list the cart quantities per unit.
- **Migrated from 17.0 to 19.0:** `_get_additionnal_combination_info` gained a `uom` argument; `website.sale_get_order()` became `request.cart`; `product_uom` became `product_uom_id`; the v17 JavaScript patch of the availability widget is no longer needed, since the v19 template is extended directly; the product form anchor moved from `detailed_type` to `type`.

---
Developed and maintained by **Plennix Technologies** — https://www.plennix.com
