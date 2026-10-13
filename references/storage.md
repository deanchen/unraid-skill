# Storage, exclusive access and FUSE

## Exclusive shares

On Unraid 6.12+, native exclusive access retains /mnt/user/<share> while using
a symlink to the actual pool directory. Eligibility: permit exclusive shares
globally; primary storage is a named pool; secondary storage is none; the
share exists only on that pool; NFS export disabled. Verify installed-version
rules and actual placement across all mounted pools/array disks. Plenty of
pool free space does not establish placement or authorize moving/deleting data.

For the investigated Unraid 7.3.2 UI/backend, global shareUserExclusive=yes and a pool-only
share uses shareUseCache=only, shareCachePool=<pool>, shareCachePool2 empty.
Cache-preferred (prefer) still permits an array secondary and is not pool-only.
Use the supported UI/emhttp configuration path with preserved unrelated fields,
not hand-created symlinks or edits to generated runtime INI. The global setting
requires the array stopped in that installed UI. Local emhttp uses
/var/run/emhttpd.socket and POST /update.htm; read the installed form field names,
use its current CSRF privately, and verify actual state after the request.
A successful HTTP response alone is insufficient.

Before an authorized array stop: check mover/parity, active encoding/workers,
VMs, Docker services and open users of affected paths. Preserve the exact prior
running and stopped service sets. Unraid array/Docker startup can launch
containers listed in /var/lib/docker/unraid-autostart even if manually stopped.
During scoped maintenance, a temporary filtered list can preserve stopped
containers; restore the exact original list afterward without overwriting
concurrent edits. A disabled container restart cron does not disable autostart.
For active encoding, read the installation's worker/coordinator guidance and use
current registry/locks; never reset leases or stale coordinator snapshots.

After apply/start verify persistent config, runtime/UI Exclusive access status Yes (inspect the installed field name),
readlink resolution of /mnt/user/<share> to /mnt/<pool>/<share>, and service
health. Existing open FUSE descriptors, QEMU files and Docker bind mounts may
retain the prior inode/mount until reopened or recreated. Check live fd/mountinfo
or a bounded FUSE trace under relevant workload before claiming those users now
bypass shfs. Reopen only the affected services within the authorized maintenance.
Do not restart shfs or replace live share paths as a shortcut.

Candidate assessment: appdata, system, domains, isos and development can benefit
when proven pool-only. Check every candidate's actual placement, NFS policy,
writers and desired storage semantics. Mixed array/pool media, photos, storage
or private shares are not candidates without a separately authorized policy/data
migration. Do not remove even apparently empty array remnants without knowing
why they exist and having deletion authorization. Pool-only removes array
fallback; preserve the user's informed preference rather than re-asking it.

Source: [Unraid exclusive shares](https://docs.unraid.net/unraid-os/release-notes/6.12.0/#exclusive-shares).

## Direct Docker pool mounts

For a proven single-pool data directory, /mnt/<pool>/appdata/... bypasses shfs
without changing global share policy. Prefer native exclusive access when it
fits the intended share semantics. Before changing a bind, check array copies,
existing data ownership, backup policy and mounted pool identity. Recreate with
the exact existing image ID, environment, ports, networks, cpuset, user and all
unrelated HostConfig settings; do not pull newer tags incidentally. Update the
persistent Unraid template too. Save full inspect/template XML privately because
they may contain secrets. Keep data in place and verify application health,
alerts/configuration, existing volumes and actual FUSE bypass afterward.

## Directory caching

Folder Caching keeps metadata warm to avoid spinning array drives for browsing;
it is not a file-content cache. Stable scan pacing differs from adaptive rebuild
scans. Changing the stable maximum to 3600 seconds may suit infrequent directory
changes, but does not guarantee exactly one scan/hour after cache loss. Change
only requested pacing in persistent plugin config and runtime configuration;
use the supported service reload, then verify effective arguments/daemon state.
Keep data disk standby and current safe SATA ALPM policy; historical resets are
material evidence when considering deeper link savings.
