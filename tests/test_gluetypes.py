import subprocess
import sys
from pathlib import Path


def test_import_gluetypes(tmp_path: Path) -> None:
    """
    Make sure gluetypes uses lazy imports by default.
    Note that this is not fully reliable as pytest itself already loads a ton of modules.
    """
    prog = """\
import sys

def audit(event: str, args: tuple) -> None:
    match event:
        case "import":
            print(args[0])

sys.addaudithook(audit)

import gluetypes
"""
    prog_path = tmp_path / "prog.py"
    prog_path.write_text(prog)

    # Use audit hooks to detect imports, audit hooks cannot be removed so do it in a sub-process
    src_path = Path(__file__).parent.parent / "src"
    process = subprocess.run(
        [sys.executable, "-S", prog_path],
        check=True,
        capture_output=True,
        env={"PYTHONPATH": str(src_path)},
    )
    loaded_modules = set(process.stdout.decode("utf-8").splitlines(keepends=False))

    assert loaded_modules == {"gluetypes"}
