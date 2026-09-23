# Website Hide Prices

Hides prices and ordering on the B2B web shop from visitors who are not logged in.

## Business Purpose
Transmed sells at customer-specific prices that competitors and the general
public should not see. The catalogue itself is public, so customers can browse
products before logging in. This module hides every price and every ordering
button from visitors who are not logged in, and invites them to log in instead.

## Key Features
- No prices on the shop, the product page or the product snippets for visitors.
- "Log in to see prices" instead of the price and the add-to-cart button.
- Adding to the cart is refused for visitors, also when the request is sent directly.
- Prices are removed from the product data sent to visitors, not just hidden on screen.

## How It Works (User Flow)
1. A visitor browses the shop and the product pages, and sees products without prices.
2. Where prices and the add-to-cart button would be, they see an invitation to log in.
3. After logging in, prices and ordering appear as normal.

## Dependencies
| Module | Why it is needed |
|--------|------------------|
| website_sale | Shop, product page and cart. |
| custom_website | Transmed shop templates, including the product snippets. |

## Configuration
No configuration required.

## Technical Notes
- Templates hide the price block on the tiles (`website_sale.products_item`), the product page price section, the call-to-action block and the Transmed product snippet for public users.
- `product.template._get_additionnal_combination_info` zeroes the price fields for public users, so prices are not exposed through the product data either.
- `/shop/cart/add` and `/shop/cart/update` raise an access error for public users (`/shop/cart/quick_add` already requires a login in 19.0).
- **Migrated from 17.0 to 19.0:** the price templates were rewritten on the v19 shop templates (v17 copied the whole price block, which duplicated the per-kg logic of custom_website); the cart routes were replaced by the v19 ones; and the shop/product controller overrides that zeroed prices in the page values were replaced by the combination-info override.
- The 17.0 manifest declared "Odoo" as the author, which appears to be a placeholder; it is now attributed to Plennix Technologies. Tell us if it should credit someone else.

---
Developed and maintained by **Plennix Technologies** — https://www.plennix.com
