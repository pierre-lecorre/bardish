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
        self._init_db()

    def _init_db(self):
        """Initializes the database with a table for storing JSON data."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Create a simple key-value store where value is the JSON string
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS json_store (
                        id TEXT PRIMARY KEY,
                        data TEXT,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                conn.commit()
                logger.info(f"Database initialized at {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Error initializing database: {e}")

    def store_json(self, key_id: str, json_data: Union[Dict[Any, Any], List[Any], str]):
        """
        Stores or updates JSON data for a given ID.
        
        Args:
            key_id (str): The unique identifier for this data
            json_data (dict, list, or str): The JSON data to store
        """
        # Convert to string if it's a dict or list
        if isinstance(json_data, (dict, list)):
            data_str = json.dumps(json_data)
        else:
            data_str = json_data
            
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Insert or update based on the ID
                cursor.execute('''
                    INSERT INTO json_store (id, data, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(id) DO UPDATE SET
                        data=excluded.data,
                        updated_at=CURRENT_TIMESTAMP
                ''', (key_id, data_str))
                conn.commit()
                logger.debug(f"Successfully stored JSON data for key: {key_id}")
        except sqlite3.Error as e:
            logger.error(f"Error storing JSON data for ID {key_id}: {e}")

    def get_json(self, key_id: str) -> Optional[Union[Dict[Any, Any], List[Any]]]:
        """
        Retrieves JSON data for a given ID.
        
        Args:
            key_id (str): The unique identifier for the data
            
        Returns:
            The parsed JSON data (dict or list) or None if not found
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT data FROM json_store WHERE id = ?', (key_id,))
                result = cursor.fetchone()
                
                if result:
                    return json.loads(result[0])
                return None
        except sqlite3.Error as e:
            logger.error(f"Error retrieving JSON data for ID {key_id}: {e}")
        except json.JSONDecodeError as e:
             logger.error(f"Error decoding JSON data for ID {key_id}: {e}")
             
        return None

    def delete_json(self, key_id: str):
        """
        Deletes JSON data for a given ID.
        
        Args:
            key_id (str): The unique identifier for the data
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM json_store WHERE id = ?', (key_id,))
                conn.commit()
                logger.debug(f"Successfully deleted JSON data for key: {key_id}")
        except sqlite3.Error as e:
            logger.error(f"Error deleting JSON data for ID {key_id}: {e}")
