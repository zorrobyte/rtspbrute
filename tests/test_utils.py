import pytest

from rtspbrute.modules import utils


class TestAppendResult:
    rtsp_url = "rtsp://1.1.1.1:554/1"

    def test_result_file_only(self, result_file, tmp_path):
        pic_file = tmp_path / "non_existing.file"

        utils.append_result(pic_file, self.rtsp_url)
        assert self.rtsp_url in result_file.read_text()

    def test_html_file(self, result_file, html_file, tmp_path):
        pic_file = tmp_path / "picture.jpg"
        pic_file.open("w", encoding="utf-8")

        utils.append_result(pic_file, self.rtsp_url)
        assert self.rtsp_url in result_file.read_text()
        assert f'src="{pic_file.parent.name}/{pic_file.name}"' in html_file.read_text()
        assert f'alt="{self.rtsp_url}"' in html_file.read_text()


def test_escape_chars():
    text = r'slashes\/column:star*mark?quotes"arrows<>bar|'
    assert utils.escape_chars(text) == "slashes__column_star_mark_quotes_arrows__bar_"


class TestFind:
    response_with_auth = """
    RTSP/1.0 401 Unauthorized
	CSeq: 1
	Server: Hipcam RealServer/V1.0
	WWW-Authenticate: Digest realm="Hipcam RealServer/V1.0", nonce="somenonce"
    """
    response_without_auth = """
    RTSP/1.0 400 Bad Request
    CSeq: 2
    Server: Hipcam RealServer/V1.0
    """

    def test_realm(self):
        var = "realm"
        assert utils.find(var, self.response_with_auth) == "Hipcam RealServer/V1.0"
        assert utils.find(var, self.response_without_auth) == ""

    def test_nonce(self):
        var = "nonce"
        assert utils.find(var, self.response_with_auth) == "somenonce"
        assert utils.find(var, self.response_without_auth) == ""


class TestLoadTxt:
    def test_credentials(self, tmp_path):
        credentials = "user:\nadmin:12345\t\n1111:1111"

        p = tmp_path / "credentials.txt"
        p.write_text(credentials)

        assert utils.load_txt(p, "credentials") == credentials.split()

    def test_routes(self, tmp_path):
        routes = "/1\n/11\n/h264"

        p = tmp_path / "routes.txt"
        p.write_text(routes)

        assert utils.load_txt(p, "routes") == routes.split()

    def test_targets(self, tmp_path):
        targets = "1.2.3.4\n192.168.0.0/29\n1.1.1.1 - 1.1.1.4"

        p = tmp_path / "targets.txt"
        p.write_text(targets)

        assert utils.load_txt(p, "targets") == [
            "1.2.3.4",
            "192.168.0.0",
            "192.168.0.1",
            "192.168.0.2",
            "192.168.0.3",
            "192.168.0.4",
            "192.168.0.5",
            "192.168.0.6",
            "192.168.0.7",
            "1.1.1.1",
            "1.1.1.2",
            "1.1.1.3",
            "1.1.1.4",
        ]


def test_get_lines(tmp_path):
    text = "test\nfunc\nslpitlines"

    p = tmp_path / "test.txt"
    p.write_text(text)

    assert utils.get_lines(p) == text.split()


class TestParseInputLine:
    def test_single_ip(self):
        assert utils.parse_input_line("1.2.3.4") == ["1.2.3.4"]

    def test_ip_range(self):
        assert utils.parse_input_line("1.1.1.1-1.1.1.4") == [
            "1.1.1.1",
            "1.1.1.2",
            "1.1.1.3",
            "1.1.1.4",
        ]
        assert utils.parse_input_line("1.1.1.1 - 1.1.1.4") == [
            "1.1.1.1",
            "1.1.1.2",
            "1.1.1.3",
            "1.1.1.4",
        ]

    def test_cidr(self):
        assert utils.parse_input_line("192.168.0.0/30") == [
            "192.168.0.0",
            "192.168.0.1",
            "192.168.0.2",
            "192.168.0.3",
        ]

    def test_bad_ip(self):
        assert utils.parse_input_line("666.6.6.6") == []
