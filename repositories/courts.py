# app/repositories/courts.py
import sqlite3
from typing import List, Optional

from model.Court import Court, CourtCreate, CourtUpdate


def _row_to_court(row: sqlite3.Row) -> Court:
    """
    Pomocná funkce – vezme sqlite3.Row a převede ho na Pydantic model Court.
    Pydantic si s typy (bool, str, None) poradí sám.
    """
    return Court.model_validate(dict(row))


def list_courts(conn: sqlite3.Connection) -> List[Court]:
    """
    Vrátí všechny kurty seřazené podle courts_id.
    """
    rows = conn.execute(
        """
        SELECT courts_id, court_name, outdoor, status, note
        FROM courts
        ORDER BY courts_id
        """
    ).fetchall()
    return [_row_to_court(r) for r in rows]


def get_court(conn: sqlite3.Connection, courts_id: int) -> Optional[Court]:
    """
    Vrátí jeden kurt podle ID, nebo None, když neexistuje.
    """
    row = conn.execute(
        """
        SELECT courts_id, court_name, outdoor, status, note
        FROM courts
        WHERE courts_id = ?
        """,
        (courts_id,),
    ).fetchone()
    return _row_to_court(row) if row else None


def create_court(conn: sqlite3.Connection, data: CourtCreate) -> Court:
    """
    Vytvoří nový kurt a vrátí ho jako Court.

    - bool `outdoor` převádíme na INTEGER 0/1
    """
    payload = data.model_dump(mode="json")

    cur = conn.execute(
        """
        INSERT INTO courts (court_name, outdoor, status, note)
        VALUES (?, ?, ?, ?)
        """,
        (
            payload["court_name"],
            int(payload["outdoor"]),
            payload["status"],
            payload.get("note"),
        ),
    )
    conn.commit()
    new_id = cur.lastrowid
    return get_court(conn, new_id)


def update_court(
    conn: sqlite3.Connection,
    courts_id: int,
    data: CourtUpdate,
) -> Optional[Court]:
    """
    Aktualizuje kurt – dynamicky jen ta pole, která nejsou None.

    - používáme `exclude_unset=True`, takže bereme jen to, co v update modelu opravdu přišlo
    - `exclude_none=True` zajistí, že None se do SQL nedostane (nejde tedy tímto způsobem nastavit note zpět na NULL)
    """
    update_data = data.model_dump(
        exclude_unset=True,
        exclude_none=True,
        mode="json",
    )

    # speciální převod bool -> INTEGER
    if "outdoor" in update_data:
        update_data["outdoor"] = int(update_data["outdoor"])

    if not update_data:
        return get_court(conn, courts_id)

    set_clause = ", ".join(f"{col} = ?" for col in update_data.keys())
    values = list(update_data.values()) + [courts_id]

    cur = conn.execute(
        f"UPDATE courts SET {set_clause} WHERE courts_id = ?",
        values,
    )
    conn.commit()

    if cur.rowcount == 0:
        return None

    return get_court(conn, courts_id)


def delete_court(conn: sqlite3.Connection, courts_id: int) -> bool:
    """
    Smaže kurt podle ID.
    Vrací True, když se něco smazalo, False když kurt neexistoval.
    """
    cur = conn.execute(
        "DELETE FROM courts WHERE courts_id = ?",
        (courts_id,),
    )
    conn.commit()
    return cur.rowcount > 0
