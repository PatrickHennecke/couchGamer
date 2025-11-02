#!/bin/bash

LOCKFILE="/tmp/xbox-controller.lock"
LOGFILE="/tmp/xbox-controller.log"

: > "$LOGFILE"  # Overwrite the log file on each run

if [ -e "$LOCKFILE" ] && [ "$(($(date +%s) - $(stat -c %Y "$LOCKFILE")))" -lt 5 ]; then
  echo "$(date): Skipped due to lock" >> "$LOGFILE"
  exit 0
fi

touch "$LOCKFILE"

echo "$(date): Controller connected, checking for .exe..." >> "$LOGFILE"

if [ "$(id -u)" -eq 0 ]; then
  echo "$(date): ERROR — Script must not run as root" >> "$LOGFILE"
  exit 1
fi

if ! pgrep -f '\.exe' > /dev/null; then
  echo "$(date): Launching couchGamer" >> "$LOGFILE"
  dbus-send --session --dest=com.couchGamer.Trigger --type=signal /com/couchGamer/Trigger com.couchGamer.Trigger.Launch
else
  echo "$(date): .exe already running, skipping couchGamer" >> "$LOGFILE"
  notify-send "🎮 Xbox Controller" "Skipped launching couchGamer — .exe already running"
fi

