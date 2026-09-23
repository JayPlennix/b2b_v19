# Integration Log

Keeps a central, read-only record of every request Odoo sends to JD Edwards (JDE) and to the HyperPay / Apple Pay payment gateways, together with the reply received.

## Business Purpose
The B2B shop relies on external systems. Orders, stock availability, deliveries,
order tracking and customer delivery schedules are exchanged with the JD Edwards
ERP, and online payments go through HyperPay and Apple Pay. When an order does
not reach JDE, stock looks wrong or a payment fails, the support team needs to
know exactly what Odoo sent and what came back. This module records each of
those exchanges in one list, so administrators and support consultants can
diagnose integration problems from inside Odoo instead of digging through
server logs.

## Key Features
- One list showing every call made to JDE and to the payment gateways.
- Each entry shows the address called, the headers, the data sent and the reply received.
- Entries cannot be created, edited or deleted from the screen, so the history stays trustworthy.
- Newest entries appear first.
- Only administrators can see the log, because entries can contain access tokens and payment details.

## How It Works (User Flow)
1. The integration modules (JDE order, stock, delivery and scheduler sync, HyperPay, Apple Pay) automatically add an entry each time they call an external system.
2. An administrator opens **Settings → SAP-Odoo Log → Integration Log**.
3. They search or filter by name or URL to find the call they are interested in.
4. They open the entry to read the data that was sent and the reply that came back.

## Dependencies
| Module | Why it is needed |
|--------|------------------|
| base | Core Odoo framework and the Settings menu. |

## Configuration
No configuration required.

## Technical Notes
- **Model:** `integration.log` with fields `name`, `url`, `headers`, `payload`, `model`, `res_id`, `response`; ordered `id desc`. The module has no logic of its own. Other modules write to it with `self.env['integration.log'].sudo().create({...})`, including `custom_saleorder_management`, `checkavailability_integration_jde`, `delivery_scheduler`, `payment_hyperpay`, `payment_hyperpay_extended` and `payment_applepay`.
- **Views/menu:** read-only list and form views (`create="0" edit="0" delete="0"`). The menu `menu_parent_integration_log` ("SAP-Odoo Log") sits under `base.menu_administration`.
- **Security:** full access for `base.group_system` only. All writers use `sudo()`, so non-admin flows are unaffected.
- **Migrated from 17.0 to 19.0:** `tree` view became `list`; `view_mode` is now `list,form`; unused imports removed; default order set to newest first; access restricted from internal users (`base.group_user`) to administrators (`base.group_system`); manifest re-branded to the Plennix Technologies standard, with the licence changed from AGPL-3 to LGPL-3.

---
Developed and maintained by **Plennix Technologies** — https://www.plennix.com
