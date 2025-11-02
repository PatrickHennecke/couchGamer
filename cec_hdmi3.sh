#!/bin/bash

DEBUG=0
LOGFILE="/tmp/cec_hdmi3.log"

# Always redirect output to log file (overwrite on each run)
exec > "$LOGFILE" 2>&1

echo "----- $(date) - Starting script -----"

sleep 1

# Try turning on the TV, retry up to 10 times
tries=0
success=0
while [ $tries -lt 5 ]; do
    echo "on 0" | cec-client -s -d 1
    if [ $? -eq 0 ]; then
        echo "[INFO] TV power-on command sent (try $((tries+1)))."
        success=1
        break
    fi
    echo "[WARN] TV power-on attempt $((tries+1)) failed. Retrying..."
    tries=$((tries+1))
    sleep 2
done

if [ $success -ne 1 ]; then
    echo "[ERROR] Failed to power on TV after $tries attempts."
    exit 1
fi

# Switch to HDMI3
tries=0
success=0
while [ $tries -lt 5 ]; do
    echo "tx 4F:82:30:00" | cec-client -s -d 1
    if [ $? -eq 0 ]; then
        echo "[INFO] HDMI3 switch command sent (try $((tries+1)))."
        success=1
        break
    fi
    echo "[WARN] HDMI3 switch attempt $((tries+1)) failed. Retrying..."
    tries=$((tries+1))
    sleep 5
done

if [ $success -ne 1 ]; then
    echo "[ERROR] Failed to switch to HDMI3 after $tries attempts."
    exit 1
fi

# Adjust display outputs
echo "Configuring monitors..."
hyprctl keyword monitor "DP-5, disable"
hyprctl keyword monitor "DP-6, disable"
hyprctl keyword monitor "HDMI-A-2, enable"

sleep 5

echo "Applying updated window rules..."
hyprctl keyword monitor "HDMI-A-2,1920x1080@60,auto"
# Main Steam window
hyprctl keyword windowrulev2 "workspace 1, class:^(steam)$, title:^(Steam)$"
hyprctl keyword windowrulev2 "monitor HDMI-A-2, class:^(steam)$, title:^(Steam)$"

# Steam game windows
hyprctl keyword windowrulev2 "workspace 1, class:^(steam_app_.*)$"
hyprctl keyword windowrulev2 "monitor HDMI-A-2, class:^(steam_app_.*)$"

# Set TV audio
echo "Setting audio output to TV..."
AUDIO_TARGET=74
tries=0
while [ $tries -lt 5 ]; do
    wpctl set-default "$AUDIO_TARGET"
    sleep 2

    CURRENT=$(wpctl status | grep "Sinks:" | grep -o "[0-9]\+")
    echo "[DEBUG] Current sink ID: $CURRENT — Target: $AUDIO_TARGET"

    if [ "$CURRENT" -eq "$AUDIO_TARGET" ] 2>/dev/null; then
        echo "[INFO] Successfully switched audio to sink $AUDIO_TARGET."
        break
    fi

    echo "[WARN] Audio switch attempt $((tries+1)) failed. Retrying..."
    tries=$((tries+1))
done

# Launch Steam Big Picture
echo "Launching Steam Big Picture..."
steam -bigpicture &
STEAM_PID=$!
echo "[INFO] Launched Steam Big Picture with PID $STEAM_PID"

# Wait for that specific process to exit
while kill -0 "$STEAM_PID" 2>/dev/null; do
    sleep 2
done

echo "[INFO] Steam Big Picture has exited—running cleanup..."
/usr/local/bin/bigpicture_closed.sh

