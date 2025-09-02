#!/usr/bin/env python3

"""
Adds a mark at the end of line of "codebinField"

"""
import sys
args = sys.argv

inputFilename = args [1]
lines = open (inputFilename).readlines ()

newlines = []
for line in lines:
	if "\"y\"" in line:
		if "," in line:
			line = line.replace (",", "")

	if "codebinField" in line:
		line = "        " + line

	newlines.append (line)

outFilename = inputFilename.split (".")[0] + "-NEW.json" 
open (outFilename, "w").writelines (newlines)
