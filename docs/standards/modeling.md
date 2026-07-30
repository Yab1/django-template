# Django Modeling Standard

When creating or modifying Django models in this project, you MUST follow the Django Modeling Standard. This ensures consistency, predictability, and AI-friendly code generation.

## Core Requirements

### 1. Base Model

- All models MUST inherit from `core.common.models.BaseModel`
- BaseModel provides: UUID `id`, `created_at`, `updated_at`, `metadata`, and `history` tracking

### 2. Model Structure

- Include docstring with description and relevant documentation link
- Use type hints (Python 3.12+ has postponed evaluation of annotations by default)
- Import `gettext_lazy as _` for all user-facing strings
- Import `ValidationError` and `timezone` for validation

### 3. Field Naming

- Use lowercase with underscores: `clinical_status`, `onset_date_time`
- Do NOT prefix with model name (avoid `allergy_intolerance_code`)
- Use clear, descriptive names that match domain terminology

### 4. Field Ordering (REQUIRED)

Fields MUST follow this exact order:

1. `identifier` fields (if any)
2. Core classification fields (status, type, category)
3. Main descriptive fields (code, subject/patient, encounter)
4. Timing fields (onset, recorded_date, last_occurrence)
5. Participants
6. Notes and annotations
7. Reactions or nested structures

**IMPORTANT**: Do NOT add section comments (e.g., `# 1. Identifiers`, `# 2. Core classification fields`) above field groups. Fields should be listed directly without organizational comments.

### 5. Field Parameter Ordering (REQUIRED)

Field parameters MUST follow this order:

1. Database-level: `on_delete`, `primary_key`, `unique`, `db_index`, `db_column`
2. Null/empty: `null`, `blank`, `default`
3. Relations: `related_name`, `related_query_name`, `to_field`
4. Form/presentation: `help_text`, `verbose_name`, `choices`
5. Metadata: `validators`
6. Custom arguments

### 6. ForeignKey Rules

- MUST include `on_delete` parameter
- MUST include `related_name` following pattern: `<model_name_snake_case>_<field_name>`
- Example: `related_name="allergy_intolerance_clinical_status"`
- **DO NOT specify `null=False, blank=False`** - these are the defaults for ForeignKey fields
- **Only specify `null=True, blank=True`** when making fields optional
- **Required fields**: Use `on_delete=models.PROTECT` or `models.CASCADE` (omit `null`/`blank` parameters)
- **Optional fields**: Use `on_delete=models.SET_NULL` with `null=True, blank=True`
- **CRITICAL**: `on_delete=models.SET_NULL` requires `null=True` - never use `SET_NULL` with `null=False`
- Use `gettext_lazy` for `help_text`

**Examples:**

```python
# Required field (defaults to null=False, blank=False)
subject = models.ForeignKey(
    "fhir.Reference",
    on_delete=models.PROTECT,
    related_name="condition_subject",
    help_text=_("Who has the condition?"),
)

# Optional field (explicitly set null=True, blank=True)
encounter = models.ForeignKey(
    "fhir.Reference",
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name="condition_encounter",
    help_text=_("The Encounter during which this Condition was created"),
)
```

### 7. ManyToManyField Rules

- MUST include `blank=True` unless required
- MUST include `related_name` following pattern: `<model_name_snake_case>_<field_name>`
- Use `gettext_lazy` for `help_text`

### 8. Help Text (REQUIRED)

- Every field MUST have `help_text` using `gettext_lazy`
- Describe purpose, domain meaning, and possible values
- Example: `help_text=_("Clinical status: active | inactive | resolved")`

### 9. Meta Configuration (REQUIRED)

Every model MUST include:

```python
class Meta:
    db_table = "<app>_<model_snake_case>"  # Convert CamelCase to snake_case
    verbose_name = _("Human Readable Name")
    verbose_name_plural = _("Human Readable Names")
    ordering = ["-created_at"]
    default_related_name = "<model_name_plural_snake_case>"
```

**db_table Naming:**

- Format: `<app_name>_<model_name_snake_case>`
- Convert CamelCase to snake_case: `AllergyIntoleranceParticipant` → `allergy_intolerance_allergy_intolerance_participant`
- Examples:
  - `AllergyIntolerance` → `allergy_intolerance_allergy_intolerance`
  - `PractitionerRole` → `practitioner_role_practitioner_role`

**Exception for Nested Component Models in ManyToManyField:**

- If a nested component model (e.g., `AllergyIntoleranceParticipant`, `AllergyIntoleranceReaction`) is referenced via `ManyToManyField` from the parent model, use a shorter `db_table` format to avoid conflicts with Django's auto-generated intermediary table names.
- Format: `<app_name>_<component_name_snake_case>` (without repeating the full parent model name)
- Examples:
  - `AllergyIntoleranceParticipant` (when used in ManyToManyField) → `allergy_intolerance_participant`
  - `AllergyIntoleranceReaction` (when used in ManyToManyField) → `allergy_intolerance_reaction`
- This prevents Django's intermediary table naming (`<app>_<parent_model>_<field>`) from conflicting with the model's table name.

### 10. clean() Method (REQUIRED)

- Every model MUST have a `clean()` method
- Always call `super().clean()` first
- Add validation logic for cross-field business rules
- Raise `ValidationError` with field names and `gettext_lazy` messages

### 11. __str__ Method (REQUIRED)

- MUST return a concise, meaningful string representation
- Use fallbacks when necessary
- Never cause additional queries (avoid `.all()` unless prefetched)
- Example: `return f"AllergyIntolerance {self.id}"`

### 12. Type Hints (REQUIRED)

- All methods MUST include return type annotations
- Python 3.12+ has postponed evaluation of annotations by default (no need for `from __future__ import annotations`)
- Use `TYPE_CHECKING` for conditional imports

### 13. Model Directory Structure

For apps with multiple models, use a `models/` package structure:

**Structure:**

```text
core/
└── app_name/
    ├── models.py              # Optional: Re-exports from models package
    └── models/
        ├── __init__.py        # Package barrel export (REQUIRED)
        ├── model_name.py      # Individual model files
        └── ...
```

**models/__init__.py** MUST use **relative imports**:

```python
from .allergy_intolerance import AllergyIntolerance
from .onset import AllergyIntoleranceOnset
```

**models.py** (if present) should re-export from package:

```python
from .models import (
    AllergyIntolerance,
    AllergyIntoleranceOnset,
)
```

**Benefits:**

- Prevents circular imports (one-way dependency)
- Better organization (one model per file)
- Django discovers models from `models/` package automatically
- Scalable for apps with many models

**When to use:**

- Apps with 3+ models
- Apps with nested/component models
- Apps where models will grow over time

For single model apps, a simple `models.py` file is sufficient.

### 14. Nested/Component Models

- Include **only the immediate parent** prefix in class name, not the full chain
- **CRITICAL**: If model X is related to A, and A is related to B, the name of B should only include A (the immediate parent), not both X and A
- Examples:
  - ✅ `IncludedStructureBodyLandmarkOrientation` (FK to `BodyStructureIncludedStructure`)
  - ❌ `BodyStructureIncludedStructureBodyLandmarkOrientation` (includes full chain)
  - ✅ `OrderDetailParameter` (FK to `ServiceRequestOrderDetail`)
  - ❌ `ServiceRequestOrderDetailParameter` (includes full chain)
  - ✅ `AnalysisInput` (FK to `GenomicStudyAnalysis`)
  - ❌ `GenomicStudyAnalysisInput` (includes full chain)
- Follow same field/related_name conventions
- Each nested model must have its own Meta configuration
- **Important**: If the nested model is used in a `ManyToManyField` from the parent, use the shorter `db_table` format (see exception in section 9) to avoid intermediary table naming conflicts

### 15. External Resource References

- Always use string references for cross-app models: `"app.ModelName"`
- Use string format: `"<app>.<ModelName>"` for ForeignKey/M2M strings
- Example: `"fhir.CodeableConcept"`, `"fhir.Reference"`

### 16. Polymorphic Field Patterns

- When a field can take multiple types, provide multiple optional fields
- Use clear suffix matching the type: `onset_date_time`, `onset_age`, `onset_period`, `onset_range`, `onset_string`
- Keep them grouped together

## Complete Model Template

```python
from typing import TYPE_CHECKING

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from core.common.models import BaseModel

if TYPE_CHECKING:
    pass


class ModelName(BaseModel):
    """
    Description of the model.
    See: <relevant-documentation-url>
    """

    identifier = models.ManyToManyField(
        "fhir.Identifier",
        blank=True,
        related_name="model_name_identifier",
        help_text=_("External identifiers"),
    )

    # Required field - no null/blank needed (defaults to null=False, blank=False)
    subject = models.ForeignKey(
        "fhir.Reference",
        on_delete=models.PROTECT,
        related_name="model_name_subject",
        help_text=_("The subject this resource is about"),
    )

    # Optional field - explicitly set null=True, blank=True
    status = models.ForeignKey(
        "fhir.CodeableConcept",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="model_name_status",
        help_text=_("Status of this resource"),
    )

    class Meta:
        db_table = "app_model_name"
        verbose_name = _("Model Name")
        verbose_name_plural = _("Model Names")
        ordering = ["-created_at"]
        default_related_name = "model_names"

    def clean(self) -> None:
        """Validate model-level business rules."""
        super().clean()
        # Add cross-field validation here when business rules require it

    def __str__(self) -> str:
        return f"ModelName {self.id}"
```

## Reference

For complete details, see: `docs/standards/modeling.md`

For example implementation, see: `core/practitioner_role/example_allergy_intolerance.py`

