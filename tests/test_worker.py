from queue import Queue

import pytest

from rtspbrute.modules import worker
from rtspbrute.modules.cli.output import ProgressBar
from rtspbrute.modules.rtsp import RTSPClient

target = RTSPClient("0.0.0.0")


@pytest.fixture
def queues():
    input_queue = Queue()
    output_queue = Queue()
    input_queue.put(target)
    input_queue.put(None)

    return input_queue, output_queue


class TestBruteRoutes:
    def test_with_result(self, queues, monkeypatch):
        input_queue, output_queue = queues
        worker.PROGRESS_BAR = ProgressBar()
        worker.CHECK_PROGRESS = worker.PROGRESS_BAR.add_task("Check", total=1)
        worker.BRUTE_PROGRESS = worker.PROGRESS_BAR.add_task("Brute", total=0)
        check_task = worker.PROGRESS_BAR.tasks[worker.CHECK_PROGRESS]
        brute_task = worker.PROGRESS_BAR.tasks[worker.BRUTE_PROGRESS]

        _attack_route_good = lambda t: t
        monkeypatch.setattr(worker, "attack_route", _attack_route_good)

        worker.brute_routes(input_queue, output_queue)
        assert input_queue.qsize() == 0
        assert target == output_queue.get()
        assert output_queue.qsize() == 0
        assert check_task.finished
        assert check_task.remaining == 0
        assert not brute_task.finished
        assert brute_task.remaining == 1

    def test_without_result(self, queues, monkeypatch):
        input_queue, output_queue = queues
        worker.PROGRESS_BAR = ProgressBar()
        worker.CHECK_PROGRESS = worker.PROGRESS_BAR.add_task("Check", total=1)
        check_task = worker.PROGRESS_BAR.tasks[worker.CHECK_PROGRESS]

        _attack_route_bad = lambda t: False
        monkeypatch.setattr(worker, "attack_route", _attack_route_bad)

        worker.brute_routes(input_queue, output_queue)
        assert input_queue.qsize() == 0
        assert output_queue.qsize() == 0
        assert check_task.finished
        assert check_task.remaining == 0


class TestBruteCredentials:
    def test_with_result(self, queues, monkeypatch):
        input_queue, output_queue = queues
        worker.PROGRESS_BAR = ProgressBar()
        worker.BRUTE_PROGRESS = worker.PROGRESS_BAR.add_task("Brute", total=1)
        worker.SCREENSHOT_PROGRESS = worker.PROGRESS_BAR.add_task("Screenshot", total=0)
        brute_task = worker.PROGRESS_BAR.tasks[worker.BRUTE_PROGRESS]
        screenshot_task = worker.PROGRESS_BAR.tasks[worker.SCREENSHOT_PROGRESS]

        _attack_credentials_good = lambda t: t
        monkeypatch.setattr(worker, "attack_credentials", _attack_credentials_good)

        worker.brute_credentials(input_queue, output_queue)
        assert input_queue.qsize() == 0
        assert str(target) == output_queue.get()
        assert output_queue.qsize() == 0
        assert brute_task.finished
        assert brute_task.remaining == 0
        assert not screenshot_task.finished
        assert screenshot_task.remaining == 1

    def test_without_result(self, queues, monkeypatch):
        input_queue, output_queue = queues
        worker.PROGRESS_BAR = ProgressBar()
        worker.BRUTE_PROGRESS = worker.PROGRESS_BAR.add_task("Brute", total=1)
        brute_task = worker.PROGRESS_BAR.tasks[worker.BRUTE_PROGRESS]

        _attack_credentials_bad = lambda t: False
        monkeypatch.setattr(worker, "attack_credentials", _attack_credentials_bad)

        worker.brute_credentials(input_queue, output_queue)
        assert input_queue.qsize() == 0
        assert output_queue.qsize() == 0
        assert brute_task.finished
        assert brute_task.remaining == 0


class TestScreenshotTargets:
    def test_with_result(self, queues, tmp_path, result_file, html_file, monkeypatch):
        input_queue, _ = queues
        worker.PROGRESS_BAR = ProgressBar()
        worker.SCREENSHOT_PROGRESS = worker.PROGRESS_BAR.add_task("Screenshot", total=1)
        screenshot_task = worker.PROGRESS_BAR.tasks[worker.SCREENSHOT_PROGRESS]

        pic_file = tmp_path / "pic.jpg"
        pic_file.open("w", encoding="utf-8")
        _get_screenshot_good = lambda t: pic_file

        monkeypatch.setattr(worker, "get_screenshot", _get_screenshot_good)

        worker.screenshot_targets(input_queue)
        assert input_queue.qsize() == 0
        assert str(target) in result_file.read_text()
        assert f'src="{pic_file.parent.name}/{pic_file.name}"' in html_file.read_text()
        assert f'alt="{target}"' in html_file.read_text()
        assert screenshot_task.finished
        assert screenshot_task.remaining == 0

    def test_without_result(self, queues, monkeypatch):
        input_queue, _ = queues
        worker.PROGRESS_BAR = ProgressBar()
        worker.SCREENSHOT_PROGRESS = worker.PROGRESS_BAR.add_task("Screenshot", total=1)
        screenshot_task = worker.PROGRESS_BAR.tasks[worker.SCREENSHOT_PROGRESS]

        _get_screenshot_bad = lambda t: False
        monkeypatch.setattr(worker, "get_screenshot", _get_screenshot_bad)

        worker.screenshot_targets(input_queue)
        assert input_queue.qsize() == 0
        assert screenshot_task.finished
        assert screenshot_task.remaining == 0
