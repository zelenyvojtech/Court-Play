# services/courts.py
import sqlite3
from typing import List, Optional

from model.Court import Court, CourtCreate, CourtUpdate
from repositories.courts import (
    list_courts as repo_list_courts,
    get_court as repo_get_court,
    create_court as repo_create_court,
    update_court as repo_update_court,
    delete_court as repo_delete_court,
)


class CourtsService:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def list_courts(self) -> List[Court]:
        return repo_list_courts(self.conn)

    def get_court(self, courts_id: int) -> Optional[Court]:
        return repo_get_court(self.conn, courts_id)

    def create_court(self, data: CourtCreate) -> Court:
        return repo_create_court(self.conn, data)

    def update_court(self, courts_id: int, data: CourtUpdate) -> Optional[Court]:
        return repo_update_court(self.conn, courts_id, data)

    def delete_court(self, courts_id: int) -> bool:
        return repo_delete_court(self.conn, courts_id)
