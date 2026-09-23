# Custom Sale Order Management (JDE)

Connects the Transmed B2B web shop to JD Edwards (JDE): orders are sent to JDE, and deliveries, prices, invoices, returns and delivery tracking are kept in sync.

## Business Purpose
Transmed's customers order on the B2B web shop, but orders are fulfilled and
invoiced in JD Edwards. Without this module the customer-service team would
re-key every web order into JDE and then copy back delivery quantities, final
prices and invoice numbers by hand. This module sends each confirmed web order
to JDE and follows it through JDE's workflow. It mirrors JDE's delivery notes,
updates quantities and prices when JDE invoices, and brings JDE returns back into
Odoo, refunding cash customers to their eWallet. Customers see JDE's final prices
and totals on their portal and printed quotation, get an expected delivery date
at checkout (following their agreed delivery days in Saudi Arabia), and can track
their delivery live. The warehouse, customer-service and finance teams all work
from the same, up-to-date order information.

## Key Features
- Confirmed web orders are created in JDE automatically, and split into the delivery notes JDE creates.
- Every 10 minutes Odoo picks up each delivery's JDE status (credit control, at warehouse, ready to ship, invoice printed, ...).
- When JDE prints the invoice, delivered quantities, lots (KSA), final prices, taxes, delivery charge and invoice number are copied back, and the delivery is validated automatically.
- Returns entered in JDE are created in Odoo every 10 minutes. For cash customers the returned amount is added to their eWallet and they are notified by email.
- A **Create JDE Order** button re-sends a confirmed order to JDE if needed.
- Checkout shows the expected delivery date (next day for orders before 16:00, otherwise the day after). In KSA, the expected date follows the customer's delivery days.
- For ARP products, customers can choose sliced or shredded and the number of pieces; each piece is ordered as a separate line.
- Packagings (for example BOX of 12) are chosen with Odoo's standard unit selector and ordered in units, as JDE expects.
- Customers see JDE prices and totals on the portal and on the printed quotation, and can open **Track Order** to see the driver, vehicle and a map route.
- Product brands can be managed under Sales → Products → Product Brands.

## How It Works (User Flow)
1. The customer adds products to the cart. For ARP items they can choose sliced or shredded and the number of pieces; for packaged items they choose the packaging in the unit selector.
2. At checkout the customer sees the expected delivery date and places the order.
3. When the order is confirmed it is sent to JDE. JDE's order numbers are read back and the Odoo delivery is split into one delivery per JDE delivery note (state **JDE Confirmed**).
4. Every 10 minutes Odoo updates each delivery's JDE status. When JDE prints the invoice, quantities, prices and the invoice number are copied back and the delivery is validated.
5. The customer follows the order on the portal, with JDE prices and totals, and can click **Track Order** once the invoice is printed.
   Before that, **Track Order** says that live tracking is not available yet (17.0 did nothing at all).
6. Returns created in JDE appear in Odoo as return deliveries and are validated. Cash customers are refunded to their eWallet.

## Dependencies
| Module | Why it is needed |
|--------|------------------|
| sale, sale_stock, stock, stock_delivery | Orders, deliveries, returns and JDE tracking reference on deliveries. |
| website, website_sale | Web shop cart, checkout and portal. |
| loyalty, website_sale_loyalty | eWallet program used for refunds on returns. |
| integration_log | Records every call to JDE and the tracking service. |
| customer_create_api | JDE customer number on customers, cash payment terms. |
| checkavailability_integration_jde | JDE login (token) and logout URL for each company. |
| payment_hyperpay_extended | Online payment collection once all deliveries are invoiced (`payment_done`, `recuring_payment`). |

## Configuration
1. In **Settings → JDE Saleorder Integration**, fill in for each company the JDE URLs (create order, order status, search by reference, return order create, return order scheduler, invoiced orders), the DTA schema name, the tracking URL with its username and password, and the delivery scheduler URL.
2. Tick **Is Transmed KSA** or **Is Transmed Jordan** on the company where applicable. For KSA customers, set their **Customer Location** (warehouse).
3. Check the two scheduled actions: **Call Update SaleOrder Status Every 10 Minutes** and **Call Return Order JDE Every 10 Minutes**.
4. Review the **eWallet** loyalty program created by the module (currency label "AED").
5. Enable **Units of Measure & Packagings** so customers can choose packagings on the web shop.

## Technical Notes
- **Models:**
  - New model `product.brand`.
  - `sale.order` gets the `jde_confirmed` state, JDE amounts, `jde_invoice_no`, and the JDE create/confirm/status/invoice logic. Expected and validity dates are overridden for KSA, and the invoice address comes from the parent company.
  - `sale.order.line` gets `item_type`, `sl_no_comp`, JDE price, tax and delivery fields.
  - `stock.picking` gets `jde_state`, the GRV order type, driver tracking fields and JDE return logic.
  - `stock.move.line` gets `sl_no_comp` and `is_sl_no_comp`.
  - `loyalty.card` gets `picking_id`.
  - `res.company` gets the JDE settings plus `is_ksa` and `is_jordan`.
  - `res.partner` gets `customer_location_id`.
  - `product.template` gets `jde_product_id` and `item_type`, which are also defined in product_create_api.
  - `stock.rule` sources KSA moves from the customer's location.
- **Cart:**
  - `sale.order._cart_add` converts a packaging unit (`product.uom_ids`) into the product's unit, writes `item_type` from the `productItemOption` kwarg, and creates one extra line per additional piece (`quantityPieces`).
  - `_cart_find_product_line` never merges sliced/shredded lines.
  - `cart_quantity` counts lines, excluding delivery and reward lines.
  - The kwargs are added to the root product by patching `WebsiteSale._updateRootProduct`.
- **JDE quantities:** JDE works in the product's unit. Order lines in a packaging unit are converted before sending, and quantities received from JDE are converted to the stock move's unit.
- **Scheduled actions:** `ir_cron_call_saleorder_api` runs `sale.order.update_saleorder_status()` and `ir_cron_call_return_order_api` runs `stock.picking._fetch_return_order_grv_from_jde()`, both every 10 minutes.
- **Routes:**
  - `/tracking_sale_order` (jsonrpc) calls the tracking API. It is protected by the portal access check (customer, or valid access token).
  - `/shop/checkout` is extended to set `commitment_date`.
- **Soft dependencies:** `delivery.scheduler` (delivery_scheduler) and `stock.picking.return_order_pick` (website_return_management) are used only when installed, because those modules depend on this one. `is_ksa`, `is_jordan`, `customer_location_id` (also in custom_website) and `jde_product_id`, `item_type` (also in product_create_api) are defined here too, because those modules depend on this one; defining a field in two modules is harmless.
- **Portal deliveries:** the portal lists every delivery of the order, not only the latest three, because JDE splits orders into several deliveries.
- **Security:** everyone can read `product.brand` (the web shop shows brands); internal users can manage brands.
- **Migrated from 17.0 to 19.0:**
  - Cart: `/shop/cart/update_json` and `_cart_update` were replaced by v19 `_cart_add`. The custom packaging/UoM selector and its JS were replaced by the standard v19 unit selector. `product_packaging_id` and `uom.category` no longer exist.
  - Frontend: `WebsiteSale.include` became a `patch` of the v19 interaction, and the public widgets became interactions using `rpc`.
  - Templates: checkout, product page, portal and report XPaths were adapted to the v19 templates (`td_product_quantity`, `td_product_subtotal`, `td_product_taxes`, `print_invoice_sidebar_button`, CTA section).
  - Stock: `move_ids_without_package` became `move_ids`, `scrapped` became `location_dest_usage == 'inventory'`, and `_create_returns()` became `_create_return()`. The v17 copy of `_sanity_check` was replaced by an override that only skips the "no quantities" check for JDE validations.
  - Crons: `numbercall`/`doall` removed. `self._cr` became `self.env.cr`, tuple commands became `Command`, and timeouts were added to every JDE call.
  - Dependencies used implicitly in 17.0 are now declared: `sale_stock`, `stock_delivery`, `website_sale_loyalty`, `integration_log`, `customer_create_api`, `checkavailability_integration_jde`.
  - Security: removed the access rule giving every user, including public visitors, full write access to units of measure. Brand write access is limited to internal users.
- **Bugs fixed during migration** (all present in 17.0):
  - `/tracking_sale_order` accepted any order id from anyone and returned driver, vehicle and GPS positions. It now requires portal access to the order.
  - The tracking popup inserted driver and vehicle text as HTML. It is now inserted as plain text.
  - Returns: adding a line to an existing JDE return used an undefined or stale picking id for the eWallet amount. The eWallet refund check also used the payment term of the last order processed instead of the return's own order.
  - Order confirmation checked `is_jordan` on the whole batch instead of each order.
  - When several deliveries were validated in one run, all backorder decisions used the first delivery's ids.
  - Adding a plain item could merge into, and reset, an existing sliced/shredded line.
  - A failed JDE return raised a Python `UserWarning` instead of a user error.
  - If JDE was unreachable or not configured, confirming a paid web order crashed, because the JDE token request was outside the error handling, and the order stayed unconfirmed. Now the JDE step is skipped and logged; it can be re-sent with **Create JDE Order**.
  - "Excepted Delivery Date" was corrected to "Expected Delivery Date".

---
Developed and maintained by **Plennix Technologies** — https://www.plennix.com
