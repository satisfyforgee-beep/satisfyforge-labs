# SatisfyForge Payment Routing

## Default payment path

SatisfyForge uses PayPal as the default customer-payment destination through Payhip wherever a Payhip checkout exists.

- Digital products and memberships: Payhip checkout -> connected PayPal account.
- Fixed-price services and deposits: create a Payhip/PayPal-backed checkout before asking the customer to pay.
- Custom projects: scope the work first, then send a PayPal/Payhip payment link or invoice for the agreed amount or deposit.
- Do not ask customers to send money directly to a bank account.

## Chime policy

Chime is not a customer-facing payment method. Do not publish or send Chime account or routing information to customers.

Chime may be used only as the owner's settlement/payout bank on a platform that requires a bank destination, after the owner completes any required bank verification.

## Stripe policy

Do not connect Stripe or route payments through Stripe unless the owner explicitly asks for it. Existing PayPal-backed Payhip checkout remains the default.

## Current verified checkout

SatisfyForge Tool Vault: https://payhip.com/b/KLjBb

Price: $49 one-time Founding Lifetime Access.

## Custom-service rule

A custom-service CTA can collect the lead and scope first. Payment should follow only after the price and deliverable are agreed. The payment link/invoice must use the PayPal/Payhip route once available.

## Safety

- Never store PayPal passwords, Chime credentials, bank account numbers, routing numbers, tax IDs, or other payment secrets in GitHub.
- Never invent a PayPal username, payment link, bank destination, or payout account.
- Never describe a checkout as live until the external checkout is verified.
