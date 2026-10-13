# SatisfyForge Payment Routing

## Default payment path

SatisfyForge prefers PayPal as the customer-payment destination through a verified Payhip checkout when a checkout is confirmed to have the intended price and terms.

- Digital products: use only a checkout whose current price and product status were independently verified.
- Custom services: collect the lead and written scope first, then send a verified payment option for the agreed amount.
- Do not ask customers to send money directly to a bank account.
- Never tell a customer that a checkout is ready unless that exact URL, price, and product configuration have been verified.

## Current payment safety hold — 2026-10-12

A Payhip audit showed the SatisfyForge Tool Vault dashboard/listing at **$0.00** while the Wix site was advertising it as **$49 one time**. Because of this mismatch, the direct Tool Vault purchase path is temporarily paused.

The live Wix homepage and pricing page now route Tool Vault calls-to-action to the existing Wix request form rather than directly to the Payhip product. The site tells visitors that checkout is temporarily paused while payment setup is corrected.

Do **not** advertise or send `https://payhip.com/b/KLjBb` as a $49 checkout until Payhip itself has been rechecked and the intended price is confirmed.

Earlier automation state also contained six alleged Payhip coaching/service checkout URLs. Tool evidence about these conflicted, so they are **unverified**. Do not send or promote them until each URL, price, product type, terms, and status are independently rechecked in Payhip.

TinyFish interactive Payhip editing is currently blocked by a negative wallet balance. Under the standing zero-spend rule, do not top it up automatically. Continue other $0 work instead.

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
