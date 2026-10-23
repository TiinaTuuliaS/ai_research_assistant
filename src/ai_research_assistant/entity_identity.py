"""Conservative name identity: ignore casing and whitespace, never guess typos."""

def entity_key(name):
    return " ".join((name or "").split()).casefold()
