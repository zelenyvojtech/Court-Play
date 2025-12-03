# services/time_block.py
import sqlite3
from datetime import datetime
from typing import List, Optional

from model import TimeBlock, TimeBlockCreate, TimeBlockUpdate
from repositories.time_block import (
    list_time_blocks as repo_list_time_blocks,
    list_time_blocks_for_court_between as repo_list_time_blocks_for_court_between,
    get_time_block as repo_get_time_block,
    create_time_block as repo_create_time_block,
    update_time_block as repo_update_time_block,
    delete_time_block as repo_delete_time_block,
)


class TimeBlockService:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def list_time_blocks(self) -> List[TimeBlock]:
        return repo_list_time_blocks(self.conn)

    def list_time_blocks_for_court_between(
        self,
        court_id: int,
        start: datetime,
        end: datetime,
    ) -> List[TimeBlock]:
        return repo_list_time_blocks_for_court_between(self.conn, court_id, start, end)

    def get_time_block(self, time_block_id: int) -> Optional[TimeBlock]:
        return repo_get_time_block(self.conn, time_block_id)

    def create_time_block(self, data: TimeBlockCreate) -> TimeBlock:
        return repo_create_time_block(self.conn, data)

    def update_time_block(
        self,
        time_block_id: int,
        data: TimeBlockUpdate,
    ) -> Optional[TimeBlock]:
        return repo_update_time_block(self.conn, time_block_id, data)

    def delete_time_block(self, time_block_id: int) -> bool:
        return repo_delete_time_block(self.conn, time_block_id)
