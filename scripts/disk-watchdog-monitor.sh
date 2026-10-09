#!/bin/bash
# Disk watchdog monitor — fires the agent only when free space CHANGES on either disk.
# Deterministic output (no timestamps) so the change-detector works.
ROOT_AVAIL=$(df -BG --output=avail / | tail -1 | tr -dc '0-9')
DATA_AVAIL=$(df -BG --output=avail /mnt/data | tail -1 | tr -dc '0-9')
echo "root:${ROOT_AVAIL}G data:${DATA_AVAIL}G"
