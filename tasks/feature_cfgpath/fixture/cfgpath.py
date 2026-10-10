"""Tiny helpers for reading values out of nested config dicts."""


def get(cfg, path, default=None):
    """Return the value at a dotted path like 'db.host', or default if missing."""
    cur = cfg
    for key in path.split("."):
        if isinstance(cur, dict) and key in cur:
            cur = cur[key]
        else:
            return default
    return cur
