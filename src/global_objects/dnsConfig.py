from typing import Optional
import ipaddress as ipaddress

class dnsV4ConfigRecord(object):
    name: str = ""

    def __init__(self, name: str):
        self.name = name

    def __repr__(self):
        return str(
            {
                "name": self.name,
            }
        )

class dnsV4Config(object):
    zone: str = ""
    records: list[dnsV4ConfigRecord]

    def __init__(self, zone: str, records: list[dnsV4ConfigRecord]):
        self.zone = zone
        self.records = records

    def __repr__(self):
        return str(
            {
                "zone": self.zone,
                "records": self.records,
            }
        )

class dnsV6ConfigRecord(object):
    name: str = ""
    prefixOffset: str = ""
    suffix: Optional[str] = None

    def __init__(self, name: str, prefixOffset: str, suffix: str | None = None):
        self.name = name
        self.prefixOffset = prefixOffset
        self.suffix = suffix

    def __repr__(self):
        return str(
            {
                "name": self.name,
                "prefixOffset": self.prefixOffset,
                "suffix": self.suffix
            }
        )

class dnsV6Config(object):
    zone: str = ""
    records: list[dnsV6ConfigRecord]

    def __init__(self, zone: str, records: list[dnsV6ConfigRecord]):
        self.zone = zone
        self.records = records

    def __repr__(self):
        return str(
            {
                "zone": self.zone,
                "records": self.records,
            }
        )
