# scripts/seed_products.py
# Seeds the products table with the base subscription and add-on products.
# Run from the project root: python scripts/seed_products.py

import sys
import os

# Add project root to path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from extensions import db
from models.billing import Product


def seed_products():
    """
    Inserts the base subscription and add-on products into the database.

    Skips any product that already exists (safe to run multiple times).
    """

    products = [
        {
            "slug": "base",
            "display_name": "Base",
            "description": "The complete four-phase audit framework for advertising platforms",
            "icon_class": "fa-solid fa-magnifying-glass",
            "marketing_headline": "The Complete Audit Framework",
            "marketing_description": (
                "Auditmaton for Ad Audits walks you through your entire advertising "
                "account audit, step by step. The Base plan includes all four "
                "audit phases.\n\n"
                "Educate. Learn what each check measures and why it matters, with "
                "plain-language explanations written for practitioners.\n\n"
                "Investigate. Follow guided instructions to inspect your account "
                "directly inside the ad platform.\n\n"
                "Evaluate. Review your findings against benchmarks and best practices, "
                "with clear pass/fail criteria.\n\n"
                "Validate. Confirm your fixes are live and working with "
                "post-implementation verification steps.\n\n"
                "Audit categories cover demand-side platforms (Google Ads, Meta, TikTok, "
                "Microsoft) and supply-side platforms (Ad Manager, AdSense, SSPs)."
            ),
            "price_cents": 29500,                                                # $295.00/year
            "product_type": "base",
            "annual_token_allocation": 0,                                        # No AI tokens
            "features": {
                "educate": True,
                "investigate": True,
                "evaluate": True,
                "validate": True,
                "charts": False,
                "ai_narrative": False,
                "ai_chatbot": False,
                "contextual_queries": False,
                "timeline_overlay": False,
            },
            "sort_order": 1,
        },
        {
            "slug": "viz",
            "display_name": "Viz Add-on",
            "description": "Interactive Plotly charts and data visualizations for every audit check",
            "icon_class": "fa-solid fa-chart-line",
            "marketing_headline": "See Your Data Come Alive",
            "marketing_description": (
                "Turn raw audit data into interactive Plotly charts that make patterns "
                "and problems impossible to miss. Every audit check that benefits from "
                "visualization gets its own chart. Hover for details, zoom into ranges, "
                "and export as PNG for client reports.\n\n"
                "Without the Viz add-on, you'll see 'ghost charts', blurred previews "
                "that show you what's available. With it, every chart is fully interactive "
                "and exportable.\n\n"
                "It includes bar charts, treemaps, scatter plots, heatmaps, and more, "
                "each chosen to best represent the data for that specific audit check."
            ),
            "price_cents": 10000,                                                # $100.00/year
            "product_type": "addon",
            "annual_token_allocation": 0,                                        # No AI tokens
            "features": {
                "charts": True,
            },
            "sort_order": 2,
        },
        {
            "slug": "ai",
            "display_name": "AI Add-on",
            "description": "AI-generated narrative, contextual queries, and audit chatbot",
            "icon_class": "fa-solid fa-robot",
            "marketing_headline": "AI-Powered Audit Intelligence",
            "marketing_description": (
                "Let AI analyze your audit findings and generate professional narrative "
                "summaries you can drop straight into client reports. The AI add-on "
                "includes three features.\n\n"
                "AI Narrative. Automatically generates written analysis for each audit "
                "check, explaining what the data means and what to do about it. "
                "Adapts to your brand voice preferences set during intake.\n\n"
                "Contextual Queries. Ask follow-up questions about any audit finding "
                "and get answers grounded in your actual data, not generic advice.\n\n"
                "Audit Chatbot. A conversational assistant that knows your full audit "
                "context. Ask it to compare categories, prioritize fixes, or explain "
                "findings in plain language for stakeholders.\n\n"
                "It includes 500,000 tokens per year, enough for dozens of full audits."
            ),
            "price_cents": 10000,                                                # $100.00/year
            "product_type": "addon",
            "annual_token_allocation": 500000,                                   # Annual token budget
            "features": {
                "ai_narrative": True,
                "ai_chatbot": True,
                "contextual_queries": True,
            },
            "sort_order": 3,
        },
    ]

    app = create_app()
    with app.app_context():
        for product_data in products:

            # Check if this product already exists
            existing = Product.query.filter_by(slug=product_data["slug"]).first()
            if existing:

                # Update all fields on the existing row
                for key, value in product_data.items():
                    if key != "slug":
                        setattr(existing, key, value)
                print(f"  Updated '{product_data['slug']}'")
            else:

                # Create new product
                product = Product(**product_data)
                db.session.add(product)
                print(f"  Created '{product_data['display_name']}' (${product_data['price_cents'] / 100:.2f}/yr)")

        db.session.commit()
        print("Done! Products seeded.")


if __name__ == "__main__":
    seed_products()
