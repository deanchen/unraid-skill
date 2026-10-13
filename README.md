# Unraid

A Codex skill for evidence-based Unraid diagnosis and tuning: power and wake
activity, Docker storage paths, exclusive shares, QEMU USB controllers and PCIe
power management. See [SKILL.md](SKILL.md) for the operating workflow.

## Install

Clone this repository into your Codex skills directory:

```sh
git clone https://github.com/deanchen/unraid-skill.git ~/.codex/skills/unraid
```

Invoke it as `$unraid`. Use the `epyc-tuning` skill, when available, for AMD EPYC
BIOS and firmware work.

## Installation context

Store hostnames, server history, meter entity IDs and rollback locations in
ignored `private/context.md`. Keep credentials and raw diagnostic records
private. Refresh recorded facts before making changes.

## Helpers

- `scripts/sample-intel-power.sh` samples Intel RAPL and host activity on a
  compatible Linux host. Verify prerequisites described in the skill first.
- `scripts/solarflare-aspm-enable.sh` is a guarded hardware-specific example
  for an SFN7122F and Intel root port. Its PCI IDs and addresses are fixed; it
  requires explicit authorization and verified topology before execution.

Lower software wake counts do not establish lower whole-server power. Measure
comparable windows and verify application health after authorized changes.
