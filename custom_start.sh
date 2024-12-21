#!/bin/bash

set -e

echo "=============================="
echo "Current directory: $(pwd)"
echo "=============================="
echo "First-level contents:"
echo "------------------------------"
ls -1 "$(dirname "$0")" | sed 's/^/  /'
echo "------------------------------"

# Hack to enable the use of the config.json file
if [ ! -f "$(dirname "$0")/config.json" ]; then
    echo "Error: config.json file not found!"
    exit 1
fi
cp "$(dirname "$0")/config.json" "$(dirname "$0")/data/config.json"

echo "=============================="
echo "Running custom_start.py..."
echo "=============================="
python custom_start.py

echo "=============================="
echo "Starting start.sh..."
echo "=============================="
./start.sh