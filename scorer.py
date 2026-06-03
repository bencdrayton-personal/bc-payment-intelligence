"""
BigCommerce Merchant Payment Intelligence Scorer
Ben Drayton | June 2026

Scores 14 BigCommerce-integrated payment methods against merchant profiles
across 8 dimensions. Outputs a prioritised action list per merchant segment.

Data source: BigCommerce developer docs + payments/gateways pages (June 2026)
  - developer.bigcommerce.com/docs/store-operations/payments
  - bigcommerce.com/payments/gateways/united-states
  - bigcommerce.com/payments/gateways/australia
  - Commerce Live EMEA 2026 product roadmap announcements
"""

import pandas as pd

pd.set_option("display.max_colwidth", 80)
pd.set_option("display.width", 160)

# ─── Payment Methods Database ──────────────────────────────────────────────────
#
# Built from BigCommerce's live gateway pages (June 2026).
# bc_native scores:
#   5 = native control panel (one-click, no dev required)
#   4 = native partner (pre-integrated, minimal config)
#   3 = partner integration (app store / supported gateway)
#   2 = B2B Edition feature
#   1 = custom / headless only
# All other dimensions scored 1–5 (higher = better fit)

PAYMENT_METHODS = {
    "BC Payments (PayPal)": {
        "bc_native": 5,
        "bc_integration_type": "Native — control panel",
        "b2c_fit": 4,
        "b2b_fit": 2,
        "aov_sweet_spot": (10, 500),
        "geo_coverage": ["US"],
        "mobile_agentic": 4,
        "conversion_lift_pct": 8,
        "impl_complexity": 5,
        "note": (
            "Embedded solution powered by PayPal. Single on-site flow includes "
            "Apple Pay, Google Pay, Afterpay, Klarna, Venmo, PayPal Pay Later. "
            "US-only (Standard/Plus/Pro). Announced at Commerce Live 2026."
        ),
    },
    "Stripe": {
        "bc_native": 4,
        "bc_integration_type": "Native partner",
        "b2c_fit": 5,
        "b2b_fit": 4,
        "aov_sweet_spot": (10, 50000),
        "geo_coverage": ["US", "AU", "UK", "EU", "GLOBAL"],
        "mobile_agentic": 5,
        "conversion_lift_pct": 6,
        "impl_complexity": 4,
        "note": (
            "BC's designated partner for the Agentic Commerce Suite "
            "(Commerce Live 2026). Stripe Link accelerates guest checkout. "
            "Supports OCS, ACH, stored instruments, and agentic cart/checkout via API. "
            "GitHub: bigcommerce/checkout-sdk-js."
        ),
    },
    "Adyen": {
        "bc_native": 3,
        "bc_integration_type": "Native partner",
        "b2c_fit": 4,
        "b2b_fit": 4,
        "aov_sweet_spot": (100, 100000),
        "geo_coverage": ["US", "AU", "UK", "EU", "GLOBAL"],
        "mobile_agentic": 4,
        "conversion_lift_pct": 5,
        "impl_complexity": 3,
        "note": (
            "Title sponsor of Commerce Live EMEA 2026. Preferred enterprise partner "
            "for multi-geo merchants. Adyen UK MD presented on agentic commerce "
            "infrastructure. Strong local payment method coverage across 30+ markets."
        ),
    },
    "PayPal Commerce Platform": {
        "bc_native": 4,
        "bc_integration_type": "Native partner",
        "b2c_fit": 5,
        "b2b_fit": 2,
        "aov_sweet_spot": (10, 500),
        "geo_coverage": ["US", "AU", "UK", "EU", "GLOBAL"],
        "mobile_agentic": 3,
        "conversion_lift_pct": 7,
        "impl_complexity": 4,
        "note": (
            "Standalone from BC Payments bundle. High consumer trust globally. "
            "Fastlane by PayPal available for accelerated guest checkout. "
            "Also powers BC Payments (US) as underlying processor."
        ),
    },
    "Afterpay / Clearpay": {
        "bc_native": 3,
        "bc_integration_type": "Native partner",
        "b2c_fit": 5,
        "b2b_fit": 1,
        "aov_sweet_spot": (30, 500),
        "geo_coverage": ["US", "AU", "UK"],
        "mobile_agentic": 3,
        "conversion_lift_pct": 15,
        "impl_complexity": 4,
        "note": (
            "AU-originator BNPL. ~15% documented conversion + AOV lift in $30–$500 range. "
            "Available standalone or bundled in BC Payments (US). "
            "Listed on BC's AU gateway page natively."
        ),
    },
    "Klarna": {
        "bc_native": 3,
        "bc_integration_type": "Native partner",
        "b2c_fit": 5,
        "b2b_fit": 2,
        "aov_sweet_spot": (30, 1500),
        "geo_coverage": ["US", "AU", "UK", "EU"],
        "mobile_agentic": 3,
        "conversion_lift_pct": 12,
        "impl_complexity": 4,
        "note": (
            "Broad BNPL AOV range; stronger than Afterpay above $500. "
            "Dominant in EU/UK. Included in BC Payments bundle (US). "
            "Listed on AU gateway page."
        ),
    },
    "Affirm": {
        "bc_native": 3,
        "bc_integration_type": "Native partner",
        "b2c_fit": 4,
        "b2b_fit": 1,
        "aov_sweet_spot": (100, 3000),
        "geo_coverage": ["US"],
        "mobile_agentic": 3,
        "conversion_lift_pct": 10,
        "impl_complexity": 4,
        "note": (
            "US-only. Better fit than Afterpay/Klarna for $100–$3k AOV range. "
            "Listed on BC US gateway page natively."
        ),
    },
    "Amazon Pay": {
        "bc_native": 4,
        "bc_integration_type": "Native partner",
        "b2c_fit": 4,
        "b2b_fit": 2,
        "aov_sweet_spot": (20, 500),
        "geo_coverage": ["US", "UK", "EU"],
        "mobile_agentic": 3,
        "conversion_lift_pct": 5,
        "impl_complexity": 4,
        "note": (
            "Leverages Amazon account trust and stored payment/address data. "
            "Strong for Prime-aligned consumer segments. "
            "Mentioned in BC's digital wallets accelerated checkout offering."
        ),
    },
    "Apple Pay / Google Pay": {
        "bc_native": 4,
        "bc_integration_type": "Native via gateway",
        "b2c_fit": 5,
        "b2b_fit": 2,
        "aov_sweet_spot": (10, 300),
        "geo_coverage": ["US", "AU", "UK", "EU", "GLOBAL"],
        "mobile_agentic": 5,
        "conversion_lift_pct": 10,
        "impl_complexity": 4,
        "note": (
            "Enabled via Stripe, BC Payments (US), or Braintree — no separate gateway needed. "
            "Critical for mobile conversion and agentic checkout interfaces "
            "(Commerce's stated 2026 strategic direction). "
            "Eliminates form-fill friction on mobile."
        ),
    },
    "ACH / Bank Transfer": {
        "bc_native": 3,
        "bc_integration_type": "Native via gateway",
        "b2c_fit": 2,
        "b2b_fit": 5,
        "aov_sweet_spot": (500, 500000),
        "geo_coverage": ["US"],
        "mobile_agentic": 3,
        "conversion_lift_pct": 8,
        "impl_complexity": 3,
        "note": (
            "US ACH available via Stripe (bank debit) and Braintree. "
            "Dominant B2B payment rail for high-AOV transactions. "
            "Eliminates ~2.9% card fee — material at enterprise order values. "
            "BC Payments API supports stored instruments for recurring ACH."
        ),
    },
    "B2B Invoice / Net Terms": {
        "bc_native": 2,
        "bc_integration_type": "B2B Edition",
        "b2c_fit": 1,
        "b2b_fit": 5,
        "aov_sweet_spot": (1000, 1000000),
        "geo_coverage": ["US", "AU", "UK", "EU", "GLOBAL"],
        "mobile_agentic": 2,
        "conversion_lift_pct": 20,
        "impl_complexity": 2,
        "note": (
            "BC B2B Edition supports net terms and invoice payment natively. "
            "B2B automation and pricing were headline items in Commerce Live 2026 roadmap. "
            "Removes payment as a blocker in enterprise sales cycles — "
            "highest potential lift for B2B segments."
        ),
    },
    "Zip / Quadpay": {
        "bc_native": 3,
        "bc_integration_type": "Native partner",
        "b2c_fit": 4,
        "b2b_fit": 1,
        "aov_sweet_spot": (30, 1000),
        "geo_coverage": ["US", "AU"],
        "mobile_agentic": 3,
        "conversion_lift_pct": 8,
        "impl_complexity": 4,
        "note": (
            "AU-originator; listed natively on BC AU gateway page. "
            "US presence growing under Zip brand (formerly Quadpay). "
            "Good BNPL complement to Afterpay for AU merchants."
        ),
    },
    "Checkout.com": {
        "bc_native": 3,
        "bc_integration_type": "Native partner",
        "b2c_fit": 4,
        "b2b_fit": 3,
        "aov_sweet_spot": (20, 100000),
        "geo_coverage": ["US", "AU", "UK", "EU", "GLOBAL"],
        "mobile_agentic": 3,
        "conversion_lift_pct": 4,
        "impl_complexity": 3,
        "note": (
            "Listed on BC AU and US gateway pages. "
            "Strong for high-volume international enterprise; "
            "competitive fraud tooling and local payment method coverage."
        ),
    },
    "Square": {
        "bc_native": 4,
        "bc_integration_type": "Native partner",
        "b2c_fit": 4,
        "b2b_fit": 2,
        "aov_sweet_spot": (10, 500),
        "geo_coverage": ["US", "AU", "UK"],
        "mobile_agentic": 3,
        "conversion_lift_pct": 3,
        "impl_complexity": 5,
        "note": (
            "Best for omnichannel merchants running POS + online from one account. "
            "Lowest setup friction (native BC integration). "
            "Listed on AU and US gateway pages."
        ),
    },
}

# ─── Merchant Profiles ─────────────────────────────────────────────────────────
#
# Each profile includes dimension weights that sum to 1.0.
# Weights reflect what matters most for that merchant's context.
# Zero-weighted dimensions are excluded from scoring — intentional signal
# about what NOT to optimise for.

MERCHANT_PROFILES = {
    "smb_apparel_b2c": {
        "name": "SMB Apparel — B2C (US, AOV $85)",
        "description": "Fashion retailer, US market, 72% mobile traffic, growing DTC brand",
        "segment": "B2C",
        "geography": ["US"],
        "avg_order_value": 85,
        "mobile_traffic_pct": 72,
        "b2b_pct": 0,
        "bc_plan": "Plus",
        "current_methods": ["Stripe", "PayPal Commerce Platform"],
        "weights": {
            "conversion_uplift": 0.35,  # Primary lever: add-to-cart → purchase
            "mobile_agentic":    0.25,  # 72% mobile means wallet + agent-readiness critical
            "impl_complexity":   0.20,  # SMB — time to value matters
            "b2c_fit":           0.10,
            "bc_native":         0.10,
            "b2b_fit":           0.00,  # Not relevant
            "geo_coverage":      0.00,  # US only — not a differentiator
            "aov_fit":           0.00,
        },
    },
    "b2b_software_enterprise": {
        "name": "B2B SaaS — Enterprise (US + AU, AOV $2,400)",
        "description": "Enterprise software, complex sales cycle, annual contracts, 90% B2B",
        "segment": "B2B",
        "geography": ["US", "AU"],
        "avg_order_value": 2400,
        "mobile_traffic_pct": 25,
        "b2b_pct": 90,
        "bc_plan": "Enterprise",
        "current_methods": ["Stripe", "PayPal Commerce Platform"],
        "weights": {
            "b2b_fit":           0.30,  # B2B payment behaviour dominates
            "conversion_uplift": 0.25,  # Reducing friction in enterprise purchase flow
            "aov_fit":           0.20,  # Must suit high-value transactions
            "geo_coverage":      0.15,  # US + AU both active markets
            "bc_native":         0.05,
            "impl_complexity":   0.05,  # Enterprise can absorb implementation effort
            "mobile_agentic":    0.00,  # Desktop-dominant
            "b2c_fit":           0.00,
        },
    },
    "multi_geo_marketplace": {
        "name": "Multi-Geo Marketplace (US / UK / AU, AOV $150)",
        "description": "B2B+B2C marketplace expanding internationally, mixed segment",
        "segment": "B2B+B2C",
        "geography": ["US", "UK", "AU"],
        "avg_order_value": 150,
        "mobile_traffic_pct": 55,
        "b2b_pct": 35,
        "bc_plan": "Enterprise",
        "current_methods": ["Stripe", "PayPal Commerce Platform", "Afterpay / Clearpay"],
        "weights": {
            "geo_coverage":      0.25,  # Multi-market reach is the hard constraint
            "conversion_uplift": 0.20,
            "b2c_fit":           0.15,
            "b2b_fit":           0.15,
            "mobile_agentic":    0.15,  # 55% mobile + Commerce's agentic direction
            "aov_fit":           0.05,
            "bc_native":         0.05,
            "impl_complexity":   0.00,
        },
    },
}


# ─── Scoring Engine ────────────────────────────────────────────────────────────

def score_aov_fit(aov: float, aov_min: float, aov_max: float) -> float:
    """Score how well merchant AOV falls within the method's documented sweet spot."""
    if aov_min <= aov <= aov_max:
        return 5.0
    elif aov < aov_min:
        gap_ratio = (aov_min - aov) / aov_min
        return max(1.0, round(5 * (1 - gap_ratio), 1))
    else:
        gap_ratio = (aov - aov_max) / aov_max
        return max(1.0, round(5 * (1 - min(gap_ratio, 0.8)), 1))


def score_geo_coverage(merchant_geos: list, method_geos: list) -> float:
    """Fraction of merchant's active markets covered by this payment method."""
    if "GLOBAL" in method_geos:
        return 5.0
    covered = sum(1 for g in merchant_geos if g in method_geos)
    return round((covered / len(merchant_geos)) * 5, 1)


def lift_to_score(lift_pct: float) -> float:
    """Normalise estimated conversion lift % to a 0–5 score."""
    return min(5.0, round(lift_pct / 4.0, 1))


def score_method(method_key: str, method_data: dict, merchant: dict) -> dict:
    """
    Score a single payment method against a merchant profile.

    Returns a dict suitable for a DataFrame row.
    """
    weights = merchant["weights"]

    scores = {
        "bc_native":         float(method_data["bc_native"]),
        "b2c_fit":           float(method_data["b2c_fit"]),
        "b2b_fit":           float(method_data["b2b_fit"]),
        "aov_fit":           score_aov_fit(
                                 merchant["avg_order_value"],
                                 *method_data["aov_sweet_spot"]
                             ),
        "geo_coverage":      score_geo_coverage(
                                 merchant["geography"],
                                 method_data["geo_coverage"]
                             ),
        "mobile_agentic":    float(method_data["mobile_agentic"]),
        "conversion_uplift": lift_to_score(method_data["conversion_lift_pct"]),
        "impl_complexity":   float(method_data["impl_complexity"]),
    }

    weighted_total = sum(
        scores[dim] * weight for dim, weight in weights.items()
    )

    # Hard exclusion: method doesn't operate in any of the merchant's markets
    geo_score = scores["geo_coverage"]
    if geo_score == 0:
        weighted_total = 0.0
        status = "❌  Not available in merchant's markets"
    elif method_key in merchant.get("current_methods", []):
        status = "✅  Already active"
    elif weighted_total >= 3.5:
        status = "🚀  High priority — add this"
    elif weighted_total >= 2.0:
        status = "💡  Worth evaluating"
    else:
        status = "⬇   Low priority"

    return {
        "Payment Method":   method_key,
        "Score /5":         round(weighted_total, 2),
        "Recommendation":   status,
        "BC Integration":   method_data["bc_integration_type"],
        "Est. Lift":        f"+{method_data['conversion_lift_pct']}%",
        "Notes":            method_data["note"],
    }


def run_analysis(profile_key: str) -> pd.DataFrame:
    """Score all payment methods for a given merchant profile and print results."""
    merchant = MERCHANT_PROFILES[profile_key]

    print()
    print("=" * 80)
    print(f"  {merchant['name']}")
    print(f"  {merchant['description']}")
    print("=" * 80)
    print(f"  Segment: {merchant['segment']}  |  "
          f"Markets: {', '.join(merchant['geography'])}  |  "
          f"AOV: ${merchant['avg_order_value']:,}  |  "
          f"Mobile: {merchant['mobile_traffic_pct']}%  |  "
          f"BC Plan: {merchant['bc_plan']}")
    print()

    # Score every method
    results = [
        score_method(k, v, merchant)
        for k, v in PAYMENT_METHODS.items()
    ]

    df = (
        pd.DataFrame(results)
        .sort_values("Score /5", ascending=False)
        .reset_index(drop=True)
    )
    df.index += 1  # 1-based rank

    # ── Summary table (without Notes column for readability) ──
    summary_cols = ["Payment Method", "Score /5", "Recommendation", "BC Integration", "Est. Lift"]
    print(df[summary_cols].to_string(index=True))
    print()

    # ── Detail: high-priority items only ──
    high = df[df["Recommendation"].str.contains("High priority", na=False)]
    if not high.empty:
        print("── High Priority — Rationale " + "─" * 50)
        for _, row in high.iterrows():
            print(f"\n  {row['Payment Method']} (Score: {row['Score /5']})")
            # Word-wrap the note at 72 chars
            import textwrap
            for line in textwrap.wrap(row["Notes"], width=72):
                print(f"    {line}")
        print()

    return df


# ─── Run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\nBigCommerce Merchant Payment Intelligence Scorer")
    print("Data: BC developer docs + gateway pages + Commerce Live 2026")
    print("Ben Drayton | June 2026\n")

    for profile_key in MERCHANT_PROFILES:
        run_analysis(profile_key)

    print("\n" + "=" * 80)
    print("  SCORING MODEL — Dimension Weights by Merchant Profile")
    print("=" * 80)
    weight_rows = []
    dims = list(next(iter(MERCHANT_PROFILES.values()))["weights"].keys())
    for pk, profile in MERCHANT_PROFILES.items():
        row = {"Profile": profile["name"]}
        row.update({d: profile["weights"][d] for d in dims})
        weight_rows.append(row)
    wdf = pd.DataFrame(weight_rows).set_index("Profile")
    print(wdf.to_string())
    print()
    print("  All weights sum to 1.0. Zero-weighted dimensions are intentionally")
    print("  excluded — they signal what NOT to optimise for in that context.\n")
