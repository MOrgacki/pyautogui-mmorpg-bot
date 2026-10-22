import threading
import time
from collections import deque
from dataclasses import dataclass


@dataclass(frozen=True)
class ActivityLogEntry:
    time: float
    source: str
    level: str
    message: str


class ActivityLog:
    """ Thread-safe ring buffer of recent events shown in the UI """

    def __init__(self, capacity=500):
        self._entries = deque(maxlen=capacity)
        self._lock = threading.Lock()

    def add(self, source, message, level='info'):
        entry = ActivityLogEntry(time.time(), source, level, message)
        with self._lock:
            self._entries.append(entry)
        print(f"[{source}] {level}: {message}")
        return entry

    def entries(self, limit=100, source=None):
        """ Newest first, optionally only from one source """
        with self._lock:
            items = list(self._entries)
        items.reverse()
        if source is not None:
            items = [e for e in items if e.source == source]
        return items[:limit]

    def __len__(self):
        with self._lock:
            return len(self._entries)
