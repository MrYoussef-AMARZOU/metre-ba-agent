"""
core — Module métier pour l'extraction et le calcul Béton Armé.
"""
from .calculator import CivilEngine
from .ingestion import UniversalPlanIngestor, IngestionResult, PlanSource
from .schemas import (
    BarreAcierSchema,
    ElementStructureSchema,
    FamilleElement,
    ProjetBAParseOutput,
    RoleArmature,
    TypeBarre,
)

__all__ = [
    "CivilEngine",
    "UniversalPlanIngestor",
    "IngestionResult",
    "PlanSource",
    "BarreAcierSchema",
    "ElementStructureSchema",
    "FamilleElement",
    "ProjetBAParseOutput",
    "RoleArmature",
    "TypeBarre",
]
