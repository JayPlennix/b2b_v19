# Website Return Order Management

Lets web shop customers request the return of products they received, and lets Transmed process those requests as return transfers.

## Business Purpose
B2B customers receive goods that sometimes have to go back: damaged, expired or
wrongly delivered items. Without this module every return starts with a phone
call or an email, and nothing is traceable. Here the customer asks for the return
from the portal, on the order itself, choosing the product, the quantity (never
more than what was delivered) and a reason. Customer service receives an email,
checks the request and confirms it, which creates the return transfer for the
warehouse and, for Transmed, the return order in JD Edwards. Customers follow
their requests in the portal.

## Key Features
- Return request from the customer portal, on a delivered order.
- The requested quantity can never exceed what was actually delivered and not yet returned.
- Return reasons (damaged, expired, ...) configurable under Sales.
- Return orders with quantity, unit price, total, the source delivery and the return transfer.
- Confirmation email to the salesperson, and a printable return order.
- Return counts on the customer and the sales order, with direct links.
- Return transfers are sent to JD Edwards by Custom Sale Order Management.

## How It Works (User Flow)
1. The customer opens a delivered order in the portal and clicks **Return**.
2. In the dialog they pick the product, the quantity and the reason, and submit. A return order is created in the **Draft** state and the salesperson receives an email.
3. Customer service opens the return order and clicks **Confirm**. The return transfer is created for the warehouse (and the return is sent to JDE).
4. When the warehouse validates the return transfer, the return order becomes **Done**.
5. The customer follows the request under **My Account → Return Orders**.

## Dependencies
| Module | Why it is needed |
|--------|------------------|
| website_sale, sale_management, stock | Portal orders, sales orders and transfers. |
| custom_saleorder_management | JDE return (GRV) integration and the return order type on transfers. |

## Configuration
1. Create the return reasons under **Sales → Configuration → Return Reasons**.
2. Make sure salespersons are set on customers or orders: the confirmation email goes to the order's salesperson.

## Technical Notes
- The **Return** button appears on a portal order only when the order is confirmed (including JDE
  Confirmed) and something has already been delivered; the return form itself is a modal on the
  order page. Its title is not an `<h2>`, so the portal sidebar does not list a menu entry pointing
  at the hidden modal.

- **Original module:** *Website Return Order Management* by **Cybrosys Techno Solutions** (https://www.cybrosys.com), AGPL-3. Migrated to Odoo 19.0 by Plennix Technologies; the licence and author credits are kept.
- **Models:** `sale.return` (portal.mixin), `return.reason`; `stock.picking` gets `return_order`, `return_order_pick` and `return_order_picking`; `sale.order.line` gets `remaining_qty_return`; return counts on `sale.order` and `res.partner`.
- **Routes:** `/sale_return` (POST, logged-in customers) creates the request; `/my/return_orders` and `/my/return_orders/<id>` are the portal pages; `/my/request-thank-you` is the confirmation page.
- **Security:** internal users manage return orders; portal users only read their own (access rule on `user_id` or their company). The marketing images of the original module were not kept.
- **Migrated from 17.0 to 19.0:**
  - `read_group` became `_read_group`, `_create_returns()` became `_create_return()`, `move_ids_without_package` became `move_ids`, `quantity_done` became `quantity`, and `ir.sequence.get()` became `next_by_code()`.
  - `tree` views became `list`, the search view group-by syntax was updated, and the portal quantity column now anchors on the v19 cell.
  - The frontend widget became a v19 interaction (dialog service for the validation messages).
- **Bugs and security fixed during migration** (present in 17.0):
  - `/sale_return` was public, without CSRF protection, and trusted the order, product and quantity it was given: anyone could create return orders on any order, for any quantity. It now requires a logged-in customer, the order must belong to their company, and the quantity cannot exceed what is still returnable.
  - Return orders were readable and writable by everyone, including public visitors. Access is now limited to staff, with portal users reading their own.
  - The portal list showed only the returns the user created; it now also shows their company's.

---
Original module by **Cybrosys Techno Solutions** — Odoo 19.0 migration developed and maintained by **Plennix Technologies** — https://www.plennix.com
