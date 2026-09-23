# Hyperpay Payment Acquirer

Lets web shop customers pay by card or mada through HyperPay. The amount is pre-authorized at checkout and captured later for the final invoiced amount.

## Business Purpose
Transmed's B2B customers pay online when they place an order, but the final
amount is only known once the goods are delivered and invoiced (quantities and
prices can change). This module connects Odoo to the HyperPay payment gateway.
At checkout, the customer's card is only **pre-authorized** for the order amount.
Later, when the order has been invoiced, the finance team or the automatic
process of *Hyperpay Payment Acquirer Extended* **captures** the final amount.
Nothing is charged twice, and the customer is never charged more than was
delivered. Unused authorizations can be released (void), and captured amounts
can be refunded, directly from Odoo.

## Key Features
- Customers pay by card (Visa, Mastercard) or mada on a secure HyperPay payment page within the web shop.
- The amount is reserved at checkout and charged later, in full or in part.
- Odoo's standard **Capture**, **Void** and **Refund** actions are sent to HyperPay, and Odoo records the corresponding payments automatically.
- mada can use its own HyperPay entity.
- Every call to HyperPay is recorded in the integration log, with the access token hidden.

## How It Works (User Flow)
1. The customer chooses **Card** (or **mada**) on the payment page and clicks **Pay**.
2. The customer is taken to the HyperPay payment page, enters the card details and confirms.
3. HyperPay pre-authorizes the amount. Odoo marks the payment as **Authorized** and confirms the order.
4. When the order has been invoiced, the amount is captured (automatically by *Hyperpay Payment Acquirer Extended*, or with **Capture** on the order's transaction). Odoo then posts the payment.
5. If needed, the remaining authorization is released with **Void**, or a captured amount is returned with **Refund**.

## Dependencies
| Module | Why it is needed |
|--------|------------------|
| payment, account_payment | Odoo payment provider framework and automatic payment posting. |
| website_sale | Web shop checkout and the payment page layout. |
| integration_log | Records every HyperPay request and response. |

## Configuration
1. Go to **Website / Invoicing → Configuration → Payment Providers → HyperPay**.
2. Enter the **Entity Id** and **Access Token** from HyperPay; optionally a separate **Mada Entity Id**.
3. Keep **Capture Amount Manually** enabled so payments are pre-authorized, set the payment **Journal**, and set the state to **Test Mode** or **Enabled**.
4. Under **Payment Methods**, activate **mada** if mada cards are accepted (it is archived by default in Odoo).
5. If your HyperPay account uses another host than `eu-prod.oppwa.com` / `test.oppwa.com`, set the system parameters `payment_hyperpay.live_domain` / `payment_hyperpay.test_domain` (for example `https://oppwa.com`).

## Technical Notes
- **Original module:** *Hyperpay Payment Acquirer* by **Webkul Software Pvt. Ltd.** (https://webkul.com), distributed under the Webkul license (see `LICENSE`). Migrated to Odoo 19.0 by Plennix Technologies for Transmed, the licensee, as allowed by that license. **Do not redistribute or publish this module.** It keeps the Webkul icon and license.
- **Provider code:** `hyperpay`. Uses the v19 **redirect** flow. The redirect form posts the reference and an access token to `/payment/hyperpay/checkout`, which creates the COPYandPAY checkout (`paymentType` `PA` when *Capture Amount Manually* is on, `DB` otherwise) and renders the widget page. HyperPay returns the customer to `/payment/hyperpay/return`, where the result is fetched server-side and must match the transaction's reference and checkout id.
- **Capture / void / refund:** `_send_capture_request` (`CP`), `_send_void_request` (`RV`) and `_send_refund_request` (`RF`) are sent on `/v1/payments/<id>` with the entity id stored on the transaction. `support_manual_capture` and `support_refund` are `partial`. Partial captures create child transactions (standard v19).
- **Extension points** (used by payment_applepay): `_hyperpay_provider_codes`, `_hyperpay_get_access_token`, `_hyperpay_get_entity_id`, `_hyperpay_get_brands`, `_hyperpay_get_widget_options`.
- **Models:**
  - `payment.provider` gets `hyperpay_merchant_id`, `hyperpay_mada_entity_id` and `hyperpay_authorization`. These are visible to administrators only; the token field is masked.
  - `payment.transaction` gets `hyperpay_checkout_id` and `hyperpay_entity_id`.
- **Migrated from 17.0 to 19.0:**
  - The blob-iframe modal and jQuery / blockUI JavaScript were replaced by a v19 redirect flow, so no custom JS is needed.
  - `_get_tx_from_notification_data` / `_process_notification_data` became `_extract_reference` / `_extract_amount_data` / `_apply_updates`. A pre-authorization now becomes **Authorized** instead of **Done**.
  - Native capture, void and refund were added. Card brands come from the provider's payment methods (card, Visa, Mastercard, mada).
  - The `account.payment.method` override was removed (v19 registers provider methods automatically). The 17.0-only `pre_init_hook` series check and the Webkul test credentials were removed from data.
  - The 17.0 `hyperpay` payment method is kept (archived) for existing transactions.
- **Security fixes during migration:**
  - The return route used to process whatever result it was given for any transaction id. It now requires the matching checkout id, a `/v1/checkouts/<id>/` resource path, and a matching merchant reference.
  - The checkout creation route was public and keyed only on a transaction id. It now requires the transaction's access token.
  - The HyperPay access token is no longer written to the integration log.

---
Original module by **Webkul Software Pvt. Ltd.** — Odoo 19.0 migration developed and maintained by **Plennix Technologies** — https://www.plennix.com
