# SatisfyForge Payment Routing

## Default payment path

SatisfyForge prefers PayPal as the customer-payment destination through a verified Payhip checkout when a checkout is confirmed to have the intended price and terms.

- Digital products: use only a checkout whose current price and product status were independently verified.
- Custom services: collect the lead and written scope first, then send a verified payment option for the agreed amount.
- Do not ask customers to send money directly to a bank account.
- Never tell a customer that a checkout is ready unless that exact URL, price, and product configuration have been verified.

## Current payment safety hold — 2026-10-16

Signed-out Chrome verification confirmed the following public Payhip prices and pages:

- Tool Vault `KLjBb` — **$49** Founding Lifetime Access.
- Lead Rescue Sprint `hxbPR` — **$299**.
- Custom Platform / Licensing `HXq9E` — **$5,000**.

All three remain **quarantined from promotion**. Tool Vault still exposes default Payhip membership-template copy. Lead Rescue Sprint and Custom Platform / Licensing still expose default Payhip coaching-template headings, example sections, and generic FAQ copy. Authenticated seller identity is not yet verified in the current session. Completed checkout/automatic fulfillment is still transaction-untested for the digital offer, and the service handoff/commercial terms must be reviewed before service checkout is promoted.

The live Wix request/scope form remains the safe route for quarantined offers. Do not advertise or send those Payhip checkout URLs until the corresponding entry in `commerce/checkout_registry.json` has been cleared after identity, copy, terms, and required checkout/handoff verification.

The Strange True Story Shorts Creator Kit `MSLBK` was rechecked signed-out on 2026-10-16 at **$7.99** with the correct title, Add to Cart / Buy Now controls, full sales copy, and a **250 KB ZIP** disclosure. Successful completed payment and automatic file delivery remain unverified without a real transaction or supported seller-side fulfillment preview.

## Chime policy

Chime is not a customer-facing payment method. Do not publish or send Chime account or routing information to customers.

Chime may be used only as the owner's settlement/payout bank on a platform that requires a bank destination, after the owner completes any required bank verification.

## Stripe policy

Do not connect Stripe or route payments through Stripe unless the owner explicitly asks for it.

## Custom-service rule

Use the Wix request/scope form to collect the project details first. Agree to the deliverable, boundaries, price, and any no-guarantee terms in writing before payment. Payment should follow only through a verified customer-facing payment path.

## Safety

- Never store PayPal passwords, Chime credentials, bank account numbers, routing numbers, tax IDs, or other payment secrets in GitHub.
- Never invent a PayPal username, payment link, bank destination, or payout account.
- Never describe a checkout as live until the external checkout is verified.
- Never spend money to repair a payment workflow without explicit approval for that exact charge.
