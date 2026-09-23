# Hyperpay Payment Acquirer Extended

Captures the pre-authorized HyperPay or Apple Pay payment of a web order once JD Edwards (JDE) has invoiced it.

## Business Purpose
Web shop orders are paid by card or Apple Pay at checkout, but the final amount
is only known after JD Edwards has delivered and invoiced the order: quantities,
prices, taxes and delivery charges can change, and eWallet credit is deducted. At
checkout the customer's money is therefore only reserved (pre-authorized). This
module charges the customer the exact amount invoiced by JDE, as soon as all
deliveries of the order are invoiced, and Odoo records the payment automatically.
Finance no longer has to charge customers by hand, and customers are only charged
for what they actually received.

## Key Features
- The amount invoiced by JDE is charged automatically on the customer's pre-authorization once all deliveries are invoiced.
- Odoo posts the payment and links it to the sales order.
- A **Payment Done** indicator on the sales order shows which orders have been charged.
- A declined charge stays visible on the order's transactions and is retried at the next JDE update.
- Orders pre-authorized before the upgrade to Odoo 19 are still charged correctly.
- Single-use payment references are never offered to customers as saved cards.

## How It Works (User Flow)
1. The customer pays a web order by card or Apple Pay. The amount is pre-authorized and the order is confirmed.
2. JDE delivers and invoices the order. Custom Sale Order Management picks up the invoices every 10 minutes.
3. When every delivery of the order is invoiced, the JDE invoiced total is charged on the pre-authorization.
4. Odoo records the payment, links it to the order and ticks **Payment Done**.

## Dependencies
| Module | Why it is needed |
|--------|------------------|
| sale | Sales orders. |
| payment_hyperpay | HyperPay transactions and the capture request. |
| integration_log | Records every HyperPay request. |

## Configuration
No configuration required. The HyperPay and Apple Pay providers must have **Capture Amount Manually** enabled (the default).

## Technical Notes
- **`sale.order.recuring_payment()`** (name kept because custom_saleorder_management calls it): finds the order's `authorized` HyperPay / Apple Pay transaction and calls the standard v19 `_capture(amount_to_capture=jde_amount_total)`. Payment posting is done by the standard post-processing. It skips orders already paid or with a capture in progress.
- **Legacy orders:** orders authorized in 17.0 have no authorized v19 transaction, but have `payment_token_id` (its `payment_details` holds the HyperPay payment id). They are captured with `CP` on that id, and the resulting v19 transaction is post-processed so the payment is created.
- **Other models:**
  - `payment.transaction._create_child_transaction` links captures, voids and refunds to the source sales order.
  - `payment.token._get_available_tokens` hides HyperPay / Apple Pay tokens.
  - `sale.order` gets `payment_token_id` (legacy) and `payment_done`.
- **Soft dependency:** `jde_amount_total` comes from custom_saleorder_management, which depends on this module. The capture falls back to `amount_total` if it is not installed.
- **Migrated from 17.0 to 19.0:**
  - The manual `CP` request, transaction and `account.payment` creation were replaced by the native v19 capture.
  - The override of `/payment/hyperpay/result` and the token creation were removed. The override of `/shop/confirmation`, which forced order confirmation, was removed because v19 confirms orders when the payment is authorized.
  - The payment confirmation template override was removed (the amount now always matches), as were the unused `test_cp_api` method and commented code.
- **Behaviour change — please review:** 17.0 captured `jde_amount_total − eWallet`, but `jde_amount_total` already has the eWallet deducted, so the gateway charged the eWallet amount twice while the posted payment used the correct total. 19.0 captures `jde_amount_total` (eWallet deducted once), so the charged amount and the posted payment now match.

---
Developed and maintained by **Plennix Technologies** — https://www.plennix.com
