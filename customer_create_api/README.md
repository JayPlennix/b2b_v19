# Customer API (JDE)

Lets JD Edwards (JDE) create and update B2B customers in Odoo automatically through an API, so customers never have to be entered twice.

## Business Purpose
Transmed's B2B customers are opened and maintained in JD Edwards. Without this
module the sales or master-data team would have to re-create every customer in
Odoo by hand, and keep addresses, salespeople, payment terms and pricelists in
step with JDE. This module lets JDE send each new or changed customer straight to
Odoo. The customer then appears in Odoo with the right company (KSA or Jordan),
salesperson, payment terms, pricelist and warehouse location, ready to order on
the B2B shop. When a customer is blocked in JDE, the customer and their shop
login are archived in Odoo as well.

## Key Features
- New customers created in JDE appear in Odoo automatically, with their address and, when needed, a separate delivery address.
- Changes in JDE (address, classification, salesperson, payment terms, status) are applied to the existing Odoo customer.
- Customers are identified by their JDE customer number, so the same customer is never created twice.
- Blocking a customer in JDE archives the customer in Odoo and switches off their shop login. Unblocking re-activates both.
- Company, payment terms, pricelist, salesperson and KSA warehouse location (Jeddah, Riyadh, Dammam) are assigned from the codes JDE sends.
- The JDE classification (customer group, channel, area, sub-area, type, mailing name) is shown on a **Transmed-b2b** tab on the customer.
- Changing a customer's company does not change the company of its existing contacts and addresses.

## How It Works (User Flow)
1. JDE logs in to Odoo with a dedicated user and receives a session id.
2. When a customer is created in JDE, JDE sends it to Odoo. If the JDE customer number already exists in Odoo, the request is refused and the existing customer is returned. Otherwise the customer is created.
3. When a customer changes in JDE, JDE sends the update and Odoo applies it to the customer with the same JDE customer number.
4. The sales team finds the customer in **Contacts**, with the JDE information on the **Transmed-b2b** tab.

## Dependencies
| Module | Why it is needed |
|--------|------------------|
| base | Customers, companies, countries and states. |
| web | Web session login used by JDE. |
| crm | Kept from the original module for the sales setup it expects. |
| account | Payment terms, which get a JDE code. |
| sale | Customer pricelists and salespeople. |
| stock | Warehouse locations, which get a KSA location code. |

## Configuration
1. On each **company** (Settings → Companies), set **Source** to the value JDE sends to identify that company.
2. On each **payment term** (Accounting → Configuration → Payment Terms), set the **B2B Code** used by JDE. Tick **IS Cash Payment Term** where applicable.
3. On the KSA **warehouse locations** (Inventory → Configuration → Locations), set **KSA Location** and **KSA Location Code**.
4. Make sure pricelist names in Odoo match the pricelist names JDE sends.
5. Create an internal Odoo user for JDE, with rights to create and edit contacts, and give JDE its login.

## Technical Notes
- **Endpoints** (`type='jsonrpc'`, `auth='user'`): `POST /api/partners` creates a customer and `PUT /api/partners` updates one. Both match on `b2b_customer_id`, including archived partners. `/web/session/authenticate` is extended to add `session_id` to the result.
- **Inherited models:**
  - `res.partner` gets the JDE fields `b2b_customer_id`, `customer_group(_name)`, `customer_channel(_name)`, `customer_area(_name)`, `customer_subarea(_name)`, `customer_type`, `customer_mailing_name`, `timestamp_jde`, `create_via_api` and `create_b2b_owner`. It also gets a `write()` override that stops core from copying a new `company_id` down to `child_ids`.
  - `res.company` gets `source`.
  - `account.payment.term` gets `b2b_code` and `is_cash_payment_term`.
  - `stock.location` gets `ksa_location` and `ksa_location_code`.
- **Views:** a Transmed-b2b page on the partner form, plus extra fields on the company, payment term and location forms.
- **Soft dependency:** `customer_location_id` on `res.partner` comes from `custom_website`, which itself depends on this module. It is written only when that field exists.
- **Security:** no new models, so no access rules. API calls run with the rights of the authenticated JDE user.
- **Migrated from 17.0 to 19.0:**
  - Routes changed from `type='json'` to `type='jsonrpc'`.
  - The monkey-patch of core `res.partner.write` (a copy of the 17.0 method) was replaced by a small `write()` override with the same effect: no company cascade to children. The patch's `arch_validation` branch was dropped, because nothing ever sets that context.
  - The monkey-patch of `Request._serve_ir_http` was removed. In 19.0, core rotates and saves the session inside `authenticate()`, so the session id is read directly after `super()`.
  - Portal-user archiving uses `_is_portal()` on the matched users, because `has_group()` now requires exactly one user.
  - `Command.set` is used for `child_ids`. `stock` is declared as a dependency. The unused security CSV (it referenced a non-existent model) was removed.
  - The "Customer Not Found" message is now a string instead of a Python set, which could not be sent as JSON.
- **Bugs fixed during migration** (all present in 17.0):
  - Updating a customer that has a parent always failed with "recursive Partner hierarchies", because the update tried to make the parent a child of the customer. Updates no longer touch `child_ids`.
  - Create and update now run inside a database savepoint. Errors are returned to JDE rather than raised, so a failed call used to commit whatever it had half-written. This could leave, for example, two partners pointing at each other as parents.
  - Blocking a customer who has a portal login failed with "You cannot archive contacts linked to an active user". Because the partner is looked up including archived records, core counted the portal user that had just been archived. The partner is now written with `active_test=True`. Internal users linked to the customer still block archiving, as core intends.

---
Developed and maintained by **Plennix Technologies** — https://www.plennix.com
