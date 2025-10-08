"""remove event constraints

Revision ID: a1b2c3d4e5f6
Revises: f852d93efa1a
Create Date: 2025-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'b3b09e687ad6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Use raw SQL to drop constraints safely
    connection = op.get_bind()
    
    # Check and drop unique_user_event constraint
    result = connection.execute(
        text("SELECT 1 FROM information_schema.table_constraints "
             "WHERE constraint_name = 'unique_user_event' AND table_name = 'events'")
    ).fetchone()
    if result:
        op.drop_constraint('unique_user_event', 'events', type_='unique')
    
    # Check and drop unique_user_event_start_date constraint
    result = connection.execute(
        text("SELECT 1 FROM information_schema.table_constraints "
             "WHERE constraint_name = 'unique_user_event_start_date' AND table_name = 'events'")
    ).fetchone()
    if result:
        op.drop_constraint('unique_user_event_start_date', 'events', type_='unique')
    
    # Check and drop check_end_after_start constraint
    result = connection.execute(
        text("SELECT 1 FROM information_schema.table_constraints "
             "WHERE constraint_name = 'check_end_after_start' AND table_name = 'events'")
    ).fetchone()
    if result:
        op.drop_constraint('check_end_after_start', 'events', type_='check')


def downgrade() -> None:
    # Recreate the check constraint for end_date > start_date
    op.create_check_constraint(
        'check_end_after_start',
        'events',
        'end_date > start_date'
    )
    
    # Recreate the original unique constraint with user_id, title, and start_date
    op.create_unique_constraint('unique_user_event', 'events', ['user_id', 'title', 'start_date'])
