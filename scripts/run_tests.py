from __future__ import annotations

import inspect
import pathlib
import runpy
import tempfile


def main() -> None:
    total = 0
    for path in sorted(pathlib.Path("tests").glob("test_*.py")):
        namespace = runpy.run_path(str(path))
        for name, obj in namespace.items():
            if name.startswith("test_") and callable(obj):
                signature = inspect.signature(obj)
                if "tmp_path" in signature.parameters:
                    with tempfile.TemporaryDirectory() as temp_dir:
                        obj(pathlib.Path(temp_dir))
                else:
                    obj()
                total += 1
                print(f"PASS {path}::{name}")
    print(f"{total} tests passed")


if __name__ == "__main__":
    main()

