#!/bin/bash
# Daily phone snapshot for Narusya
# Captures battery, location, and device status

BASE="http://100.120.37.106:8765"
TOKEN="narusya-bridge-2026"
DATE=$(date +%Y-%m-%d)
TIME=$(date +%H:%M)
OUTFILE="/home/adora/.hermes/phone-data/snapshot_${DATE}.json"

# Fetch data
BATTERY=$(curl -s -H "X-Auth-Token: $TOKEN" "$BASE/battery" 2>/dev/null)
DEVICE=$(curl -s -H "X-Auth-Token: $TOKEN" "$BASE/device" 2>/dev/null)
LOCATION=$(curl -s -H "X-Auth-Token: $TOKEN" "$BASE/location" 2>/dev/null)

# Combine into one JSON
echo "{\"date\":\"$DATE\",\"time\":\"$TIME\",\"battery\":$BATTERY,\"device\":$DEVICE,\"location\":$LOCATION}" > "$OUTFILE"

# Log
echo "[$DATE $TIME] Phone snapshot saved to $OUTFILE" >> /home/adora/.hermes/phone-data/snapshot.log
