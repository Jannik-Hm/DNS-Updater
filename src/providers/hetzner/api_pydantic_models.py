from pydantic import BaseModel

from ..abstract import Record

class HetznerPagination(BaseModel):
    page: int
    per_page: int
    last_page: int
    total_entries: int

class HetznerZoneTextVerification(BaseModel):
    name: str
    token: str

class HetznerZone(BaseModel):
    id: str
    created: str
    modified: str
    legacy_dns_host: str
    legacy_ns: list[str]
    name: str
    ns: list[str]
    owner: str
    paused: bool
    permission: str
    project: str
    registrar: str
    status: str
    ttl: int
    verified: str
    records_count: int
    is_secondary_dns: bool
    txt_verification: HetznerZoneTextVerification

class HetznerZonesMeta(BaseModel):
    pagination: HetznerPagination

class HetznerZones(BaseModel):
    zones: list[HetznerZone]
    meta: HetznerZonesMeta

class HetznerRecord(Record):
    id: str | None = None # not part of post, put, bulk post
    created: str | None = None # not part of post, put, bulk post and put
    modified: str | None = None # not part of post, put, bulk post and put
    zone_id: str

class HetznerRecords(BaseModel):
    records: list[HetznerRecord]