import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from .models import HistoryItem, Settings

APP_NAME = "pomo"
DATA_FILE_NAME = "data.json"


def get_data_path() -> Path:
    """Get the path to the data file, respecting XDG_CONFIG_HOME."""
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        base_dir = Path(xdg_config)
    else:
        base_dir = Path.home() / ".config"
    
    app_dir = base_dir / APP_NAME
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir / DATA_FILE_NAME


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder for datetime objects."""
    def default(self, obj: Any) -> Any:
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def load_data() -> tuple[Settings, list[HistoryItem]]:
    """Load settings and history from disk."""
    path = get_data_path()
    if not path.exists():
        return Settings(), []

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Load Settings
        settings_dict = data.get("settings", {})
        settings = Settings(**settings_dict)

        # Load History
        history_list = data.get("history", [])
        history_items = []
        for item in history_list:
            # Parse datetimes
            item["start"] = datetime.fromisoformat(item["start"])
            item["end"] = datetime.fromisoformat(item["end"])
            history_items.append(HistoryItem(**item))

        return settings, history_items

    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
        # If file is corrupt or schema changed, fallback to defaults
        # In a real app we might want to backup the corrupt file
        print(f"Error loading data: {e}")
        return Settings(), []


def save_data(settings: Settings, history: list[HistoryItem]) -> None:
    """Save settings and history to disk."""
    path = get_data_path()
    
    data = {
        "settings": settings.__dict__,
        "history": [h.__dict__ for h in history]
    }

    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, cls=DateTimeEncoder, indent=2)
    except IOError as e:
        print(f"Error saving data: {e}")
