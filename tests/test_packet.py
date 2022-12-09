import pytest

from rtspbrute.modules import packet

# Credentials - "admin:admin"
basic_auth_str = "Authorization: Basic YWRtaW46YWRtaW4="
# Credentials - "user:user"
digest_auth_str = (
    "Authorization: Digest "
    'username="user", '
    'realm="realm", '
    'nonce="nonce", '
    'uri="rtsp://0.0.0.0:554", '
    'response="03183d81a44f1e402bd7983108917856"'
)


@pytest.fixture
def clear_cache():
    packet._basic_auth.cache_clear()
    packet._ha1.cache_clear()


def test_basic_auth(clear_cache):
    assert packet._basic_auth("admin:admin") == basic_auth_str
    cache = packet._basic_auth.cache_info()
    assert cache.hits == 0
    assert cache.misses == 1
    assert cache.currsize == 1

    packet._basic_auth("admin:admin")
    packet._basic_auth("user:user")
    cache = packet._basic_auth.cache_info()
    assert cache.hits == 1
    assert cache.misses == 2
    assert cache.currsize == 2


def test_ha1(clear_cache):
    assert packet._ha1("user", "realm", "user") == "54cdcbe980ed379cae3e478ac29c67dc"
    cache = packet._ha1.cache_info()
    assert cache.hits == 0
    assert cache.misses == 1
    assert cache.currsize == 1

    packet._ha1("user", "realm", "user")
    packet._ha1("admin", "realm", "admin")
    cache = packet._ha1.cache_info()
    assert cache.hits == 1
    assert cache.misses == 2
    assert cache.currsize == 2


def test_digest_auth(clear_cache):
    option = "DESCRIBE"
    ip = "0.0.0.0"
    port = 554
    path = ""
    username, password = "user", "user"
    credentials = f"{username}:{password}"
    realm = "realm"
    nonce = "nonce"
    assert (
        packet._digest_auth(option, ip, port, path, credentials, realm, nonce)
        == digest_auth_str
    )


def test_describe(clear_cache):
    ip = "0.0.0.0"
    port = 554
    path = ""
    cseq = 1
    credentials = ":"
    assert packet.describe(ip, port, path, cseq, credentials) == (
        f"DESCRIBE rtsp://{ip}:{port}{path} RTSP/1.0\r\n"
        f"CSeq: {cseq}\r\n"
        "User-Agent: Mozilla/5.0\r\n"
        "Accept: application/sdp\r\n"
        "\r\n"
    )

    credentials = "user:user"
    realm = "realm"
    nonce = "nonce"
    assert packet.describe(ip, port, path, cseq, credentials, realm, nonce) == (
        f"DESCRIBE rtsp://{ip}:{port}{path} RTSP/1.0\r\n"
        f"CSeq: {cseq}\r\n"
        f"{digest_auth_str}\r\n"
        "User-Agent: Mozilla/5.0\r\n"
        "Accept: application/sdp\r\n"
        "\r\n"
    )

    credentials = "admin:admin"
    assert packet.describe(ip, port, path, cseq, credentials) == (
        f"DESCRIBE rtsp://{ip}:{port}{path} RTSP/1.0\r\n"
        f"CSeq: {cseq}\r\n"
        f"{basic_auth_str}\r\n"
        "User-Agent: Mozilla/5.0\r\n"
        "Accept: application/sdp\r\n"
        "\r\n"
    )
