"""Add notifications table and notification_preferences table

Revision ID: 0015
Revises: 0013
Create Date: 2026-06-05 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0015'
down_revision = '0013'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create notifications table
    op.create_table(
        'notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.func.gen_random_uuid()),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.String(1000), nullable=False),
        sa.Column('action_url', sa.String(500), nullable=True),
        sa.Column('read', sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column('delivered', sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column('email_sent', sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('email_sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )

    # Create index for user lookups
    op.create_index(
        'ix_notifications_user_id',
        'notifications',
        ['user_id'],
    )

    # Create index for recent notifications
    op.create_index(
        'ix_notifications_created_at',
        'notifications',
        ['created_at'],
    )

    # Create index for unread notifications
    op.create_index(
        'ix_notifications_read',
        'notifications',
        ['read'],
    )

    # Create notification_preferences table
    op.create_table(
        'notification_preferences',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.func.gen_random_uuid()),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('email_notifications', sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column('in_app_notifications', sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column('notification_types', postgresql.JSONB, nullable=False, server_default=sa.text("""
            jsonb_build_object(
                'interview_scheduled', true,
                'scorecard_request', true,
                'candidate_advanced', true,
                'pipeline_update', true,
                'system_alerts', true
            )
        """)),
        sa.Column('quiet_hours_enabled', sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column('quiet_hours_start', sa.String(5), nullable=True),
        sa.Column('quiet_hours_end', sa.String(5), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )

    # Create index for user preferences lookups
    op.create_index(
        'ix_notification_preferences_user_id',
        'notification_preferences',
        ['user_id'],
    )


def downgrade() -> None:
    # Drop notification_preferences table and its indexes
    op.drop_index('ix_notification_preferences_user_id', table_name='notification_preferences')
    op.drop_table('notification_preferences')

    # Drop notifications table and its indexes
    op.drop_index('ix_notifications_read', table_name='notifications')
    op.drop_index('ix_notifications_created_at', table_name='notifications')
    op.drop_index('ix_notifications_user_id', table_name='notifications')
    op.drop_table('notifications')
