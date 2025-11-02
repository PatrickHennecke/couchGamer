#!/bin/bash

# Restore monitor layout
echo "[INFO] Restoring monitor layout..."
hyprctl keyword monitor "DP-5, 2560x1440@240, 0x0, 1"
hyprctl keyword monitor "DP-6, 1920x1080@60, 2560x0, 1, transform, 1"
hyprctl keyword monitor "HDMI-A-2, disable"

# Restore audio output
# Set TV audio
echo "Setting audio output to TV..."
tries=0
success=0
while [ $tries -lt 5 ]; do
	wpctl set-default 34
	sleep 2

	CURRENT=$(wpctl status | grep -E 'Default Sink' | awk '{print $NF}')
	if [ "$CURRENT" = "$AUDIO_TARGET" ]; then
        echo "[INFO] Successfully switched audio to sink $AUDIO_TARGET."
        success=1
        break
    fi

    echo "[WARN] Audio switch attempt $((tries+1)) failed. Retrying..."
    tries=$((tries+1))
done

if [ $success -ne 1 ]; then
    echo "[ERROR] Failed to switch audio after $tries attempts."
    exit 1
fi

# Power cycle the TV to simulate Home (best effort)
echo "[INFO] Sending CEC power cycle..."
echo "standby 0" | cec-client -s -d 1
sleep 1
echo "on 0" | cec-client -s -d 1

echo "Applying updated window rules..."
# Main Steam window
hyprctl keyword windowrulev2 "workspace 14, class:^(steam)$, title:^(Steam)$"
hyprctl keyword windowrulev2 "monitor DP-6, class:^(steam)$, title:^(Steam)$"

# Steam game windows
hyprctl keyword windowrulev2 "workspace 6, class:^(steam_app_.*)$"
hyprctl keyword windowrulev2 "monitor DP-5, class:^(steam_app_.*)$"

