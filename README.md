# DNS-Updater
A python script to update Hetzner DNS records automatically
- IPv4 A (via api.ipify.org)
- IPv6 AAAA prefixes (prefix updater using local json config)

## Dependencies
- requests
- pyyaml
- discord-webhook
  
Install with `pip3 install requests pyyaml discord-webhook`

## Development / Contribution
This script is targeted to be expanded with other DNS providers. <br>
Since I personally don't use any other providers, I currently cannot test and develop for them.

The same applies to other Logging providers (currently stdout and Discord).

So, if you have need for a specific provider, feel free to contribute code yourself and open a PR or help me to add them by opening an issue.
