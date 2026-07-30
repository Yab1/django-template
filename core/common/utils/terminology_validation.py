"""
Utilities for validating terminology fields (Coding, CodeableConcept, CodeableReference)
against expected CodeSystems.

This module provides validation functions to ensure that terminology fields only
accept values from the correct CodeSystem as specified in .fhir_specs files or
explicit mappings in app's code_systems.py files.
"""

import importlib
import re
from pathlib import Path
from typing import Optional

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def get_code_system_for_field(app_name: str, field_name: str) -> Optional[str]:
    """
    Get CodeSystem URL for a given field.

    Priority:
    1. Check explicit mapping in app's code_systems.py (if exists)
    2. Extract from .fhir_specs file

    Args:
        app_name: Name of the app (e.g., "allergy_intolerance")
        field_name: Name of the field (e.g., "clinical_status")

    Returns:
        CodeSystem URL if found, None otherwise
    """
    try:
        module_name = f"core.{app_name}.code_systems"
        code_systems_module = importlib.import_module(module_name)
        if hasattr(code_systems_module, "CODE_SYSTEM_MAPPING"):
            mapping = code_systems_module.CODE_SYSTEM_MAPPING
            if field_name in mapping:
                return mapping[field_name]
    except (ImportError, AttributeError):
        pass

    fhir_specs_file = Path(f".fhir_specs/{app_name}/{field_name}.txt")
    if not fhir_specs_file.exists():
        return None

    content = fhir_specs_file.read_text(encoding="utf-8")

    pattern1 = r"Include all codes defined in\s+(http://[^\s]+)"
    match = re.search(pattern1, content)
    if match:
        return match.group(1)

    pattern2 = r"Include codes from\s+(http://[^\s]+)"
    match = re.search(pattern2, content)
    if match:
        return match.group(1)

    return None


def validate_code_system_for_coding(coding, expected_code_system: str, field_name: str) -> None:
    """
    Validate that a Coding instance uses the expected CodeSystem.

    Args:
        coding: Coding model instance
        expected_code_system: Expected CodeSystem URL
        field_name: Name of the field being validated (for error messages)

    Raises:
        ValidationError: If Coding system doesn't match expected CodeSystem
    """
    if coding is None:
        return

    if not hasattr(coding, "system"):
        return

    if coding.system != expected_code_system:
        raise ValidationError({
            field_name: _(
                f"Invalid CodeSystem. Expected '{expected_code_system}', "
                f"but got '{coding.system}'. "
                f"Only codes from the expected CodeSystem are allowed."
            )
        })


def validate_code_system_for_codeable_concept(codeable_concept, expected_code_system: str, field_name: str) -> None:
    """
    Validate that a CodeableConcept contains Coding entries with the expected CodeSystem.

    Args:
        codeable_concept: CodeableConcept model instance
        expected_code_system: Expected CodeSystem URL
        field_name: Name of the field being validated (for error messages)

    Raises:
        ValidationError: If any Coding in CodeableConcept doesn't match expected CodeSystem
    """
    if codeable_concept is None:
        return

    if not hasattr(codeable_concept, "coding"):
        return

    codings = codeable_concept.coding.all()

    if not codings.exists():
        return

    invalid_codings = []
    for coding in codings:
        if coding.system != expected_code_system:
            invalid_codings.append(f"{coding.system}#{coding.code}")

    if invalid_codings:
        raise ValidationError({
            field_name: _(
                f"Invalid CodeSystem in CodeableConcept. Expected '{expected_code_system}', "
                f"but found: {', '.join(invalid_codings)}. "
                f"All Coding entries must use the expected CodeSystem."
            )
        })


def validate_code_system_for_codeable_reference(codeable_reference, expected_code_system: str, field_name: str) -> None:
    """
    Validate that a CodeableReference's concept contains Coding entries with the expected CodeSystem.

    Args:
        codeable_reference: CodeableReference model instance
        expected_code_system: Expected CodeSystem URL
        field_name: Name of the field being validated (for error messages)

    Raises:
        ValidationError: If any Coding in CodeableReference's concept doesn't match expected CodeSystem
    """
    if codeable_reference is None:
        return

    if not hasattr(codeable_reference, "concept"):
        return

    if codeable_reference.concept:
        validate_code_system_for_codeable_concept(codeable_reference.concept, expected_code_system, field_name)


def validate_terminology_field(
    value,
    app_name: str,
    field_name: str,
    field_type: str,  # "Coding", "CodeableConcept", or "CodeableReference"
) -> None:
    """
    Validate a terminology field against its expected CodeSystem.

    This is the main entry point for validation. It extracts the CodeSystem
    from .fhir_specs and validates the value accordingly.

    Args:
        value: The terminology value (Coding, CodeableConcept, or CodeableReference instance)
        app_name: Name of the app (e.g., "allergy_intolerance")
        field_name: Name of the field (e.g., "clinical_status")
        field_type: Type of the field ("Coding", "CodeableConcept", or "CodeableReference")

    Raises:
        ValidationError: If value doesn't match expected CodeSystem
    """
    if value is None:
        return

    expected_code_system = get_code_system_for_field(app_name, field_name)

    if not expected_code_system:
        return

    if field_type == "Coding":
        validate_code_system_for_coding(value, expected_code_system, field_name)
    elif field_type == "CodeableConcept":
        validate_code_system_for_codeable_concept(value, expected_code_system, field_name)
    elif field_type == "CodeableReference":
        validate_code_system_for_codeable_reference(value, expected_code_system, field_name)
