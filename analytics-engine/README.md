# SatisfyForge Analytics Import Layer

Zero-cost analytics normalization for Creator OS and the wider SatisfyForge stack.

The first version consumes CSV exports and converts them into one evidence schema so platform data can be compared without another paid dashboard.

## Supported normalized fields

- platform
- content ID
- title/caption
- published date
- views
- likes
- comments
- shares
- saves
- clicks
- revenue
- source file
- observation timestamp

Common alternate column names are recognized automatically. Missing metrics become zero rather than being invented.

## Run

```bash
python analytics-engine/normalize.py \
  --input youtube-export.csv \
  --platform youtube \
  --output normalized.json
```

The result includes raw normalized observations plus evidence-only totals and ratios:

- engagement / view
- click / view
- revenue per 1,000 views
- leaders by views, revenue and revenue per 1,000 views

## Why this exists

Creator OS should rank content and money experiments from observed results rather than guesses. This layer is the bridge from platform exports/APIs into that owned data model.

## Boundaries

- No fabricated views, engagement, sales or revenue.
- No scraping private analytics pages or bypassing platform authentication.
- CSV/API data stays separate from recommendations so observed facts can be audited.
- Live API connectors can be added only through official/authorized routes.

## Next

1. Creator OS import button for `satisfyforge.analytics.v1`.
2. Official API adapters for connected accounts where permissions exist.
3. Content-family tagging so hooks/topics/offers can be compared.
4. Time-window comparison and retention metrics when the source platform provides them.
