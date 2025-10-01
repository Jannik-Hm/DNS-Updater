# DNS-Updater
A python-based docker application to regularly update DNS records automatically
- IPv4 A Records (via api.ipify.org)
- IPv6 AAAA Records (dynamic prefix updater using a combination of api6.ipify.org and prefixOffst + suffix config)

## Configuration

A detailed config guide can be found [here](/docs/config/README.md).

## Dependencies
If you are interested in the dependencies of this application, feel free to analyze the [requirements.txt](/requirements.txt) or [Dependency Licenses](/Dependency-Licenses/).

## Development / Contribution
This application is targeted to be expanded with other DNS providers. <br>
Since I personally don't use any other providers, I currently cannot test and develop for them.

The same applies to other Logging providers (currently stdout and Discord).

So, if you have need for a specific provider, feel free to contribute code yourself and open a PR or help me to add them by opening an issue.
