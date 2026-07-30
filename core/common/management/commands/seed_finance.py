"""
Management command to seed minimum required financial data for testing.

Creates:
    - PaymentMethod: CASH, CARD, MOBILE_MONEY
    - POSTerminal: POS-001
    - GLAccount: 1100 (Cash), 1200 (Accounts Receivable)

Usage:
    python manage.py seed_finance
"""

from django.apps import apps
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Seed minimum financial data required for POS testing"
    requires_system_checks = []

    def handle(self, *args, **options):
        self._seed_payment_methods()
        self._seed_pos_terminal()
        self._seed_gl_accounts()
        self.stdout.write(self.style.SUCCESS("✔ Finance seed data loaded successfully"))

    def _seed_payment_methods(self):

        PaymentMethod = apps.get_model("payments", "PaymentMethod")

        methods = [
            {"name": "Cash", "code": "CASH"},
            {"name": "Card", "code": "CARD"},
            {"name": "Mobile Money", "code": "MOBILE_MONEY"},
            {"name": "Bank Transfer", "code": "BANK_TRANSFER"},
            {"name": "Wallet", "code": "WALLET"},
        ]
        created = 0
        for m in methods:
            _, is_new = PaymentMethod.objects.get_or_create(
                code=m["code"], defaults={"name": m["name"], "active": True}
            )
            if is_new:
                created += 1

        self.stdout.write(f"  PaymentMethod: {created} created, {len(methods) - created} already existed")

    def _seed_pos_terminal(self):

        POSTerminal = apps.get_model("pos", "POSTerminal")

        terminals = [
            {"terminal_code": "POS-001", "name": "Cashier Desk 1", "location": "OPD Reception"},
            {"terminal_code": "POS-002", "name": "Cashier Desk 2", "location": "Pharmacy"},
        ]
        created = 0
        for t in terminals:
            _, is_new = POSTerminal.objects.get_or_create(
                terminal_code=t["terminal_code"],
                defaults={"name": t["name"], "location": t["location"], "is_active": True},
            )
            if is_new:
                created += 1

        self.stdout.write(f"  POSTerminal: {created} created, {len(terminals) - created} already existed")

    def _seed_gl_accounts(self):

        GLAccount = apps.get_model("accounting", "GLAccount")
        Concept = apps.get_model("terminology", "Concept")

        def get_type(code):
            return Concept.objects.filter(code_system__name="gl-account-type", code=code).first()

        accounts = [
            {"code": "1000", "name": "Current Assets", "type_code": "ASSET", "parent_code": None},
            {"code": "1100", "name": "Cash / Bank", "type_code": "ASSET", "parent_code": "1000"},
            {"code": "1200", "name": "Accounts Receivable", "type_code": "ASSET", "parent_code": "1000"},
            {"code": "2000", "name": "Current Liabilities", "type_code": "LIABILITY", "parent_code": None},
            {"code": "4000", "name": "Revenue", "type_code": "REVENUE", "parent_code": None},
            {"code": "4100", "name": "Service Revenue", "type_code": "REVENUE", "parent_code": "4000"},
            {"code": "5000", "name": "Expenses", "type_code": "EXPENSE", "parent_code": None},
            {"code": "5100", "name": "Write-off Expense", "type_code": "EXPENSE", "parent_code": "5000"},
        ]

        created = 0
        for a in accounts:
            type_concept = get_type(a["type_code"])
            if not type_concept:
                self.stdout.write(
                    self.style.WARNING(
                        f"  Skipping {a['code']} — gl-account-type fixture not loaded. "
                        "Run: manage.py loaddata gl_account_type"
                    )
                )
                continue
            _, is_new = GLAccount.objects.get_or_create(
                code=a["code"],
                defaults={"name": a["name"], "type": type_concept, "is_active": True},
            )
            if is_new:
                created += 1

        # Wire up parents
        for a in accounts:
            if a["parent_code"]:
                try:
                    account = GLAccount.objects.get(code=a["code"])
                    parent = GLAccount.objects.get(code=a["parent_code"])
                    if account.parent != parent:
                        account.parent = parent
                        account.save(update_fields=["parent"])
                except GLAccount.DoesNotExist:
                    pass

        self.stdout.write(f"  GLAccount: {created} created, {len(accounts) - created} already existed")
