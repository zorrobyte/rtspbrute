from rich.console import Console
from rich.progress import BarColumn, Progress, TaskID


class ProgressBar(Progress):
    def __init__(self, console: Console = Console()) -> None:
        super().__init__(
            "[progress.description]{task.description}",
            BarColumn(),
            "{task.completed} of {task.total}",
            console=console,
        )

    def add_total(self, task_id: TaskID, n: int = 1) -> None:
        with self._lock:
            self._tasks[task_id].total += n


console = Console(highlight=False)
progress_bar = ProgressBar(console)
