import json
from copy import deepcopy
from pathlib import Path
from threading import Lock


class JsonStore:
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._ensure()

    def _empty(self):
        return {
            'clients': [],
            'plans': [],
            'subscriptions': [],
            'appointments': [],
            'settings': [],
            'meta': {'counters': {'clients': 0, 'plans': 0, 'subscriptions': 0, 'appointments': 0}},
        }

    def _ensure(self):
        if not self.path.exists():
            self.path.write_text(json.dumps(self._empty(), ensure_ascii=False, indent=2), encoding='utf-8')

    def read(self):
        with self._lock:
            data = json.loads(self.path.read_text(encoding='utf-8'))
            return deepcopy(data)

    def write(self, data):
        with self._lock:
            self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

    def next_id(self, data, table):
        data['meta']['counters'][table] += 1
        return data['meta']['counters'][table]
