from pydantic import BaseModel


class ipFetchFails(BaseModel):
    ipV4Fail: int = 0
    ipV6Fail: int = 0
