"""Live process test for single-instance Windows mutex."""

import subprocess
import sys
import time


def test_live_mutex():
    cmd1 = [
        sys.executable,
        "-c",
        "from scriber.single_instance import ensure_single_instance; import time; print('P1:', ensure_single_instance()); time.sleep(1.5)",
    ]
    p1 = subprocess.Popen(cmd1, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    time.sleep(0.4)

    cmd2 = [
        sys.executable,
        "-c",
        "from scriber.single_instance import ensure_single_instance; print('P2:', ensure_single_instance())",
    ]
    p2 = subprocess.Popen(cmd2, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    out1, _ = p1.communicate(timeout=5)
    out2, _ = p2.communicate(timeout=5)

    print("Process 1 Output:", out1.strip())
    print("Process 2 Output:", out2.strip())

    assert "P1: True" in out1, f"Process 1 must acquire mutex, got: {out1}"
    assert "P2: False" in out2, f"Process 2 must be blocked, got: {out2}"
    print("[+] SUCCESS: Single instance mutex cleanly blocked second process and allowed first!")


if __name__ == "__main__":
    test_live_mutex()
