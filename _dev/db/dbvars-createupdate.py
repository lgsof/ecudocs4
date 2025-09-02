#!/usr/bin/python3

"""
Create/Update Postgress env vars from Railway vars
Get Postgres vars from Railway vars
"""

import sys, json, re

def main ():
	args = sys.argv
	vars = None
	if args [1] == "--createFromJson":
		inputVarsFile = sys.argv [2]
		varsFull = json.load (open (inputVarsFile))
		vars = getPublicVars (varsFull)
	elif args [1] == "--updateVarFile":
		varsFile = sys.argv [2]
		varLine  = sys.argv [3]
		vars     = updateVar (varLine, varsFile)

	printVars (vars)


#-- Update variable in vars from varsFile
def updateVar (varLine, varsFile):
	varsDic = {}
	lines = open (varsFile).readlines ()
	for line in lines:
		if line.startswith ("#") or line == "\n":
			continue
		varName  = line.split("=")[0]
		varValue = line.split("=")[1]
		if varName in varLine:
			varValue = varLine.split("=")[1]
		varsDic [varName] = varValue.strip()

	return varsDic


#-- Get public vars
def getPublicVars (vars):
	urlFull = vars ["DATABASE_PUBLIC_URL"]
	res  = re.search ("(.*)://(.*)[:](.*)[@](.*)[:](.*)[/](.*)", urlFull).groups()

	srvc = res [0]

	user = res [1]
	pswd = res [2]
	host = res [3]
	port = res [4]
	name = res [5]
	
	return {"PGDATABASE":name, "PGHOST":host, "PGPASSWORD":pswd, "PGPORT":port, "PGUSER":user}

#-- Print vars
def printVars (vars):
	for key in vars.keys():
		if key.startswith ("PG"):
			print (f"{key}={vars[key]}")

#--------------------------------------------------------------------
#--------------------------------------------------------------------
main ()
