# Measurement and source attribution

## Keep the metrics distinct

Interrupts/s and context switches/s are deltas of /proc/stat intr and ctxt.
Scheduler wakes/s are successful sched_wakeup events, preferably attributed by
PID/TID and owner. They are neither interrupt counts nor physical CPU wakes.
CPUIdle entries/residency are per-logical-CPU software proxies: C3_ACPI does
not prove a hardware package C-state. Intel RAPL energy deltas measure CPU
package power, not NIC, drives, PSU losses or total wall draw; handle wraparound.
Discover available energy domains on another processor instead of assuming
Intel paths. Hardware package residency requires separate suitable telemetry.

Use matched 30–60-second windows, noting startup, backups, encoding, SMB load,
UI polling, diagnostics and disk spin state. Avoid transferring raw traces
inside counter windows: SSH transfer itself creates network interrupts. Collect
counters before transfer, stop recording before decoding, inspect per-CPU
trace overruns and remove only the trace instances created by this session.
A sample with overruns cannot supply complete wake counts. Do not install
missing perf/BPF tools automatically if bounded tracefs suffices.

Attribute threads to containers, QEMU guests or host services using fresh
process/cgroup records. Thread-name totals can combine distinct owners.
Use short syscall/waker/kernel-stack/timer/FUSE traces to explain a dominant
source. Never replay scripts with old snapshot PIDs after restart. Go's short
sysmon sleeps and repeated subprocess wakes are not the same as application
polling frequency; confirm actual call stacks before recommending a timer knob.
Healthcheck invocation rates alone do not predict subprocess wake counts.

## Home Assistant whole-server meter

Use the installation's Home Assistant integration or meter API. Keep credentials
inside the consuming process. Record the actual entity IDs, units and update
cadence in ignored installation context. Distinguish instantaneous watts,
cumulative kWh and whole-day kWh; use interval deltas for energy comparisons.

Read latest state plus historical windows. URL-encode history timestamps and
query parameters; literal timezone '+' in end_time can produce HTTP 400.
Report exact windows in the user's timezone. Integrate power over elapsed time
rather than only averaging state-change records. Bound stale-value holding;
label sampling gaps and interpolation instead of claiming continuous coverage.
Exclude startup/outage intervals from a quiet comparison. A 0.001-kWh counter
step is 1 Wh: over six minutes it corresponds to 10 W, too coarse to resolve a
small ASPM effect. Minute samples can alias brief load spikes. Neither an
isolated low reading nor lower CPU wake counts proves lasting wall savings.
