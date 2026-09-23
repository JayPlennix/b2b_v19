# Portal Address Restriction

Customer account details and addresses can only be changed by Transmed staff, not by portal users.

## Business Purpose
Transmed keeps each customer's name, contact details and addresses in line with its
own records (JD Edwards), so orders, invoices and deliveries always use the approved
details. Customers and salespersons log in to the B2B website as portal users. This
module stops them from changing those details on the website: they can still see
their account and addresses, but any change has to be requested from the support
team. Internal staff keep full editing rights in Odoo and on the website.

## Key Features
- Customers see their account details on **My Account** but cannot change them, with a clear message to contact support
- The **My Addresses** page shows the customer's addresses without add, edit or remove buttons
- The checkout and payment pages no longer offer to edit an existing address
- The same rule applies to salespersons, so all address changes go through Transmed's team
- Changes are refused by the server too, so they cannot be made by getting around the website screens
- Internal users are not affected

## How It Works (User Flow)
1. A customer or salesperson logs in to the website and opens **My Account** (Edit information).
2. They see their details in greyed-out fields, a message asking them to contact support, and a **Back** button instead of **Save**.
3. On **My Addresses**, they see their delivery and billing addresses without add, edit or remove buttons.
4. During checkout and on the payment page, addresses are shown without an **Edit** link.
5. To change an address, the customer contacts Transmed. Staff update it in Odoo.

## Dependencies
| Module | Why it is needed |
|--------|------------------|
| portal | My Account and My Addresses pages of the customer portal. |
| website_sale | Checkout and payment pages of the web shop. |

## Configuration
No configuration required. The restriction applies to every portal user.

## Technical Notes
- **Rule:** a user is restricted when `res.users._is_portal()` is true (share users, which includes Transmed salespersons). Public (guest) and internal users are not affected.
- **`res.partner._can_be_edited_by_current_customer`** returns `False` for portal users. In Odoo 19, this one method drives the edit and remove buttons of the address cards (`portal.address_card`, `website_sale.address_card`) and the server checks of `/my/address`, `/my/address/submit`, `/my/address/archive`, `/shop/address` and `/shop/address/submit` for existing addresses. It also stops checkout from redirecting portal users to the address form to complete an address.
- **`CustomerPortal.portal_address` / `portal_address_submit`:** portal users are redirected from `/my/address` to `/my/addresses`, and `/my/address/submit` is refused (403). This covers creating addresses from the portal and saving the My Account form.
- **Templates:**
  - `portal.portal_my_details`: fields wrapped in a disabled `<fieldset>`, info message, and **Back** instead of Discard / Save.
  - `portal.my_addresses`: the **Add Address** buttons are hidden.
  - `website_sale.address_edit_button`: the payment page **Edit** / **Want an invoice?** link is hidden.
- **Not changed:** adding a *new* address during checkout is governed by `custom_website`, which lets salespersons add one for their customer.
- **Migrated from 17.0:** 17.0 only hid buttons and disabled fields on `/my/account`, `website_sale.address_kanban` and `website_sale.address_on_payment`. In 19.0 My Account uses the shared portal address form, there is a new My Addresses page, and checkout uses address cards, so the restriction was rebuilt on the 19.0 permission method and is now also enforced by the server.

---
Developed and maintained by **Plennix Technologies** — https://www.plennix.com
