from loguru import logger
from src.utils.settings import get_settings
class MongoClient:
    def __init__(self): self.settings=get_settings(); self._db=None
    @property
    def db(self):
        if self._db is None:
            try:
                from pymongo import MongoClient as PM
                c=PM(self.settings.mongodb_uri,serverSelectionTimeoutMS=3000); c.server_info()
                self._db=c[self.settings.mongodb_db]
            except Exception as e: logger.debug(f"MongoDB unavailable: {e}")
        return self._db
    def find(self,collection,filter_doc=None,limit=20):
        if self.db is None: raise ConnectionError("MongoDB not available")
        return list(self.db[collection].find(filter_doc or {},{"_id":0}).limit(limit))
    def insert_one(self,collection,document):
        if self.db is None: raise ConnectionError("MongoDB not available")
        return str(self.db[collection].insert_one(document).inserted_id)
