#!/bin/sh
# Temporary Mac scheduler for raw snapshots until the cloud deployment (stage 3, step 5).
# Usage: deploy/launchd/install.sh            install and load both slots
#        deploy/launchd/install.sh --uninstall  unload and remove
# launchd uses the system time zone (Europe/Warsaw expected) and runs a missed job once
# after the Mac wakes; such a run is stored and marked valid_for_cutoff=false.
set -eu

REPO=$(cd "$(dirname "$0")/../.." && pwd)
AGENTS="$HOME/Library/LaunchAgents"
UV=$(command -v uv)
DOMAIN="gui/$(id -u)"

for entry in reserves:8:0 dayahead:10:30; do
  slot=${entry%%:*}
  hm=${entry#*:}
  label="pl.bess.snapshot.$slot"
  plist="$AGENTS/$label.plist"
  launchctl bootout "$DOMAIN/$label" 2>/dev/null || true
  rm -f "$plist"
  [ "${1:-}" = "--uninstall" ] && { echo "removed $label"; continue; }

  mkdir -p "$AGENTS" "$REPO/data/logs"
  cat > "$plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$label</string>
  <key>ProgramArguments</key>
  <array>
    <string>$UV</string><string>run</string><string>--frozen</string>
    <string>bess</string><string>snapshot</string><string>--slot</string><string>$slot</string>
  </array>
  <key>WorkingDirectory</key><string>$REPO</string>
  <key>EnvironmentVariables</key>
  <dict><key>PATH</key><string>/usr/bin:/bin:$(dirname "$UV")</string></dict>
  <key>StartCalendarInterval</key>
  <dict><key>Hour</key><integer>${hm%%:*}</integer><key>Minute</key><integer>${hm#*:}</integer></dict>
  <key>StandardOutPath</key><string>$REPO/data/logs/snapshot-$slot.log</string>
  <key>StandardErrorPath</key><string>$REPO/data/logs/snapshot-$slot.log</string>
</dict>
</plist>
EOF
  launchctl bootstrap "$DOMAIN" "$plist"
  echo "loaded $label at ${hm%%:*}:$(printf %02d "${hm#*:}")"
done
