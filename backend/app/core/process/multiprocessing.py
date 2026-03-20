import os
from collections.abc import Callable, Sequence
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures.process import BrokenProcessPool


def _resolve_worker_count(task_count: int, max_workers: int | None = None) -> int:
    cpu_bound_limit = max_workers or os.cpu_count() or 1
    return max(1, min(cpu_bound_limit, task_count))


def _resolve_chunksize(task_count: int, worker_count: int) -> int:
    return max(1, task_count // max(worker_count * 4, 1))


def accelerate_lemma_io(worker: Callable[[str], str], source_texts: Sequence[str], max_workers: int | None = None) -> list[str]:
    if not source_texts:
        return []

    worker_count = _resolve_worker_count(len(source_texts), max_workers=max_workers)
    if worker_count <= 1:
        return [worker(source_text) for source_text in source_texts]

    try:
        with ProcessPoolExecutor(max_workers=worker_count) as executor:
            return list(executor.map(worker, source_texts, chunksize=_resolve_chunksize(len(source_texts), worker_count)))
        
    except (BrokenProcessPool, OSError):
        return [worker(source_text) for source_text in source_texts]
