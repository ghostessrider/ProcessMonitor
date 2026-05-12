# Systems-Level Resource Monitor

A lightweight process profiler built with nothing but `psutil` and standard Python.
Attach it to any running process — Firefox, a Python script, or an ADB-forwarded
shell process — and get 100ms-resolution CPU, RAM, and thread counts for 10 seconds,
plus a std dev breakdown that tells you whether the process is stable or bursty.

No PyTorch, no pandas, no heavy dependencies. Just psutil.

---

## What it looks like

```
[+] Found 'firefox'  →  PID 3847
[+] Sampling every 100ms for 10s ...

  [00.00s] CPU:  12.40%  |  RAM:  341.20 MB  |  Threads:  42
  [00.10s] CPU:   8.30%  |  RAM:  341.44 MB  |  Threads:  42
  [00.20s] CPU:  67.10%  |  RAM:  349.80 MB  |  Threads:  44
  ...

──────────────────────────────────────────────────────────────
  SUMMARY  —  firefox  (PID 3847)
  Samples : 100  over 10s
──────────────────────────────────────────────────────────────
  CPU  avg   :  18.40%
  CPU  peak  :  91.20%
  CPU  std   :  24.73%   →  Bursty  (heavy spikes — expect thermal pressure)
  RAM  avg   :  344.10 MB
  RAM  peak  :  368.50 MB
  Threads max:  47
──────────────────────────────────────────────────────────────
```

---

## Install and run

```bash
pip install psutil
python monitor.py firefox
python monitor.py python
python monitor.py chrome --duration 30
```

That's it. No environment setup beyond psutil.

---

## Why Use This?

Most profiling tools are either too heavy (requiring massive AI libraries) or too abstract. This tool was built to solve a specific problem: understanding hardware-level constraints on resource-constrained devices.

The core metric here is Standard Deviation (std dev). While average CPU usage tells you the total load, the variance tells you about "burstiness." In mobile and edge environments, bursty behavior triggers the DVFS (Dynamic Voltage and Frequency Scaling) governor to ramp up clock speeds, leading to higher power consumption and thermal throttling.

## Key Hardware Insights

- **Memory Bandwidth Bottlenecks:** On budget SoCs, memory bus saturation often happens before CPU exhaustion. Frequent allocation spikes show up as "bursty" CPU signatures due to cache-miss stalls.
- **Thermal Pressure:** High thread counts on passively cooled devices lead to rapid heat buildup. Monitoring thread peaks helps predict when thermal throttling will kick in.
- **Peak vs. Average RAM:** Mobile OS low-memory killers (LMK) respond to Peak RSS, not the average. This tool tracks the maximum footprint to identify crash risks.
- **Battery Impact:** Unstable CPU draws (high std dev) prevent the processor from settling into low-power states, significantly reducing battery efficiency on mobile hardware.

---

## Installation & Usage

### Setup

Ensure you have `psutil` installed:

```bash
pip install psutil
```

### Running the Monitor

Monitor a process by name for the default duration (10 seconds):

```bash
python monitor.py firefox
```

Monitor a specific process for a custom duration:

```bash
python monitor.py python --duration 30
```

### Remote Monitoring (ADB)

To monitor an Android process, you can track the `adb` shell process on your host machine while the app is active on the connected device.

---

## Technical Details

- **Sampling Interval:** 100ms (optimized to capture spikes without introducing significant profiling overhead).
- **Metric Collection:** Uses `psutil.oneshot()` to batch system calls, minimizing the performance impact on the target process.
- **Zero-Heavy-Dependency:** Relies only on the Python standard library and `psutil`.
