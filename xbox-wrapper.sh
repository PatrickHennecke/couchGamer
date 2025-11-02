#!/bin/bash

USER=modus
USER_ID=$(id -u $USER)
export DISPLAY=:0
export XDG_RUNTIME_DIR=/run/user/$USER_ID

sudo -u $USER --preserve-env=DISPLAY,XDG_RUNTIME_DIR \
  systemd-run --user --scope /usr/local/bin/xbox-connected.sh

