# GraphQL API and predefined operations

## Endpoint and authentication

Unraid 7.2+ includes the official API. Earlier supported versions require the
Unraid Connect plugin; local API use does not require a Connect cloud login.
Use the trusted canonical HTTPS origin plus `/graphql`. Preserve the inherited
HTTP/HTTPS proxy and CA trust in managed cloud environments. Keep TLS verification
enabled and use the hostname that matches the certificate and server's TLS SNI;
an HTTPS IP URL or changed Host header is not an equivalent connection.

Create/manage a key in **Settings → Management Access → API Keys**. Grant the
permissions required for the requested resources; a diagnostic key should use
read permissions. The helper reads `UNRAID_API_KEY` directly from its environment
and sends it in `x-api-key`. An SSH key and a UniFi key cannot authenticate this
API. Supply values through secure environment settings, not chat, CLI arguments,
tracked files, or saved setup instructions. Keys stay in memory; the helper does
not cache them. Set `UNRAID_URL` to the trusted HTTPS origin, or use `--url` for
the non-secret origin. Installation-specific values belong in `private/context.md`.

The developer sandbox is a browser tool, not a prerequisite for authenticated
GraphQL POSTs. A disabled sandbox can reject GET `/graphql` while API POSTs remain
available. Enabling the sandbox does not grant API permissions or necessarily
enable introspection; the installed server may still reject `__schema` queries.

```sh
# Example non-secret origin; the API key must already be supplied securely.
export UNRAID_URL=https://server.example.invalid
python3 scripts/unraid_api.py system
python3 scripts/unraid_api.py array
python3 scripts/unraid_api.py containers
python3 scripts/unraid_api.py vms
python3 scripts/unraid_api.py shares
```

## Predefined reads

| Operation | Selection | Interpretation |
| --- | --- | --- |
| `system` | `info.os`, `info.cpu` | OS release, CPU identity/counts; OS `uptime` is a timestamp, not elapsed seconds |
| `array` | `array.state`, `array.disks` | Data-disk IDs, name, size, status and temperature; not parity/cache inventory or mover/parity readiness |
| `containers` | `docker.containers` | Exact API IDs, names, runtime state/status and autostart; not full inspect/template/configuration |
| `vms` | `vms.domains` | Exact API IDs, names and runtime states; not full domain XML |
| `shares` | `shares` | Share names and free/used/size in KB; does not prove pool-only placement or exclusive access |

Queries are GraphQL documents sent with HTTP POST, even for reads. Requests use
JSON `{ "query": "...", "variables": { ... } }`. HTTP 200 alone is insufficient:
inspect GraphQL `errors` and the returned data. The helper retains partial data,
reports error messages, and exits nonzero if any GraphQL error occurs. Fixed
queries avoid exposing container command/environment/mounts or VM XML by default;
inventory output still contains private infrastructure details.

On the validated Unraid 7.3 server, selecting `Share.id` produced `Cannot return
null for non-nullable field Share.id`. The read-only share preset deliberately
omits that unnecessary field; it does not invent share IDs or suppress errors
from fields it actually requests.

## Predefined lifecycle operations

These are available for task-specific authorized changes, not installation or
smoke tests. The helper requires `--write`; container/VM operations additionally
require `--id` with the exact API ID from a fresh inventory read. IDs are sent as
GraphQL variables (`PrefixedID!`), never interpolated into the document. Do not
assume a Docker engine ID, name, or raw VM UUID is interchangeable with an API ID.

| Operation | Mutation | Required readback |
| --- | --- | --- |
| `array-start` | `array.setState(input: { desiredState: START })` | `array`, then prior service sets and application health |
| `array-stop` | `array.setState(input: { desiredState: STOP })` | `array`, then confirm intended services and affected paths |
| `container-start` | `docker.start(id: $id)` | `containers`, then target application health |
| `container-stop` | `docker.stop(id: $id)` | `containers`, then confirm intended target stopped |
| `container-restart` | `docker.restart(id: $id)` | `containers`, then target application health |
| `vm-start` | `vm.start(id: $id)` | `vms`, then guest service health |
| `vm-stop` | `vm.stop(id: $id)` | `vms`, then confirm target state; shutdown can be asynchronous |
| `vm-reboot` | `vm.reboot(id: $id)` | `vms`, then guest/service recovery; running state alone does not prove reboot completed |

```sh
# Only after authorization and fresh target discovery:
python3 scripts/unraid_api.py container-restart --id '<API-ID>' --write
python3 scripts/unraid_api.py containers
```

Fresh-read before each mutation, preserve unrelated state, and follow the
[storage maintenance checks](storage.md) before stopping/starting the array.
Do not infer safe maintenance from this helper's minimal array query. Preserve
the exact prior running/stopped container and VM sets; autostart may change them.
The array-start preset does not send encryption passwords/keyfiles; use the
supported secure unlock workflow if required. No force stop, reset, disk format,
container deletion/update, key management, or arbitrary shell execution is
included. Mutations are not automatically retried: a timeout or lost connection
requires readback before deciding whether another request is safe.

## Compatibility, errors and SSH boundary

The official generated schema is a reference, not proof of the installed
version's capabilities. The predefined reads were exercised on an Unraid 7.3
server; mutation documents were checked against the official schema and tested
offline, without executing live lifecycle changes. Refresh installed-version
evidence before unfamiliar operations. Do not silently rewrite a rejected
mutation or assume a newer schema applies to an older server.

- **401/403:** check the local Unraid key, resource/action permissions, proxy and
  HTTP destination policy. Do not swap credentials or fall back to root SSH.
- **Invalid CSRF token:** verify API-key authentication is accepted at the
  canonical endpoint. A cookie-authenticated WebGUI flow has different CSRF rules.
- **GraphQL validation error:** inspect the exact field/type/argument and the
  installed-version schema. Introspection may be disabled; use official version
  documentation/source or the authenticated sandbox as available.
- **Redirect or HTML login response:** check endpoint/proxy routing. The helper
  refuses redirects so a key is not forwarded to another origin.
- **Transport/TLS/proxy error:** preserve proxy and TLS settings. In managed
  cloud execution, use the normal approval flow for the same bounded request
  when sandbox access to the inherited proxy fails. Do not bypass policy or
  install a separate VPN client.

The client uses verified TLS, honors inherited proxies, caps responses at 4 MiB,
and uses a 20-second request timeout (`--timeout` may increase it up to 60).
It prints only selected data and error messages, omits extension/stack records,
and redacts the API key if echoed. Keep output private when it identifies hosts,
services or storage; never publish raw diagnostics.

Use SSH for unsupported host operations such as `/proc` and tracefs sampling,
RAPL, PCI registers, filesystem placement/open descriptors, persistent template
edits, and detailed VM XML. Do not claim GraphQL replaces these measurements.
Check cloud raw-TCP support separately: working HTTPS does not establish SSH
transport. If SSH is unavailable, finish supported API work and report the
remaining host-access prerequisite.

## Official references

- [Unraid API overview](https://docs.unraid.net/API/)
- [Authentication, queries and sandbox](https://docs.unraid.net/API/how-to-use-the-api/)
- [Official documentation source](https://github.com/unraid/docs/tree/main/docs/API)
- [Official generated schema](https://github.com/unraid/api/blob/main/api/generated-schema.graphql)
- [Apollo schema explorer](https://studio.apollographql.com/graph/Unraid-API/variant/current/home)

## Offline validation

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s scripts -p 'test_*.py'
```

Tests use synthetic keys and mocked transport. Never invoke live mutations to
validate this skill. Preserve failures and partial data rather than treating a
zero exit from HTTP transport as success.
