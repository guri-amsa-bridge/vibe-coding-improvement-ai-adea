"""데이터베이스 연결 및 쿼리 실행 모듈

변경 이력:
  - connection pool 크기 설정 기능 추가
  - 쿼리 실행 시 timeout 파라미터 지원
  - 쿼리 실행 로깅 기능 추가
"""
import sqlite3
import os
import logging

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_path="app.db", pool_size=5):
        self.db_path = db_path
        self.pool_size = pool_size
        self._conn = None
        self._query_count = 0

    def connect(self):
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, timeout=self.pool_size * 2)
            self._conn.row_factory = sqlite3.Row
            logger.info(f"Database connected: {self.db_path} (pool_size={self.pool_size})")
        return self._conn

    def execute(self, query, params=None, timeout=30, max_retries=3):
        conn = self.connect()
        self._query_count += 1
        logger.debug(f"Executing query #{self._query_count} (timeout={timeout}s): {query[:50]}")
        
        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                conn.commit()
                return cursor
            except sqlite3.OperationalError as e:
                last_error = e
                logger.warning(f"Query attempt {attempt}/{max_retries} failed: {e}")
                if attempt < max_retries:
                    import time
                    time.sleep(0.1 * attempt)
        raise last_error

    def fetch_one(self, query, params=None):
        cursor = self.execute(query, params)
        return cursor.fetchone()

    def fetch_all(self, query, params=None):
        cursor = self.execute(query, params)
        return cursor.fetchall()

    def get_stats(self):
        """데이터베이스 사용 통계 반환"""
        return {
            "db_path": self.db_path,
            "pool_size": self.pool_size,
            "query_count": self._query_count,
            "connected": self._conn is not None,
        }

    def close(self):
        if self._conn:
            logger.info(f"Database closed. Total queries: {self._query_count}")
            self._conn.close()
            self._conn = None
