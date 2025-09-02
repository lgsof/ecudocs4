#!/usr/bin/env python3

"""
Scrips for handling re-create DB, USER, SCHEMA, and MIGRATIONS
"""
import os, sys
import subprocess as sb


APPPATH    = "/home/lg/BIO/ecuapassdocs/EcuapassDocs/EcuapassDocs-dev"
DJUSER     = "admin"
DJPASSWORD = "admin"
DJEMAIL    = f"{DJUSER}@gmail.com"
DJPAIS     = "TODOS"

# Postgress env vars
print ("Postgres DB settings:")
PGUSER     = os.environ.get ("PGUSER")     ; print ("\t",PGUSER)
PGPASSWORD = os.environ.get ("PGPASSWORD") ; print ("\t",PGPASSWORD)
PGDATABASE = os.environ.get ("PGDATABASE") ; print ("\t",PGDATABASE)
PGHOST     = os.environ.get ("PGHOST")     ; print ("\t",PGHOST)
PGPORT     = os.environ.get ("PGPORT")     ; print ("\t",PGPORT)
print ("")

if input ("Desea continuar (yes/no): ")!="yes":
	sys.exit (0)

def main ():
	#dropUserAndDatabase ()
	#createDBUserAndDatabase ()
	#resetMigrations ()
	runMigrationsSuperuserExtensions ()
	#runCollectStatics ()

	#---
	#createPublicSchemaGrantUser ()
	#checkUserPrivileges ()
	#viewSchemasAndOwnership ()
	#checkForOwnedObjects ()
	#dropOwnedObjects ()

#----------------------------------------------------------
#-- Drop current DB user and database
#----------------------------------------------------------
def dropUserAndDatabase ():
	if input (f"Remove USER: {PGUSER} and DATABASE: {PGDATABASE} : (yes/no) ") == "yes":
		exe (f"drop database {PGDATABASE};")
		#exe (f"ALTER SCHEMA public OWNER TO postgres;")
		exe (f"DROP OWNED BY {PGUSER};")
		exe (f"drop user $PGUSER;")

#----------------------------------------------------------
#-- Create DB user, DB, and grant permissions
#----------------------------------------------------------
def createDBUserAndDatabase ():
	sql = f"createuser -d {PGUSER}"; exe (sql, SQL=False)
	sql = f"ALTER USER {PGUSER} WITH PASSWORD '{PGPASSWORD}';"; exe (sql)
	sql = f"CREATE DATABASE {PGDATABASE} OWNER {PGUSER};" ; exe (sql)
	sql = f"GRANT ALL PRIVILEGES ON DATABASE {PGDATABASE} TO {PGUSER};"; exe (sql)
	sql = f"ALTER SCHEMA public OWNER TO {PGUSER};"; exe (sql, DB=PGDATABASE)

#----------------------------------------------------------
# Remove old migrations and make new migrations
#----------------------------------------------------------
def resetMigrations ():
	appsList = ["app_usuarios", "app_docs", 
			    "app_cartaporte", "app_manifiesto", "app_declaracion"]

	for app in appsList:
		cmm = f"rm {APPPATH}/{app}/migrations/00*.py"
		print (cmm) ; sb.run (cmm, shell=True, env=os.environ)

#----------------------------------------------------------
#-- Create public schema and grants to user
#----------------------------------------------------------
def createPublicSchemaGrantUser ():
	sql = "CREATE SCHEMA public;"; exe (sql)
	sql = f"ALTER SCHEMA public OWNER TO {PGUSER};"; exe (sql)
	sql = f"GRANT USAGE ON SCHEMA public TO PUBLIC;"; exe (sql)
	sql = f"GRANT CREATE ON SCHEMA public TO {PGUSER}"; exe (sql)

#----------------------------------------------------------
#-- Run migrations and create superuser
#----------------------------------------------------------
def runMigrationsSuperuserExtensions ():
	print (f"+++ DJUSER: '{DJUSER}'")
	cmm = f"python3 {APPPATH}/manage.py flush --noinput"
	print (cmm) ; sb.run (cmm, shell=True, env=os.environ)

	cmm = f"python3 {APPPATH}/manage.py makemigrations"
	print (cmm) ; sb.run (cmm, shell=True, env=os.environ)

	cmm = f"python3 {APPPATH}/manage.py migrate"
	print (cmm) ; sb.run (cmm, shell=True, env=os.environ)

	#cmm = f"python3 {APPPATH}/manage.py createsuperuser --noinput --username {DJUSER} --email {DJEMAIL} --password {DJPASSWORD}"

	# Create admin user and set pais="TODOS"
	cmm = f"python3 {APPPATH}/manage.py createsuperuser --username {DJUSER} --email {DJEMAIL}"
	print (cmm) ; sb.run (cmm, shell=True, env=os.environ)

	sql = f"UPDATE usuario SET pais='TODOS' WHERE username='admin';"; exe (sql, DB=PGDATABASE)

	# Create extension for advanced text searches
	sql = f"CREATE EXTENSION IF NOT EXISTS pg_trgm;"; exe (sql, DB=PGDATABASE)
#----------------------------------------------------------
# Collect migrations
#----------------------------------------------------------
def runCollectStatics ():
	cmm = f"python3 {APPPATH}/manage.py collectstatic"
	print (cmm) ; sb.run (cmm, shell=True, env=os.environ)


#----------------------------------------------------------
#----------------------------------------------------------
def exe (sql, SQL=True, PROMPT=False, DB=""):
	cmm = ""
	if SQL:
		#cmm = f"sudo -u postgres psql {DB} -c \"{sql}\""; 
		cmm = f"psql {DB} -c \"{sql}\""; 
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
# For changing DB user password as user 'postgres'
#----------------------------------------------------------
def changePasswordDBUser (dbUser, newPassword):
	sql = f"ALTER USER {dbUser} WITH PASSWORD '{newPassword}';"
	exe (sql)

#----------------------------------------------------------
#-- Call to main
#----------------------------------------------------------
main ()
