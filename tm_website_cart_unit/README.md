# Website Cart Unit

Shows the unit of measure of every line in the web shop cart.

## Business Purpose
B2B customers order the same product in different units: pieces, boxes or
cartons. Seeing only a quantity in the cart is ambiguous ("12" of what?). This
module shows the unit on every cart line, so customers can check their order
before confirming it.

## Key Features
- Unit of measure shown on each line of the cart.

## How It Works (User Flow)
1. The customer adds products to the cart, choosing a packaging or unit on the product page.
2. In the cart, each line shows its unit under the product name.

## Dependencies
| Module | Why it is needed |
|--------|------------------|
| website_sale | The web shop cart. |

## Configuration
No configuration required.

## Technical Notes
- Inherits `website_sale.cart_lines` and shows `line.product_uom_id` under the line description.
- **Migrated from 17.0 to 19.0:** the 17.0 XPath targeted the cart line loop, which no longer exists in the v19 cart template; the unit is now added after the line description, next to the sliced/shredded option of Custom Sale Order Management. `product_uom` became `product_uom_id`.
- The 17.0 manifest declared "Odoo" as the author, which appears to be a placeholder; it is now attributed to Plennix Technologies.

---
Developed and maintained by **Plennix Technologies** — https://www.plennix.com
