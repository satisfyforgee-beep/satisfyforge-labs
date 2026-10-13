# SatisfyForge zero-cost content operations

This directory contains independent building blocks. They are **not** a deployed service or an unlimited substitute for third-party APIs.

## Generate content drafts

```bash
python3 tools/content_factory.py --topic "missed roofing calls" --audience "roofing contractors" --url "https://example.com/audit"
```

The generator creates JSON drafts. Review factual claims, licensing and audience fit before publishing.

## Store drafts and leads locally

```bash
python3 tools/library.py add-asset --kind social --title "Missed calls" --body "A practical tip..."
python3 tools/library.py add-lead --source wix --company "Example Co" --notes "Demo only"
python3 tools/library.py list --type assets
python3 tools/library.py export --type leads
```

Default database: `data/satisfyforge.db`. Keep real contact data out of public GitHub. Back up this database privately. Never commit it or API keys.

## Build a queue

```bash
python3 tools/build_queue.py --max-items 10
```

Only assets marked `approved` are included; new assets default to `draft`. Current library CLI intentionally does not have an approval command; approval requires deliberate database/workflow integration before production use. The queue is exported locally and **not posted to Buffer**.

## Production boundaries

- No autonomous email sending, platform posting, payment collection, or live website deployment is enabled by these scripts.
- No claimed revenue, customer testimonials, performance results, or success rates without evidence.
- Platform API quotas, hosting capacity, rate limits, anti-spam requirements and licensed media restrictions still apply.
- Use business sender `satisfyforgee@gmail.com` for authorized business communications; do not hardcode account credentials.
- Run locally or on infrastructure you control. Add explicit review gates, retry logic, backups, deduplication, security and monitoring before unattended deployment.
