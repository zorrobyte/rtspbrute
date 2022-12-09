import socket
from enum import Enum
from ipaddress import ip_address
from time import sleep
from typing import List, Union

from rtspbrute.modules.packet import describe
from rtspbrute.modules.utils import find

MAX_RETRIES = 2


class AuthMethod(Enum):
    NONE = 0
    BASIC = 1
    DIGEST = 2


class Status(Enum):
    CONNECTED = 0
    TIMEOUT = 1
    UNIDENTIFIED = 100
    NONE = -1

    @classmethod
    def from_exception(cls, exception: Exception):
        if type(exception) is type(socket.timeout()) or type(exception) is type(
            TimeoutError()
        ):
            return cls.TIMEOUT
        else:
            return cls.UNIDENTIFIED


class RTSPClient:
    __slots__ = (
        "ip",
        "port",
        "credentials",
        "routes",
        "status",
        "auth_method",
        "last_error",
        "realm",
        "nonce",
        "socket",
        "timeout",
        "packet",
        "cseq",
        "data",
    )

    def __init__(
        self,
        ip: str,
        port: int = 554,
        timeout: int = 2,
        credentials: str = ":",
    ) -> None:
        try:
            ip_address(ip)
        except ValueError as e:
            raise e

        if port not in range(65536):
            raise ValueError(f"{port} is not a valid port")

        self.ip = ip
        self.port = port
        self.credentials = credentials
        self.routes: List[str] = []
        self.status: Status = Status.NONE
        self.auth_method: AuthMethod = AuthMethod.NONE
        self.last_error: Union[Exception, None] = None
        self.realm: str = ""
        self.nonce: str = ""
        self.socket = None
        self.timeout = timeout
        self.packet = ""
        self.cseq = 0
        self.data = ""

    @property
    def route(self):
        if len(self.routes) > 0:
            return self.routes[0]
        else:
            return ""

    @property
    def is_connected(self):
        return self.status is Status.CONNECTED

    @property
    def is_authorized(self):
        return "200" in self.data

    def connect(self, port: int = None):
        if self.is_connected:
            return True

        if port is None:
            port = self.port

        self.packet = ""
        self.cseq = 0
        self.data = ""
        retry = 0
        while retry < MAX_RETRIES and not self.is_connected:
            try:
                self.socket = socket.create_connection((self.ip, port), self.timeout)
            except Exception as e:
                self.status = Status.from_exception(e)
                self.last_error = e

                retry += 1
                sleep(1.5)
            else:
                self.status = Status.CONNECTED
                self.last_error = None

                return True

        return False

    def authorize(self, port=None, route=None, credentials=None):
        if not self.is_connected:
            return False

        if port is None:
            port = self.port
        if route is None:
            route = self.route
        if credentials is None:
            credentials = self.credentials

        self.cseq += 1
        self.packet = describe(
            self.ip, port, route, self.cseq, credentials, self.realm, self.nonce
        )
        try:
            self.socket.sendall(self.packet.encode())
            self.data = self.socket.recv(1024).decode()
        except Exception as e:
            self.status = Status.from_exception(e)
            self.last_error = e
            self.socket.close()

            return False

        if not self.data:
            return False

        if "Basic" in self.data:
            self.auth_method = AuthMethod.BASIC
        elif "Digest" in self.data:
            self.auth_method = AuthMethod.DIGEST
            self.realm = find("realm", self.data)
            self.nonce = find("nonce", self.data)
        else:
            self.auth_method = AuthMethod.NONE

        return True

    @staticmethod
    def get_rtsp_url(
        ip: str, port: Union[str, int] = 554, credentials: str = ":", route: str = "/"
    ):
        """Return URL in RTSP format."""
        if credentials != ":":
            ip_prefix = f"{credentials}@"
        else:
            ip_prefix = ""
        return f"rtsp://{ip_prefix}{ip}:{port}{route}"

    def __str__(self) -> str:
        return self.get_rtsp_url(self.ip, self.port, self.credentials, self.route)

    def __rich__(self) -> str:
        return f"[underline cyan]{self.__str__()}[/underline cyan]"
