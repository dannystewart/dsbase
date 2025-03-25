# iplooker

This script will perform a lookup for an IP address using multiple sources. It can be used to get more information about an IP address, including the country, region, city, ISP, and any organization that may be associated to it. It collates the information and combines identical sources.

## Installation

Install from `pip` with:

```bash
pip install iplooker
```

## Usage

The script's primary purpose is for looking up another IP address, but as a bonus feature, it can also tell you your current public IP address. You can even combine the two features to get a lookup for your public IP to see what other people might see if they were to look you up.

Here are the commands you can use:

```bash

# Running with no arguments will prompt for an IP
iplooker

# You can specify an IP as part of the command
iplooker 12.34.56.78

# You can use `-m` or `--me` to check your public IP
iplooker -m
iplooker --me

# You can do both with `-l` or `--lookup`
iplooker -l
iplooker --lookup
```

## Sources

It retrieves information from the following sources:

- ip2location
- ipinfo
- dbip
- ipregistry
- ipgeolocation
- ipapico
- ipbase
