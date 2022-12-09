from argparse import ArgumentTypeError

import pytest

from rtspbrute.modules.cli.input import file_path, port


def test_file_path(tmp_path):
    assert file_path(tmp_path) == tmp_path
    with pytest.raises(ArgumentTypeError) as excinfo:
        non_existing_path = tmp_path / "file.txt"
        file_path(non_existing_path)
    assert str(non_existing_path) in str(excinfo.value)


def test_port():
    assert port("554") == 554
    with pytest.raises(ArgumentTypeError) as excinfo:
        bad_port = 65536
        port(bad_port)
    assert str(bad_port) in str(excinfo.value)
