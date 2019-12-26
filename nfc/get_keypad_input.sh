#!/bin/bash

#
# File: get_keypad_input.sh
#
# get_keypad_input prints handler number, e.g. event0 of USB numeric keypad
#   that will be used by main program to read its input
# Copyright (c) 2019 KukFight Group
# Authors:
#   Nicolaus Christian Gozali
# This program is free script/software. This program is distributed in the 
# hope that it will be useful, but WITHOUT ANY WARRANTY; without even the 
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#

cat /proc/bus/input/devices | grep -A 4 "HID 13ba" | tail -1 | cut -d " " -f 5