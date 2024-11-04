from typing import Optional


class Record(object):
    ttl: int = 0
    name: str = ""
    value: str = ""
    type: str = ""
    id: Optional[str]
    zone_id: Optional[str]

    def __init__(
        self, type: str, name: str, value: str, ttl: int, id: str | None = None, zone_id: str | None = None
    ):
        self.ttl = ttl
        self.name = name
        self.value = value
        self.type = type
        self.id = id
        self.zone_id = zone_id

    def __repr__(self):
        return str(
            {
                "name": self.name,
                "value": self.value,
                "type": self.type,
                "ttl": str(self.ttl),
                "id": str(self.id),
                "zone_id": str(self.zone_id)
            }
        )
