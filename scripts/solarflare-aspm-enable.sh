#!/bin/bash
# Hardware-specific L1 override example for SFN7122F on the guarded PCIe path.
# Execution requires explicit owner authorization; adapt only after verification.
# Linux's advertised-latency check is deliberately overridden.
set -euo pipefail
export PATH=/usr/bin:/bin:/usr/sbin:/sbin
root=00:1d.0
children=(06:00.0 06:00.1)
fail() { printf '%s\n' "$*" >&2; logger -t solarflare-aspm "$*"; exit 1; }
command -v setpci >/dev/null || fail 'setpci is unavailable; no ASPM changes made'
command -v flock >/dev/null || fail 'flock is unavailable; no ASPM changes made'
exec 9>/var/lock/codex-solarflare-aspm.lock
flock -n 9 || fail 'Another ASPM apply is running'
[ "$(setpci -s "$root" VENDOR_ID.w)" = 8086 ] || fail 'Root-port vendor mismatch'
[ "$(setpci -s "$root" DEVICE_ID.w)" = 7ab0 ] || fail 'Root-port device mismatch'
for bdf in "${children[@]}"; do
    [ "$(setpci -s "$bdf" VENDOR_ID.w)" = 1924 ] || fail 'NIC vendor mismatch'
    [ "$(setpci -s "$bdf" DEVICE_ID.w)" = 0903 ] || fail 'NIC device mismatch'
    [ "$(readlink -f "/sys/bus/pci/devices/0000:$bdf/..")" = "/sys/devices/pci0000:00/0000:$root" ] || fail 'NIC topology mismatch'
    [ "$(basename "$(readlink -f "/sys/bus/pci/devices/0000:$bdf/driver")")" = sfc ] || fail 'NIC driver not ready'
done
declare -A original
for bdf in "$root" "${children[@]}"; do
    capability=$(setpci -s "$bdf" CAP_EXP+0c.l)
    (( (16#$capability & 0x800) != 0 )) || fail 'L1 capability missing'
    original[$bdf]=$(setpci -s "$bdf" CAP_EXP+10.w)
done
rollback() {
    local bdf bit
    for bdf in "${children[@]}" "$root"; do
        printf -v bit '%04x' "$((16#${original[$bdf]} & 2))"
        setpci -s "$bdf" "CAP_EXP+10.w=$bit:0002" || true
    done
    logger -t solarflare-aspm 'L1 apply failed; attempted restoring original L1 bits'
}
trap rollback ERR
trap 'rollback; exit 130' INT
trap 'rollback; exit 143' TERM
# PCIe ordering: enable the root first, then every endpoint function.
for bdf in "$root" "${children[@]}"; do
    setpci -s "$bdf" CAP_EXP+10.w=0002:0002
    actual=$(setpci -s "$bdf" CAP_EXP+10.w)
    (( (16#$actual & 2) == 2 ))
done
# Verify the whole link after all function writes.
for bdf in "$root" "${children[@]}"; do
    actual=$(setpci -s "$bdf" CAP_EXP+10.w)
    (( (16#$actual & 2) == 2 ))
done
trap - ERR INT TERM
logger -t solarflare-aspm 'L1 enabled on 00:1d.0 and SFN7122F 06:00.0/1'
printf '%s\n' 'Solarflare ASPM L1 enabled and verified'
