import ipaddress as ipaddress

def calculateIPv6Address(prefix: list[str], prefixOffset: str, currentAddressOrFixedSuffix: str) -> str:
  print(prefix[:4])
  prefix_int = int("".join(prefix[:4]), 16)
  prefix_id_int = int(prefixOffset, 16)
  new_prefix = f"{(prefix_int + prefix_id_int) & 0xFFFFFFFFFFFFFFFF:016x}"
  print(list(map(lambda x: int(x, 16), ipaddress.IPv6Address(currentAddressOrFixedSuffix).exploded.split(sep=":"))))
  print(list(map(lambda x: int(x, 16), ipaddress.IPv6Address(currentAddressOrFixedSuffix).exploded.split(sep=":")))[-4:])
  return ipaddress.IPv6Address(":".join(new_prefix[i:i+4] for i in range(0, len(new_prefix), 4)) + ":" + ":".join(ipaddress.IPv6Address(currentAddressOrFixedSuffix).exploded.split(sep=":")[-4:])).compressed