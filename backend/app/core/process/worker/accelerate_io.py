import os
from collections.abc import Callable, Sequence
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor


T = object
R = object


def _resolve_worker_count(task_count: int, max_workers: int | None = None) -> int:
    worker_limit = max_workers or os.cpu_count() or 1
    return max(1, min(worker_limit, task_count))


def _resolve_chunksize(task_count: int, worker_count: int) -> int:
    return max(1, task_count // max(worker_count * 4, 1))


def accelerate_io(
    worker: Callable[[object], object],
    items: Sequence[object],
    *,
    max_workers: int | None = None,
    use_multiprocessing: bool = False,
) -> list[object]:
    if not items:
        return []

    worker_count = _resolve_worker_count(len(items), max_workers=max_workers)
    if worker_count <= 1:
        return [worker(item) for item in items]

    executor_cls = ProcessPoolExecutor if use_multiprocessing else ThreadPoolExecutor
    with executor_cls(max_workers=worker_count) as executor:
        return list(
            executor.map(
                worker,
                items,
                chunksize=_resolve_chunksize(len(items), worker_count),
            )
        )
