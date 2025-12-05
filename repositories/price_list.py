# app/repositories/price_list.py
import sqlite3
from typing import List, Optional

from model import PriceList, PriceListCreate, PriceListUpdate


def _row_to_price_list(row: sqlite3.Row) -> PriceList:
    """
    Převede řádek z tabulky price_list na Pydantic model PriceList.
    TEXT časů (např. '08:00') se v Pydanticu přeparsuje na datetime.time.
    """
    return PriceList.model_validate(dict(row))


def list_price_lists(conn: sqlite3.Connection) -> List[PriceList]:
    """
    Vrátí všechny položky ceníku.
    """
    rows = conn.execute(
        """
        SELECT price_list_id,
               duration_min,
               opening_time,
               closing_time,
               base_price,
               indoor_multiplier
        FROM price_list
        ORDER BY price_list_id
        """
    ).fetchall()
    return [_row_to_price_list(r) for r in rows]


def get_price_list(conn: sqlite3.Connection, price_list_id: int) -> Optional[PriceList]:
    """
    Vrátí jednu položku ceníku podle ID, nebo None.
    """
    row = conn.execute(
        """
        SELECT price_list_id,
               duration_min,
               opening_time,
               closing_time,
               base_price,
               indoor_multiplier
        FROM price_list
        WHERE price_list_id = ?
        """,
        (price_list_id,),
    ).fetchone()
    return _row_to_price_list(row) if row else None


def create_price_list(conn: sqlite3.Connection, data: PriceListCreate) -> PriceList:
    """
    Vytvoří novou položku v ceníku.

    - `opening_time` / `closing_time` jdou do DB jako TEXT (ISO 'HH:MM[:SS]')
    """
    payload = data.model_dump(mode="json")

    cur = conn.execute(
        """
        INSERT INTO price_list (
            duration_min,
            opening_time,
            closing_time,
            base_price,
            indoor_multiplier
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            payload["duration_min"],
            payload["opening_time"],   # str, např. "08:00"
            payload["closing_time"],
            payload["base_price"],
            payload["indoor_multiplier"],
        ),
    )
    conn.commit()
    new_id = cur.lastrowid
    return get_price_list(conn, new_id)  # type: ignore[return-value]


def update_price_list(
    conn: sqlite3.Connection,
    price_list_id: int,
    data: PriceListUpdate,
) -> Optional[PriceList]:
    """
    Update ceníku – dynamicky jen neprázdná pole.
    """
    update_data = data.model_dump(
        exclude_unset=True,
        exclude_none=True,
        mode="json",
    )

    if not update_data:
        return get_price_list(conn, price_list_id)

    set_clause = ", ".join(f"{col} = ?" for col in update_data.keys())
    values = list(update_data.values()) + [price_list_id]

    cur = conn.execute(
        f"UPDATE price_list SET {set_clause} WHERE price_list_id = ?",
        values,
    )
    conn.commit()

    if cur.rowcount == 0:
        return None

    return get_price_list(conn, price_list_id)


def delete_price_list(conn: sqlite3.Connection, price_list_id: int) -> bool:
    """
    Smaže položku ceníku podle ID.
    """
    cur = conn.execute(
        "DELETE FROM price_list WHERE price_list_id = ?",
        (price_list_id,),
    )
    conn.commit()
    return cur.rowcount > 0
