# Providers

This application allows the use of many different DNS providers using their API.

If your provider is not yet implemented, feel free to either contribute yourself or open a request issue.

Currently supported Providers:
- [Hetzner](#hetzner)

## General config options

| Attribute                  | Alias | Type                                | Default   | Description                                                                 |
|-----------------------------|-------|-------------------------------------|-----------|-----------------------------------------------------------------------------|
| `provider`                  | –     | `str`                               | –         | Name of the provider (identifier for the DNS provider implementation).      |
| `allowed_consecutive_timeouts` | –  | `int \| None`                       | `None`    | Number of consecutive timeouts allowed before triggering an alert. If `None`, falls back to global settings. |
| `provider_config`           | –     | `ProviderConfigConfig`              | –         | Provider-specific configuration, e.g. API Key (type depends on the provider implementation). |
| `zones`                     | –     | `list[ZonesConfig]`                 | –         | List of zone configurations (`ZonesConfig` objects) managed by this provider. |

### Zone Config

Each Zone has the following config options:

| Attribute       | Alias | Type                        | Default | Description                                                                 |
|-----------------|-------|-----------------------------|---------|-----------------------------------------------------------------------------|
| `name`          | –     | `str`                       | –       | The DNS zone name (e.g., a domain name such as `example.com`).              |
| `ipv4_records`  | –     | `list[RecordConfigV4]`      | –       | List of IPv4 DNS record configurations (`RecordConfigV4` objects).          |
| `ipv6_records`  | –     | `list[RecordConfigV6]`      | –       | List of IPv6 DNS record configurations (`RecordConfigV6` objects).          |

#### A (IPv4) Record Config

| Attribute | Alias | Type  | Default | Description                              |
|-----------|-------|-------|---------|------------------------------------------|
| `name`    | –     | `str` | –       | The record name within the DNS zone (e.g., `@` for root, `www`, etc.). |

#### AAAA (IPv6) Record Config

| Attribute     | Alias | Type  | Default | Description                                                                 |
|---------------|-------|-------|---------|-----------------------------------------------------------------------------|
| `name`        | –     | `str` | –       | The record name within the DNS zone (e.g., `@` for root, `www`, etc.).      |
| `prefixOffset`| –     | `str` | –       | Hexadecimal prefix offset used when constructing IPv6 addresses dynamically. Needs to match the e.g. Prefix ID in OPNSense of the interface the destination is connected to. |
| `suffix`      | –     | `str` | –       | Suffix to append to the IPv6 address, finalizing the record address.         |

## Hetzner

Provider Name: `hetzner`

The Hetzner provider utilises the api of `dns.hetzner.com`

### ProviderConfig

| Attribute   | Alias | Type  | Default | Description                                                                 |
|-------------|-------|-------|---------|-----------------------------------------------------------------------------|
| `api_token` | –     | `str` | –       | API token used to authenticate requests against the Hetzner DNS API.        |

### Sample Config

```yaml
- provider: hetzner
  allowed_consecutive_timeouts: 1 # Hetzner API often times out during peak times
  provider_config:
    api_token: "{{DNS_UPDATER_VAR_HETZNER_API_KEY}}"
  zones:
  - name: "my.tld"
    ipv4_records:
    - name: "@"
    - name: "*"
```