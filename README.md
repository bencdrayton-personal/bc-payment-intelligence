# BigCommerce Merchant Payment Intelligence Scorer

A lightweight scoring model that prioritises payment methods for BigCommerce merchants based on merchant profile, segment, geography, and AOV.

Built as a portfolio artefact demonstrating applied payments product thinking. Relevant to Commerce's stated 2026 direction: embedded payments expansion, B2B innovation, and agent-enabled checkout (Commerce Live 2026).

---

## The Problem

Most BigCommerce merchants choose payment methods reactively — enable Stripe, add PayPal, maybe Afterpay because a friend recommended it. The selection is rarely driven by structured analysis of who their customers are, what they're buying, where they are, or how they pay.

The consequence: checkout conversion left on the table, processing costs higher than necessary, and a payment method mix that doesn't map to the merchant's actual growth levers.

---

## What This Does

Given a merchant profile, the scorer evaluates **14 payment methods** available on BigCommerce across **8 dimensions** weighted to match the merchant's context.

Output: a ranked table with scores, recommendations (`🚀 High priority`, `✅ Already active`, `💡 Worth evaluating`, `⬇ Low priority`), and rationale for high-priority items.

---

## Scoring Dimensions

| Dimension | What it measures |
|---|---|
| `bc_native` | How natively integrated? (5 = one-click control panel, 1 = custom/headless) |
| `b2c_fit` | Match to B2C consumer checkout expectations |
| `b2b_fit` | Support for enterprise purchasing — invoicing, ACH, net terms |
| `aov_fit` | Does the merchant's AOV fall in this method's documented sweet spot? |
| `geo_coverage` | Fraction of the merchant's active markets supported |
| `mobile_agentic` | SDK-compatible? Works in agent-driven checkout flows? |
| `conversion_uplift` | Evidence-based estimated lift, normalised 0–5 |
| `impl_complexity` | Time to activate for a BC merchant (5 = trivial, 1 = heavy build) |

Weights are merchant-specific and sum to 1.0. Zero-weighted dimensions are intentionally excluded — they signal what *not* to optimise for in that context.

---

## Merchant Profiles Included

| Profile | Segment | Markets | AOV | Key weight |
|---|---|---|---|---|
| SMB Apparel | B2C | US | $85 | Conversion uplift (0.35), mobile/agentic (0.25) |
| B2B SaaS Enterprise | B2B | US + AU | $2,400 | B2B fit (0.30), conversion uplift (0.25), AOV fit (0.20) |
| Multi-Geo Marketplace | B2B+B2C | US / UK / AU | $150 | Geo coverage (0.25), conversion uplift (0.20) |

---

## Sample Output — B2B SaaS Enterprise (US + AU, AOV $2,400)

```
Payment Method            Score /5   Action                         BC Integration          Est. Lift
B2B Invoice / Net Terms   4.70       🚀  High priority — add this   B2B Edition             +20%
Stripe                    3.73       ✅  Already active              Native partner           +6%
ACH / Bank Transfer       3.67       🚀  High priority — add this   Native via gateway        +8%
Adyen                     3.55       🚀  High priority — add this   Native partner            +5%
Checkout.com              3.20       💡  Worth evaluating            Native partner            +4%
Klarna                    2.85       💡  Worth evaluating            Native partner           +12%
...
```

High Priority rationale for B2B Invoice / Net Terms:
> BC B2B Edition supports net terms and invoice payment natively. "B2B automation and pricing" was a headline item in Commerce Live 2026 roadmap. Removes payment as a blocker in enterprise sales cycles — highest potential lift for B2B merchants.

---

## Running It

```bash
pip install pandas
jupyter notebook bc_payment_intelligence.ipynb
```

Or run the scorer standalone:

```bash
python scorer.py
```

---

## Data Sources

Built against BigCommerce's live ecosystem as of June 2026:

- [Payments API docs](https://developer.bigcommerce.com/docs/store-operations/payments)
- [US payment gateway list](https://www.bigcommerce.com/payments/gateways/united-states) — Adyen, Affirm, Afterpay, Amazon Pay, Authorize.net, Bolt, Chase, Checkout.com, Klarna, PayPal, Braintree, Sezzle, Square, Stripe, WorldPay, Zip + others
- [AU payment gateway list](https://www.bigcommerce.com/payments/gateways/australia) — Adyen, Afterpay, Checkout.com, CommBank MIGS, eWAY, Humm, Klarna, Laybuy, OpenPay, Stripe, Windcave, Zip
- [Commerce Live EMEA 2026](https://www.bigcommerce.com/blog/commerce-live-emea-2026/) — agentic commerce roadmap, Adyen partnership
- [BigCommerce × Stripe Agentic Commerce Suite](https://investors.bigcommerce.com/news-releases/news-release-details/bigcommerce-partners-stripe-support-new-agentic-commerce-suite)
- [checkout-sdk-js](https://github.com/bigcommerce/checkout-sdk-js) — Checkout SDK underpinning agentic and custom checkout flows

---

## What I'd Build Next

**1. Live merchant data connection** — Pull AOV, traffic split, and geo distribution from BC's Merchant and Orders APIs rather than manually-specified profiles. Scoring becomes per-merchant, not per-archetype.

**2. Cohort benchmarking** — Compare a merchant's payment method mix against cohort peers (same MCC, similar AOV band, same geography). Surface gaps: "B2B merchants in your band with ACH enabled see 8% lower abandonment."

**3. Commerce Companion integration** — The Commerce Live 2026 roadmap introduced Commerce Companion (AI assistant embedded in BC admin). Natural integration: surface scorer output as a Companion recommendation at the right moment in the merchant's journey.

**4. A/B hypothesis generator** — For each high-priority method, generate a pre-formatted test hypothesis: statement, primary metric, MDE, estimated sample size at current traffic. Moves from "what to add" to "how to validate it."

**5. Agentic checkout readiness score** — A separate assessment of a merchant's overall readiness for agent-driven purchases (Commerce's explicit 2026 direction): Checkout SDK integration, stored instrument support, Apple Pay / Google Pay presence, headless storefront capability. Output: a readiness score with specific gap list.

---

*All conversion lift estimates are drawn from published payment provider research. Actual uplift varies by merchant context.*
