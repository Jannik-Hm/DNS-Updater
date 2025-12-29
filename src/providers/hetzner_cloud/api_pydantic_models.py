from pydantic import BaseModel
from typing import Literal

from ..abstract import Record

class HetznerCloudPagination(BaseModel):
    page: int
    per_page: int
    previous_page: int | None
    next_page: int | None
    last_page: int | None
    total_entries: int | None

class HetznerCloudZoneTextVerification(BaseModel):
    name: str
    token: str

class HetznerCloudNameServer(BaseModel):
    address: str
    port: int = 53
    tsig_key: str | None = None
    tsig_algorithm: str | None = None

class HetznerCloudZoneProtection(BaseModel):
    delete: bool

class HetznerCloudRRSetProtection(BaseModel):
    change: bool

class HetznerCloudAuthoritativeNameservers(BaseModel):
    assigned: list[str]
    delegated: list[str]
    delegation_last_check: str | None
    delegation_status: Literal["valid", "partially-valid", "invalid", "lame", "unregistered", "unknown"]

class HetznerCloudZone(BaseModel):
    id: int
    name: str
    created: str
    mode: Literal["primary", "secondary"]
    primary_nameservers: list[HetznerCloudNameServer] | None = None # Only set if mode is secondary
    labels: dict[str, str]
    protection: HetznerCloudZoneProtection
    ttl: int
    status: str
    record_count: int
    authoritative_nameservers: HetznerCloudAuthoritativeNameservers
    registrar: str

class HetznerCloudZonesMeta(BaseModel):
    pagination: HetznerCloudPagination

class HetznerCloudZones(BaseModel):
    zones: list[HetznerCloudZone]
    meta: HetznerCloudZonesMeta

class HetznerCloudRRSetRecord(BaseModel):
    value: str
    comment: str | None = None

class HetznerCloudRRSet(BaseModel):
    id: str
    name: str
    type: str
    ttl: int | None = None
    labels: dict[str, str] | None = None
    protection: HetznerCloudRRSetProtection | None = None
    records: list[HetznerCloudRRSetRecord]
    zone: int

class CreateHetznerCloudRRSet(BaseModel):
    name: str
    type: str
    ttl: int | None = None
    labels: dict[str, str] | None = None
    records: list[HetznerCloudRRSetRecord]

class HetznerCloudRecords(BaseModel):
    rrsets: list[HetznerCloudRRSet]
    meta: HetznerCloudZonesMeta