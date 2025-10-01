# Configuration

Configuration is handled by a `config.yaml` file, mounted into the container under `/etc/dns_updater/config.yaml`.
This path can be adjusted using the `CONFIG_PATH` environment variable.

The config file is seperated into `global` and `providers` config.

## Env Var substitution

Values in your config file can be substituted using env vars, e.g. for keeping secrets seperately.

To do this, replace the value in your config file with `{{DNS_UPDATER_VAR_*custom_name*}}`.
The respective config directive value will then be replaced by the value of the env var `DNS_UPDATER_VAR_*custom_name*`.

## Global config

The `global` config contains settings like logging, enabling/disabling IPv4 and IPv6, toggling the `dry-run` mode, etc.

### Global config options

| Attribute                           | Alias                | Type                  | Default   | Description                                                                                         |
|-------------------------------------|----------------------|-----------------------|-----------|-----------------------------------------------------------------------------------------------------|
| `cron`                              | –                    | `str`                 | `"*/1 * * * *"` | Cron expression that controls scheduling (default: run every minute).                              |
| `ttl`                               | –                    | `int`                 | `60`      | Time-to-live in seconds.                                                                           |
| `current_prefix_offset`             | –                    | `str \| None`         | `None`    | Hexadecimal prefix offset. **Required when IPv6 is enabled** (`disable-ipv6 == False`). Must be provided to properly calculate IPv6 addresses. Needs to match the e.g. Prefix ID in OPNSense of the interface this container is connected to. |
| `dry_run`                           | `dry-run`            | `bool`                | `False`   | If `True`, runs in dry-run mode without making actual changes.                                     |
| `disable_v4`                        | `disable-ipv4`       | `bool`                | `False`   | If `True`, disables IPv4 (IPv4 enabled by default).                                                |
| `disable_v6`                        | `disable-ipv6`       | `bool`                | `True`    | If `True`, disables IPv6 (IPv6 disabled by default). **If set to `False`, then `current_prefix_offset` becomes mandatory**. |
| `python_root_logger`                | `python-root-logger` | `bool`                | `False`   | If `True`, attaches logging to Python’s root logger instead of DNS Updater only.                   |
| `allowed_consecutive_ip_fetch_timeouts` | –                 | `int`                 | `0`       | Number of consecutive IP fetch timeouts allowed before triggering an alert.                        |
| `allowed_consecutive_provider_timeouts` | –                 | `int`                 | `0`       | Number of consecutive provider timeouts allowed before triggering an alert.                        |
| `logging`                           | –                    | `list[LoggingConfig]` | –         | List of logging configuration entries (`LoggingConfig` objects).                                   |

### Logging config

More details about the logging config can be found [here](./logger-conf.md).

## Providers config

The Providers config contains your actual DNS Provider configuration and the Records you want to manage.

The Providers config is a list of single ProviderConfigs.
To read more about configuring a provider, read [here](./provider-config.md).

## Example Config

```yaml
# Global Parameters
global:
  # TTL of created / updated records, should match your cron interval
  ttl: 60

  # Prefix ID of this device, will be subtracted to get the base delegated prefix
  current_prefix_offset: '3'

  dry-run: true
  disable-ipv4: false
  disable-ipv6: false
  allowed_consecutive_ip_fetch_timeouts: 1

  logging:
  - provider: "stdio"
    loglevel: info
  - provider: discord
    loglevel: info
    provider_config:
      webhook_url: "{{DNS_UPDATER_VAR_DISCORD_WEBHOOK}}"

# List of different providers
providers:
- provider: hetzner
  allowed_consecutive_timeouts: 1
  provider_config:
    api_token: "{{DNS_UPDATER_VAR_HETZNER_API_KEY}}"
  zones:
  - name: "my.tld"
    ipv4_records:
    - name: "@"
    - name: "*"
    ipv6_records:
    - name: "@"
      prefixOffset: '3'
      suffix: "::10"
    - name: "*"
      prefixOffset: '3'
      suffix: "::10"
    - name: example
      prefixOffset: '82'
      suffix: "::1"
```
