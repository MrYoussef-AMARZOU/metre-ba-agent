"""BAEL 91 Morocco Partner Pack for OpenConstructionERP.

Béton Armé Marocain — nomenclature génie civil, extraction automatique de métrés,
base de prix unitaires armature + béton + coffrage.

Standards: BAEL 91, Réglement Parasismique Marocain, Norme CP 2001.
"""

from __future__ import annotations

from app.core.partner_pack.manifest import PartnerBranding, PartnerPackManifest

MANIFEST = PartnerPackManifest(
    slug="bael91-ma",
    partner_name="Métré BA Agent",
    partner_url="https://github.com/Youssef-AMARZOU/metre-ba-agent",
    pack_version="1.0.0",
    description=(
        "Pack Béton Armé Marocain — BAEL 91, nomenclature génie civil, "
        "extraction automatique de métrés, base de prix unitaires armature + béton + coffrage."
    ),
    default_locale="fr",
    additional_locales={
        "fr": "locales/fr.json",
        "ar": "locales/ar.json",
    },
    cwicr_regions=[],
    default_currency="MAD",
    default_tax_template=None,
    validation_rule_sets=["boq_quality"],
    validation_rule_packs=[],
    default_modules=["projects", "boq", "takeoff", "costs"],
    hidden_modules=[],
    branding=PartnerBranding(
        primary_color="#1e40af",
        accent_color="#f59e0b",
        logo_path="logo.svg",
        favicon_path=None,
        powered_by_text="Métré BA Agent — Génie Civil Marocain · Built on OpenConstructionERP",
    ),
    onboarding_script_path=None,
    metadata={
        "country": "MA",
        "country_name_en": "Morocco",
        "country_name_fr": "Maroc",
        "regulator_refs": ["BAEL 91", "Réglement Parasismique Marocain", "Norme CP 2001"],
        "support_email": "youssef.amarzou@gmail.com",
        "standards": ["BAEL 91", "Eurocode 2", "NPRC 2000"],
        "currency": "MAD",
        "currency_name": "Dirham Marocain",
    },
)