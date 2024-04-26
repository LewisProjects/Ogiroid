"""empty message

Revision ID: 235e78366c89
Revises: 6546c41828df
Create Date: 2024-04-26 17:43:30.151521

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '235e78366c89'
down_revision: Union[str, None] = '6546c41828df'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('auto_response_messages', 'ephemeral')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('auto_response_messages', sa.Column('ephemeral', sa.BOOLEAN(), autoincrement=False, nullable=True))
    # ### end Alembic commands ###
