# SatisfyForge Kroger Deal Engine

Zero-cost Kroger price/store intelligence built on Kroger's public developer API.

## What it does now

- Finds Kroger-family locations near a ZIP code.
- Searches products at a specific location so the API can return local price/availability data.
- Normalizes regular vs promotional price.
- Builds a simple basket estimate and chooses the lowest-priced returned match for each search term.
- Keeps client credentials out of source code and output.
- Uses only Node's built-in APIs; no paid dependency is required.

## What it does **not** do

It does **not** clip Kroger digital coupons. A supported public coupon-clipping API operation has not been established. Do not label this tool as a coupon clipper or claim coupons were loaded to a loyalty account.

The public Kroger developer surface documents Products, Locations, Identity and Cart capabilities. Actual account coupon clipping remains a separate authenticated-store capability unless Kroger provides a supported endpoint/workflow.

## Credentials

Create/register an application in Kroger's developer program and provide credentials at runtime only:

```bash
export KROGER_CLIENT_ID='...'
export KROGER_CLIENT_SECRET='...'
```

Optional:

```bash
export KROGER_SCOPE='product.compact'
```

Never commit these values, print them in CI logs or paste them into a public GitHub issue.

## Commands

```bash
node cli.mjs locations --zip 45044 --limit 10
node cli.mjs search --location LOCATION_ID --term "whole milk" --limit 10
node cli.mjs basket --location LOCATION_ID --item "milk*2" --item "eggs" --item "bread"
```

All command output is JSON so the Master Command Center, a future Control Center panel or another script can consume it safely.

## Basket truth boundary

The basket command is an **estimate**, not an order or guaranteed final receipt. Search matching can choose an imperfect substitute, store prices/availability change, taxes are not computed, loyalty-only discounts may not be represented, and digital coupons are not clipped. Before shopping, review the actual selected products/store cart.

## Tests

```bash
npm test
```

The test suite mocks Kroger network responses. It verifies token caching, URL/filter construction, price normalization, basket math and safety errors without requiring real credentials or API usage.

## Future zero-cost additions

When a Kroger developer credential is connected securely:
- save a preferred store ID in the private Control Center rather than source code;
- compare recurring grocery-list prices over time;
- flag promo-price drops;
- output a store-ready shopping list;
- optionally add authenticated Cart integration only through Kroger's documented user OAuth flow;
- keep digital-coupon status separate until a supported coupon endpoint exists.
