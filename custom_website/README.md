# Custom Website (Transmed B2B)

Turns the Odoo web shop into Transmed's B2B ordering portal: a category menu, per-kg prices, a customer-specific catalogue, salesperson ordering and checkout without online payment for credit customers.

## Business Purpose
Transmed's customers are businesses (restaurants, hotels, retailers) that
reorder regularly, mostly on credit terms, and are often served by a field
salesperson. The standard web shop is built for consumers paying by card. This
module adapts it to how Transmed sells:
- **Catalogue per customer:** customers only see the products meant for them (items reserved to specific customers; in Saudi Arabia only what their warehouse stocks).
- **Prices per kilogram:** products sold by the gram are priced per kg, the way customers compare them.
- **Credit checkout:** customers on credit confirm orders without paying online.
- **Salesperson ordering:** portal salespersons place orders on behalf of their customers.
- **Order follow-up:** customers track orders with the JD Edwards delivery status.
- **Controlled addresses:** customer addresses are maintained by Transmed, not changed by customers themselves.

## Key Features
- Category mega menu under the header (and in the mobile menu) listing the shop categories and sub-categories.
- Products sold by the gram show their price per kg (for example "$ 37.00 / KG") on the product page, shop, search results and product snippets. Other products show their unit ("/ Units").
- **Limited Items** on a product: it is visible (and reachable by URL) only for the selected customers.
- KSA: customers with a **Customer Location** only see products stocked in that location, and see its stock.
- Specifications table on the product page (JDE item number, category, brand, brand type, family, origin, storage, temperature).
- Brand filter: `/shop?brand_id=<id>`, used by the **Popular Brands** snippet.
- Credit checkout: customers without a cash-to-deliver ("CTD") payment term, and orders placed by a salesperson, are confirmed when clicking **Confirm**, without online payment and without an Odoo delivery method.
- **Salesperson ordering:** portal users flagged **Is SalesPerson** choose, on the checkout page, one of the customers whose Salesperson they are. The order is placed for that customer, and the salesperson follows it and sees it in their orders.
- Contacts of a company always invoice the company. Customers cannot edit their addresses online (they are sent to Contact Us); salespersons can.
- My Orders shows each contact's own orders (not the whole company's), including orders confirmed in JDE, with a **Status** column. Deliveries show their JDE status.
- The payment status shows "Your payment was processed successfully" once JDE has printed the invoice of every delivery.
- **Clear Cart** button in the cart. The sliced/shredded option is shown on cart lines. The cart keeps the 17.0
  layout: no promo code, no "save for later", no quick reorder.
- Delivery charges come from JDE: orders confirmed without online payment carry no Odoo delivery method. The
  delivery-method block is hidden on the checkout page and Odoo's delivery line never reaches the order.
- Wishlist only for logged-in customers. Login page sends new customers to Contact Us instead of self sign-up.
- Snippets: **Popular Brands**, **Main Categories**, and dynamic **Best Selling Products**, **High Review Products** (Mini Products card) and **Featured Categories** (up to 50).
- **Home page**: installing the module puts the Transmed home page on the site — banner carousel, Main
  Categories, High Review Products, Featured Categories, Best Selling Products and Popular Brands. It follows
  the data (categories flagged *Is Main Category*, brands flagged *Main Brand*), so there is nothing to
  configure per database, and it stays editable in the website editor.
- Optional **Transmed Footer** with a WhatsApp button.

## How It Works (User Flow)
1. The customer logs in and browses the shop through the category menu; only their catalogue is shown, with per-kg prices where relevant.
2. They add products to the cart (choosing packagings / sliced options on the product page) and click **Checkout**.
3. On the checkout page they check the delivery and billing addresses (billing is always their company) and click **Confirm**.
4. Credit customers: the order is confirmed immediately and sent to JDE. Cash (CTD) customers: they continue to online payment.
5. A salesperson does the same, but first chooses the customer under **Order for customer** on the checkout page.
6. Customers and salespersons follow orders in **My Orders**, with the JDE status of each delivery.

## Dependencies
| Module | Why it is needed |
|--------|------------------|
| website, website_sale, portal, auth_signup | Web shop, checkout, portal and login pages. |
| website_sale_comparison, website_sale_wishlist, website_sale_stock_wishlist | Product specifications section and wishlist. |
| sale, sale_stock, product, payment | Orders, deliveries and payment status. |
| mail, utm, digest, http_routing, social_media, google_recaptcha, im_livechat | Kept from the original module (website features used by the shop). |
| custom_saleorder_management | JDE order flow, order states, brands, cart options, JDE delivery status. |
| product_create_api | JDE product fields shown on the product page and product lists. |

## Configuration
1. **Salespersons:** create a portal user for each salesperson, tick **Is SalesPerson** on the user, and set this user as **Salesperson** on their customers (the field accepts portal users).
2. **Payment terms:** set **B2B Code** `CTD` on the cash-to-deliver payment term. Customers with any other payment term confirm without online payment.
3. **Delivery methods:** cash (CTD) customers paying online need one published delivery method (for example a free delivery), as in 17.0. Its line is hidden in the cart.
4. **KSA:** tick **Is Transmed KSA** on the company and set the **Customer Location** on KSA customers.
5. **Catalogue:** use **Limited Items** on products reserved to specific customers. Flag categories as **Is Featured Category** / **Is Main Category**, products as **Is Best Selling** / **Is High Review**, and brands as **Main Brand**.
6. **Footer:** activate the **Transmed Footer** view (Settings → Technical → Views) to use the Transmed footer.
7. **Home page:** flag the categories to show in **Main Categories** (*Is Main Category*, first four) and the
   brands of **Popular Brands** (*Main Brand*, first twelve); both sections are hidden while nothing is flagged.
   Replace the five banner pictures in the website editor.

## Technical Notes
- **Models:**
  - `res.company` / `website`: `is_ksa`, `is_jordan`.
  - `res.users`: `is_salesperson`.
  - `res.partner`: `customer_location_id`, plus related `is_ksa` / `is_jordan`.
  - `product.template`: `limited_item_ids`, `is_ksa`, `is_jordan`.
  - `product.product`: `high_review_product`, `best_selling_product`.
  - `product.public.category`: `is_featured_category`, `is_main_category`.
  - `product.pricelist`: related `is_ksa` / `is_jordan`.
  - `sale.order`: `is_salesperson_customer_id`.
- **Catalogue:** `website.sale_product_domain()` adds the Limited Items and KSA location rules, so they apply to the shop, search and product page (the product route returns 404 otherwise). `website._get_product_available_qty` uses the customer location.
- **Prices:** `product.template._b2b_price_display()` returns `(1000, 'KG')` for products in grams. It is used by the product price, product tile and Mini Products templates, and by search results (`_get_additionnal_combination_info` under the `b2b_search_result` context). `_apply_taxes_to_price` computes taxes without per-unit rounding.
- **Checkout:**
  - `shop_payment` confirms orders where `sale.order._b2b_skip_online_payment()` is true and redirects to `/shop/confirmation`.
  - `/shop/salesperson/customer` (POST, CSRF) switches the cart customer, restricted to the salesperson's customers. `sale.order._update_address` keeps that customer when the web shop resets the cart to the logged-in user.
  - `_prepare_address_data` limits billing to the parent company. `shop_address` / `shop_address_submit` are blocked for portal users who are not salespersons.
  - The cart's next step always goes to `/shop/checkout` (no skip), and `sale.order.action_confirm` sets the salesperson's customer.
  - **Order Again** is hidden on an order that was placed on another Transmed website: that website belongs to
    another company, so its products cannot be added to the cart here. When a reorder fails for another reason,
    the message is shown to the customer (19.0 core only logs it in the browser console).
  - `sale.order._get_delivery_methods()` returns nothing for orders that skip online payment, the delivery-method
    block on the checkout page is hidden (it stays in the DOM, the checkout javascript refreshes it when the
    delivery address changes), and `shop_payment` clears the carrier and its line before confirming.
  - Checkout steps are named as in 17.0 (**Review Order**, **Shipping**, **Payment**) on the website record.
- **Portal:**
  - `_prepare_orders_domain` / `_prepare_quotations_domain` show orders where the contact is the customer (or a child) or a follower.
  - Record rules (additive, read-only, portal): partners under the user's own contact, and sale orders the user follows.
- **Snippet filters:** `ir.filters` and `website.snippet.filter` records for best selling, high review and featured categories. The snippet limit constraint is raised to 50.
- **Home page:** `custom_website.homepage_transmed` extends `website.homepage`. It uses no database ids: the
  dynamic snippets resolve their filter with `env.ref`, the categories and brands are searched at render time
  and the five banners are module pictures (`static/src/img/home_banner_*.jpg`) meant to be replaced in the
  editor. Deactivate the view **Transmed Homepage** (Settings → Technical → Views) to go back to an empty
  home page; editing the page in the editor keeps working (the view is copied to the website as usual).
- **Migrated from 17.0 to 19.0:**
  - v17 kept full copies of core methods: `shop`, `address`, `checkout_values`, `_checkout_form_save`, `confirm_order`, `update_cart_address`, `website.sale_get_order`, `sale.order._cart_update`, `product.pricelist.item._compute_price`, `website.snippet.filter._filter_records_to_values` and `_apply_taxes_to_price`. They were replaced by small overrides of the v19 hooks, keeping only the Transmed-specific behaviour.
  - The address-form customer selector (`/get_customer_info` and its JavaScript) became a customer selector on the checkout page.
  - `confirm_order` no longer exists in v19; credit confirmation now happens on the **Confirm** step (`shop_payment`).
  - The cart-count, header cart link, optional-products modal, packaging/UoM selector and reorder overrides were removed. Packagings and cart options now come from custom_saleorder_management and the standard v19 cart, and the cart count is set by custom_saleorder_management.
  - The v17 `/shop/cart/custom_clear` route was replaced by the core `/shop/cart/clear`.
  - The core record rule `base.res_partner_portal_public_rule` is no longer modified; an additive rule is used instead.
  - Removed as unused in 17.0: `choose_category.js` and `/get_subcategories_products` (never loaded; its template did not exist), and `payment_post_processing.xml` (not in the assets).
  - The coupon points override was removed (same result in v19). The `_is_sold_out` override was removed (v19 core already ignores products that can be sold out of stock).
  - `ir.filters.user_id` became `user_ids`. Website templates were adapted to the v19 layout, product tile, checkout, portal and payment templates.
- **Not ported:**
  - The "Fetched elements up to 50" option in the website editor, and the footer-template choice in the editor. Both are JavaScript builder options in v19. The 50 limit is still accepted by the model, and the footer is available as the **Transmed Footer** view.
  - The sliced/shredded option is not copied when reordering (v19 reorder keeps product, quantity and unit).
- **Bugs fixed during migration** (present in 17.0):
  - `/get_customer_info` returned the name, email, phone and address of any contact to any logged-in user. The new selector only accepts the salesperson's own customers.
  - Products reserved to other customers could be opened by URL.
  - The crossed-out original price of gram products was shown per gram next to a per-kg price.

---
Developed and maintained by **Plennix Technologies** — https://www.plennix.com
