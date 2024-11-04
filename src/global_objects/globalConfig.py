class globalConfig(object):
    ttl: int = 60
    prefix_offset: int = 0

    def __init__(self, ttl: int, prefix_offset: str):
        self.ttl = ttl
        self.prefix_offset = int(prefix_offset, 16)

    def __repr__(self):
        return str(
            {
                "ttl": self.ttl,
                "prefix_offset": hex(self.prefix_offset)
            }
        )