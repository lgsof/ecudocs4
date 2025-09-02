#!/usr/bin/env python3

"""
Scrips for handling re-create EcuapassDocs as
recreate DB, USER, data, and MIGRATIONS
"""
import os, sys
import subprocess as sb
import traceback # format_exc
import psycopg2
from psycopg2 import sql

import django
from django.contrib.auth.hashers import make_password

#----------- GLOBALS ------------------------------------------------------------------------
PROJECT_ROOT = "/ecuapp/ecudocs4/app"
APPPATH      = PROJECT_ROOT

#-- Postgres vars
print ("Postgres DB settings:")
PGUSER     = os.environ.get ("PGUSER")     ; print ("\t",PGUSER)
PGPASSWORD = os.environ.get ("PGPASSWORD") ; print ("\t",PGPASSWORD)
PGDATABASE = os.environ.get ("PGDATABASE") ; print ("\t",PGDATABASE)
PGHOST     = os.environ.get ("PGHOST")     ; print ("\t",PGHOST)
PGPORT     = os.environ.get ("PGPORT")     ; print ("\t",PGPORT)
DB_PARAMS  = {'dbname':PGDATABASE, 'user':PGUSER, 'password':PGPASSWORD, 'host':PGHOST,'port': PGPORT}

#-- Django superuser
DJUSER  = os.environ.get ("DJANGO_SUPERUSER_USERNAME")  ; print ("\t",DJUSER)
DJPASSWORD  = os.environ.get ("DJANGO_SUPERUSER_PASSWORD")  ; print ("\t",DJPASSWORD)
DJEMAIL  = os.environ.get ("DJANGO_SUPERUSER_EMAIL")  ; print ("\t",DJEMAIL)

#---------------------------------------------------------------------------------------------
# Main
#---------------------------------------------------------------------------------------------
def main ():
	initSettings ()
#	dropUserAndDatabase ()
#	createDBUserAndDatabase ()
#	resetMigrations ()
#	runMigrations ()
#	createDocsAdminUser ()
#	runCollectStatics ()
	populateDBWithTestData ()

	#---
	#createPublicSchemaGrantUser ()
	#checkUserPrivileges ()
	#viewSchemasAndOwnership ()
	#checkForOwnedObjects ()
	#dropOwnedObjects ()

#----------------------------------------------------------
# Set up Django environment
#----------------------------------------------------------
def initSettings ():
	sys.path.insert (0, PROJECT_ROOT)  # Add project root to Python path
	os.environ.setdefault ("DJANGO_SETTINGS_MODULE", "app_main.settings") #appdocs_main") #/settings")
	django.setup ()
	#----------------------------------------------------------

#	# Postgress env vars
#	print ("Postgres DB settings:")
#	PGUSER     = os.environ.get ("PGUSER")     ; print ("\t",PGUSER)
#	PGPASSWORD = os.environ.get ("PGPASSWORD") ; print ("\t",PGPASSWORD)
#	PGDATABASE = os.environ.get ("PGDATABASE") ; print ("\t",PGDATABASE)
#	PGHOST     = os.environ.get ("PGHOST")     ; print ("\t",PGHOST)
#	PGPORT     = os.environ.get ("PGPORT")     ; print ("\t",PGPORT)
#
#	# Var for execute sql using DJango API
#	DB_PARAMS= {'dbname':PGDATABASE, 'user':PGUSER, 'password':PGPASSWORD, 'host':PGHOST,'port': PGPORT}
#	print ("")
#
#	if input ("Desea continuar (*yes/no): ")=="no":
#		sys.exit (0)


#----------------------------------------------------------
#-- Drop current DB user and database
#----------------------------------------------------------
def dropUserAndDatabase ():
	if input (f"Remove USER: {PGUSER} and DATABASE: {PGDATABASE} : (yes/no) ") == "yes":
		exe (f"drop database IF EXISTS {PGDATABASE};", DB='postgres')
		exe (f"drop user IF EXISTS $PGUSER;", SUPER=True)

#----------------------------------------------------------
#-- Create DB user, DB, and grant permissions
# Create PostgreSQL role and database
#----------------------------------------------------------
def createDBUserAndDatabase ():
	sql = f"createuser -d {PGUSER}"; exe (sql, SQL=False)
	sql = f"ALTER USER {PGUSER} WITH PASSWORD '{PGPASSWORD}';"; exe (sql, SUPER=True)
	sql = f"CREATE DATABASE {PGDATABASE} OWNER {PGUSER};" ; exe (sql, SUPER=True)
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
#-- Run migrations and create superuser
#----------------------------------------------------------
def runMigrations ():
	cmm = f"python3 {APPPATH}/manage.py flush --noinput"
	print (cmm) ; sb.run (cmm, shell=True, env=os.environ)

	cmm = f"python3 {APPPATH}/manage.py makemigrations"
	print (cmm) ; sb.run (cmm, shell=True, env=os.environ)

	cmm = f"python3 {APPPATH}/manage.py migrate"
	print (cmm) ; sb.run (cmm, shell=True, env=os.environ)

	#cmm = f"python3 {APPPATH}/manage.py createsuperuser --noinput --username {DJUSER} --email {DJEMAIL} --password {DJPASSWORD}"

#----------------------------------------------------------
# Create admin user and set pais="TODOS"
#----------------------------------------------------------
def createDocsAdminUser ():
	print (f"+++ DJUSER '{DJUSER}'")
	cmm = f"python3 {APPPATH}/manage.py createsuperuser --noinput"
	print (cmm) ; sb.run (cmm, shell=True, env=os.environ)

	sql = f"UPDATE usuario SET pais='TODOS' WHERE username='admin';"; exe (sql, DB=PGDATABASE)

	# Create extension for advanced text searches
	sql = f"CREATE EXTENSION IF NOT EXISTS pg_trgm;"; exe (sql, DB=PGDATABASE)
#----------------------------------------------------------
# Collect migrations
#----------------------------------------------------------
def runCollectStatics ():
	cmm = f"python3 {APPPATH}/manage.py collectstatic --noinput"
	print (cmm) ; sb.run (cmm, shell=True, env=os.environ)


#----------------------------------------------------------
# Populate DB with Test Data (clientes, conductores, vehiculos)
#----------------------------------------------------------
def populateDBWithTestData ():
	clientes_data = [
		(1001, '1020', "CHEVROLET S.A", "AV. COLON", "CALI", "COLOMBIA", "NIT"),
		(1002, '1030', "MAZDA S.A.", "AV. RIO", "IBARRA",  "ECUADOR", "RUC"),
		(1003, '1040', "RENAULT S.A.", "AV. CIRC", "QUITO", "ECUADOR", "RUC") ]

	conductores_data = [
		(1001, '11030', "LUIS GARRETA", "ECUADOR", "1103011", "1990-12-31", ),
		(1002, '11020', "JAIRO MORA", "COLOMBIA", "1102011", "1990-10-25", 1001 ),
		(1003, '99040', "JAIRO GARRETA", "PERU", "9904011", "1995-05-22",   ),
		(1004, '11040', "LUIS DIAZ", "COLOMBIA", "1104011", "2000-05-22", 1003 ) ]

	vehiculos_data = [
		(1001, 'PNA12A', "CHEVROLET", "COLOMBIA", "1020", "2000", 1001 ),
		(1002, 'PNB12B', "MAZDA", "ECUADOR", "1030", "1999", 1003 ),
		(1003, 'PNC12C', "RENAULT", "ECUADOR", "1040", "1995", ) ]
	#------------------------------------------------------------------------
	def populate_database (data, table):
		try:
			for entry in data:
				query = sql.SQL (f"INSERT INTO {table} VALUES {entry};")
				execute_sql_query(query)
		except:
			print (">>> Exception en:", table, data)
			print (traceback.format_exc())

	def populate_empresas ():
		from app_usuarios.models import Empresa
		Empresa.objects.create (nickname="byza", nombre="GRUPO BYZA")

	def populate_usuarios ():
		from app_usuarios.models import Usuario
		Usuario.objects.create (username="lg", password=make_password ('lge'), email="lg@gmail.com",
						  pais="COLOMBIA", perfil="funcionario")
	
	#------------------------------------------------------------------------
	populate_empresas ()
	populate_usuarios ()
	populate_database (clientes_data, "cliente")
	populate_database (conductores_data, "conductor")
	populate_database (vehiculos_data, "vehiculo")

#----------------------------------------------------------
# Execute query from linux shell
#----------------------------------------------------------
def exe (sql, SQL=True, SUPER=False, PROMPT=False, DB=""):
	cmm = ""
	if not SQL:
		cmm = f"sudo -u postgres {sql}"; 
	elif not SUPER:
		cmm = f"psql {DB} -c \"{sql}\""; 
	else:
		cmm = f"sudo -u postgres psql {DB} -c \"{sql}\""; 

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

#--------------------------------------------------------------------
# Execute query from DJango API
#--------------------------------------------------------------------
def execute_sql_query (query, values=None):
	print (f"+++ DEBUG: query '{query}'")
	print (f"+++ DEBUG: values '{values}'")
	conn = psycopg2.connect(**DB_PARAMS)
	with conn.cursor() as cursor:
		cursor.execute(query, values)
	conn.commit()
	conn.close()

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
#-- Create public schema and grants to user
#----------------------------------------------------------
def createPublicSchemaGrantUser ():
	sql = "CREATE SCHEMA public;"; exe (sql)
	sql = f"ALTER SCHEMA public OWNER TO {PGUSER};"; exe (sql)
	sql = f"GRANT USAGE ON SCHEMA public TO PUBLIC;"; exe (sql)
	sql = f"GRANT CREATE ON SCHEMA public TO {PGUSER}"; exe (sql)


#----------------------------------------------------------
#-- Call to main
#----------------------------------------------------------
main ()
