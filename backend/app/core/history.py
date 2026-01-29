import json
import os
from typing import List, Dict, Any
from datetime import datetime

AUDIT_LOG_FILE = "audit_log.json"

class HistoryRepository:
    def __init__(self):
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(AUDIT_LOG_FILE):
            with open(AUDIT_LOG_FILE, 'w') as f:
                json.dump([], f)

    def save_entry(self, entry: Dict[str, Any]):
        """Save a pipeline execution entry."""
        current_data = self.get_all()
        # Add timestamp if not present (though main.py handles it via request logic usually, 
        # but let's ensure we have a saved_at time)
        entry['saved_at'] = datetime.now().isoformat()
        current_data.insert(0, entry) # Newest first
        
        with open(AUDIT_LOG_FILE, 'w') as f:
            json.dump(current_data, f, indent=2)

    def get_all(self) -> List[Dict[str, Any]]:
        """Retrieve all history entries."""
        try:
            with open(AUDIT_LOG_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
