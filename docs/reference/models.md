# Models Reference

This document provides a reference for all models in the EHR Practitioner Service.

## Core Models

### Practitioner

Represents a healthcare practitioner.

**Location**: `core.practitioners.models.Practitioner`

**Fields**:
- `id` - UUID primary key
- `name` - Practitioner name
- `active` - Whether practitioner is active
- `created_at` - Creation timestamp
- `updated_at` - Update timestamp

### PractitionerRole

Represents a practitioner's role and specialties.

**Location**: `core.practitioner_role.models.PractitionerRole`

**Fields**:
- `id` - UUID primary key
- `practitioner` - ForeignKey to Practitioner
- `organization` - ForeignKey to Organization
- `code` - ManyToMany to CodeableConcept (roles)
- `specialty` - ManyToMany to CodeableConcept (specialties)
- `active` - Whether role is active
- `period` - ForeignKey to Period (validity period)

## FHIR Data Types

All FHIR data types are located in `core.fhir.data_types.models`.

### CodeableConcept

Represents a coded concept with optional text.

### Reference

Represents a reference to another resource.

### Period

Represents a time period with start and end dates.

### Identifier

Represents an external identifier.

## Model Directory Structure

Apps with multiple models should use a `models/` package structure for better organization and to prevent circular imports.

### Structure Pattern

```
core/
└── app_name/
    ├── models.py              # Barrel re-export (optional, for compatibility)
    └── models/
        ├── __init__.py        # Package barrel export (REQUIRED)
        ├── model_name.py      # Individual model files
        └── ...
```

**Note**: When both `models.py` and `models/` directory exist, Python prioritizes the package (`models/`) for imports. The `models.py` file serves as a compatibility re-export.

### Example: Allergy Intolerance

```
core/allergy_intolerance/
├── models.py                  # Re-exports from models package
└── models/
    ├── __init__.py            # Exports all models using relative imports
    ├── allergy_intolerance.py # Main AllergyIntolerance model
    ├── onset.py               # AllergyIntoleranceOnset model
    ├── participant.py         # AllergyIntoleranceParticipant model
    └── reaction.py            # AllergyIntoleranceReaction model
```

### Implementation Details

1. **`models/` directory**: Contains individual model files, one model per file
2. **`models/__init__.py`**: Barrel export that imports all models using **relative imports**
3. **`models.py`** (optional): Re-exports from the package for compatibility

### Import Patterns

**models/__init__.py** MUST use **relative imports** to prevent circular dependencies:

```python
# models/__init__.py - Package barrel export
from .allergy_intolerance import AllergyIntolerance
from .onset import AllergyIntoleranceOnset
from .participant import AllergyIntoleranceParticipant
from .reaction import AllergyIntoleranceReaction

__all__ = [
    "AllergyIntolerance",
    "AllergyIntoleranceOnset",
    "AllergyIntoleranceParticipant",
    "AllergyIntoleranceReaction",
]
```

**models.py** (if present) should re-export from the package:

```python
# models.py - Compatibility re-export
from .models import (  # noqa: F401
    AllergyIntolerance,
    AllergyIntoleranceOnset,
    AllergyIntoleranceParticipant,
    AllergyIntoleranceReaction,
)
```

### How It Works

1. **Import resolution**: `from core.allergy_intolerance.models import AllergyIntolerance`
2. **Python resolves to**: `models/__init__.py` (package takes precedence over file)
3. **`__init__.py` imports**: `from .allergy_intolerance import AllergyIntolerance` (relative)
4. **No circular imports**: Direct import from sibling module, `models.py` is never executed

### Usage

All imports use the standard Django pattern:

```python
# From anywhere in the codebase
from core.allergy_intolerance.models import AllergyIntolerance, AllergyIntoleranceOnset
```

This resolves to `models/__init__.py`, which then imports from the individual model files.

### Benefits

- **No circular imports**: Package uses relative imports, `models.py` imports from package (one-way)
- **No duplicate registration**: Django discovers models from package (`models/__init__.py`)
- **Better organization**: Each model in its own file
- **Easier maintenance**: Find and modify specific models quickly
- **Scalability**: Easy to add new models without cluttering a single file
- **Django compatibility**: Django automatically discovers models from `models/` package
- **Backward compatibility**: `models.py` provides compatibility if needed

### When to Use This Structure

- Apps with 3+ models
- Apps with nested/component models
- Apps where models are likely to grow over time

### Single Model Apps

For apps with a single model, a simple `models.py` file is sufficient:

```python
# models.py
class SingleModel(BaseModel):
    # ...
```

## Model Standards

All models follow the [Django Modeling Standard](../standards/modeling.md).

## Related Documentation

- [Django Modeling Standard](../standards/modeling.md)
- [Data Models](../architecture/data-models.md)

