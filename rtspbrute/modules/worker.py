from queue import Queue
from threading import RLock

from rich.progress import TaskID

from rtspbrute.modules.attack import attack_credentials, attack_route, get_screenshot
from rtspbrute.modules.cli.output import ProgressBar
from rtspbrute.modules.rtsp import RTSPClient
from rtspbrute.modules.utils import append_result

PROGRESS_BAR: ProgressBar
CHECK_PROGRESS: TaskID
BRUTE_PROGRESS: TaskID
SCREENSHOT_PROGRESS: TaskID
LOCK = RLock()


def brute_routes(input_queue: Queue, output_queue: Queue) -> None:
    while True:
        target: RTSPClient = input_queue.get()
        if target is None:
            break

        result = attack_route(target)
        if result:
            PROGRESS_BAR.add_total(BRUTE_PROGRESS)
            output_queue.put(result)

        PROGRESS_BAR.update(CHECK_PROGRESS, advance=1)
        input_queue.task_done()


def brute_credentials(input_queue: Queue, output_queue: Queue) -> None:
    while True:
        target: RTSPClient = input_queue.get()
        if target is None:
            break

        result = attack_credentials(target)
        if result:
            PROGRESS_BAR.add_total(SCREENSHOT_PROGRESS)
            output_queue.put(str(result))

        PROGRESS_BAR.update(BRUTE_PROGRESS, advance=1)
        input_queue.task_done()


def screenshot_targets(input_queue: Queue) -> None:
    while True:
        target_url: str = input_queue.get()
        if target_url is None:
            break

        # check if "/Streaming/Channels/101/" is in target_url
        if "/Streaming/Channels/101/" in target_url:
            # iterate "/Streaming/Channels/101/" to "/Streaming/Channels/1601/"
            for i in range(1, 17):
                modified_target_url = target_url.replace("/Streaming/Channels/101/", f"/Streaming/Channels/{i}01/")
                image = get_screenshot(modified_target_url)
                if image:
                    with LOCK:
                        append_result(image, modified_target_url)
                PROGRESS_BAR.update(SCREENSHOT_PROGRESS, advance=1)
        # if "/Streaming/Channels/101/" is not in target_url
        else:
            # check if target_url doesn't have anything after :554/
            if target_url.endswith(':554/'):
                # first try the unmodified URL
                image = get_screenshot(target_url)
                if image:
                    with LOCK:
                        append_result(image, target_url)
                PROGRESS_BAR.update(SCREENSHOT_PROGRESS, advance=1)

                # append and iterate /cam/realmonitor?channel=1&subtype=0, /cam/realmonitor?channel=2&subtype=0, ..., /cam/realmonitor?channel=8&subtype=0
                # disabled for now as it causes dupes, need some sort of dupe handler, but hard problem
                #for i in range(1, 17):
                #    modified_target_url = target_url + f'cam/realmonitor?channel={i}&subtype=0'
                #    image = get_screenshot(modified_target_url)
                #    if image:
                #        with LOCK:
                #            append_result(image, modified_target_url)
                #    PROGRESS_BAR.update(SCREENSHOT_PROGRESS, advance=1)
            else:
                image = get_screenshot(target_url)
                if image:
                    with LOCK:
                        append_result(image, target_url)
                PROGRESS_BAR.update(SCREENSHOT_PROGRESS, advance=1)

        input_queue.task_done()
