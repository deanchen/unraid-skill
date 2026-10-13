# CPU, USB and PCIe devices

## Intel CPU preference

On intel_pstate/HWP, the energy-balanced preference spelling is balance_power.
Verify available preferences/governor on every policy before writing; retain
requested profile and unrelated turbo/performance limits. Apply after existing
PowerTOP boot tuning and verify live readback plus persistent script/schedule.
Do not transplant EPYC cTDP/BIOS advice onto Intel; use epyc-tuning for AMD firmware.

## QEMU USB timer overhead

Legacy UHCI emulates 1-ms USB frames and can create roughly 1000 main-thread
wakes/s. Test qemu-xhci for a modern guest while preserving real USB passthrough.
Back up live/inactive XML privately. Replace only USB controllers; preserve
hostdev IDs, USB bus/port, all disks/NICs, pinning, NVRAM and TPM. On Q35 use a
verified free PCI address; occupied root ports can force unintended topology
changes if allocation is left automatic. Validate XML and normalized unrelated
settings before a graceful VM shutdown/define/start. Allow shutdown/startup
settling; lack of guest-agent support does not imply force-destroy permission.

For HA, verify Core readiness, Z-Wave add-on started, integration loaded,
configured serial-by-id and existing node availability. Retained entity states
alone are weaker than fresh device communication. Do not actuate devices just
to test without scoped authorization. Compare main QEMU and vCPU wakes separately
because guest work after restart can rise. Restore original XML on failed start
or recovery without overwriting later edits. [QEMU USB guidance](https://www.qemu.org/docs/master/system/devices/usb.html).

## Solarflare SFN7122F / SFC9120

The investigated Linux 6.18 sfc driver exposes system sleep callbacks but no runtime PM,
EEE or public PHY/module power-mode controls. power/control=auto and
d3cold_allowed=1 permit rather than prove suspension. D3cold removes normal
network availability. Two NIC functions share the ASIC and upstream PCIe link;
unbinding one unused function is not a proven independent power-off method.
Administratively down stops monitoring/datapath work without guaranteeing PHYoff.
A NO-CARRIER interface can still be administratively UP. Adaptive coalescing
reduces host interrupt work under traffic, not necessarily idle ASIC power.

The card advertises basic ASPM L0s/L1 but not L1 substates. Its advertised L1 exit
bound 64 us exceeds endpoint acceptable 8 us; Linux masks L1 out. Policy changes
and pcie_aspm=force do not bypass that latency check. Distinguish advertised
capability, enabled register state and measured hardware residency.

An L1 override requires explicit authorization for the affected server and
latency mismatch. Preserve an existing authorized choice recorded in private
installation context; do not generalize it to other cards or hosts.
For a newly requested override, verify exact identities/topology and arrange
host-local automatic rollback before the live trial so SSH loss cannot strand
it. Change only Link Control L1 bit 0x2 with masked writes: enable root first,
then both endpoint functions; restore endpoint bits first, then root. Keep L0s
and unsupported L1 substates untouched. Check all register readbacks, AER totals,
NIC errors, kernel reset/timeout logs, link, gateway and dependent service health.

The bundled hardware-specific example helper guards IDs, topology, sfc binding and L1 support,
locks concurrent execution, restores original bits on command/readback failure,
and checks all three devices. Its error trap cannot detect network failure when
PCI writes succeed: it is not a substitute for the initial timed rollback trial.
Startup installation goes after PowerTOP in the existing boot script, with fresh
hash comparison and backup. Raw writes do not update Linux's cached ASPM state;
a later driver reset can clear them. Boot-script verification without a reboot
is saved persistence, not proof of next-boot execution. No watt saving is assumed.

Sources: [sfc callbacks](https://github.com/torvalds/linux/blob/v6.18/drivers/net/ethernet/sfc/efx.c#L1383),
[ASPM latency checks](https://github.com/torvalds/linux/blob/v6.18/drivers/pci/pcie/aspm.c#L568),
[programming order](https://github.com/torvalds/linux/blob/v6.18/drivers/pci/pcie/aspm.c#L979).
