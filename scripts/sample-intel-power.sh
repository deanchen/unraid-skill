#!/bin/bash
# Read-only 30-second CPU package energy and host activity sample.
set -euo pipefail
seconds=${1:-30}
energy=/sys/class/powercap/intel-rapl:0/energy_uj
maximum=$(cat /sys/class/powercap/intel-rapl:0/max_energy_range_uj)
ncpu=$(getconf _NPROCESSORS_ONLN)
trace_instance=
cleanup() {
  if [ -n "$trace_instance" ]; then
    printf '0\n' > "$trace_instance/tracing_on"
    printf '0\n' > "$trace_instance/events/sched/sched_wakeup/enable"
    rmdir "$trace_instance"
  fi
}
trap cleanup EXIT
if [ "${TRACE_WAKE:-0}" = 1 ]; then
  trace_instance=/sys/kernel/debug/tracing/instances/unraid-power-$$
  mkdir "$trace_instance"
  printf '16384\n' > "$trace_instance/buffer_size_kb"
  printf '1\n' > "$trace_instance/events/sched/sched_wakeup/enable"
  printf '1\n' > "$trace_instance/tracing_on"
fi
snapshot() {
  cat /proc/uptime
  cat "$energy"
  awk '$1=="cpu" || $1=="intr" || $1=="ctxt" { if ($1=="intr") print $1,$2; else print }' /proc/stat
  for d in /sys/devices/system/cpu/cpu[0-9]*/cpuidle/state*; do
    read -r name < "$d/name"
    read -r usage < "$d/usage"
    read -r time < "$d/time"
    printf 'idle %s %s %s\n' "$name" "$usage" "$time"
  done
}
before=$(snapshot)
sleep "$seconds"
after=$(snapshot)
printf '%s\n---\n%s\n' "$before" "$after" | awk -v maximum="$maximum" -v ncpu="$ncpu" '
  BEGIN {second=0; line=0}
  /^---$/ {second=1; line=0; next}
  /^idle / {usage[second,$2]+=$3; residency[second,$2]+=$4; states[$2]=1; next}
  {line++; for(i=1;i<=NF;i++) a[second,line,i]=$i}
  END {
    dt=a[1,1,1]-a[0,1,1]; de=a[1,2,1]-a[0,2,1]; if(de<0)de+=maximum;
    for(i=2;i<=9;i++) { total+=a[1,3,i]-a[0,3,i] }
    idle=a[1,3,5]-a[0,3,5]; wait=a[1,3,6]-a[0,3,6];
    printf "seconds=%.2f package_watts=%.3f cpu_busy_pct=%.2f iowait_pct=%.2f interrupts_per_sec=%.1f context_switches_per_sec=%.1f\n",dt,de/dt/1000000,(total-idle-wait)*100/total,wait*100/total,(a[1,4,2]-a[0,4,2])/dt,(a[1,5,2]-a[0,5,2])/dt;
    for(state in states) {
      delta=usage[1,state]-usage[0,state]; entries+=delta;
      printf "idle_state=%s entries_per_sec=%.1f residency_pct=%.2f\n",state,delta/dt,(residency[1,state]-residency[0,state])/dt/1000000/ncpu*100;
    }
    printf "idle_entries_per_sec=%.1f (CPUIdle software entry proxy, not physical package wakes)\n",entries/dt;
  }'
if [ -n "$trace_instance" ]; then
  printf '0\n' > "$trace_instance/tracing_on"
  awk '/sched_wakeup:/ {name=$0; sub(/^.* comm=/,"",name); sub(/ pid=.*$/,"",name); count[name]++; total++} END {printf "scheduler_wakeups=%d scheduler_wakeups_per_sec=%.1f\n",total,total/'"$seconds"'; for(name in count) printf "%9d wake_task=%s\n",count[name],name}' "$trace_instance/trace"
  awk '/^overrun:/ {n+=$2} END{print "trace_overruns="n+0}' "$trace_instance"/per_cpu/cpu*/stats
fi
date -u +%FT%TZ
