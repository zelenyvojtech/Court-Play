# app/repositories/time_block.py
import sqlite3
from datetime import datetime
from typing import List, Optional

from model.TimeBlock import TimeBlock, TimeBlockCreate, TimeBlockUpdate


def _row_to_time_block(row: sqlite3.Row) -> TimeBlock:
    """
    Převede řádek z tabulky time_block na Pydantic model TimeBlock.
    """
    return TimeBlock.model_validate(dict(row))


def list_time_blocks(conn: sqlite3.Connection) -> List[TimeBlock]:
    """
    Vrátí všechny blokace (údržba atd.).
    """
    rows = conn.execute(
        """
        SELECT time_block_id,
               start,
               end,
               courts_id
        FROM time_block
        ORDER BY start
        """
    ).fetchall()
    return [_row_to_time_block(r) for r in rows]


def list_time_blocks_for_court_between(
    conn: sqlite3.Connection,
    court_id: int,
    start: datetime,
    end: datetime,
) -> List[TimeBlock]:
    """
    Vrátí všechny časové bloky (údržba / blokace) pro daný kurt,
    které se jakkoli překrývají s intervalem (start, end).

    Stejná logika překryvu jako u rezervací:
        blok.start < end AND blok.end > start
    """
    start_str = start.isoformat()
    end_str = end.isoformat()

    rows = conn.execute(
        """
        SELECT time_block_id,
               start,
               end,
               courts_id
        FROM time_block
        WHERE courts_id = ?
          AND start < ?
          AND end > ?
        ORDER BY start
        """,
        (court_id, end_str, start_str),
    ).fetchall()
    return [_row_to_time_block(r) for r in rows]


def get_time_block(conn: sqlite3.Connection, time_block_id: int) -> Optional[TimeBlock]:
    """
    Vrátí jednu blokaci podle ID nebo None.
    """
    row = conn.execute(
        """
        SELECT time_block_id,
               start,
               end,
               courts_id
        FROM time_block
        WHERE time_block_id = ?
        """,
        (time_block_id,),
    ).fetchone()
    return _row_to_time_block(row) if row else None


def create_time_block(conn: sqlite3.Connection, data: TimeBlockCreate) -> TimeBlock:
    """
    Vytvoří nový časový blok.

    - `start` / `end` jsou datetime → do DB jdou jako ISO TEXT.
    """
    payload = data.model_dump(mode="json")

    cur = conn.execute(
        """
        INSERT INTO time_block (start, end, courts_id)
        VALUES (?, ?, ?)
        """,
        (
            payload["start"],
            payload["end"],
            payload["courts_id"],
        ),
    )
    conn.commit()
    new_id = cur.lastrowid
    return get_time_block(conn, new_id)  # type: ignore[return-value]


def update_time_block(
    conn: sqlite3.Connection,
    time_block_id: int,
    data: TimeBlockUpdate,
) -> Optional[TimeBlock]:
    """
    Update časového bloku – jen neprázdná pole.
    """
    update_data = data.model_dump(
        exclude_unset=True,
        exclude_none=True,
        mode="json",
    )

    if not update_data:
        return get_time_block(conn, time_block_id)

    set_clause = ", ".join(f"{col} = ?" for col in update_data.keys())
    values = list(update_data.values()) + [time_block_id]

    cur = conn.execute(
        f"UPDATE time_block SET {set_clause} WHERE time_block_id = ?",
        values,
    )
    conn.commit()

    if cur.rowcount == 0:
        return None

    return get_time_block(conn, time_block_id)


def delete_time_block(conn: sqlite3.Connection, time_block_id: int) -> bool:
    """
    Smaže blokaci podle ID.
    """
    cur = conn.execute(
        "DELETE FROM time_block WHERE time_block_id = ?",
        (time_block_id,),
    )
    conn.commit()
    return cur.rowcount > 0
