# Delivery Scheduler

Keeps each B2B customer's delivery days and validity dates in Odoo in sync with the schedules maintained in JD Edwards (JDE).

## Business Purpose
Delivery schedules for B2B customers (which weekdays a customer can receive
goods, and the period that schedule applies to) are maintained in JD Edwards.
This module brings those schedules into Odoo automatically, so the eCommerce and
sales teams can see each customer's agreed delivery days directly in Odoo without
logging into JDE or copying the information by hand. Changes made in JDE show up
in Odoo within two hours.

## Key Features
- Customer delivery schedules are refreshed from JDE every two hours, with no manual work.
- For each customer Odoo stores the delivery weekdays, the JDE delivery code, and the effective and expiry dates of the schedule.
- Schedules are listed in one place under the eCommerce configuration menu, where they can be reviewed or corrected.
- Every call to JDE is recorded in the integration log, so failed or unexpected synchronisations can be investigated.

## How It Works (User Flow)
1. An administrator enters the JDE connection details for the company (see Configuration).
2. Every two hours Odoo requests the latest delivery schedules from JDE for every company that has these details filled in.
3. Each schedule row from JDE is matched to the Odoo customer carrying the same B2B customer ID. Rows for customers that do not exist in Odoo are skipped.
4. If the customer already has a schedule in Odoo it is updated; otherwise a new one is created.
5. Users open **Website → Configuration → eCommerce → Delivery Scheduler** to see each customer's delivery days and validity dates.

## Dependencies
| Module | Why it is needed |
|--------|------------------|
| base | Core Odoo framework. |
| website | Parent of the eCommerce menus. |
| website_sale | Provides the eCommerce configuration menu where the schedules are listed. |
| integration_log | Records every request sent to JDE and the response received. |
| customer_create_api | Adds the B2B customer ID used to match JDE rows to Odoo customers. |
| checkavailability_integration_jde | Provides the JDE login (token) and logout URL for each company. |
| custom_saleorder_management | Provides the company's Delivery Scheduler URL and JDE schema name. |

## Configuration
1. Go to **Settings** and, for each company that should synchronise, fill in the JDE login details, the **JDE Logout Url**, the **Delivery Scheduler Url** and the **DTA_SchemaName**. Companies without a Delivery Scheduler Url or schema name are skipped.
2. Make sure the B2B customer ID is filled in on the customers whose schedules should be imported.
3. Optionally, adjust the frequency of the scheduled action **Call Update Delivery Scheduler API Every 2 Hours** under **Settings → Technical → Scheduled Actions**.

## Technical Notes
- **Models:** `delivery.scheduler` (one schedule per customer) and `days.days` (weekday names, Monday–Sunday, loaded from `data/data.xml`). JDE day names are matched to `days.days` by name.
- **Scheduled action:** `ir_cron_call_bulk_quantity_api` runs `delivery.scheduler.update_delivery_scheduler_api()` every 2 hours. It posts `{token, DTA_SchemaName}` to `res.company.delivery_scheduler_url`, reads `rows[]` (`CUSTOMER_ID`, `EFFECTIVE_DATE`, `DELIVERY_UDC`, `DELIVERY_DAYS`, `EXPIRY_DATE`; dates in `dd/mm/YYYY`), then calls `jde_logout_url`. The integration log is committed right after each request.
- **Weekday sync is additive:** delivery days returned by JDE are linked to the schedule, but days that JDE no longer returns are not removed.
- **Views/menu:** list and form views for `delivery.scheduler`, menu under `website_sale.menu_ecommerce_settings`.
- **Security:** full access for internal users (`base.group_user`). Portal and public users have no access.
- **Migrated from 17.0 to 19.0:** `tree` views became `list`; `numbercall`/`doall` removed from the cron; `self._cr` replaced by `self.env.cr`; `Command.link` used for many2many writes; timeouts added to JDE HTTP calls; the stray `mpmath` import removed; the dependencies that were previously implicit are now declared; access rights restricted to internal users; the integer field `delivery_days` relabelled "Number of Delivery Days" so it no longer shares a label with `day_ids`.

---
Developed and maintained by **Plennix Technologies** — https://www.plennix.com
