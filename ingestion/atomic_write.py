"""Replace a file only once its new content is completely written."""

from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path


def replace_atomically(path: Path, write: Callable[[Path], None]) -> None:
    """Call `write(temp_path)` on a same-directory temp file, then `os.replace()` it onto `path`
    (atomic on POSIX, the guarantee Python documents; a same-volume replace on Windows). After a
    process kill `path` holds either the last complete write or the new one, never a partial one.
    A write that raises leaves no temp file; a killed process can leave `<name>.tmp-<pid>` beside
    `path`. Power loss is not covered: nothing is fsynced."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f"{path.name}.tmp-{os.getpid()}")
    try:
        write(tmp_path)
        os.replace(tmp_path, path)
    except BaseException:
        tmp_path.unlink(missing_ok=True)
        raise
