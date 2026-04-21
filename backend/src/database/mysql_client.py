from loguru import logger
from src.utils.settings import get_settings
class MySQLClient:
    def __init__(self): self.settings=get_settings(); self._engine=None
    @property
    def engine(self):
        if self._engine is None:
            try:
                from sqlalchemy import create_engine
                self._engine = create_engine(self.settings.mysql_url,pool_size=10,max_overflow=20,pool_pre_ping=True)
            except Exception as e: logger.debug(f"MySQL unavailable: {e}")
        return self._engine
    def execute_query(self, sql, params=None):
        if self.engine is None: raise ConnectionError("MySQL not available")
        from sqlalchemy import text
        with self.engine.connect() as c:
            r=c.execute(text(sql),params or {}); return [dict(zip(r.keys(),row)) for row in r.fetchall()]
