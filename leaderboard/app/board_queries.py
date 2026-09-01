"""Ranking queries shared by every board type.

A board is ranked from a "values" relation: one row per player, columns
`player_id`, `value`, `created_at`. Where that relation comes from depends on
the board type — submitted scores, or the rating carried on the player — but
once it exists, ordering, paging and rank arithmetic are identical.
"""

from sqlalchemy import Select, Subquery, and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.board import Aggregation, Board, BoardType, SortDirection
from app.models.player import Player
from app.models.score import Score


def values_subquery(board: Board) -> Subquery:
    """One row per player with their current value on this board."""
    if board.type == BoardType.RATING:
        return (
            select(
                Player.id.label("player_id"),
                Player.rating.label("value"),
                Player.created_at.label("created_at"),
            )
            .where(Player.game_id == board.game_id)
            .subquery()
        )

    if board.aggregation == Aggregation.BEST:
        best_first = (
            Score.value.desc()
            if board.sort_direction == SortDirection.DESC
            else Score.value.asc()
        )
        # Among equal values keep the earliest — the same rule the ranking uses.
        inner_order = (Score.player_id, best_first, Score.created_at.asc(), Score.id.asc())
    else:  # Aggregation.LAST
        inner_order = (Score.player_id, Score.created_at.desc(), Score.id.desc())

    return (
        select(Score.player_id, Score.value, Score.created_at)
        .where(Score.board_id == board.id)
        .distinct(Score.player_id)
        .order_by(*inner_order)
        .subquery()
    )


def _ranking_order(board: Board, values: Subquery):
    """Best first, ties broken by who got there first.

    Without the tie-break equal values order arbitrarily, so ranks shift between
    requests and paging silently drops and repeats players.
    """
    primary = (
        values.c.value.desc()
        if board.sort_direction == SortDirection.DESC
        else values.c.value.asc()
    )
    return primary, values.c.created_at.asc(), values.c.player_id.asc()


def top_statement(board: Board, values: Subquery, limit: int, offset: int) -> Select:
    return (
        select(values.c.player_id, values.c.value, Player.display_name)
        .join(Player, Player.id == values.c.player_id)
        .order_by(*_ranking_order(board, values))
        .limit(limit)
        .offset(offset)
    )


async def player_standing(
    db: AsyncSession, board: Board, player_id: int
) -> tuple[float | None, int | None]:
    """The player's value and absolute rank, or (None, None) if they have none."""
    values = values_subquery(board)

    mine = (
        await db.execute(
            select(values.c.value, values.c.created_at).where(
                values.c.player_id == player_id
            )
        )
    ).one_or_none()
    if mine is None:
        return None, None

    my_value, my_created_at = mine
    strictly_better = (
        values.c.value > my_value
        if board.sort_direction == SortDirection.DESC
        else values.c.value < my_value
    )
    ahead = await db.scalar(
        select(func.count())
        .select_from(values)
        .where(
            or_(
                strictly_better,
                and_(
                    values.c.value == my_value,
                    values.c.created_at < my_created_at,
                ),
                # Mirrors the last tie-break in _ranking_order, so the rank
                # reported here always matches the position in /top.
                and_(
                    values.c.value == my_value,
                    values.c.created_at == my_created_at,
                    values.c.player_id < player_id,
                ),
            )
        )
    )
    return my_value, (ahead or 0) + 1
