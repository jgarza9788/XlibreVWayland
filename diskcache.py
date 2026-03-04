from __future__ import annotations

import os
import pickle


class Cache(dict):
    def __init__(self, directory: str):
        self.directory = directory
        os.makedirs(directory, exist_ok=True)
        self.path = os.path.join(directory, "cache.pkl")
        if os.path.exists(self.path):
            try:
                with open(self.path, "rb") as f:
                    data = pickle.load(f)
                    super().update(data)
            except Exception:
                pass

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        with open(self.path, "wb") as f:
            pickle.dump(dict(self), f)
