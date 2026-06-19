# Project Overview

Auditmaton: Ads is a professional-grade Python/Flask SaaS audit application targeting digital analytics practitioners and agencies. It provides guided, step-by-step advertising account audits with AI-powered insights, visualizations, and detailed audit reporting across demand-side and supply-side advertising platforms.

The product differentiator is the manual/checklist intake model: practitioners work through audit checks directly inside each platform's own UI. There is no API connection, no OAuth flow, and no platform data ingestion in v1. This keeps the audit AI-slop free by keeping the human in the loop.

## Architecture: Demand vs. Supply Fork

Auditmaton: Ads handles two distinct advertiser roles, each with its own category tree:

- **Demand-side (advertisers)**: audits of Google Ads, Meta Ads, TikTok Ads, Microsoft Ads, LinkedIn Ads, and similar platforms where brands buy ad inventory.
- **Supply-side (publishers)**: audits of Google Ad Manager, AdSense, header-bidding setups (Prebid), and SSP configurations where publishers monetize traffic.

The intake form captures the practitioner's role (demand or supply) and the specific platform they're auditing. The platform selection gates which category tree loads in the dashboard. Taxonomy categories for both sides are TBD and being designed collaboratively.


## Development Environment

- **Python 3.11** with a local virtual environment at `./venv/`
- Activate venv: `source venv/bin/activate`
- Dependencies managed via `requirements.txt`
- Core stack: Flask, SQLAlchemy, PostgreSQL (psycopg2), pandas, Plotly, jsonschema
- Static chart export via kaleido for PDF reports
- Payment processing via Authorize.net (existing merchant services with Bank of America)


### Subscription Tiers

- **Base** — Educate, Investigate, Evaluate, Validate (no charts, no AI), contextual queries
- **Viz** — Everything in Base + Plotly visualizations
- **AI** — Everything in Base + AI chatbot

Lower-tier users see "ghost charts" (watermarked/blurred visualizations) as upgrade incentives.

### Token Allocation

Annual token allocation (not monthly) due to the feast/famine nature of audit work. Users can purchase token packs when they run low.

### Intake System

This edition uses MANUAL / checklist intake only. Practitioners are guided through checks directly inside the ad platform's own UI (Educate + Investigate steps). The intake form captures: audit name/label, the advertiser role (demand-side or supply-side), the specific platform, site type, and narrative voice preferences. There is no file upload and no API connection to any ad platform in v1.

### Device Access Controls

Two-device limit per account using browser fingerprinting and persistent tokens to prevent credential sharing among agency teams.
