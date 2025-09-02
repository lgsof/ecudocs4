#!/usr/bin/env python3
"""
Join "ciudades from three files: colombia, ecuador, peru"
"""
import sys

colFile = open ("ciudades_principales_colombia.txt")
ecuFile = open ("ciudades_principales_ecuador.txt")
peFile  = open ("ciudades_principales_peru.txt")

allCities = []

colLines = colFile.readlines ()
ecuLines = ecuFile.readlines ()
peLines  = peFile.readlines ()

for prefix, paisLines in [("COLOMBIA", colLines), ("ECUADOR", ecuLines), ("PERU", peLines)]:
	for line in paisLines:
		citiesString = line.split (":")[1]
		cities = citiesString.split (",")
		for city in cities:
			allCities.append (f"{city.strip()}-{prefix}\n")

allCities.sort ()
outFilename = "ciudades_paises_principales.txt"
open (outFilename, "w").writelines (allCities)

