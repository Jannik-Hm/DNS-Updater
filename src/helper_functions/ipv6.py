import ipaddress as ipaddress

def calculateIPv6Address(prefix: list[str], prefixOffset: str, currentAddressOrFixedSuffix: str) -> str:
  prefix_int = int("".join(prefix[:4]), 16)
  prefix_id_int = int(prefixOffset, 10)
  if f"{(prefix_int + prefix_id_int):016x}".__len__() > 16:
    raise ValueError(f"The generated prefix for base prefix {':'.join(prefix[:4])} and prefixOffset {prefixOffset} is overflowing. Please check your config.")
  new_prefix = f"{(prefix_int + prefix_id_int) & 0xFFFFFFFFFFFFFFFF:016x}"
  return ipaddress.IPv6Address(":".join(new_prefix[i:i+4] for i in range(0, len(new_prefix), 4)) + ":" + ":".join(ipaddress.IPv6Address(currentAddressOrFixedSuffix).exploded.split(sep=":")[-4:])).compressed