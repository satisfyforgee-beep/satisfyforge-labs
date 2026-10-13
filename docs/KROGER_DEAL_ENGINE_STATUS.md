# Kroger Deal Engine — Status

Updated 2026-10-13.

## Built and merged

The owned zero-cost Kroger Deal Engine is now in `tools/kroger-deal-engine/` on `main`.

Capabilities:
- find Kroger-family locations near a ZIP code;
- search store-specific products/prices by location ID;
- normalize regular and promotional prices;
- estimate a multi-item basket and choose the lowest-priced returned match for each search term;
- JSON CLI output for future Control Center integration;
- runtime-only client credentials, never hardcoded in source;
- mocked automated tests and a dedicated GitHub Actions CI workflow.

Pull request: #13 — `Add owned Kroger Deal Engine`.
Branch CI run `38372393352` passed before merge.

## Not a coupon clipper

No supported public Kroger digital-coupon clipping endpoint has been established. This tool must not claim it clipped or loaded digital coupons to a loyalty account.

Kroger's public developer API can support store/product/location/cart intelligence; coupon clipping remains a separate authenticated-store capability unless Kroger provides a supported operation.

## Remaining owner-only connection

A Kroger developer application/client credential is required before real API calls can run. Do not put the client secret in GitHub, chat, public issues or screenshots.

Once credentials exist, the preferred next integration is a private Control Center secret/resource connection. Store only non-sensitive preferred-store metadata in the database.

## Next zero-cost capability after connection

1. Resolve the preferred store near the desired ZIP/location.
2. Run recurring grocery-list searches on demand.
3. Save price observations privately so price drops can be compared over time.
4. Produce a store-ready shopping list with promo flags.
5. Add Kroger Cart integration only through Kroger's documented user-auth flow if useful.
6. Keep coupon status explicitly separate until a supported clipping API/workflow exists.

## Tests

The current tests verify:
- location normalization;
- promo-price selection;
- OAuth client-credential token caching;
- safe URL/filter construction;
- basket quantity/math behavior;
- missing-credential and empty-basket failures.

No real Kroger credentials or customer loyalty data are used by CI.
