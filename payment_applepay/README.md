# Hyperpay Payment Acquirer - Applepay

Lets web shop customers pay with Apple Pay, processed by HyperPay. The amount is pre-authorized at checkout and captured later for the final invoiced amount.

## Business Purpose
Many of Transmed's customers order from an iPhone or a Mac. This module adds
Apple Pay as a payment option on the web shop, processed by HyperPay with its own
Apple Pay merchant account. It works like card payments: at checkout the amount is
only **pre-authorized**, and the final invoiced amount is **captured** later, by
*Hyperpay Payment Acquirer Extended* or from the order. The customer is never
charged more than what was delivered, and unused authorizations can be released
from Odoo.

## Key Features
- Apple Pay appears as a payment option on the web shop payment page.
- Payments go through HyperPay with a dedicated Apple Pay entity and access token.
- The amount is reserved at checkout and charged later, in full or in part. Void and refund work from Odoo.
- The Apple Pay sheet (merchant name, supported networks and countries, merchant identifier) is configured in the provider, not in code.
- Every call to HyperPay is recorded in the integration log.

## How It Works (User Flow)
1. The customer chooses **Apple Pay** on the payment page and clicks **Pay**.
2. On the HyperPay payment page the customer taps the **Apple Pay** button and confirms with Face ID / Touch ID.
3. HyperPay pre-authorizes the amount. Odoo marks the payment as **Authorized** and confirms the order.
4. When the order has been invoiced, the final amount is captured and Odoo posts the payment.

## Dependencies
| Module | Why it is needed |
|--------|------------------|
| payment_hyperpay | HyperPay payment page, API calls, capture, void and refund. |
| payment_hyperpay_extended | Automatic capture after invoicing. |
| integration_log | Records every HyperPay request and response. |

## Configuration
1. Go to **Website / Invoicing → Configuration → Payment Providers → Apple Pay**.
2. Enter the Apple Pay **Merchant ID/Entity Id** and **Authorization Bearer** from HyperPay.
3. Optionally set the **Apple Pay Display Name** (defaults to the company name), the **Apple Merchant Identifier** (the button is then only shown on devices ready to pay this merchant), the **Supported Networks** (e.g. `masterCard,visa,mada`) and the **Supported Countries** (e.g. `AE,SA`).
4. Keep **Capture Amount Manually** enabled, set the **Journal**, and set the state to **Test Mode** or **Enabled**.
5. Register and verify the web shop domain for Apple Pay with HyperPay / Apple (domain association file), as required by Apple.

## Technical Notes
- **Original module:** *Hyperpay Payment Acquirer - Applepay* by **Technaureus Info Solutions Pvt. Ltd.** (http://www.technaureus.com), under the Odoo Proprietary License v1.0 (see `LICENSE` / `COPYRIGHT`). Migrated to Odoo 19.0 by Plennix Technologies for Transmed, the licensee. **Do not publish, distribute or sell this module.** It keeps the Technaureus icon and license.
- **Provider code:** `applepay`. It reuses the HyperPay v19 flow by extending `_hyperpay_provider_codes`, `_hyperpay_get_access_token`, `_hyperpay_get_entity_id`, `_hyperpay_get_brands` (`APPLEPAY`) and `_hyperpay_get_widget_options` (the `wpwlOptions.applePay` configuration). The payment method `payment_method_apple_pay` (code `Applepay`) is kept from 17.0.
- **Models:** `payment.provider` gets `applepay_entity_id` and `applepay_authorization_bearer` (administrators only, the token is masked), plus `applepay_display_name`, `applepay_merchant_identifier`, `applepay_supported_networks` and `applepay_supported_countries`.
- **Migrated from 17.0 to 19.0:**
  - v17 created a payment transaction and a HyperPay checkout every time the payment page was displayed, and swapped the Pay button for the Apple Pay widget with JavaScript. The transaction and checkout are now created only when the customer clicks **Pay**, through the standard v19 redirect flow. The custom controllers, popup templates and JavaScript were removed.
  - A pre-authorization now becomes **Authorized** (v17: **Done**), and capture, void and refund are native.
  - The hard-coded staging URL for the Apple Pay stylesheet was removed. The Apple Pay options from `tm_payment_applepay_extend` (version 3, `checkAvailability`, merchant identifier) are now provider settings, so that module is no longer needed.
  - The duplicate `account.payment.method` record and override were removed (v19 creates them automatically). Debug `print()` calls that logged the access token were removed.
  - The manifest license was aligned with the module's `LICENSE` file (`OPL-1`).

---
Original module by **Technaureus Info Solutions Pvt. Ltd.** — Odoo 19.0 migration developed and maintained by **Plennix Technologies** — https://www.plennix.com
