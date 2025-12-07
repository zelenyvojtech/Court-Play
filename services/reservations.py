# services/reservations.py
import sqlite3
from datetime import datetime
from typing import List, Optional

from model.Reservation import Reservation, ReservationCreate, ReservationUpdate
from repositories.reservations import (
    list_reservations as repo_list_reservations,
    list_reservations_for_user as repo_list_reservations_for_user,
    list_reservations_for_court_between as repo_list_reservations_for_court_between,
    list_future_reservations as repo_list_future_reservations,
    get_reservation as repo_get_reservation,
    create_reservation as repo_create_reservation,
    update_reservation as repo_update_reservation,
    delete_reservation as repo_delete_reservation,
)
from repositories.time_block import (
    list_time_blocks_for_court_between as repo_list_time_blocks_for_court_between,
)
from repositories.price_list import get_price_list as repo_get_price_list
from repositories.courts import get_court as repo_get_court


class ReservationsService:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    # ----- jednoduché obalení repo -----

    def list_reservations(self) -> List[Reservation]:
        return repo_list_reservations(self.conn)

    def list_reservations_for_user(self, user_id: int) -> List[Reservation]:
        return repo_list_reservations_for_user(self.conn, user_id)

    def list_future_reservations(
        self,
        now: Optional[datetime] = None,
    ) -> List[Reservation]:
        return repo_list_future_reservations(self.conn, now)

    def get_reservation(self, reservation_id: int) -> Optional[Reservation]:
        return repo_get_reservation(self.conn, reservation_id)

    def update_reservation(
        self,
        reservation_id: int,
        data: ReservationUpdate,
    ) -> Optional[Reservation]:
        return repo_update_reservation(self.conn, reservation_id, data)

    def delete_reservation(self, reservation_id: int) -> bool:
        return repo_delete_reservation(self.conn, reservation_id)

    # ----- doménová logika: kolize + cena -----

    def _ensure_slot_is_free(
        self,
        court_id: int,
        start: datetime,
        end: datetime,
    ) -> None:
        """
        Zkontroluje, že pro daný kurt a interval (start, end) neexistuje:
        - žádná kolidující rezervace
        - žádný kolidující time_block

        Při kolizi vyhodí ValueError (v routeru z toho uděláš HTTP 400
        nebo zobrazíš chybovou hlášku ve UI).
        """
        reservations = repo_list_reservations_for_court_between(
            self.conn,
            court_id,
            start,
            end,
        )
        blocks = repo_list_time_blocks_for_court_between(
            self.conn,
            court_id,
            start,
            end,
        )

        if reservations or blocks:
            raise ValueError("Vybraný termín je obsazený nebo blokovaný.")

    def _compute_price(self, data: ReservationCreate) -> float:
        """
        Spočítá cenu rezervace podle:
        - položky ceníku (`price_list_id`)
        - toho, zda je kurt indoor/outdoor
        - délky rezervace vs. `duration_min`

        Jednoduchý model:
            price_total = base_price * (indoor_multiplier pokud indoor, jinak 1)
        """
        price_list = repo_get_price_list(self.conn, data.price_list_id)
        if price_list is None:
            raise ValueError("Položka ceníku neexistuje.")

        court = repo_get_court(self.conn, data.courts_id)
        if court is None:
            raise ValueError("Kurt neexistuje.")

        # ověříme, že délka rezervace odpovídá ceníku
        duration_minutes = int((data.end - data.start).total_seconds() // 60)
        if duration_minutes != price_list.duration_min:
            raise ValueError("Délka rezervace neodpovídá zvolenému ceníku.")

        base_price = price_list.base_price
        multiplier = price_list.indoor_multiplier if not court.outdoor else 1.0

        return base_price * multiplier

    def create_reservation(self, data: ReservationCreate) -> Reservation:
        """
        Vytvoří rezervaci:

        1. Zkontroluje, že slot je volný (rezervace + blokace).
        2. Spočítá cenu podle ceníku a typu kurtu.
        3. Zavolá repository.create_reservation a vrátí výslednou rezervaci.
        """
        # 1) kolize
        self._ensure_slot_is_free(data.courts_id, data.start, data.end)

        # 2) cena
        price_total = self._compute_price(data)

        # 3) uložíme do DB
        return repo_create_reservation(self.conn, data, price_total)
