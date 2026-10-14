---
name: unraid
description: Operate and diagnose Unraid through its HTTPS GraphQL API, preferring predefined system, array, Docker, VM and share operations. Use SSH for host diagnostics and tuning the API does not expose, including wake activity, storage paths and PCIe power management.
---

# Unraid

Optimize the requested workload using current host evidence. Fewer software
wake events do not establish lower wall power. Preserve the owner's chosen
storage policy, services and hardware overrides; distinguish recorded settings
from freshly verified operating state.

## Choose the relevant reference

- [GraphQL API and predefined operations](references/graphql.md): HTTPS endpoint,
  API keys, read queries, scoped mutations, compatibility and transport checks.
- [Measurement and diagnosis](references/measurement.md): interrupts, scheduler
  wakes, context switches, RAPL, Home Assistant wall-meter history and tracing.
- [Storage efficiency](references/storage.md): exclusive shares, FUSE bypass,
  direct Docker mounts, directory caching and safe array/service maintenance.
- [Device efficiency](references/devices.md): Intel EPP, xHCI passthrough,
  Solarflare ASPM, runtime D3 and rollback/persistence.
- Installation context, when present, is in ignored `private/context.md`. Read
  it for the owner's recorded settings, evidence and rollback locations; refresh
  facts before treating that record as current.

## Operating approach

Prefer the trusted canonical HTTPS GraphQL endpoint for operations the installed
API supports. Use `scripts/unraid_api.py` for the predefined operations below;
read the GraphQL reference before using a new field or mutation. An unsupported
schema field can justify checking the installed-version schema or another
supported interface; authentication, permission and transport failures require
diagnosis, not silent fallback to SSH. Use the installation's existing trusted
SSH access only for operations not exposed by GraphQL, keeping host-key
verification. Read the workspace AGENTS and relevant operating
notes before changes. Inspection/research requests authorize investigation;
tuning/apply requests authorize their scoped changes, including necessary
service maintenance already supported by the session. Do not infer firmware,
physical-device, migration or forced PCI-register authorization from a general
power request. Existing explicit authorization takes precedence over examples.

Establish hardware/kernel, workload, service state, disk/pool placement and
current persistent configuration. Attribute the dominant wake or I/O source
before changing it. Capture original values privately; keep credentials, full
Docker inspect records, VM XML and CSRF tokens out of public artifacts.
Fresh-read and compare expected state before each edit because other threads,
coordinators and workers may be active. Never replace later edits with an older
backup. Coordinate live maintenance with ongoing work.

Compare equivalent bounded windows after settling. A restart can change guest
workload and caches; take another window only when the first is ambiguous.
Check application/device health, configuration readback and relevant errors.
Keep successful scoped changes; restore failed changes without overwriting
unrelated current state. Record runtime state, persistence mechanism, exact
rollback and whether a real restart/boot was actually tested.

## Included helpers

- `scripts/unraid_api.py`: dependency-free Python 3.9+ client for predefined
  GraphQL reads and explicitly gated lifecycle mutations. Reads include
  `system`, `array`, `containers`, `vms`, and `shares`. Set `UNRAID_URL` to the
  trusted HTTPS origin and supply `UNRAID_API_KEY` securely; never pass keys in
  command arguments. `--write` permits a mutation in the helper, but the user's
  task must authorize the operation and target. No automatic retries or SSH
  fallback. Verify state and application health after authorized changes.
- `scripts/sample-intel-power.sh`: tested Intel-host activity/RAPL sampler.
  Requires root, Intel RAPL at `intel-rapl:0`, per-CPU idle telemetry and optional
  tracefs. Use only after verifying those prerequisites; do not apply its Intel
  assumptions to AMD. Example: `TRACE_WAKE=1 bash sample-intel-power.sh 60` on
  the server. Private trace instances are cleaned on exit; inspect overruns.
- `scripts/solarflare-aspm-enable.sh`: guarded write helper for the documented
  SFN7122F/root-port example path. Read device guidance before execution. It deliberately
  overrides Linux's latency eligibility; never run automatically merely because
  this skill was invoked. It rejects different PCI IDs, topology or driver.
