from collections import namedtuple

import pytest

from rtspbrute.modules import attack, rtsp
from tests.test_packet import basic_auth_str


class MockSocket:
    OK = b"RTSP/1.0 200 OK"
    BAD = b"RTSP/1.0 400 Bad Request"

    def __init__(self, valid_route: str, valid_auth: str = "") -> None:
        self.valid_route: str = valid_route
        self.valid_auth: str = valid_auth
        self.packet: bytes = b""

    def sendall(self, data: bytes):
        self.packet = data

    def recv(self, bufsize: int):
        if (
            self.valid_route.encode() in self.packet
            and self.valid_auth.encode() in self.packet
        ):
            return self.OK
        else:
            return self.BAD


def factory_create_connection(valid_port, valid_route, valid_auth=""):
    def _create_connection(address, timeout):
        if address[1] == valid_port:
            return MockSocket(valid_route, valid_auth)
        else:
            raise TimeoutError()

    return _create_connection


def test_attack_route(monkeypatch):
    valid_port = 8554
    valid_route = "/valid/route"
    attack.PORTS = [554, valid_port]
    attack.ROUTES = ["/1", "/11", valid_route]

    target = rtsp.RTSPClient("0.0.0.0")
    _create_connection = factory_create_connection(valid_port, valid_route)
    monkeypatch.setattr(rtsp.socket, "create_connection", _create_connection)

    successful = attack.attack_route(target)
    assert successful
    assert target.data == MockSocket.OK.decode()
    assert target.port == 8554
    assert target.route == "/valid/route"


def test_attack_credentials(monkeypatch):
    valid_credentials = "admin:admin"
    valid_auth = basic_auth_str
    attack.CREDENTIALS = ["user:user", "admin:12345", valid_credentials]

    target = rtsp.RTSPClient("0.0.0.0")
    _create_connection = factory_create_connection(
        target.port, target.route, valid_auth
    )
    monkeypatch.setattr(rtsp.socket, "create_connection", _create_connection)

    successful = attack.attack_credentials(target)
    assert successful
    assert target.credentials == valid_credentials


def test_is_video_stream():
    CodecContext = namedtuple("CodecContext", ["format"])
    Stream = namedtuple("Stream", ["profile", "start_time", "codec_context"])

    valid_stream = Stream("1", 12301230, CodecContext("YUV"))
    assert attack._is_video_stream(valid_stream)

    bad_stream = Stream("1", 12301230, CodecContext(None))
    assert not attack._is_video_stream(bad_stream)
