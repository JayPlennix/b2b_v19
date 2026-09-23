# System Monitor

Records every error users hit in Odoo and emails it, with full details, to selected staff.

## Business Purpose
When something goes wrong in Odoo, users often see only a short error message, and the
support team hears about it late, if at all, and without the details needed to fix it.
This module records every error automatically: who got it, what they were doing, and
the full technical details. It then emails it straight to the people responsible for
support. Support and IT staff learn about problems as soon as they happen and can start
investigating right away, without asking users for screenshots or needing server
access. Users do not need to do anything differently.

## Key Features
- Every error shown to a user or an integration is recorded automatically, nothing to report by hand
- The staff chosen in Settings receive each error by email, with a spreadsheet of the details attached
- An optional daily email summarises all of the day's errors in one spreadsheet
- Administrators can search the error list and group it by error type, screen, action or user to spot recurring problems
- Error records are visible to administrators only, since they can contain business data and technical details

## How It Works (User Flow)
1. An administrator opens **Settings → System Monitor** and chooses the staff who should receive error emails.
2. A user works in Odoo as usual. If an action fails, the user sees the error message as before.
3. At the same moment, the error is recorded and emailed to the chosen staff, with a spreadsheet attached.
4. Support staff open **Settings → Technical → Parameters → System Errors Monitor** to see the full error, the user, the action and the technical details.
5. If the daily summary is switched on, the chosen staff also receive one email per day listing all of that day's errors.

## Dependencies
| Module | Why it is needed |
|--------|------------------|
| base | Users, companies, settings and scheduled actions. |
| mail | Sending error emails to the chosen staff. |

## Configuration
1. Go to **Settings → System Monitor** and select the staff under **Daily Error Report**. No emails are sent until at least one user is selected.
2. Make sure an outgoing mail server is configured (**Settings → Technical → Outgoing Mail Servers**).
3. Optional: to also receive one summary email per day, activate the scheduled action **System Monitor: Send Daily Errors Log** (**Settings → Technical → Scheduled Actions**).

## Technical Notes
- **Error capture:** `controllers/json_rpc_dispatcher.py` extends `odoo.http.JsonRPCDispatcher` (`type='jsonrpc'` routes: web client, website, JSON APIs) and overrides `handle_error`. In Odoo 19 this runs inside the failed request's transaction, which is rolled back and can be read-only. The log is therefore written with its own cursor (`registry.cursor()`) as superuser, and the failed request's own changes are never committed. Any failure while logging is only written to the server log, so the user always gets the original error. Errors on `type='http'` and Odoo 19 `json2` (`/json/2/...`) routes are not captured.
- **Model:** `system.monitor.log` (inherits `mail.thread`) stores the model, method, arguments, user, companies, language, timezone, exception name, message, stack trace and the raw request and response. Each new record emails a CSV to the chosen users, using mail template `email_template_daily_errors_log` (queued, sent by the mail queue).
- **Settings:** `res.config.settings.logger_user_ids` (internal users), stored in `ir.config_parameter` `logger_user_ids`.
- **Scheduled action:** `system_monitor_log_cron`, daily, inactive by default. It calls `send_daily_log()`, which emails all of today's errors.
- **Views and menu:** list, form and search views, menu **Settings → Technical → Parameters → System Errors Monitor** (`base.menu_ir_property`).
- **Security:** `base.group_system` can read and delete logs. Logs are created by the system only.
- **Migrated from 17.0:** `tree` views became `list`, the cron no longer uses `numbercall`, the settings user domain no longer uses `res.groups.users` (renamed `user_ids` in 19.0), the license changed from OEEL-1 to LGPL-3, and emails are no longer sent when no user is selected (in 17.0 this raised an error).

---
Developed and maintained by **Plennix Technologies** — https://www.plennix.com
