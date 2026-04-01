import sqlite3
import json
import logging
from typing import Optional, Union, Dict, Any, List

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    A simple SQLite database manager to store and retrieve JSON data.
    """
    def __init__(self, db_path: str = "app_data.db"):
        self.db_path = db_path
        self._known_tables = set()

    def _ensure_table(self, table_name: str):
        """Ensures the specified table exists before operating on it."""
        if table_name in self._known_tables:
            return
            
        if not table_name.isidentifier():
            raise ValueError(f"Invalid table name: {table_name}")
            
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        id TEXT PRIMARY KEY,
                        data TEXT,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                conn.commit()
                self._known_tables.add(table_name)
        except sqlite3.Error as e:
            logger.error(f"Error ensuring table {table_name}: {e}")

    def store_json(self, key_id: str, json_data: Union[Dict[Any, Any], List[Any], str], table_name: str = "default_store"):
        """
        Stores or updates JSON data for a given ID in a specific table.
        """
        self._ensure_table(table_name)
        
        # Convert to string if it's a dict or list
        if isinstance(json_data, (dict, list)):
            data_str = json.dumps(json_data)
        else:
            data_str = json_data
            
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Insert or update based on the ID
                cursor.execute(f'''
                    INSERT INTO {table_name} (id, data, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(id) DO UPDATE SET
                        data=excluded.data,
                        updated_at=CURRENT_TIMESTAMP
                ''', (key_id, data_str))
                conn.commit()
                logger.debug(f"Successfully stored JSON data for key: {key_id} in {table_name}")
        except sqlite3.Error as e:
            logger.error(f"Error storing JSON data for ID {key_id} in {table_name}: {e}")

    def get_json(self, key_id: str, table_name: str = "default_store") -> Optional[Union[Dict[Any, Any], List[Any]]]:
        """
        Retrieves JSON data for a given ID from a specific table.
        """
        self._ensure_table(table_name)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(f'SELECT data FROM {table_name} WHERE id = ?', (key_id,))
                result = cursor.fetchone()
                
                if result:
                    return json.loads(result[0])
                return None
        except sqlite3.Error as e:
            logger.error(f"Error retrieving JSON data for ID {key_id} from {table_name}: {e}")
        except json.JSONDecodeError as e:
             logger.error(f"Error decoding JSON data for ID {key_id} in {table_name}: {e}")
             
        return None

    def delete_json(self, key_id: str, table_name: str = "default_store"):
        """
        Deletes JSON data for a given ID from a specific table.
        """
        self._ensure_table(table_name)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(f'DELETE FROM {table_name} WHERE id = ?', (key_id,))
                conn.commit()
                logger.debug(f"Successfully deleted JSON data for key: {key_id} in {table_name}")
        except sqlite3.Error as e:
            logger.error(f"Error deleting JSON data for ID {key_id} in {table_name}: {e}")

    def key_exists(self, key_id: str, table_name: str = "default_store") -> bool:
        """
        Fast check to see if a key exists without parsing the JSON payload.
        """
        self._ensure_table(table_name)
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(f'SELECT 1 FROM {table_name} WHERE id = ?', (key_id,))
                return cursor.fetchone() is not None
        except sqlite3.Error as e:
            logger.error(f"Error checking if key exists: {e}")
            return False
