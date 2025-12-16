# app/repositories/reservations.py
import sqlite3
from datetime import datetime
from typing import List, Optional

from model.Reservation import Reservation, ReservationCreate, ReservationUpdate


def _row_to_reservation(row: sqlite3.Row) -> Reservation:
    """
    Převede řádek z tabulky reservation na Pydantic model Reservation.
    TEXT dat se převede na datetime automaticky.
    """
    return Reservation.model_validate(dict(row))


def list_reservations(conn: sqlite3.Connection) -> List[Reservation]:
    """
    Vrátí všechny rezervace, seřazené podle začátku (novější první).
    """
    rows = conn.execute(
        """
        SELECT reservation_id,
               start,
               end,
               price_total,
               created_at,
               user_id,
               price_list_id,
               state,
               courts_id
        FROM reservation
        ORDER BY start DESC
        """
    ).fetchall()
    return [_row_to_reservation(r) for r in rows]


def list_reservations_for_user(
    conn: sqlite3.Connection,
    user_id: int,
) -> List[Reservation]:
    """
    Vrátí všechny rezervace daného uživatele, seřazené od nejnovější.
    """
    rows = conn.execute(
        """
        SELECT reservation_id,
               start,
               end,
               price_total,
               created_at,
               user_id,
               price_list_id,
               state,
               courts_id
        FROM reservation
        WHERE user_id = ?
        ORDER BY start DESC
        """,
        (user_id,),
    ).fetchall()
    return [_row_to_reservation(r) for r in rows]


def list_reservations_for_court_between(
    conn: sqlite3.Connection,
    court_id: int,
    start: datetime,
    end: datetime,
) -> List[Reservation]:
    """
    Vrátí všechny rezervace pro daný kurt, které se
    jakkoli překrývají s intervalem (start, end).

    Logika překryvu:
        rezervace.start < end AND rezervace.end > start
    """
    start_str = start.isoformat()
    end_str = end.isoformat()

    rows = conn.execute(
        """
        SELECT reservation_id,
               start,
               end,
               price_total,
               created_at,
               user_id,
               price_list_id,
               state,
               courts_id
        FROM reservation
        WHERE courts_id = ?
          AND start < ?
          AND end > ?
          AND state != 'CANCELLED'
        ORDER BY start
        """,
        (court_id, end_str, start_str),
    ).fetchall()
    return [_row_to_reservation(r) for r in rows]


def list_future_reservations(
    conn: sqlite3.Connection,
    now: Optional[datetime] = None,
) -> List[Reservation]:
    """
    Vrátí všechny budoucí rezervace – tj. se startem >= now.

    Pokud `now` není zadáno, bere se aktuální čas.
    """
    if now is None:
        now = datetime.now()

    now_str = now.isoformat()

    rows = conn.execute(
        """
        SELECT reservation_id,
               start,
               end,
               price_total,
               created_at,
               user_id,
               price_list_id,
               state,
               courts_id
        FROM reservation
        WHERE start >= ?
        AND state != 'CANCELLED'
        ORDER BY start
        """,
        (now_str,),
    ).fetchall()
    return [_row_to_reservation(r) for r in rows]


def get_reservation(conn: sqlite3.Connection, reservation_id: int) -> Optional[Reservation]:
    """
    Vrátí jednu rezervaci podle ID nebo None.
    """
    row = conn.execute(
        """
        SELECT reservation_id,
               start,
               end,
               price_total,
               created_at,
               user_id,
               price_list_id,
               state,
               courts_id
        FROM reservation
        WHERE reservation_id = ?
        """,
        (reservation_id,),
    ).fetchone()
    return _row_to_reservation(row) if row else None


def create_reservation(
    conn: sqlite3.Connection,
    data: ReservationCreate,
    price_total: float,
    created_at: Optional[datetime] = None,
) -> Reservation:
    """
    Vytvoří novou rezervaci.

    Speciálně:
    - `price_total` předáváš zvenčí (services spočítá dle ceníku a kurtu).
    - `created_at` když nepředáš, nastavíme na aktuální čas.
    """
    if created_at is None:
        created_at = datetime.now()

    payload = data.model_dump(mode="json")

    cur = conn.execute(
        """
        INSERT INTO reservation (
            start,
            end,
            price_total,
            created_at,
            user_id,
            price_list_id,
            state,
            courts_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            payload["start"],        # ISO string
            payload["end"],          # ISO string
            price_total,
            created_at.isoformat(),
            payload["user_id"],
            payload["price_list_id"],
            payload["state"],        # TEXT v DB, Pydantic hlídá hodnoty
            payload["courts_id"],
        ),
    )
    conn.commit()
    new_id = cur.lastrowid
    return get_reservation(conn, new_id)  # type: ignore[return-value]


def update_reservation(
    conn: sqlite3.Connection,
    reservation_id: int,
    data: ReservationUpdate,
) -> Optional[Reservation]:
    """
    Update rezervace – dynamicky jen neprázdná pole.

    Poznámka:
    - `start` / `end` / `price_total` jdou jako ISO/float díky `mode="json"`.
    """
    update_data = data.model_dump(
        exclude_unset=True,
        exclude_none=True,
        mode="json",
    )

    if not update_data:
        return get_reservation(conn, reservation_id)

    set_clause = ", ".join(f"{col} = ?" for col in update_data.keys())
    values = list(update_data.values()) + [reservation_id]

    cur = conn.execute(
        f"UPDATE reservation SET {set_clause} WHERE reservation_id = ?",
        values,
    )
    conn.commit()

    if cur.rowcount == 0:
        return None

    return get_reservation(conn, reservation_id)


def delete_reservation(conn: sqlite3.Connection, reservation_id: int) -> bool:
    """
    Smaže rezervaci podle ID.
    """
    cur = conn.execute(
        "DELETE FROM reservation WHERE reservation_id = ?",
        (reservation_id,),
    )
    conn.commit()
    return cur.rowcount > 0
