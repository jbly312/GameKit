"""match lifecycle

Revision ID: b3dd921816fe
Revises: 'f8e9345f03e4'
Create Date: 2026-08-11 00:20:26.086097

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3dd921816fe'
down_revision: Union[str, None] = 'f8e9345f03e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table('matches')
    op.create_table(
        'matches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('game_id', sa.UUID(), nullable=False),
        sa.Column('winner_id', sa.Integer(), nullable=False),
        sa.Column('loser_id', sa.Integer(), nullable=False),
        sa.Column('idempotency_key', sa.String(length=128), nullable=False),
        sa.Column('winner_rating_after', sa.Float(), nullable=True),
        sa.Column('loser_rating_after', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),   # см. ниже
        sa.Column('submitted_by_id', sa.Integer(), nullable=False),
        sa.Column('confirmed_by_id', sa.Integer(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['game_id'], ['games.id']),
        sa.ForeignKeyConstraint(['winner_id'], ['players.id']),
        sa.ForeignKeyConstraint(['loser_id'], ['players.id']),
        sa.ForeignKeyConstraint(['submitted_by_id'], ['players.id']),
        sa.ForeignKeyConstraint(['confirmed_by_id'], ['players.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('game_id', 'idempotency_key', name='uq_match_game_idempotency'),
    )
    op.create_index(op.f('ix_matches_status'), 'matches', ['status'])


def downgrade() -> None:
    pass