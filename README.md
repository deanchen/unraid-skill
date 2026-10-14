# Unraid

A Codex skill for Unraid operations and evidence-based diagnosis. Prefer the
HTTPS GraphQL API for system, array, Docker, VM and share operations; use SSH for
host measurements and tuning the API does not expose. See [SKILL.md](SKILL.md)
and [GraphQL operations](references/graphql.md) for the operating workflow.

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

- `scripts/unraid_api.py` uses Python 3.9+ with no external dependencies. Supply
  `UNRAID_API_KEY` securely and set the non-secret `UNRAID_URL` HTTPS origin.
  Run `python3 scripts/unraid_api.py --help` for predefined reads and explicitly
  gated lifecycle mutations. Credentials are never passed in command arguments.
- `scripts/sample-intel-power.sh` samples Intel RAPL and host activity on a
  compatible Linux host. Verify prerequisites described in the skill first.
- `scripts/solarflare-aspm-enable.sh` is a guarded hardware-specific example
  for an SFN7122F and Intel root port. Its PCI IDs and addresses are fixed; it
  requires explicit authorization and verified topology before execution.

Lower software wake counts do not establish lower whole-server power. Measure
comparable windows and verify application health after authorized changes.

Validate the API helper offline with synthetic credentials:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s scripts -p 'test_*.py'
```
