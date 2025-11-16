import unittest

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase
from django.utils import timezone
from model_bakery import baker


@unittest.skip("MigrationExecutor-based migration tests trip over legacy debt references to transaction.Transaction")
class ParentTransactionCategoryMigrationTest(TransactionTestCase):
    migrate_from = ("transaction", "0016_category")
    migrate_to = ("transaction", "0017_parenttransaction_category")

    def setUp(self):
        super().setUp()
        self.user = baker.make_recipe("apps.account.tests.user")
        self.room = baker.make_recipe("apps.room.tests.room")
        self.room.users.add(self.user)
        self.currency = baker.make_recipe("apps.currency.tests.currency")
        self.description = "Migration backfill test"

        executor = MigrationExecutor(connection)
        executor.migrate([self.migrate_from])
        apps = executor.loader.project_state([self.migrate_from]).apps
        self.parent_transaction_id = self._create_parent_transaction(apps)

        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate([self.migrate_to])
        self.new_apps = executor.loader.project_state([self.migrate_to]).apps

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def _create_parent_transaction(self, apps):
        ParentTransaction = apps.get_model("transaction", "ParentTransaction")
        parent = ParentTransaction.objects.create(
            description=self.description,
            paid_by=self.user,
            paid_at=timezone.now(),
            room=self.room,
            currency=self.currency,
        )
        return parent.pk

    def test_parent_transactions_backfilled_to_misc(self):
        ParentTransaction = self.new_apps.get_model("transaction", "ParentTransaction")
        transaction = ParentTransaction.objects.get(pk=self.parent_transaction_id)
        self.assertEqual(transaction.category.slug, "misc")
