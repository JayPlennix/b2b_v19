# JDE Connection & Stock Availability

Connects Odoo to JD Edwards (JDE) and keeps the stock shown on the B2B web shop in line with what is really available in JDE.

## Business Purpose
Transmed's stock is managed in JD Edwards, while customers order on the Odoo
B2B web shop. If the shop showed out-of-date stock, customers could order goods
that are no longer available, or be told something is out of stock when it is
not. This module keeps Odoo's stock in line with JDE: every 20 minutes it picks
up the stock that changed in JDE, and whenever a customer opens a product page,
the cart or the checkout, it refreshes the stock of those products live. In
Saudi Arabia (KSA), stock is recorded per warehouse and lot with its expiry
date. The module also holds each company's JDE login, which every other Transmed
JDE integration (orders, deliveries, returns, delivery schedules) uses.

## Key Features
- The JDE login (URL, user, password, environment, role) is configured once per company, with a **Test Connection** button.
- Stock that changed in JDE is updated in Odoo every 20 minutes.
- Product pages, the cart and the checkout refresh stock live from JDE before they are displayed.
- If JDE is slow or unavailable, the web shop keeps working and the problem is only logged.
- For KSA, stock is recorded per warehouse (Jeddah, Riyadh, Dammam) and per lot, with its expiry date.
- Every call to JDE is recorded in the integration log, without the JDE password.

## How It Works (User Flow)
1. An administrator enters the company's JDE login and URLs in Settings and clicks **Test Connection**.
2. Every 20 minutes Odoo asks JDE for the stock that changed since the last run and updates the quantities in the product's JDE stock location (for KSA, in the warehouse and lot given by JDE).
3. When a customer opens a product page, the cart or the checkout, Odoo asks JDE for the current stock of those products and updates it before the page is shown.

## Dependencies
| Module | Why it is needed |
|--------|------------------|
| base, web | Core framework and settings. |
| crm | Kept from the original module for the sales setup it expects. |
| sale, website, website_sale | Web shop product page, cart and checkout. |
| stock | Stock quantities, locations and lots. |
| product_expiry | Expiry dates on stock and lots. |
| integration_log | Records every call to JDE. |
| customer_create_api | KSA location codes on warehouse locations. |

## Configuration
1. Go to **Settings → JDE Integration** and fill in, for each company, the JDE token URL, user name, password, environment and role, the availability URL, the bulk update URL and the logout URL. Then click **Test Connection**.
2. Set the **DTA_SchemaName** (in the JDE Saleorder Integration settings of Custom Sale Order Management), which is required for the 20-minute update.
3. Set the **JDE Stock Location** on products (done automatically by the Product API), and the **KSA Location** on KSA warehouse locations.
4. Tick **Is Transmed KSA** on the KSA company.
5. Optionally adjust the scheduled action **Call Update Quantity Bulk API Every 20 Minutes**.

## Technical Notes
- **Inherited models:**
  - `res.company` gets the JDE login fields, availability, bulk and logout URLs, and `jde_last_integration_timestamp`. It also provides `get_jde_token()` and `jde_logout()`, which the other JDE modules use.
  - `res.config.settings` gets the related fields plus the connection test (a display notification).
  - `product.template` gets `update_quantity_bulk_api()` and `update_stock_bulk_quantities()`.
- **Scheduled action:** `ir_cron_call_bulk_quantity_api` runs `product.template.update_quantity_bulk_api()` every 20 minutes. It posts the last integration timestamp and reads `rows[]` (`SKU`, `QTYAVAILABLE_S`, `EXPIRY` in `dd/mm/YYYY`, `WHLOC`, `TIMESTAMP`). Quantities are set to the JDE available quantity plus the quantity reserved in Odoo.
- **Web shop:** `WebsiteSale.product`, `cart` and `shop_checkout` call `update_product_jde_quantity()`. It posts the SKUs (product JDE ids and their lot names) to the availability URL and sets the quants from `QTYAVAILABLE_P`. It runs with sudo, and all errors are caught.
- **Shared fields:** `dta_schemaname` and `is_ksa` on `res.company`, and `jde_product_id`, `jde_stock_location` and `timestamp_jde` on `product.template`, are also defined in custom_saleorder_management / product_create_api. Those modules depend on this one, which is the JDE connection base; defining a field in two modules is harmless.
- **Security:** no new models. The JDE password is shown masked in Settings and is not written to the integration log.
- **Migrated from 17.0 to 19.0:**
  - Controller overrides follow the v19 signatures (`product(product, category, pricelist)`, `cart(id, access_token, revive_method)`, `shop_checkout`), and `request.website.sale_get_order()` became `request.cart`.
  - The cart no longer overrides the cart-count session value; custom_saleorder_management sets `cart_quantity` to the number of lines.
  - Crons: `numbercall`/`doall` removed. `_cr` became `env.cr`, timeouts were added to all JDE calls, and debug `print()` calls became logging.
  - Previously implicit dependencies are now declared: `integration_log`, `product_expiry`, `customer_create_api`.
- **Bugs fixed during migration** (all present in 17.0):
  - If JDE was unreachable, product pages, the cart and the checkout crashed with a server error, because the token request was outside the error handling.
  - Refreshing the stock of a product that had no stock yet failed for visitors (public user without stock rights), or when the product had no JDE stock location.
  - The **Connect** button in Settings read old system parameters instead of the company's JDE login, so it could not work. It is now a **Test Connection** button that shows the result.
  - The JDE password was written in plain text to the integration log on every token request.
  - A KSA location code matching several locations crashed the 20-minute update.

---
Developed and maintained by **Plennix Technologies** — https://www.plennix.com
