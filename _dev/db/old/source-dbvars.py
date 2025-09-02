#!/usr/bin/python3
"""
Get Postgres vars from Railway vars
"""

import sys, json, re

inputVarsFile = sys.argv [1]

varsFull = json.load (open (inputVarsFile))

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


vars = getPublicVars (varsFull)
for key in vars.keys():
	if key.startswith ("PG"):
		print (f"{key}={vars[key]}")


