import socket
from typing import Type

import pytest

from rtspbrute.modules.rtsp import AuthMethod, RTSPClient, Status


def test_init():
    rtsp = RTSPClient("0.0.0.0")
    assert rtsp.ip == "0.0.0.0"
    assert rtsp.port == 554
    assert rtsp.timeout == 2
    assert rtsp.credentials == ":"


def test_init_error():
    with pytest.raises(ValueError) as excinfo:
        rtsp = RTSPClient("")
    assert "'' does not appear to be an IPv4 or IPv6 address" in str(excinfo.value)

    with pytest.raises(ValueError) as excinfo:
        rtsp = RTSPClient("0.0.0.0", 65536)
    assert "65536 is not a valid port" in str(excinfo.value)


def test_route():
    rtsp = RTSPClient("0.0.0.0")
    assert rtsp.route == ""
    rtsp.routes.append("/1")
    rtsp.routes.append("/2")
    assert rtsp.route == "/1"


def test_is_connected():
    rtsp = RTSPClient("0.0.0.0")
    assert not rtsp.is_connected
    rtsp.status = Status.CONNECTED
    assert rtsp.is_connected


def test_is_authorized():
    rtsp = RTSPClient("0.0.0.0")
    assert not rtsp.is_authorized
    rtsp.data = "200 OK"
    assert rtsp.is_authorized


def test_connect_successful(monkeypatch):
    def _create_connection(address, timeout):
        return (address, timeout)

    monkeypatch.setattr(socket, "create_connection", _create_connection)

    rtsp = RTSPClient("0.0.0.0")
    connected = rtsp.connect()
    assert connected
    assert rtsp.socket == (("0.0.0.0", 554), 2)
    assert rtsp.status is Status.CONNECTED
    assert not rtsp.last_error


def test_connect_unsuccessful(monkeypatch):
    def _create_connection(address, timeout):
        raise TimeoutError(address, timeout)

    monkeypatch.setattr(socket, "create_connection", _create_connection)

    rtsp = RTSPClient("0.0.0.0")
    connected = rtsp.connect(8554)
    assert not connected
    assert not rtsp.socket
    assert rtsp.status is Status.TIMEOUT
    assert rtsp.last_error.args == (("0.0.0.0", 8554), 2)


def test_authorize_without_connection():
    rtsp = RTSPClient("0.0.0.0")
    authorized = rtsp.authorize()
    assert not authorized


class MockSocket:
    def __init__(
        self,
        successful: bool = True,
        exception: Type[Exception] = TimeoutError,
        data: str = "",
    ) -> None:
        self.successful = successful
        self.exception = exception
        self.data_to_recv = data

        self.sent_data: bytes
        self.recv_bufsize: int

    def sendall(self, data):
        if self.successful:
            self.sent_data = data
            return
        else:
            raise self.exception()

    def recv(self, bufsize):
        self.recv_bufsize = bufsize
        return self.data_to_recv.encode()

    def close(self):
        return


def test_authorize_successful():
    rtsp = RTSPClient("0.0.0.0")
    rtsp.status = Status.CONNECTED
    rtsp.socket = MockSocket(
        data="RTSP/1.0 200 OK\r\nCSeq: 1\r\nServer: Hipcam RealServer/V1.0\r\n\r\n"
    )
    authorized = rtsp.authorize()
    assert authorized
    assert rtsp.cseq == 1
    assert rtsp.packet
    assert rtsp.socket.sent_data
    assert rtsp.data
    assert rtsp.auth_method is AuthMethod.NONE


def test_authorize_unsuccessful():
    rtsp = RTSPClient("0.0.0.0")
    rtsp.status = Status.CONNECTED
    rtsp.socket = MockSocket(successful=False)
    authorized = rtsp.authorize()
    assert not authorized
    assert rtsp.cseq == 1
    assert rtsp.packet
    assert not hasattr(rtsp.socket, "sent_data")
    assert not rtsp.data
    assert rtsp.status is Status.TIMEOUT
    assert rtsp.last_error


def test_str():
    rtsp = RTSPClient("0.0.0.0")
    assert str(rtsp) == f"rtsp://{rtsp.ip}:{rtsp.port}"
    rtsp.port = 8554
    rtsp.credentials = "admin:admin"
    rtsp.routes.append("/1")
    assert str(rtsp) == f"rtsp://{rtsp.credentials}@{rtsp.ip}:{rtsp.port}{rtsp.route}"
