# services/price_list.py
import sqlite3
from typing import List, Optional

from model import PriceList, PriceListCreate, PriceListUpdate
from repositories.price_list import (
    list_price_lists as repo_list_price_lists,
    get_price_list as repo_get_price_list,
    create_price_list as repo_create_price_list,
    update_price_list as repo_update_price_list,
    delete_price_list as repo_delete_price_list,
)


class PriceListService:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def list_price_lists(self) -> List[PriceList]:
        return repo_list_price_lists(self.conn)

    def get_price_list(self, price_list_id: int) -> Optional[PriceList]:
        return repo_get_price_list(self.conn, price_list_id)

    def create_price_list(self, data: PriceListCreate) -> PriceList:
        return repo_create_price_list(self.conn, data)

    def update_price_list(
        self,
        price_list_id: int,
        data: PriceListUpdate,
    ) -> Optional[PriceList]:
        return repo_update_price_list(self.conn, price_list_id, data)

    def delete_price_list(self, price_list_id: int) -> bool:
        return repo_delete_price_list(self.conn, price_list_id)
