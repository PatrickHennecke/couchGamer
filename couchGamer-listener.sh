#!/bin/bash

dbus-monitor "interface='com.couchGamer.Trigger'" | while read -r line; do
  if echo "$line" | grep -q "Launch"; then
    /home/modus/.local/bin/couchGamer &
  fi
done
