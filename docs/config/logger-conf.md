# Log Providers

This application allows the use of multiple different Log providers for messaging.

If your desired provider is not yet implemented, feel free to either contribute yourself or open a request issue.

Currently supported Providers:
- [Stdio](#stdio)
- [Discord](#discord)

## General config options

| Attribute        | Alias | Type              | Default | Description                                                                 |
|------------------|-------|-------------------|---------|-----------------------------------------------------------------------------|
| `provider`       | –     | `str`             | –       | The logging provider name.               |
| `loglevel`       | –     | `str`             | –       | Logging level (e.g., `debug`, `info`, `warning`, `error`, `fatal`).                  |
| `provider_config`| –     | `Any \| None`     | `None`  | Provider-specific configuration object. |


## Stdio

Provider Name: `stdio`

The `Stdio` Log Provider streams to `stdout`.

### ProviderConfig

No provider specific configuration.

### Example config

```yaml
- provider: "stdio"
  loglevel: info
```

## Discord

Provider Name: `discord`

The `Discord` Log Provider sends log messages to a discord channel.

### ProviderConfig

| Attribute     | Alias | Type  | Default | Description                                                                 |
|---------------|-------|-------|---------|-----------------------------------------------------------------------------|
| `webhook_url` | –     | `str` | –       | Discord webhook URL used to send log messages to a specified channel.       |

### Example config

```yaml
- provider: discord
  loglevel: info
  provider_config:
    webhook_url: "{{DNS_UPDATER_VAR_DISCORD_WEBHOOK}}"
```
