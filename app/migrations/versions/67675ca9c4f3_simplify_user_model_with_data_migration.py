"""Simplify user model with data migration

Revision ID: 67675ca9c4f3
Revises: c5aee2640c29
Create Date: 2025-09-22 12:51:59.704961

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '67675ca9c4f3'
down_revision = 'c5aee2640c29'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Step 1: Add new columns as nullable first
    op.add_column('users', sa.Column('password', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('profile_picture', sa.String(length=500), nullable=True))
    op.add_column('users', sa.Column('primary_number', sa.String(length=18), nullable=True))
    op.add_column('users', sa.Column('secondary_number', sa.String(length=18), nullable=True))
    op.add_column('users', sa.Column('timezone', sa.String(length=255), nullable=True))
    
    # Step 2: Copy data from password_hash to password
    op.execute("UPDATE users SET password = password_hash WHERE password_hash IS NOT NULL")
    
    # Step 3: Set default timezone for existing users
    op.execute("UPDATE users SET timezone = 'UTC' WHERE timezone IS NULL")
    
    # Step 4: Make password and timezone NOT NULL
    op.alter_column('users', 'password', nullable=False)
    op.alter_column('users', 'timezone', nullable=False)
    
    # Step 5: Alter column types
    op.alter_column('users', 'email',
               existing_type=sa.VARCHAR(length=255),
               type_=sa.String(length=64),
               existing_nullable=False)
    op.alter_column('users', 'first_name',
               existing_type=sa.VARCHAR(length=50),
               type_=sa.String(length=32),
               existing_nullable=False)
    op.alter_column('users', 'last_name',
               existing_type=sa.VARCHAR(length=50),
               type_=sa.String(length=32),
               existing_nullable=False)
    
    # Step 6: Drop old columns and indexes
    op.drop_index('ix_users_organization_id', table_name='users')
    op.drop_column('users', 'bio')
    op.drop_column('users', 'is_admin')
    op.drop_column('users', 'avatar_url')
    op.drop_column('users', 'is_verified')
    op.drop_column('users', 'job_title')
    op.drop_column('users', 'phone')
    op.drop_column('users', 'password_hash')
    op.drop_column('users', 'last_login')
    op.drop_column('users', 'organization_id')
    op.drop_column('users', 'verified_at')
    op.drop_column('users', 'company')
    op.drop_column('users', 'linkedin_url')


def downgrade() -> None:
    # Reverse the migration
    op.add_column('users', sa.Column('linkedin_url', sa.VARCHAR(length=255), autoincrement=False, nullable=True))
    op.add_column('users', sa.Column('company', sa.VARCHAR(length=100), autoincrement=False, nullable=True))
    op.add_column('users', sa.Column('verified_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True))
    op.add_column('users', sa.Column('organization_id', sa.UUID(), autoincrement=False, nullable=True))
    op.add_column('users', sa.Column('last_login', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True))
    op.add_column('users', sa.Column('password_hash', sa.VARCHAR(length=255), autoincrement=False, nullable=False))
    op.add_column('users', sa.Column('phone', sa.VARCHAR(length=20), autoincrement=False, nullable=True))
    op.add_column('users', sa.Column('job_title', sa.VARCHAR(length=100), autoincrement=False, nullable=True))
    op.add_column('users', sa.Column('is_verified', sa.BOOLEAN(), autoincrement=False, nullable=False))
    op.add_column('users', sa.Column('avatar_url', sa.VARCHAR(length=500), autoincrement=False, nullable=True))
    op.add_column('users', sa.Column('is_admin', sa.BOOLEAN(), autoincrement=False, nullable=False))
    op.add_column('users', sa.Column('bio', sa.TEXT(), autoincrement=False, nullable=True))
    op.create_index('ix_users_organization_id', 'users', ['organization_id'], unique=False)
    
    # Copy password back to password_hash
    op.execute("UPDATE users SET password_hash = password WHERE password IS NOT NULL")
    
    # Alter column types back
    op.alter_column('users', 'last_name',
               existing_type=sa.String(length=32),
               type_=sa.VARCHAR(length=50),
               existing_nullable=False)
    op.alter_column('users', 'first_name',
               existing_type=sa.String(length=32),
               type_=sa.VARCHAR(length=50),
               existing_nullable=False)
    op.alter_column('users', 'email',
               existing_type=sa.String(length=64),
               type_=sa.VARCHAR(length=255),
               existing_nullable=False)
    
    # Drop new columns
    op.drop_column('users', 'timezone')
    op.drop_column('users', 'secondary_number')
    op.drop_column('users', 'primary_number')
    op.drop_column('users', 'profile_picture')
    op.drop_column('users', 'password')
