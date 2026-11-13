#!/bin/bash
# usage: mkcue1.sh TAG  -> iso_TAG.cue (data track only, as the perf-hw lane's iso_*.cue)
printf 'FILE "E:\AvP\learning\lane-perf-pic\iso_%s.iso" BINARY\r\n  TRACK 01 MODE1/2048\r\n    INDEX 01 00:00:00\r\n' "$1" > /e/AvP/learning/lane-perf-pic/iso_$1.cue
