"""Windows integration: near-deadline replies, real overruns, and Gomocup grace."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from hidden_job import run


def check(manager, slow, fast, delay, tolerance, expected):
    with tempfile.TemporaryDirectory(prefix="piskvork-clock-") as temp:
        root = Path(temp)
        shutil.copyfile(manager, root / "piskvork.exe")
        for name in ("language", "skins"):
            if (manager.parent / name).exists():
                shutil.copytree(manager.parent / name, root / name)
        # Four Black stones at A1-D1; the fixture deliberately wins on its second turn.
        (root / "openings.txt").write_text("-10,-10,0,0,-9,-10,1,0,-8,-10,2,0,-7,-10\n")
        output = root / "game.psq"
        command = [str(root / "piskvork.exe"), "-benchmark", "-size", "20", "-p",
                   str(slow), str(fast), "-rule", "0", "-timeturn", "5000",
                   "-timematch", "120", "-memory", "350", "-opening", "0",
                   "-tolerance", str(tolerance), "-outfile", str(output),
                   "-outfileformat", "1", "-logpipe", str(root / "protocol-")]
        previous_delay = os.environ.get('PISKVORK_TEST_DELAY_MS')
        os.environ['PISKVORK_TEST_DELAY_MS'] = str(delay)
        try:
            code = run(command, root, 35)
        finally:
            if previous_delay is None: os.environ.pop('PISKVORK_TEST_DELAY_MS', None)
            else: os.environ['PISKVORK_TEST_DELAY_MS'] = previous_delay
        assert code == expected, (delay, tolerance, code, expected)
        assert output.is_file(), "manager did not preserve the result"
        if expected == 1:
            lines = (root / ("protocol-" + slow.name + ".log")).read_text().splitlines()
            for turn in (0, 1):
                debug = lines.index("DEBUG fixture decision " + str(turn))
                message = lines.index("MESSAGE fixture decision " + str(turn))
                coordinate = lines.index("5,5" if turn == 0 else "4,0")
                assert debug < message < coordinate, "buffering reordered protocol evidence"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("manager", type=Path)
    parser.add_argument("slow", type=Path)
    parser.add_argument("fast", type=Path)
    args = parser.parse_args()
    check(args.manager.resolve(), args.slow.resolve(), args.fast.resolve(), 4920, 0, 1)
    check(args.manager.resolve(), args.slow.resolve(), args.fast.resolve(), 5100, 0, 2)
    check(args.manager.resolve(), args.slow.resolve(), args.fast.resolve(), 5100, 1000, 1)
    print("Protocol clock integration passed: 4920/5000, late 5100, 1000-ms grace")
