import sys
import time
import statistics
import argparse
from datetime import datetime
import psutil


SAMPLE_INTERVAL = 0.1   # time between each sample (in seconds)
MONITOR_DURATION = 10   # total runtime


def find_process(name: str) -> psutil.Process | None:
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            proc_name = proc.info["name"] or ""
            cmdline   = " ".join(proc.info["cmdline"] or [])
            if name.lower() in proc_name.lower() or name.lower() in cmdline.lower():
                return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None


def sample_process(proc: psutil.Process) -> dict | None:
    try:
        with proc.oneshot():   # oneshot() batches the syscalls, faster on Linux
            cpu  = proc.cpu_percent(interval=None)
            mem  = proc.memory_info().rss / (1024 ** 2)   # bytes -> MB
            threads = proc.num_threads()
        return {"cpu": cpu, "mem_mb": mem, "threads": threads}
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None


def print_live_row(i: int, snap: dict, elapsed: float):
    print(
        f"  [{elapsed:05.2f}s] "
        f"CPU: {snap['cpu']:6.2f}%  |  "
        f"RAM: {snap['mem_mb']:7.2f} MB  |  "
        f"Threads: {snap['threads']:3d}"
    )
def print_report(proc_name: str, pid: int, samples: list[dict]):
    cpu_vals    = [s["cpu"]     for s in samples]
    mem_vals    = [s["mem_mb"]  for s in samples]
    thread_vals = [s["threads"] for s in samples]
    cpu_mean   = statistics.mean(cpu_vals)
    cpu_std    = statistics.stdev(cpu_vals) if len(cpu_vals) > 1 else 0.0
    cpu_peak   = max(cpu_vals)
    mem_mean   = statistics.mean(mem_vals)
    mem_peak   = max(mem_vals)
    thread_max = max(thread_vals)
    # std dev is the key metric here — high std dev = bursty/unpredictable CPU
    if cpu_std < 5:
        burst_label = "Stable  (steady CPU draw, predictable power)"
    elif cpu_std < 20:
        burst_label = "Moderate (some spikes, DVFS will react)"
    else:
        burst_label = "Bursty  (heavy spikes — expect thermal pressure)"

    sep = "─" * 60
    print(f"\n{sep}")
    print(f"  SUMMARY  —  {proc_name}  (PID {pid})")
    print(f"  Samples : {len(samples)}  over {MONITOR_DURATION}s")
    print(sep)
    print(f"  CPU  avg   : {cpu_mean:6.2f}%")
    print(f"  CPU  peak  : {cpu_peak:6.2f}%")
    print(f"  CPU  std   : {cpu_std:6.2f}%   →  {burst_label}")
    print(f"  RAM  avg   : {mem_mean:7.2f} MB")
    print(f"  RAM  peak  : {mem_peak:7.2f} MB")
    print(f"  Threads max: {thread_max}")
    print(sep + "\n")
def main():
    parser = argparse.ArgumentParser(
        description="Sample CPU, RAM, and threads of a running process for 10 seconds."
    )
    parser.add_argument("process", help="Process name to monitor (e.g. firefox, python)")
    parser.add_argument(
        "--duration", type=int, default=MONITOR_DURATION,
        help=f"How many seconds to monitor (default: {MONITOR_DURATION})"
    )
    args = parser.parse_args()

    proc = find_process(args.process)
    if proc is None:
        print(f"[!] No process found matching '{args.process}'. Is it running?")
        sys.exit(1)

    print(f"\n[+] Found '{args.process}'  →  PID {proc.pid}")
    print(f"[+] Sampling every {int(SAMPLE_INTERVAL * 1000)}ms for {args.duration}s ...\n")
    proc.cpu_percent(interval=None)
    time.sleep(SAMPLE_INTERVAL)
    samples  = []
    deadline = time.monotonic() + args.duration
    while time.monotonic() < deadline:
        t0   = time.monotonic()
        snap = sample_process(proc)
        if snap is None:
            print("[!] Process exited early.")
            break
        elapsed = args.duration - (deadline - time.monotonic())
        print_live_row(len(samples), snap, elapsed)
        samples.append(snap)
        sleep_for = SAMPLE_INTERVAL - (time.monotonic() - t0)
        if sleep_for > 0:
            time.sleep(sleep_for)
    if not samples:
        print("[!] No samples collected.")
        sys.exit(1)

    print_report(args.process, proc.pid, samples)


if __name__ == "__main__":
    main()
