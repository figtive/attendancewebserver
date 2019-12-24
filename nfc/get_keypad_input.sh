#!/bin/bash

cat /proc/bus/input/devices | grep -A 4 "HID 13ba" | tail -1 | cut -d " " -f 5