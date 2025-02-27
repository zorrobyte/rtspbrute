from queue import Queue, Empty
from threading import RLock, current_thread
import time
import logging

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

logger = logging.getLogger()

# Add thread tracking
active_threads = set()
thread_lock = RLock()


def brute_routes(input_queue: Queue, output_queue: Queue) -> None:
    try:
        with thread_lock:
            active_threads.add(current_thread())
            
        while True:
            try:
                target: RTSPClient = input_queue.get(timeout=5)  # Add timeout
                if target is None:
                    break

                result = attack_route(target)
                if result:
                    PROGRESS_BAR.add_total(BRUTE_PROGRESS)
                    output_queue.put(result)

                PROGRESS_BAR.update(CHECK_PROGRESS, advance=1)
                input_queue.task_done()
            except Empty:
                continue  # Keep trying if queue is empty
            except Exception as e:
                logger.error(f"Error in brute_routes: {e}")
                if target:
                    input_queue.task_done()
    finally:
        with thread_lock:
            active_threads.remove(current_thread())


def brute_credentials(input_queue: Queue, output_queue: Queue) -> None:
    while True:
        try:
            target: RTSPClient = input_queue.get(timeout=5)
            if target is None:
                break

            result = attack_credentials(target)
            if result:
                PROGRESS_BAR.add_total(SCREENSHOT_PROGRESS)
                output_queue.put(str(result))

            PROGRESS_BAR.update(BRUTE_PROGRESS, advance=1)
            input_queue.task_done()
            
        except Empty:
            continue
        except Exception as e:
            logger.error(f"Error in brute_credentials: {e}")
            if target:
                input_queue.task_done()


def screenshot_targets(input_queue: Queue) -> None:
    while True:
        try:
            target_url: str = input_queue.get(timeout=5)
            if target_url is None:
                break

            image = get_screenshot(target_url)
            if image:
                with LOCK:
                    append_result(image, target_url)

            PROGRESS_BAR.update(SCREENSHOT_PROGRESS, advance=1)
            input_queue.task_done()
            
        except Empty:
            continue
        except Exception as e:
            logger.error(f"Error in screenshot_targets: {e}")
            if target_url:
                input_queue.task_done()
