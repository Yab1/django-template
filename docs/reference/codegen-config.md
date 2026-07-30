# Codegen Configuration Reference

Complete reference for all configuration options in the codegen system.

## Configuration Hierarchy

Configurations are loaded and merged in this order (later configs override earlier ones):

1. **Base Config** - `.codegen/base.yaml` (global settings for all modules)
2. **Module Config** - `.codegen/{module}.yaml` (module-specific defaults, e.g., `graphql.yaml`)
3. **App Config** - `core/{app}/.codegen/{module}.yaml` (app-specific overrides)

---

## 1. Base Configuration (`.codegen/base.yaml`)

Global settings that apply to ALL code generation modules.

### Required Fields

None - all fields are optional with defaults.

### Optional Fields

```yaml
# Version of the configuration schema
version: "1.0.0"  # Optional: Default "1.0.0"

# Global settings that apply to all code generation
global:
  project_name: string          # Optional: Project name (default: inferred)
  base_app_path: string         # Optional: Base path for apps (default: "core")
  output_base_path: string      # Optional: Base path for output (default: "core")
  python_path: string           # Optional: Python executable path (default: "python3")
  import_prefix: string         # Optional: Import prefix for generated code (default: "core")
  default_pagination_limit: int # Optional: Default pagination limit (default: 10)
  max_pagination_limit: int     # Optional: Maximum pagination limit (default: 100)
  use_async: boolean            # Optional: Use async/await (default: true)
  use_type_checking: boolean    # Optional: Use TYPE_CHECKING blocks (default: true)

# Fields and types to exclude from generation (common across all modules)
exclusions:
  base_fields:                  # Optional: Fields to exclude from all models
    - "id"                      # Default: ["id", "created_at", "updated_at"]
    - "created_at"
    - "updated_at"
  field_types: []               # Optional: Field types to exclude (default: [])
  apps: []                      # Optional: Apps to exclude (default: [])
  models: []                    # Optional: Models to exclude (default: [])

# Hooks for custom code execution during generation (not yet implemented)
hooks:
  pre_generation: null          # Optional: Pre-generation hook (default: null)
  post_generation: null         # Optional: Post-generation hook (default: null)
  pre_model_generation: null    # Optional: Pre-model generation hook (default: null)
  post_model_generation: null   # Optional: Post-model generation hook (default: null)
```

---

## 2. GraphQL Module Configuration (`.codegen/graphql.yaml`)

GraphQL-specific defaults for all apps.

### Required Fields

None - all fields are optional with defaults.

### Optional Fields

#### Global Settings

```yaml
global:
  generate_services: boolean              # Optional: Generate services by default (default: true)
  shareable_inputs_default: boolean       # Optional: Default shareable for inputs (default: false)
  shareable_types_default: boolean        # Optional: Default shareable for types (default: false)
```

#### Naming Conventions

```yaml
naming:
  type_suffix: string                     # Optional: Suffix for type classes (default: "Type")
  input_suffix: string                    # Optional: Suffix for input classes (default: "Input")
  input_partial_suffix: string            # Optional: Suffix for partial input classes (default: "InputPartial")
  filter_suffix: string                   # Optional: Suffix for filter classes (default: "Filter")
  order_suffix: string                    # Optional: Suffix for order classes (default: "Order")
  query_class_suffix: string              # Optional: Suffix for query classes (default: "Query")
  mutation_class_suffix: string           # Optional: Suffix for mutation classes (default: "Mutation")
```

#### Output Structure

```yaml
output_structure:
  use_folders: boolean                    # Optional: Use folder structure (default: true)
  generate_barrel_exports: boolean        # Optional: Generate barrel exports (default: true)
  split_mutations: boolean                # Optional: Split mutations into separate files (default: true)
  split_queries: boolean                  # Optional: Split queries into separate files (default: false)
  split_inputs: boolean                   # Optional: Split inputs into separate files (default: false)
  split_services: boolean                 # Optional: Split services into separate files (default: true)
```

#### Output Paths

```yaml
output_paths:
  types:
    base: string                          # Optional: Base path for types (default: "{app}/types")
    file: string                          # Optional: Single file path (default: "{app}/types.py")
    folder: string                        # Optional: Folder path (default: "{app}/types/")
    barrel: string                        # Optional: Barrel export path (default: "{app}/types/__init__.py")
    model_file: string                    # Optional: Model file path (default: "{app}/types/{model_lower}_type.py")
    relationship_file: string             # Optional: Relationship file path (default: "{app}/types/{relationship_name}_type.py")
  
  inputs:
    base: string                          # Optional: Base path for inputs (default: "{app}/inputs")
    file: string                          # Optional: Single file path (default: "{app}/inputs.py")
    folder: string                        # Optional: Folder path (default: "{app}/inputs/")
    barrel: string                        # Optional: Barrel export path (default: "{app}/inputs/__init__.py")
    model_file: string                    # Optional: Model file path (default: "{app}/inputs/{model_lower}_input.py")
    relationship_file: string             # Optional: Relationship file path (default: "{app}/inputs/{relationship_name}_input.py")
  
  mutations:
    base: string                          # Optional: Base path for mutations (default: "{app}/mutations")
    file: string                          # Optional: Single file path (default: "{app}/mutations.py")
    folder: string                        # Optional: Folder path (default: "{app}/mutations/")
    barrel: string                        # Optional: Barrel export path (default: "{app}/mutations/__init__.py")
    model_folder: string                  # Optional: Model folder path (default: "{app}/mutations/{model_lower}")
    main_file: string                     # Optional: Main mutation file (default: "{app}/mutations/{model_lower}/{model_lower}_mutation.py")
    create_file: string                   # Optional: Create mutation file (default: "{app}/mutations/{model_lower}/{model_lower}_create.py")
    update_file: string                   # Optional: Update mutation file (default: "{app}/mutations/{model_lower}/{model_lower}_update.py")
    delete_file: string                   # Optional: Delete mutation file (default: "{app}/mutations/{model_lower}/{model_lower}_delete.py")
    bulk_create_file: string              # Optional: Bulk create mutation file (default: "{app}/mutations/{model_lower}/{model_lower}_bulk_create.py")
    bulk_update_file: string              # Optional: Bulk update mutation file (default: "{app}/mutations/{model_lower}/{model_lower}_bulk_update.py")
    bulk_delete_file: string              # Optional: Bulk delete mutation file (default: "{app}/mutations/{model_lower}/{model_lower}_bulk_delete.py")
    relationship_folder: string           # Optional: Relationship folder path (default: "{app}/mutations/{model_lower}/{relationship_name}")
    relationship_create_file: string      # Optional: Relationship create file (default: "{app}/mutations/{model_lower}/{relationship_name}/{model_lower}_{relationship_name}_create.py")
    relationship_update_file: string      # Optional: Relationship update file (default: "{app}/mutations/{model_lower}/{relationship_name}/{model_lower}_{relationship_name}_update.py")
    relationship_delete_file: string      # Optional: Relationship delete file (default: "{app}/mutations/{model_lower}/{relationship_name}/{model_lower}_{relationship_name}_delete.py")
    relationship_bulk_create_file: string # Optional: Relationship bulk create file (default: "{app}/mutations/{model_lower}/{relationship_name}/{model_lower}_{relationship_name}_bulk_create.py")
    relationship_bulk_update_file: string # Optional: Relationship bulk update file (default: "{app}/mutations/{model_lower}/{relationship_name}/{model_lower}_{relationship_name}_bulk_update.py")
    relationship_bulk_delete_file: string # Optional: Relationship bulk delete file (default: "{app}/mutations/{model_lower}/{relationship_name}/{model_lower}_{relationship_name}_bulk_delete.py")
    relationship_file: string             # Optional: Relationship mutation file (default: "{app}/mutations/{model_lower}/{relationship_name}/{model_lower}_{relationship_name}_mutation.py")
  
  queries:
    base: string                          # Optional: Base path for queries (default: "{app}/queries")
    file: string                          # Optional: Single file path (default: "{app}/queries.py")
    folder: string                        # Optional: Folder path (default: "{app}/queries/")
    barrel: string                        # Optional: Barrel export path (default: "{app}/queries/__init__.py")
    model_folder: string                  # Optional: Model folder path (default: "{app}/queries/{model_lower}")
    main_file: string                     # Optional: Main query file (default: "{app}/queries/{model_lower}/{model_lower}_query.py")
    single_file: string                   # Optional: Single query file (default: "{app}/queries/{model_lower}/{model_lower}_single.py")
    list_file: string                     # Optional: List query file (default: "{app}/queries/{model_lower}/{model_lower}_list.py")
    paginated_file: string                # Optional: Paginated query file (default: "{app}/queries/{model_lower}/{model_lower}_paginated.py")
    relationship_folder: string           # Optional: Relationship folder path (default: "{app}/queries/{model_lower}/{relationship_name}")
    relationship_query_file: string       # Optional: Relationship query file (default: "{app}/queries/{model_lower}/{relationship_name}/{model_lower}_{relationship_name}_query.py")
  
  filters:
    base: string                          # Optional: Base path for filters (default: "{app}/filters")
    file: string                          # Optional: Single file path (default: "{app}/filters.py")
    folder: string                        # Optional: Folder path (default: "{app}/filters/")
    barrel: string                        # Optional: Barrel export path (default: "{app}/filters/__init__.py")
    model_file: string                    # Optional: Model file path (default: "{app}/filters/{model_lower}_filter.py")
  
  orders:
    base: string                          # Optional: Base path for orders (default: "{app}/orders")
    file: string                          # Optional: Single file path (default: "{app}/orders.py")
    folder: string                        # Optional: Folder path (default: "{app}/orders/")
    barrel: string                        # Optional: Barrel export path (default: "{app}/orders/__init__.py")
    model_file: string                    # Optional: Model file path (default: "{app}/orders/{model_lower}_order.py")
  
  services:
    base: string                          # Optional: Base path for services (default: "{app}/services")
    file: string                          # Optional: Single file path (default: "{app}/services.py")
    folder: string                        # Optional: Folder path (default: "{app}/services/")
    barrel: string                        # Optional: Barrel export path (default: "{app}/services/__init__.py")
    model_folder: string                  # Optional: Model folder path (default: "{app}/services/{model_lower}")
    main_file: string                     # Optional: Main service file (default: "{app}/services/{model_lower}/{model_lower}_service.py")
    create_file: string                   # Optional: Create service file (default: "{app}/services/{model_lower}/{model_lower}_create.py")
    update_file: string                   # Optional: Update service file (default: "{app}/services/{model_lower}/{model_lower}_update.py")
    delete_file: string                   # Optional: Delete service file (default: "{app}/services/{model_lower}/{model_lower}_delete.py")
    bulk_create_file: string              # Optional: Bulk create service file (default: "{app}/services/{model_lower}/{model_lower}_bulk_create.py")
    bulk_update_file: string              # Optional: Bulk update service file (default: "{app}/services/{model_lower}/{model_lower}_bulk_update.py")
    bulk_delete_file: string              # Optional: Bulk delete service file (default: "{app}/services/{model_lower}/{model_lower}_bulk_delete.py")
    relationship_folder: string           # Optional: Relationship folder path (default: "{app}/services/{model_lower}/{relationship_name}")
    relationship_create_file: string      # Optional: Relationship create file (default: "{app}/services/{model_lower}/{relationship_name}/{model_lower}_{relationship_name}_create.py")
    relationship_update_file: string      # Optional: Relationship update file (default: "{app}/services/{model_lower}/{relationship_name}/{model_lower}_{relationship_name}_update.py")
    relationship_delete_file: string      # Optional: Relationship delete file (default: "{app}/services/{model_lower}/{relationship_name}/{model_lower}_{relationship_name}_delete.py")
    relationship_bulk_create_file: string # Optional: Relationship bulk create file (default: "{app}/services/{model_lower}/{relationship_name}/{model_lower}_{relationship_name}_bulk_create.py")
    relationship_bulk_update_file: string # Optional: Relationship bulk update file (default: "{app}/services/{model_lower}/{relationship_name}/{model_lower}_{relationship_name}_bulk_update.py")
    relationship_bulk_delete_file: string # Optional: Relationship bulk delete file (default: "{app}/services/{model_lower}/{relationship_name}/{model_lower}_{relationship_name}_bulk_delete.py")
    relationship_file: string             # Optional: Relationship service file (default: "{app}/services/{model_lower}/{relationship_name}/{model_lower}_{relationship_name}_service.py")
```

**Path Placeholders:**
- `{app}` - App name (e.g., "playground", "fhir")
- `{model_lower}` - Model name in snake_case (e.g., "playground", "author")
- `{relationship_name}` - Relationship field name (e.g., "author", "tags")

#### Base Types

```yaml
base_types:
  delete_input: string                    # Optional: Delete input type import (default: "core.common.inputs.DeleteInput")
  delete_type: string                     # Optional: Delete type import (default: "core.common.types.DeleteType")
  bulk_delete_input: string               # Optional: Bulk delete input type import (default: "core.common.inputs.BulkDeleteInput")
  bulk_delete_type: string                # Optional: Bulk delete type import (default: "core.common.types.BulkDeleteType")
```

---

## 3. App-Specific Configuration (`core/{app}/.codegen/graphql.yaml`)

App-specific overrides that merge with global and module configs.

### Required Fields

None - all fields are optional.

### Optional Fields

#### Global Overrides

```yaml
global:
  generate_services: boolean              # Optional: Override global generate_services
  shareable_inputs_default: boolean       # Optional: Override global shareable_inputs_default
  shareable_types_default: boolean        # Optional: Override global shareable_types_default

# Override output paths (same structure as module config)
output_paths:
  types:
    base: string                          # Optional: Override types base path
    # ... (same structure as module config)
```

#### Models Configuration

```yaml
models:
  - app: string                           # Required: App name (must match directory name)
    model: string                         # Required: Django model name (must match model class)
    
    # Model-level settings
    enabled: boolean                      # Optional: Enable/disable generation (default: true)
    description: string                   # Optional: Model description (default: "")
    
    # Shareable directive (GraphQL federation)
    shareable: boolean                    # Optional: Enable for both inputs and types (overrides defaults)
    shareable_inputs: boolean             # Optional: Enable only for inputs (overrides defaults)
    shareable_types: boolean              # Optional: Enable only for types (overrides defaults)
    
    # Generation options
    generate:
      types: boolean                      # Optional: Generate GraphQL types (default: true)
      inputs: boolean                     # Optional: Generate input types (default: true)
      input_partial: boolean              # Optional: Generate partial input types (default: true)
      
      mutations: boolean | object         # Optional: Generate mutations
        # If boolean: enable/disable all mutations
        # If object: specify individual operations
        create: boolean                   # Optional: Generate create mutation (default: true)
        update: boolean                   # Optional: Generate update mutation (default: true)
        upsert: boolean                   # Optional: Generate upsert mutation (default: true when mutations: true)
                                          # Upsert creates if ID missing, updates if ID provided, cleans up replaced relationships
        delete: boolean                   # Optional: Generate delete mutation (default: true)
        bulk_create: boolean              # Optional: Generate bulk create mutation (default: true)
        bulk_update: boolean              # Optional: Generate bulk update mutation (default: true)
        bulk_upsert: boolean              # Optional: Generate bulk upsert mutation (default: true when mutations: true)
        bulk_delete: boolean              # Optional: Generate bulk delete mutation (default: true)
      
      queries: boolean | object           # Optional: Generate queries
        # If boolean: enable/disable all queries
        # If object: specify individual query types
        single: boolean                   # Optional: Generate single object query (default: true)
        list: boolean                     # Optional: Generate list query (default: true)
        paginated: boolean                # Optional: Generate paginated query (default: true)
      
      filters: boolean                    # Optional: Generate filter types (default: true)
      orders: boolean                     # Optional: Generate order types (default: true)
      services: boolean                   # Optional: Generate service functions (default: true)
    
    # Field configuration
    fields:
      include: array[string]              # Optional: Only include these fields (default: [])
      exclude: array[string]              # Optional: Exclude these fields (default: [])
      overrides: object                   # Optional: Field-specific overrides (default: {})
        # field_name:
        #   type: string                   # Override field type
        #   nullable: boolean              # Override nullability
        #   description: string            # Add field description
    
    # Relationship mappings
    relationship_mappings:
      relationship_name:                  # Required: Django field name (e.g., "author", "tags")
        # Import paths (REQUIRED - cannot be auto-generated)
        type_import_path: string          # Required: Where to import the GraphQL type from
        input_import_path: string         # Required: Where to import input types from
        service_import_path: string       # Required: Where to import service functions from
        filter_import_path: string        # Optional: Where to import filter classes from (if filters enabled)
        
        # Class names (OPTIONAL - auto-generated if not provided)
        # Auto-generated from: {ModelName}{naming.type_suffix}
        type_class: string                # Optional: Override type class name (default: auto-generated)
        # Auto-generated from: {ModelName}{naming.input_suffix}
        input_class: string               # Optional: Override input class name (default: auto-generated)
        # Auto-generated from: {ModelName}{naming.input_partial_suffix}
        input_partial_class: string       # Optional: Override partial input class name (default: auto-generated)
        # Auto-generated from: {ModelName}{naming.filter_suffix}
        filter_class: string              # Optional: Override filter class name (default: auto-generated)
        
        # Filter field name configuration (OPTIONAL)
        filter_field_name: string         # Optional: Control which filter field name to use
                                         # Options:
                                         #   - "forward" (default): Use relationship field name (e.g., "provided_by")
                                         #   - "reverse": Use related_name (e.g., "healthcare_services_provided_by")
                                         #   - "both": Generate both forward and reverse filters
                                         #   - Custom string: Use this exact name for the filter field
        
        # Generation flags (REQUIRED - business logic decisions)
        mutations: boolean | object       # Optional: Generate mutations for this relationship
          # If boolean: enable/disable all
          # If object: specify individual operations
          create: boolean
          update: boolean
          upsert: boolean                 # Optional: Generate upsert mutation for this relationship
          delete: boolean
          bulk_create: boolean
          bulk_update: boolean
          bulk_upsert: boolean            # Optional: Generate bulk upsert mutation for this relationship
          bulk_delete: boolean
        
        services: boolean | object        # Optional: Generate services for this relationship
          # If boolean: enable/disable all
          # If object: specify individual operations
          create: boolean
          update: boolean
          upsert: boolean                 # Optional: Generate upsert service for this relationship
          delete: boolean
          bulk_create: boolean
          bulk_update: boolean
          bulk_upsert: boolean            # Optional: Generate bulk upsert service for this relationship
          bulk_delete: boolean
        
        # Cleanup configuration (for upsert operations)
        cleanup_on_replace: boolean      # Optional: Cleanup replaced ForeignKey/OneToOne objects when upserting (default: true)
                                        # When true: Replaced relationships will be deleted if not referenced elsewhere
                                        # When false: Replaced relationships will be kept (orphaned)
                                        # Note: ManyToMany relationships are not affected by this setting
                                        #       (they only sync relationship links, not delete objects)
        
        queries: boolean | object         # Optional: Generate queries for this relationship
          # If boolean: enable/disable all
          # If object: specify individual query types
          single: boolean
          list: boolean
          paginated: boolean
    
    # Pagination settings
    pagination:
      enabled: boolean                    # Optional: Enable pagination (default: true)
      default_limit: int                  # Optional: Default pagination limit (default: 10)
      max_limit: int                      # Optional: Maximum pagination limit (default: 50)
      include_total_count: boolean        # Optional: Include total count in pagination (default: true)
    
    # Filtering settings
    filtering:
      enabled: boolean                    # Optional: Enable filtering (default: true)
      lookups: boolean                    # Optional: Enable lookup filters (default: true)
      include_fields: array[string]       # Optional: Only include these fields in filters (default: [])
      exclude_fields: array[string]       # Optional: Exclude these fields from filters (default: [])
      relationship_filters: boolean       # Optional: Include relationship filters (default: true)
      custom_filters: array[string]       # Optional: Custom filter definitions (default: [])
    
    # Ordering settings
    ordering:
      enabled: boolean                    # Optional: Enable ordering (default: true)
      include_fields: array[string]       # Optional: Only include these fields in ordering (default: [])
      exclude_fields: array[string]       # Optional: Exclude these fields from ordering (default: [])
      default_order: string               # Optional: Default ordering (default: "-created_at")
    
    # Permissions (future feature)
    permissions:
      enabled: boolean                    # Optional: Enable permissions (default: false)
      create: array[string]               # Optional: Permissions for create (default: [])
      read: array[string]                 # Optional: Permissions for read (default: [])
      update: array[string]               # Optional: Permissions for update (default: [])
      delete: array[string]               # Optional: Permissions for delete (default: [])
    
    # Validation (future feature)
    validation:
      custom_validators: array[string]    # Optional: Custom validators (default: [])
      field_validators: object            # Optional: Field-specific validators (default: {})
    
    # Custom code injection
    custom_code:
      type_extra: string                  # Optional: Extra code for type (default: "")
      input_extra: string                 # Optional: Extra code for input (default: "")
      mutation_extra: string              # Optional: Extra code for mutations (default: "")
      query_extra: string                 # Optional: Extra code for queries (default: "")
      service_extra: string               # Optional: Extra code for services (default: "")
```

---

## Auto-Generated Fields

The following fields are **automatically generated** from Django models if not provided in config:

### Relationship Mappings

- **`type_class`**: Generated from `{ModelName}{naming.type_suffix}` (e.g., `AuthorType`)
- **`input_class`**: Generated from `{ModelName}{naming.input_suffix}` (e.g., `AuthorInput`)
- **`input_partial_class`**: Generated from `{ModelName}{naming.input_partial_suffix}` (e.g., `AuthorInputPartial`)
- **`filter_class`**: Generated from `{ModelName}{naming.filter_suffix}` (e.g., `AuthorFilter`)
- **`related_name`**: Derived from Django field's `remote_field.related_name` or Django's default
- **`relationship_type`**: Derived from Django field type (`ForeignKey`, `ManyToManyField`, `OneToOneField`)
- **`filter_field_name`**: Defaults to `"forward"` (uses relationship field name for filter)

**Source**: Django model field (`field.related_model.__name__` + naming conventions)

---

## Configuration Examples

### Minimal Relationship Mapping

```yaml
relationship_mappings:
  author:
    # Only required fields (import paths and generation flags)
    type_import_path: "core.playground.types"
    input_import_path: "core.playground.inputs"
    service_import_path: "core.playground.services"
    mutations: true
    services:
      create: true
      update: true
      delete: true
```

### Relationship Mapping with Overrides

```yaml
relationship_mappings:
  author:
    type_import_path: "core.playground.types"
    input_import_path: "core.playground.inputs"
    service_import_path: "core.playground.services"
    # Override class name (if different from convention)
    type_class: "CustomAuthorType"
    mutations: true
    services:
      create: true
      update: true
```

### Relationship Mapping with Filter Field Name Configuration

```yaml
relationship_mappings:
  provided_by:
    type_import_path: "core.fhir.data_types.types"
    input_import_path: "core.fhir.data_types.inputs"
    service_import_path: "core.fhir.data_types.services"
    filter_import_path: "core.fhir.data_types.filters"
    # Use forward relationship field name (default)
    filter_field_name: "forward"  # Generates: provided_by: Optional[ReferenceFilter]
    mutations: true
    services: true

  location:
    type_import_path: "core.fhir.data_types.types"
    input_import_path: "core.fhir.data_types.inputs"
    service_import_path: "core.fhir.data_types.services"
    filter_import_path: "core.fhir.data_types.filters"
    # Use reverse relationship (related_name)
    filter_field_name: "reverse"  # Generates: healthcare_services_location: Optional[ReferenceFilter]
    mutations: true
    services: true

  category:
    type_import_path: "core.fhir.data_types.types"
    input_import_path: "core.fhir.data_types.inputs"
    service_import_path: "core.fhir.data_types.services"
    filter_import_path: "core.fhir.data_types.filters"
    # Generate both forward and reverse filters
    filter_field_name: "both"  # Generates both: category: Optional[CodeableConceptFilter] and healthcare_services_category: Optional[CodeableConceptFilter]
    mutations: true
    services: true

  custom_field:
    type_import_path: "core.fhir.data_types.types"
    input_import_path: "core.fhir.data_types.inputs"
    service_import_path: "core.fhir.data_types.services"
    filter_import_path: "core.fhir.data_types.filters"
    # Use custom field name
    filter_field_name: "my_custom_filter_name"  # Generates: my_custom_filter_name: Optional[ReferenceFilter]
    mutations: true
    services: true
```

### Complete Model Configuration

```yaml
models:
  - app: "playground"
    model: "Playground"
    enabled: true
    description: "Playground model with all field types"
    
    generate:
      types: true
      inputs: true
      input_partial: true
      mutations:
        create: true
        update: true
        upsert: true
        delete: true
        bulk_create: false
        bulk_update: false
        bulk_upsert: false
        bulk_delete: false
      queries:
        single: true
        list: true
        paginated: true
      filters: true
      orders: true
      services: true
    
    fields:
      include: []
      exclude: ["internal_field"]
      overrides:
        name:
          description: "The name of the playground"
    
    relationship_mappings:
      author:
        type_import_path: "core.playground.types"
        input_import_path: "core.playground.inputs"
        service_import_path: "core.playground.services"
        mutations: true
        services:
          create: true
          update: true
          upsert: true
          delete: true
        cleanup_on_replace: true  # Cleanup replaced author relationships when upserting
    
    pagination:
      enabled: true
      default_limit: 10
      max_limit: 50
      include_total_count: true
    
    filtering:
      enabled: true
      lookups: true
      relationship_filters: true
    
    ordering:
      enabled: true
      default_order: "-created_at"
```

---

## Notes

1. **Config Merging**: App-specific configs override module configs, which override base configs.
2. **Auto-Generation**: Class names are auto-generated from Django models if not provided, reducing config duplication.
3. **Required vs Optional**: Only import paths and generation flags are required in `relationship_mappings`. Everything else can be auto-generated or has defaults.
4. **Backward Compatibility**: Explicitly provided class names override auto-generated ones, allowing flexibility for federation scenarios.

