# Skill Vault venue revenue model

This is a planning model only; demo plays are never counted as revenue.

## Placement model
A simple future commercial structure is owner-operated placement with a venue revenue share:
- SatisfyForge supplies/maintains the approved kiosk, software and reporting.
- Venue supplies floor space, power and day-to-day supervision.
- Prize stocking responsibility is defined in the venue agreement.
- Collected play revenue is reconciled from the payment provider, not from the game counter.
- The prototype configuration models a 70% owner / 30% venue top-line split; the real agreement can be changed after costs and compliance are known.

## Example unit economics — hypothetical approved $2 play
| Item | Per play |
| --- | ---: |
| Gross collected | $2.00 |
| Example venue share at 30% | $0.60 |
| Example merchandise cost | $0.17 |
| Example payment/ops reserve | $0.20 |
| Remaining before tax, hardware, maintenance and overhead | $1.03 |

The merchandise-cost number is only an illustrative score/redemption model. Real score distribution and redemption behavior must be measured in an approved pilot.

## Scale checkpoints
1. One approved pilot kiosk proves uptime, compliance, payment reconciliation and prize economics.
2. Expand to 3–5 nearby venues only after the pilot is positive after all real costs.
3. Standardize cabinet, approved software hash, prize catalog and venue contract.
4. Add remote health/status reporting before broader placement.
5. Only then consider machine sales, leases, licensing or a venue software subscription.

## Rules for reporting money
- `actual.collectedCents` comes only from verified payment settlement/authorization integration.
- Demo plays and modeled revenue remain separate.
- Do not call modeled margin profit; taxes, hardware depreciation, repairs, insurance, licensing, venue obligations and prize inventory still apply.
