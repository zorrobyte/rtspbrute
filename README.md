# RTSPBrute

[![pipeline status](https://gitlab.com/woolf/RTSPbrute/badges/master/pipeline.svg)](https://gitlab.com/woolf/RTSPbrute/-/commits/master)
[![coverage report](https://gitlab.com/woolf/RTSPbrute/badges/master/coverage.svg)](https://gitlab.com/woolf/RTSPbrute/-/commits/master)

<p align="center">
   <a href="https://asciinema.org/a/353291" target="_blank"><img src="https://asciinema.org/a/353291.svg" /></a>
</p>

> Inspired by [Cameradar](https://github.com/Ullaakut/cameradar)

> Forked from https://gitlab.com/woolf/RTSPbrute

## DISCLAIMER
This software is provided for research and ethical uses only!

## Features

- **Find accessible RTSP streams** on any target
- Brute-force **stream routes**
- Brute-force **credentials**
- **Make screenshots** on accessible streams
- Generate **user-friendly report** of the results:
  - `.txt` file with each found stream on new line
  - `.html` file with screenshot of each found stream

### Report files

- `result.txt`: Each target is on a new line. Import to VLC: change extension to `.m3u` and open in VLC
- `index.html`: Click on the screenshot to copy its link

## Installation

### Requirements

- `python` (> `3.6`)
- `ffmpeg` (must be installed and available in PATH)
- `Pillow`
- `rich`

Install with `pip` or your favorite PyPi package manager.

```
pip install rtspbrute
```

### Installing ffmpeg

- **Ubuntu/Debian**: `sudo apt install ffmpeg`
- **CentOS/RHEL**: `sudo yum install ffmpeg`
- **macOS**: `brew install ffmpeg`
- **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html) or install via [Chocolatey](https://chocolatey.org/): `choco install ffmpeg`

## CLI

```
USAGE
    $ rtspbrute -t TARGETS [-p PORTS [PORTS ...]] [-r ROUTES] [-c CREDENTIALS]
                [-ct N] [-bt N] [-st N] [-T TIMEOUT] [-d] [-h]

ARGUMENTS
    -h, --help                     show this help message and exit
    -t, --targets TARGETS          the targets on which to scan for open RTSP streams
    -p, --ports PORTS [PORTS ...]  the ports on which to search for RTSP streams
    -r, --routes ROUTES            the path on which to load a custom routes
    -c, --credentials CREDENTIALS  the path on which to load a custom credentials
    -ct, --check-threads N         the number of threads to brute-force the routes
    -bt, --brute-threads N         the number of threads to brute-force the credentials
    -st, --screenshot-threads N    the number of threads to screenshot the streams
    -T, --timeout TIMEOUT          the timeout to use for sockets
    -d, --debug                    enable the debug logs

EXAMPLES
    $ rtspbrute -h
    $ rtspbrute -t hosts.txt -p 554 5554 8554 -d
    $ rtspbrute -t ips.txt -r routes.txt -c combinations.txt
    $ rtspbrute -t targets.txt -st 10 -T 10
```

### **"argument"** (`default_value`):

- **"-t, --targets"** (_No default value_): Set the path to the input file. The file can contain IPs, IP ranges and CIDRs. Each one of them should be on a separate line, e.g.:

```
0.0.0.0
192.168.100.1-192.168.254.1
192.17.0.0/16
```

- **"-p, --ports"** (`554`): Set custom ports, e.g.: `-p 554 5554 8554`
- **"-r, --routes"** (`routes.txt`): Set custom path to the file with routes. Each route should start with `/` and be on a separate line, e.g.:

```
/1
/11
/h264
```

- **"-c, --credentials"** (`credentials.txt`): Set custom path to the file with credentials. Each combination should contain `:` and be on a separate line, e.g.:

```
admin:admin
user:user
```

- **"-ct, --check-threads"** (`500`): Set custom number of threads to brute-force the routes
- **"-bt, --brute-threads"** (`200`): Set custom number of threads to brute-force the credentials
- **"-st, --screenshot-threads"** (`20`): Set custom number of threads to screenshot the streams. Smaller number leads to more successful screenshots: too many concurrent ffmpeg processes can lead to resource issues.
- **"-T, --timeout"** (`2`): Set custom timeout value for socket connections
- **"-d, --debug"** (`False`): Enable debug logging to `debug.log` file
