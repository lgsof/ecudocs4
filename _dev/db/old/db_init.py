#!/usr/bin/env python3
"""
Scrips for init DB, drop, create, set. 
"""
import os
import subprocess as sb


APPPATH    = "/home/lg/BIO/iaprojects/ecuapassdocs/EcuapassDocs2-dev"
DJUSER     = "admin"
DJPASSWORD = "admin"
DJEMAIL    = f"{DJUSER}@gmail.com"

# Postgress env vars
PGUSER     = os.environ.get ("PGUSER")
PGPASSWORD = os.environ.get ("PGPASSWORD")
PGDATABASE = os.environ.get ("PGDATABASE")
PGHOST     = os.environ.get ("PGHOST")
PGPORT     = os.environ.get ("PGPORT")

def main ():
	#dropUserAndDatabase ()
	#createUserAndDatabase ()
	#createPublicSchemaGrantUser ()
	resetMigrations ()
	runMigrationsAndCreateSuperuser ()

	#---
	#checkUserPrivileges ()
	#viewSchemasAndOwnership ()
	#checkForOwnedObjects ()
	#dropOwnedObjects ()

#----------------------------------------------------------
#-- Drop current DB user and database
#----------------------------------------------------------
def dropUserAndDatabase ():
	if input (f"Remove USER: {PGUSER} and DATABASE: {PGDATABASE} : (YES/NO) ") == "YES":
		exe (f"drop database {PGDATABASE};")
		exe (f"ALTER SCHEMA public OWNER TO postgres;")
		exe (f"DROP OWNED BY {PGUSER};")
		exe (f"drop user $PGUSER;")

#----------------------------------------------------------
#-- Create DB user, DB, and grant permissions
#----------------------------------------------------------
def createUserAndDatabase ():
	sql = f"createuser -d {PGUSER}"; exe (sql, SQL=False)
	sql = f"ALTER USER {PGUSER} WITH PASSWORD '{PGPASSWORD}';"; exe (sql)
	sql = f"CREATE DATABASE {PGDATABASE} OWNER {PGUSER};" ; exe (sql)
	sql = f"GRANT ALL PRIVILEGES ON DATABASE {PGDATABASE} TO {PGUSER};"; exe (sql)

	sql = f"ALTER SCHEMA public OWNER TO {PGUSER};"; exe (sql, DB=PGDATABASE)

#----------------------------------------------------------
#-- Create public schema and grants to user
#----------------------------------------------------------
def createPublicSchemaGrantUser ():
	sql = "CREATE SCHEMA public;"; exe (sql)
	sql = f"ALTER SCHEMA public OWNER TO {PGUSER};"; exe (sql)
	sql = f"GRANT USAGE ON SCHEMA public TO PUBLIC;"; exe (sql)
	sql = f"GRANT CREATE ON SCHEMA public TO {PGUSER}"; exe (sql)

#----------------------------------------------------------
# Remove old migrations and make new migrations
#----------------------------------------------------------
def resetMigrations ():
	appsList = ["app_usuarios", "appdocs", "appdocs_main", 
			    "app_cartaportes", "app_manifiestos", "app_declaraciones"]

	for app in appsList:
		cmm = f"rm {APPPATH}/{app}/migrations/00*.py"
		print (cmm) ; sb.run (cmm, shell=True, env=os.environ)

#----------------------------------------------------------
#-- Run migrations and create superuser
#----------------------------------------------------------
def runMigrationsAndCreateSuperuser ():
	cmm = f"python3 {APPPATH}/manage.py flush --noinput"
	print (cmm) ; sb.run (cmm, shell=True, env=os.environ)

	cmm = f"python3 {APPPATH}/manage.py makemigrations"
	print (cmm) ; sb.run (cmm, shell=True, env=os.environ)

	cmm = f"python3 {APPPATH}/manage.py migrate"
	print (cmm) ; sb.run (cmm, shell=True, env=os.environ)

	#cmm = f"python3 {APPPATH}/manage.py createsuperuser --noinput --username {DJUSER} --email {DJEMAIL} --password {DJPASSWORD}"
	cmm = f"python3 {APPPATH}/manage.py createsuperuser --noinput --username {DJUSER} --email {DJEMAIL}"
	print (cmm) ; sb.run (cmm, shell=True, env=os.environ)

#----------------------------------------------------------
#----------------------------------------------------------
def exe (sql, SQL=True, PROMPT=False, DB=""):
	cmm = ""
	if SQL:
		cmm = f"sudo -u postgres psql {DB} -c \"{sql}\""; 
	else:
		cmm = f"sudo -u postgres {sql}"; 

	print ("-----------------------------------------------")
	print (cmm)
	print ("-----------------------------------------------")
	if not PROMPT:
		sb.run (cmm, shell=True, env=os.environ)
	else:
		if input ("ARE YOU SURE ? (YES/NO): ") == "YES":
			sb.run (cmm, shell=True, env=os.environ)
		else:
			print ("NO ACTION")

#----------------------------------------------------------
#-- Check current user's privileges on the public schema
#----------------------------------------------------------
def checkUserPrivileges ():
	exe (f"SELECT * FROM information_schema.schema_privileges" \
	     f" WHERE grantee = '{PGUSER}' AND schema_name = 'public';")
#----------------------------------------------------------
#-- View Schemas and Their Ownership with Permissions:
#----------------------------------------------------------
def viewSchemasAndOwnership ():
	sql = "SELECT n.nspname AS schema_name, r.rolname AS owner, \
has_schema_privilege(r.rolname, n.nspname, 'USAGE') AS usage, \
has_schema_privilege(r.rolname, n.nspname, 'CREATE') AS create \
FROM pg_catalog.pg_namespace n \
JOIN pg_catalog.pg_roles r ON n.nspowner = r.oid \
ORDER BY schema_name;"
	exe (sql, DB=PGDATABASE)

#----------------------------------------------------------
#-- Check for Owned Objects:
#----------------------------------------------------------
def checkForOwnedObjects ():
	sql = "SELECT n.nspname AS schema_name, r.rolname AS owner \
FROM pg_catalog.pg_namespace n \
JOIN pg_catalog.pg_roles r ON n.nspowner = r.oid \
WHERE r.rolname = 'your_user';"
	exe (sql)

#----------------------------------------------------------
##-- Drop Owned Objects:
#----------------------------------------------------------
def dropOwnedObjects ():
	sql = f"DROP OWNED BY {PGUSER};"
	exe (sql, PROMPT=True)

#----------------------------------------------------------
#-- Show current schemas
#----------------------------------------------------------
def showCurrentSchemas ():
	sql = "SELECT schema_name FROM information_schema.schemata;"
	exe (sql)

#----------------------------------------------------------
#-- Call to main
#----------------------------------------------------------
main ()
