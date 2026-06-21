"""reconcile live DB index/FK drift to match models (no-op on fresh DBs)

The long-lived staging ``truematch`` DB was hand-built (create_all from an
older model revision) and ``alembic stamp``'d, so it accumulated legacy
single-column indexes and ``ON DELETE`` FK behavior that the current models —
and therefore a fresh ``alembic upgrade head`` DB — do NOT declare. A fresh
migration DB already matches the models (``alembic check`` → 0 ops); only the
hand-built live DB drifts.

This migration reconciles the live DB to the models. Every statement is
idempotent (``IF EXISTS`` / ``IF NOT EXISTS`` / drop-then-add), so it is a
clean no-op when applied to a fresh DB that already matches the models. It
touches NO row data — only index/constraint metadata.

Categories:
  * 4 index renames  (legacy custom name -> model's auto-generated name)
  * 3 missing indexes created (models declare them; live lacks them)
  * 25 legacy indexes dropped (live has them; models do not declare them)
  * job_deduplication.fingerprint: unique CONSTRAINT + plain index -> single
    UNIQUE INDEX (what the model's ``unique=True, index=True`` produces)
  * 7 FK reconciliations: training_* FKs recreated without ON DELETE CASCADE;
    scraping_run / mass_upload_batch / upload_field_mapping FKs dropped
    entirely (those model columns no longer declare a ForeignKey)
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "d4e1f7a2c9b8"
down_revision = "b9a3b46fdf1b"
branch_labels = None
depends_on = None


# (old_name, new_name) — ALTER INDEX ... RENAME TO is cheap (metadata only).
_RENAMES = [
    ("ix_capability_mapping_confidence", "ix_capability_mapping_confidence_score"),
    ("ix_capability_mapping_keyword", "ix_capability_mapping_cv_keyword"),
    ("ix_credential_mapping_score", "ix_credential_mapping_match_score"),
    ("ix_virtual_brain_state_active", "ix_virtual_brain_state_is_active"),
]

# (index_name, table, column) — models declare these; live DB lacks them.
_CREATES = [
    ("ix_assessments_decision_type", "assessments", "decision_type"),
    ("ix_notifications_delivered", "notifications", "delivered"),
    ("ix_training_progress_metric_name", "training_progress", "metric_name"),
]

# Legacy indexes present on the live DB but not declared by any model.
_DROPS = [
    "ix_applications_resume_id",
    "ix_chat_session_memories_session_id",
    "ix_governance_logs_gate_name",
    "ix_job_deduplication_ingest_queue_item_id",
    "ix_job_scraping_config_enabled",
    "ix_job_scraping_config_source_type",
    "ix_mass_upload_batch_status",
    "ix_mass_upload_batch_user_id",
    "ix_scraping_run_config_id",
    "ix_scraping_run_status",
    "ix_training_chat_messages_created_at",
    "ix_training_chat_messages_session_id",
    "ix_training_chat_messages_user_id",
    "ix_training_data_items_applied",
    "ix_training_data_items_decision",
    "ix_training_data_items_upload_id",
    "ix_training_data_uploads_created_at",
    "ix_training_data_uploads_status",
    "ix_training_data_uploads_user_id",
    "ix_training_insight_batches_created_at",
    "ix_training_insight_batches_source",
    "ix_training_learning_sessions_created_at",
    "ix_training_learning_sessions_status",
    "ix_training_learning_sessions_user_id",
    "ix_upload_field_mapping_is_system",
    "ix_upload_field_mapping_name",
]

# FKs the models still declare (without ondelete) — recreate without CASCADE.
# (constraint_name, table, column, ref_table, ref_column)
_FK_RECREATE = [
    ("training_chat_messages_user_id_fkey", "training_chat_messages", "user_id", "users", "id"),
    ("training_data_items_upload_id_fkey", "training_data_items", "upload_id", "training_data_uploads", "id"),
    ("training_data_uploads_user_id_fkey", "training_data_uploads", "user_id", "users", "id"),
    ("training_learning_sessions_user_id_fkey", "training_learning_sessions", "user_id", "users", "id"),
]

# FKs the models no longer declare at all — drop entirely.
# (constraint_name, table)
_FK_DROP = [
    ("scraping_run_config_id_fkey", "scraping_run"),
    ("mass_upload_batch_user_id_fkey", "mass_upload_batch"),
    ("upload_field_mapping_created_by_fkey", "upload_field_mapping"),
]


def upgrade() -> None:
    # 1. Renames — only when the legacy name still exists (skips fresh DBs,
    #    which already carry the new name).
    for old, new in _RENAMES:
        op.execute(
            f"DO $$ BEGIN "
            f"IF EXISTS (SELECT 1 FROM pg_class WHERE relname = '{old}') THEN "
            f"ALTER INDEX {old} RENAME TO {new}; "
            f"END IF; END $$;"
        )

    # 2. Create genuinely-missing indexes.
    for name, table, col in _CREATES:
        op.execute(f"CREATE INDEX IF NOT EXISTS {name} ON {table} ({col})")

    # 3. Drop legacy indexes the models do not declare.
    for name in _DROPS:
        op.execute(f"DROP INDEX IF EXISTS {name}")

    # 4. job_deduplication.fingerprint -> single UNIQUE INDEX (model:
    #    unique=True, index=True). Live has a unique CONSTRAINT + a plain
    #    index; collapse both into the unique index the model expects.
    op.execute(
        "ALTER TABLE job_deduplication "
        "DROP CONSTRAINT IF EXISTS job_deduplication_fingerprint_key"
    )
    op.execute("DROP INDEX IF EXISTS ix_job_deduplication_fingerprint")
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_job_deduplication_fingerprint "
        "ON job_deduplication (fingerprint)"
    )

    # 5. FK reconciliation. Drop-then-add is idempotent: on a fresh DB the FK
    #    already lacks ondelete, so it is dropped and re-added identically; on
    #    live the CASCADE/SET NULL variant is replaced with the plain FK.
    for name, table, col, ref_t, ref_c in _FK_RECREATE:
        op.execute(f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {name}")
        op.execute(
            f"ALTER TABLE {table} ADD CONSTRAINT {name} "
            f"FOREIGN KEY ({col}) REFERENCES {ref_t} ({ref_c})"
        )

    # 6. Drop FKs the models no longer declare.
    for name, table in _FK_DROP:
        op.execute(f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {name}")


def downgrade() -> None:
    # Reconciliation migration: reverse only the cheap, unambiguous metadata
    # changes (index renames). Re-creating the 25 dropped legacy indexes or
    # restoring the legacy CASCADE FKs is intentionally NOT done — that drift
    # was an artifact of the hand-built live DB, never part of the models.
    for old, new in _RENAMES:
        op.execute(
            f"DO $$ BEGIN "
            f"IF EXISTS (SELECT 1 FROM pg_class WHERE relname = '{new}') THEN "
            f"ALTER INDEX {new} RENAME TO {old}; "
            f"END IF; END $$;"
        )
    for name, table, _col in _CREATES:
        op.execute(f"DROP INDEX IF EXISTS {name}")
