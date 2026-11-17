"""add unique constraint to user email

Revision ID: aa2102b46174
Revises: 90d529bbe7c4
Create Date: 2026-11-17 15:58:07.970342

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aa2102b46174'
down_revision: Union[str, Sequence[str], None] = '90d529bbe7c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint("uq_users_email", "users", ["email"])


def downgrade() -> None:
    op.drop_constraint("uq_users_email", "users", type_="unique")
