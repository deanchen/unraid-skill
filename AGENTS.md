# Unraid skill repository

`SKILL.md` is the entrypoint; `references/` contains reusable operating guidance
and `scripts/` contains host helpers. Installation records, raw diagnostics,
credentials, VM XML and Docker inspect output belong in ignored `private/`.
Do not stage private files or copy installation records into public examples.

The Solarflare helper is a hardware-specific example with explicit identity
and topology guards. Do not broaden its applicability or execute it as part of
repository validation. Publication does not authorize live server changes.

For skill edits, run the skill-creator validator. For shell edits, run `bash -n`
and appropriate offline checks; live hardware verification needs task-specific
authorization. Before publishing, inspect staged files and reachable history,
confirm private exclusions, and verify remote visibility and contents.

For GraphQL helper changes, run `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest
discover -s scripts -p 'test_*.py'`. Tests must use synthetic credentials and
mocked transport. Never execute lifecycle mutations as validation. Prefer the
canonical verified HTTPS endpoint and explicit API IDs; preserve partial GraphQL
errors, mutation authorization gates and the no-retry rule.
