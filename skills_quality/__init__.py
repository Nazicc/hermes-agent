"""
skills_quality — Hermes Skills Quality Framework

Validates Hermes skills against PM-Skills-inspired quality standards.
"""

__version__ = "0.1.0"

from skills_quality.core import (
    SkillParser,
    PedagogicScorer,
    PedagogicScore,
    DependencyGraph,
    TriggerValidator,
    TriggerResult,
    QualityReport,
    ValidationResult,
    StructValidationResult,
    ReferenceResult,
    ReportResult,
    validate_structure,
    classify_skill_type,
    extract_references,
    validate_references,
)

__all__ = [
    "SkillParser",
    "PedagogicScorer",
    "PedagogicScore",
    "DependencyGraph",
    "TriggerValidator",
    "TriggerResult",
    "QualityReport",
    "ValidationResult",
    "StructValidationResult",
    "ReferenceResult",
    "ReportResult",
    "validate_structure",
    "classify_skill_type",
    "extract_references",
    "validate_references",
]
