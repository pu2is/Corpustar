from collections.abc import Callable, Sequence

from app.core.process.worker.accelerate_io import accelerate_io


def accelerate_lemma_io(
    worker: Callable[[str], str],
    source_texts: Sequence[str],
    max_workers: int | None = None,
) -> list[str]:
    return list(
        accelerate_io(
            worker,
            list(source_texts),
            max_workers=max_workers,
            use_multiprocessing=False,
        )
    )
