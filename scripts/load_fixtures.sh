#!/usr/bin/env bash
# Load Django fixtures in dependency-safe order (terminology → catalog → policies → bundles → assignments).
#
# Uses loaddata_replace: drops fixture PK / unique-key conflicts, then loaddata (re-run safe on shared dev DB).
# Full wipe still available: python manage.py flush --no-input  (or make seed-fixtures-reset).
#
# Usage (from repo root):
#   ./scripts/load_fixtures.sh                  # full dev stack (default)
#   ./scripts/load_fixtures.sh --profile security
#   ./scripts/load_fixtures.sh procedure_session  # bare profile name OK
#   ./scripts/load_fixtures.sh --profile terminology --extra snomed,condition-code,procedure-code
#   ./scripts/load_fixtures.sh --dry-run
#   MANAGE="python manage.py" ./scripts/load_fixtures.sh
#
# Profiles:
#   full                 — ordered load for local dev (default)
#   security             — auth concepts + policies + bundles + identities + assignments
#   resources-policies   — resource catalog + security stack (no terminology / app data)
#   terminology          — all terminology bundles (code_system before value_set; 00_* first)
#   resources            — resource_definition catalog + questionnaire field fixtures
#   policies             — bootstrap policies only (needs resources loaded)
#   policy-bundles       — per-resource bundles, then super bundle
#   identities           — EMR identity groups + system-admin members
#   assignments          — policy bundle → identity group links (run after bundles)
#   app-fixtures         — remaining core/*/fixtures (excludes security, terminology, RD)
#   extras               — workflow_system_user (+ navigation/practitioner/individuals only with flags below)
#   workflows            — all core/workflows/fixtures/legacy/* (monolith flows + shared bindings/auto-start; not cleaned yet)
#   patient_visit_registration — enterprise layout (see manifests/)
#   procedure_session          — WF-17 perioperative (see manifests/procedure_session.json)
#   patient_onboarding         — enterprise layout (see manifests/)
#   triage_assessment          — enterprise layout (see manifests/)
#   consultation_assessment    — Phase-2 CWM claim-start consultation (see manifests/)
#   medication_prescription_review — pharmacy Rx review plan (enterprise layout)
#   pharmacy_fulfillment           — post-claim fulfillment plan (enterprise layout)
#   medication_administration      — MAR plan + due/overdue notify (enterprise layout)
#   inpatient-admission        — WF-06 enterprise layout (see manifests/inpatient_admission.json)
#   capacity-bed-management      — bed transit/matching/turnover ops + capacity notify (ordered FK block)
#   encounter-billing    — encounter_billing plan only (enterprise layout; see manifests/)
#   registration-billing — ethiopia billing CodeSystem/ValueSet (upsert) + registration catalog + operations policy
#   notifications-legacy     — uncleaned notification configs under fixtures/legacy/ (not for incremental cleanup)
#   core-bootstrap        — terminology + resources + security stack + org/location/users/practitioners/
#                          identities (catalog, org-access, members) + assignments. No notifications /
#                          operations / lab / inventory config, no workflows.
#
# Note: */fixtures/manifests/*.json are load-order metadata (not loaddata arrays) — skipped globally.
#       core/workflows/fixtures/legacy/ holds uncleaned monolith flows (PROFILE=workflows only).
#
# Always excluded unless opted in:
#   core/individuals/fixtures/practioner.json  (--with-practitioner)
#   core/resource_definition/fixtures/route/navigation_components.sample.generated.json
#   core/resource_definition/fixtures/route/navigation_route.generated.json  (--with-navigation)

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

MANAGE="${MANAGE:-python manage.py}"
PROFILE="full"
DRY_RUN=0
WITH_NAVIGATION=0
WITH_PRACTITIONER_TYPO_FIXTURE=0
WITH_INDIVIDUALS=0
EXTRA_TERMINOLOGY=()

# Always skip these fixture files (same as temp/commands.txt find exclusions).
# Opt in: --with-navigation (navigation_route), --with-practitioner (practioner.json).
ALWAYS_EXCLUDED_FIXTURES=(
  "core/individuals/fixtures/practioner.json"
  "core/resource_definition/fixtures/route/navigation_components.sample.generated.json"
  "core/resource_definition/fixtures/route/navigation_route.generated.json"
)

# Directory prefixes skipped by the generic app-fixtures sweep (handled in earlier phases).
EXCLUDE_APP_FIXTURES=(
  "core/terminology/fixtures/"
  "core/security/fixtures/"
  "core/resource_definition/fixtures/resources/"
  "core/resource_definition/fixtures/questionnaire/"
  "core/identities/fixtures/"
  "core/individuals/fixtures/"
  "core/workflows/fixtures/"
  "core/notifications/fixtures/"
  "core/entities/fixtures/organization/"
  "core/entities/fixtures/location/"
)

usage() {
  # Header comment block through core-bootstrap note (keep in sync with file preamble).
  sed -n '2,51p' "$0" | sed 's/^# \{0,1\}//'
  echo ""
  echo "Options:"
  echo "  --profile NAME       See profiles above (default: full); bare NAME also accepted"
  echo "  --dry-run            Print loaddata commands only"
  echo "  --with-navigation    Include navigation_route.generated.json (large; SPA routes)"
  echo "  --with-practitioner  Include core/individuals/fixtures/practioner.json (typo filename)"
  echo "  --with-individuals   Include core/individuals/fixtures/ (practitioners; excluded from all profiles by default)"
  echo "  --extra BUNDLES      Comma-separated terminology bundle dir names (with --profile terminology)"
  echo "  -h, --help           Show this help"
}

log() {
  echo "==> $*"
}

# Return 0 if this fixture path must not be loaded (default exclusions + opt-in overrides).
is_fixture_excluded() {
  local path=$1
  # Manifest files describe fixture load order for workflow profiles — not Django fixture arrays.
  if [[ "$path" == */fixtures/manifests/* ]]; then
    return 0
  fi
  case "$path" in
    core/individuals/fixtures/practioner.json)
      ((WITH_PRACTITIONER_TYPO_FIXTURE)) && return 1
      return 0
      ;;
    core/resource_definition/fixtures/route/navigation_route.generated.json)
      ((WITH_NAVIGATION)) && return 1
      return 0
      ;;
    core/resource_definition/fixtures/route/navigation_components.sample.generated.json)
      return 0
      ;;
  esac
  return 1
}

loaddata() {
  local -a files=("$@")
  local -a filtered=()
  local f
  for f in "${files[@]}"; do
    if is_fixture_excluded "$f"; then
      ((DRY_RUN)) && log "skip excluded: $f"
      continue
    fi
    filtered+=("$f")
  done
  if ((${#filtered[@]} == 0)); then
    return 0
  fi
  log "loaddata_replace ${#filtered[@]} file(s)"
  if ((DRY_RUN)); then
    printf '  %s loaddata_replace' "$MANAGE"
    printf ' %q' "${filtered[@]}"
    echo
    return 0
  fi
  # shellcheck disable=SC2086
  $MANAGE loaddata_replace "${filtered[@]}"
}

sorted_glob() {
  local pattern=$1
  local -a matches=()
  shopt -s nullglob
  matches=($pattern)
  shopt -u nullglob
  if ((${#matches[@]} == 0)); then
    return 0
  fi
  printf '%s\n' "${matches[@]}" | LC_ALL=C sort
}

collect_terminology_bundle_dirs() {
  local -a all_dirs=()
  local dir base
  while IFS= read -r dir; do
    all_dirs+=("$dir")
  done < <(find core/terminology/fixtures -mindepth 1 -maxdepth 1 -type d | LC_ALL=C sort)

  local -a ordered=()
  for dir in "${all_dirs[@]}"; do
    base="$(basename "$dir")"
    [[ "$base" == 00_* ]] && ordered+=("$dir")
  done
  for dir in "${all_dirs[@]}"; do
    base="$(basename "$dir")"
    [[ "$base" == 00_* ]] && continue
    ordered+=("$dir")
  done

  if ((${#EXTRA_TERMINOLOGY[@]} > 0)); then
    local name
    for name in "${EXTRA_TERMINOLOGY[@]}"; do
      name="${name// /}"
      name="${name%,}"
      [[ -z "$name" ]] && continue
      ordered=("core/terminology/fixtures/$name")
    done
  fi

  printf '%s\n' "${ordered[@]}"
}

phase_authorization_concepts() {
  loaddata "core/security/fixtures/authorization_concepts.json"
}

phase_terminology() {
  local -a files=()
  local bundle_dir
  while IFS= read -r bundle_dir; do
    [[ -z "$bundle_dir" || ! -d "$bundle_dir" ]] && continue
    [[ -f "$bundle_dir/code_system.json" ]] && files+=("$bundle_dir/code_system.json")
    [[ -f "$bundle_dir/value_set.json" ]] && files+=("$bundle_dir/value_set.json")
    while IFS= read -r extra; do
      [[ -z "$extra" ]] && continue
      [[ "$extra" == "$bundle_dir/code_system.json" || "$extra" == "$bundle_dir/value_set.json" ]] && continue
      files+=("$extra")
    done < <(find "$bundle_dir" -maxdepth 1 -type f -name '*.json' ! -name 'code_system.json' ! -name 'value_set.json' | LC_ALL=C sort)
  done < <(collect_terminology_bundle_dirs)

  loaddata "${files[@]}"
}

phase_resources() {
  local -a files=()
  while IFS= read -r f; do
    [[ -n "$f" ]] && files+=("$f")
  done < <(sorted_glob "core/resource_definition/fixtures/resources/*.json")
  loaddata "${files[@]}"
}

phase_resource_questionnaires() {
  local -a files=()
  while IFS= read -r f; do
    [[ -n "$f" ]] && files+=("$f")
  done < <(sorted_glob "core/resource_definition/fixtures/questionnaire/*.json")
  loaddata "${files[@]}"
}

phase_policies() {
  local -a files=()
  while IFS= read -r f; do
    [[ -n "$f" ]] && files+=("$f")
  done < <(sorted_glob "core/security/fixtures/policies/*.json")
  loaddata "${files[@]}"
}

phase_policy_bundles() {
  local -a files=()
  while IFS= read -r f; do
    [[ -n "$f" ]] && files+=("$f")
  done < <(find core/security/fixtures/policy_bundles -maxdepth 1 -type f -name '*.json' ! -name 'bootstrap_bundle_super.json' | LC_ALL=C sort)
  loaddata "${files[@]}"
  # role-scoped composite bundles (roles/ subdir) — must load before super bundle
  local -a role_files=()
  while IFS= read -r f; do
    [[ -n "$f" ]] && role_files+=("$f")
  done < <(find core/security/fixtures/policy_bundles/roles -type f -name '*.json' 2>/dev/null | LC_ALL=C sort)
  ((${#role_files[@]} > 0)) && loaddata "${role_files[@]}"
  loaddata "core/security/fixtures/policy_bundles/bootstrap_bundle_super.json"
}

phase_identity_catalog() {
  loaddata "core/identities/fixtures/identity_group/bootstrap_emr_identity_groups.json"
}

phase_identity_members() {
  local -a member_files=()
  while IFS= read -r f; do
    [[ -n "$f" ]] && member_files+=("$f")
  done < <(find core/identities/fixtures/identity_group_member -type f -name '*.json' | LC_ALL=C sort)
  ((${#member_files[@]} > 0)) && loaddata "${member_files[@]}"
}

phase_identities() {
  phase_identity_catalog
  phase_identity_members
}

# Org tree — location.managing_organization depends on organization rows existing first.
phase_entities() {
  local -a files=()
  [[ -f core/entities/fixtures/organization/bootstrap_emr_organizations.json ]] && \
    files+=("core/entities/fixtures/organization/bootstrap_emr_organizations.json")
  [[ -f core/entities/fixtures/location/bootstrap_emr_locations.json ]] && \
    files+=("core/entities/fixtures/location/bootstrap_emr_locations.json")
  ((${#files[@]} > 0)) && loaddata "${files[@]}"
}

# Human super-user accounts (no Practitioner record).
phase_system_users() {
  local -a files=()
  while IFS= read -r f; do
    [[ -n "$f" ]] && files+=("$f")
  done < <(sorted_glob "core/users/fixtures/*.json")
  ((${#files[@]} > 0)) && loaddata "${files[@]}"
}

# Service/bot account — its IdentityGroupMember row FKs into the "System Super Group"
# from phase_identity_catalog, so must load after it.
phase_system_bot_user() {
  [[ -f core/systems/fixtures/bootstrap_system_bot_user.json ]] && \
    loaddata "core/systems/fixtures/bootstrap_system_bot_user.json"
}

# Standalone identity_group/*.json files not covered by phase_identity_catalog
# (none expected after bootstrap consolidation; keep glob for future side files).
# Depends on organizations when groups reference managing_entity.
phase_identity_org_access() {
  local -a files=()
  local f
  for f in core/identities/fixtures/identity_group/*.json; do
    [[ "$f" == "core/identities/fixtures/identity_group/bootstrap_emr_identity_groups.json" ]] && continue
    [[ -f "$f" ]] && files+=("$f")
  done
  ((${#files[@]} > 0)) && loaddata "${files[@]}"
}

phase_assignments() {
  local -a files=()
  while IFS= read -r f; do
    [[ -n "$f" ]] && files+=("$f")
  done < <(sorted_glob "core/security/fixtures/policy_bundle_assignments/*.json")
  loaddata "${files[@]}"
}

phase_app_fixtures() {
  # Org/location before clinical_inventory, operations, lab, etc. (FK deps).
  phase_entities

  local -a files=()
  local path skip
  while IFS= read -r path; do
    skip=0
    for prefix in "${EXCLUDE_APP_FIXTURES[@]}"; do
      if [[ "$path" == "$prefix"* ]]; then
        skip=1
        break
      fi
    done
    if is_fixture_excluded "$path"; then
      skip=1
    fi
    ((skip)) && continue
    files+=("$path")
  done < <(find core -type f -name '*.json' -path '*/fixtures/*' | LC_ALL=C sort)

  loaddata "${files[@]}"
}

phase_individuals() {
  local -a files=()
  while IFS= read -r f; do
    [[ -n "$f" ]] && files+=("$f")
  done < <(find core/individuals/fixtures/practitioners -type f -name '*.json' 2>/dev/null | LC_ALL=C sort)
  ((${#files[@]} > 0)) && loaddata "${files[@]}"
  if ((WITH_PRACTITIONER_TYPO_FIXTURE)) && [[ -f core/individuals/fixtures/practioner.json ]]; then
    loaddata "core/individuals/fixtures/practioner.json"
  fi
}

phase_extras() {
  local -a files=()
  if ((WITH_NAVIGATION)); then
    files+=("core/resource_definition/fixtures/route/navigation_route.generated.json")
  fi
  if [[ -f core/systems/fixtures/workflow_system_user.json ]]; then
    files+=("core/systems/fixtures/workflow_system_user.json")
  fi
  if ((${#files[@]} > 0)); then
    loaddata "${files[@]}"
  fi
  if ((WITH_INDIVIDUALS)); then
    phase_individuals
  fi
}

phase_workflows() {
  local wf_dir="core/workflows/fixtures/legacy"

  # Legacy monolith layout (not yet split into activities/ + plans/ + wiring/).
  # Cleaned workflows load via patient_visit_registration, inpatient-admission, encounter-billing, etc. — see manifests/.
  # WF-06 inpatient_admission_flow.json removed — use PROFILE=inpatient-admission (enterprise layout).

  # 1. Built-in activity registry (no FK deps)
  [[ -f "$wf_dir/builtin_workflow_activities.json" ]] && \
    loaddata "$wf_dir/builtin_workflow_activities.json"

  # 2. Flow files: ActivityDefinition + PlanDefinition rows (sorted; independent of each other)
  local -a flow_files=()
  while IFS= read -r f; do
    [[ -n "$f" ]] && flow_files+=("$f")
  done < <(find "$wf_dir" -maxdepth 1 -type f -name '*_flow.json' | LC_ALL=C sort)
  ((${#flow_files[@]} > 0)) && loaddata "${flow_files[@]}"

  # 3. Plan bindings (WorkflowPlanBinding — FK to PlanDefinition)
  local -a binding_order=(
    "$wf_dir/default_plan_bindings.json"
    "$wf_dir/default_plan_bindings_clinical.json"
  )
  local -a binding_files=()
  for f in "${binding_order[@]}"; do
    [[ -f "$f" ]] && binding_files+=("$f")
  done
  ((${#binding_files[@]} > 0)) && loaddata "${binding_files[@]}"

  # 4. Auto-start rules (WorkflowAutoStartRule — uses context_key strings, no PK FK)
  local -a rule_order=(
    "$wf_dir/default_auto_start_rules.json"
    "$wf_dir/default_auto_start_rules_extended.json"
    "$wf_dir/default_auto_start_rules_clinical.json"
  )
  local -a rule_files=()
  for f in "${rule_order[@]}"; do
    [[ -f "$f" ]] && rule_files+=("$f")
  done
  ((${#rule_files[@]} > 0)) && loaddata "${rule_files[@]}"
}

phase_security() {
  phase_authorization_concepts
  phase_policies
  phase_policy_bundles
  phase_identities
  phase_assignments
}

phase_resources_policies() {
  phase_resources
  phase_resource_questionnaires
  phase_security
}

phase_full() {
  phase_authorization_concepts
  phase_terminology
  phase_resources
  phase_resource_questionnaires
  phase_policies
  phase_policy_bundles
  phase_app_fixtures
  phase_identities
  phase_assignments
  phase_extras
}

# terminology + resources + security stack + org/location/users/practitioners/identities
# + assignments. No notifications / operations / lab / inventory config, no workflows.
phase_registration_billing() {
  # Catalog ChargeItemDefinition.code FKs must exist (e.g. REG-ADMIT) even when core-bootstrap ran earlier.
  loaddata \
    "core/terminology/fixtures/charge_item_billing_codes/code_system.json" \
    "core/terminology/fixtures/charge_item_billing_codes/value_set.json" \
    "core/pricing/fixtures/registration/catalog.json" \
    "core/operations/fixtures/registration/pricing_config.json" \
    "core/operations/fixtures/registration/encounter_config.json"
}

# procedure_session — WF-17 perioperative plan (create/attach → prepay → clinical waits).
# Manifest: core/workflows/fixtures/manifests/procedure_session.json
# Prerequisite: core-bootstrap / any profile that loads activities/builtin.json
# (create-wait-binding + signal-event). Manifest load_order omits builtin on purpose.
phase_procedure_session() {
  loaddata \
    "core/workflows/fixtures/activities/perioperative.json" \
    "core/workflows/fixtures/plans/procedure_session.json" \
    "core/workflows/fixtures/wiring/procedure_session.json"
}

# patient_visit_registration — enterprise fixture layout only; does not load other workflows.
# Manifest: core/workflows/fixtures/manifests/patient_visit_registration.json
# Notification manifest: core/notifications/fixtures/manifests/patient_visit_registration.json
# Prerequisite: core-bootstrap (+ registration-billing for charge expansion policy).
phase_patient_visit_registration() {
  loaddata \
    "core/workflows/fixtures/activities/builtin.json" \
    "core/workflows/fixtures/activities/registration.json" \
    "core/workflows/fixtures/activities/documents.json" \
    "core/workflows/fixtures/plans/patient_visit_registration.json" \
    "core/workflows/fixtures/wiring/patient_visit_registration.json" \
    "core/notifications/fixtures/registration/notification_config.json"
}

# triage_assessment — enterprise fixture layout only; does not load other workflows.
# Manifest: core/workflows/fixtures/manifests/triage_assessment.json
# Loads org + identity-group catalog first (protocol config + notify routing FKs).
# Still need core-bootstrap (terminology/security/users) + WF-01 for a live triage Task.
# Auto-start: task.assigned with task_code=triage → context_key triage.assessment.
phase_triage_assessment() {
  phase_entities
  phase_identity_catalog
  loaddata \
    "core/workflows/fixtures/activities/builtin.json" \
    "core/workflows/fixtures/activities/triage.json" \
    "core/workflows/fixtures/plans/triage_assessment.json" \
    "core/workflows/fixtures/wiring/triage_assessment.json" \
    "core/operations/fixtures/ehr_triage_protocol_config.json" \
    "core/operations/fixtures/ehr_triage_esi_thresholds.json" \
    "core/operations/fixtures/ehr_encounter_completion_policy.json" \
    "core/notifications/fixtures/triage/notification_config.json" \
    "core/scheduling/fixtures/task_type_config.json"
}

# consultation_assessment — Phase-2 CWM claim-start (task.assigned + task_code=consultation).
# Manifest: core/workflows/fixtures/manifests/consultation_assessment.json
# Prerequisite: triage_assessment (or appointment intake) creates the consultation Task.
phase_consultation_assessment() {
  phase_entities
  loaddata \
    "core/workflows/fixtures/activities/builtin.json" \
    "core/workflows/fixtures/activities/consultation.json" \
    "core/workflows/fixtures/plans/consultation_assessment.json" \
    "core/workflows/fixtures/wiring/consultation_assessment.json" \
    "core/scheduling/fixtures/task_type_config.json"
}

# medication_prescription_review — enterprise layout; auto-start medication_request.created.
# Manifest: core/workflows/fixtures/manifests/medication_prescription_review.json
# Companions: notifications/medication + inventory|clinical_inventory|inventory_stock|pricing /medication/
# Legacy medication_*_flow.json removed — enterprise paths only.
phase_medication_prescription_review() {
  phase_entities
  loaddata \
    "core/workflows/fixtures/activities/builtin.json" \
    "core/workflows/fixtures/activities/medication.json" \
    "core/workflows/fixtures/plans/medication_prescription_review.json" \
    "core/workflows/fixtures/wiring/medication_prescription_review.json" \
    "core/operations/fixtures/ehr_medication_operations_config.json" \
    "core/medications/fixtures/drug_interaction_pairs.json" \
    "core/notifications/fixtures/medication/notification_config.json" \
    "core/inventory/fixtures/medication/paracetamol_inventory_item.json" \
    "core/clinical_inventory/fixtures/medication/paracetamol_binding.json" \
    "core/inventory_stock/fixtures/medication/paracetamol_opening_stock.json" \
    "core/pricing/fixtures/medication/paracetamol_package.json" \
    "core/medications/fixtures/medication/paracetamol_charge_binding.json"
}

# pharmacy_fulfillment — claim-start via task.assigned + task_code=pharmacy-review.
# Manifest: core/workflows/fixtures/manifests/pharmacy_fulfillment.json
# Companion inventory/pricing: clinical_inventory + pricing manifests/medication.json
# Prerequisite: medication_prescription_review creates the pharmacy-review Task.
phase_pharmacy_fulfillment() {
  phase_entities
  phase_identity_catalog
  loaddata \
    "core/workflows/fixtures/activities/builtin.json" \
    "core/workflows/fixtures/activities/medication.json" \
    "core/workflows/fixtures/plans/pharmacy_fulfillment.json" \
    "core/workflows/fixtures/wiring/pharmacy_fulfillment.json" \
    "core/operations/fixtures/ehr_medication_operations_config.json" \
    "core/medications/fixtures/drug_interaction_pairs.json" \
    "core/notifications/fixtures/medication/notification_config.json" \
    "core/scheduling/fixtures/task_type_config.json" \
    "core/inventory/fixtures/medication/paracetamol_inventory_item.json" \
    "core/clinical_inventory/fixtures/medication/paracetamol_binding.json" \
    "core/inventory_stock/fixtures/medication/paracetamol_opening_stock.json" \
    "core/pricing/fixtures/medication/paracetamol_package.json" \
    "core/medications/fixtures/medication/paracetamol_charge_binding.json"
}

# medication_administration — MAR plan; instances started by scan_due_medication_administrations.
# Manifest: core/workflows/fixtures/manifests/medication_administration.json
# Notify: department tenants → Ward Nursing Team (never a646e755 enterprise org).
phase_medication_administration() {
  phase_entities
  phase_identity_catalog
  loaddata \
    "core/workflows/fixtures/activities/builtin.json" \
    "core/workflows/fixtures/activities/medication.json" \
    "core/workflows/fixtures/plans/medication_administration.json" \
    "core/workflows/fixtures/wiring/medication_administration.json" \
    "core/notifications/fixtures/medication/notification_config.json" \
    "core/scheduling/fixtures/task_type_config.json"
}

# patient_onboarding — enterprise fixture layout only.
# Manifest: core/workflows/fixtures/manifests/patient_onboarding.json
# Prerequisite: core-bootstrap (patient.create emits patient.registered).
phase_patient_onboarding() {
  loaddata \
    "core/workflows/fixtures/activities/onboarding.json" \
    "core/workflows/fixtures/plans/patient_onboarding.json" \
    "core/workflows/fixtures/wiring/patient_onboarding.json"
}

# encounter_billing — enterprise fixture layout only.
# Manifest: core/workflows/fixtures/manifests/encounter_billing.json
# Prerequisite: core-bootstrap (trigger_type terminology).
phase_encounter_billing() {
  loaddata \
    "core/workflows/fixtures/activities/billing.json" \
    "core/workflows/fixtures/plans/encounter_billing.json" \
    "core/workflows/fixtures/wiring/encounter_billing.json"
}

# inpatient_admission — enterprise fixture layout only (WF-06).
# Manifest: core/workflows/fixtures/manifests/inpatient_admission.json
# Prerequisite: core-bootstrap (terminology, security, identities, org/location).
phase_inpatient_admission() {
  loaddata \
    "core/workflows/fixtures/activities/builtin.json" \
    "core/workflows/fixtures/activities/admission.json" \
    "core/workflows/fixtures/plans/inpatient_admission.json" \
    "core/workflows/fixtures/wiring/inpatient_admission.json" \
    "core/notifications/fixtures/inpatient_admission/notification_config.json" \
    "core/operations/fixtures/ehr_admission_documents_config.json"
}

# capacity-bed-management — bed ops policies + capacity notification routing (Phases E–H).
# Prerequisite: core-bootstrap + pricing charge_item_definition for accommodation policy FKs.
phase_capacity_bed_management() {
  loaddata \
    "core/terminology/fixtures/capacity_room_type/code_system.json" \
    "core/terminology/fixtures/capacity_room_type/value_set.json" \
    "core/terminology/fixtures/capacity_bed_type/code_system.json" \
    "core/terminology/fixtures/capacity_bed_type/value_set.json" \
    "core/terminology/fixtures/capacity_accommodation_class/code_system.json" \
    "core/terminology/fixtures/capacity_accommodation_class/value_set.json" \
    "core/capacity/fixtures/bootstrap_inpatient_beds.json" \
    "core/pricing/fixtures/ehr_charge_item_definition.json" \
    "core/operations/fixtures/ehr_bed_transit_policy.json" \
    "core/operations/fixtures/ehr_bed_matching_policy.json" \
    "core/operations/fixtures/ehr_bed_turnover_policy.json" \
    "core/operations/fixtures/ehr_capacity_integration_routing_config.json" \
    "core/operations/fixtures/ehr_accommodation_charge_policy.json" \
    "core/notifications/fixtures/capacity/notification_config.json"
}

# Uncleaned notification configs (monolith / per-workflow bundles not yet migrated).
phase_notifications_legacy() {
  local nf_dir="core/notifications/fixtures/legacy"
  local -a files=()
  while IFS= read -r f; do
    [[ -n "$f" ]] && files+=("$f")
  done < <(find "$nf_dir" -maxdepth 1 -type f -name '*.json' | LC_ALL=C sort)
  ((${#files[@]} > 0)) && loaddata "${files[@]}"
  if [[ -f core/notifications/fixtures/perioperative/notification_config.json ]]; then
    loaddata "core/notifications/fixtures/perioperative/notification_config.json"
  fi
}

phase_core_bootstrap() {
  phase_authorization_concepts
  phase_terminology
  # Identity catalog + system users must exist before policies load (Policy.asserter
  # FKs to the system bot user; only depends on terminology, nothing resource/policy-side).
  phase_identity_catalog
  phase_system_users
  phase_system_bot_user
  phase_resources
  phase_resource_questionnaires
  phase_policies
  phase_policy_bundles
  phase_entities
  phase_identity_org_access
  phase_individuals
  phase_identity_members
  phase_assignments
}

run_profile() {
  case "$PROFILE" in
    full) phase_full ;;
    security) phase_security ;;
    resources-policies) phase_resources_policies ;;
    terminology) phase_terminology ;;
    resources)
      phase_resources
      phase_resource_questionnaires
      ;;
    policies) phase_policies ;;
    policy-bundles) phase_policy_bundles ;;
    identities) phase_identities ;;
    assignments) phase_assignments ;;
    app-fixtures) phase_app_fixtures ;;
    extras) phase_extras ;;
    workflows) phase_workflows ;;
    patient_visit_registration) phase_patient_visit_registration ;;
    procedure_session) phase_procedure_session ;;
    patient_onboarding) phase_patient_onboarding ;;
    triage_assessment) phase_triage_assessment ;;
    consultation_assessment) phase_consultation_assessment ;;
    medication_prescription_review) phase_medication_prescription_review ;;
    pharmacy_fulfillment) phase_pharmacy_fulfillment ;;
    medication_administration) phase_medication_administration ;;
    inpatient-admission) phase_inpatient_admission ;;
    capacity-bed-management) phase_capacity_bed_management ;;
    encounter-billing) phase_encounter_billing ;;
    registration-billing) phase_registration_billing ;;
    notifications-legacy) phase_notifications_legacy ;;
    core-bootstrap) phase_core_bootstrap ;;
    *)
      echo "Unknown profile: $PROFILE" >&2
      usage >&2
      exit 1
      ;;
  esac
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile)
      PROFILE="${2:?--profile requires a value}"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --with-navigation)
      WITH_NAVIGATION=1
      shift
      ;;
    --with-practitioner)
      WITH_PRACTITIONER_TYPO_FIXTURE=1
      shift
      ;;
    --with-individuals)
      WITH_INDIVIDUALS=1
      shift
      ;;
    --extra)
      IFS=',' read -ra EXTRA_TERMINOLOGY <<< "${2:?--extra requires comma-separated bundle names}"
      shift 2
      ;;
    -h | --help)
      usage
      exit 0
      ;;
    -*)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
    *)
      # Positional profile name (same as --profile NAME).
      PROFILE="$1"
      shift
      ;;
  esac
done

log "profile=$PROFILE root=$ROOT manage=$MANAGE"
run_profile
log "done"
