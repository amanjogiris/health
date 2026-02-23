"""Fix duplicate enum types

Revision ID: 4021fb30b727
Revises: 4021fb30b726
Create Date: 2024-02-24 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '4021fb30b727'
down_revision = '4021fb30b726'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop existing types if they exist
    op.execute("DROP TYPE IF EXISTS appointment_status CASCADE")
    op.execute("DROP TYPE IF EXISTS user_roles CASCADE")
    
    # Recreate the enum types
    op.execute("CREATE TYPE user_roles AS ENUM ('admin', 'doctor', 'patient')")
    op.execute("CREATE TYPE appointment_status AS ENUM ('pending', 'confirmed', 'cancelled', 'completed', 'no_show')")


def downgrade() -> None:
    # Drop the enum types
    op.execute("DROP TYPE IF EXISTS appointment_status CASCADE")
    op.execute("DROP TYPE IF EXISTS user_roles CASCADE")
