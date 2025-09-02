## 1. Create realway project in the web (https://railway.app/)

## 2. Add a Postgres service in the web

## 3. Login to Railway and link to project using railway CLI: 
    # 3.1 railway login
    # 3.2 railway link : environment (production), project (ecuapassdocs), service (Postgres-byza)
ECUAPASSDOCS_ID=d44a0b40-8164-498c-9b08-282dbcfd589f
railway link --environment production $ECUAPASSDOCS_ID "Postgres-byza"    

## 4. Get Railway vars:
railway variables --json > dbvars-byza-railway.json

## 5. Create and source Postgres DB variables from Railway vars:
dbvars-createupdate.py --createFromJson dbvars-byza-railway.json > dbvars-byza-railway-ORG.sh
source dbvars-byza-railway-ORG.sh
envpg

## 6. Create database, user, and GRANT privileges
db="ecuapassdocsdb"
usr="postgres"
pwd="postgres2024"

psql -c "CREATE DATABASE $db WITH OWNER='$usr';"
psql -c "GRANT ALL PRIVILEGES ON DATABASE $db TO $usr;"
psql -c "ALTER USER postgres WITH PASSWORD '$pwd';"

## 7. Update Railway PG variables to current DB settings:
dbvars-createupdate.py --updateVarFile dbvars-byza-railway-ORG.sh PGDATABASE=$db > dbvars-byza-railway.sh
dbvars-createupdate.py --updateVarFile dbvars-byza-railway-ORG.sh PGPASSWORD=$pwd > dbvars-byza-railway.sh

## 8. Source new PG variables
source dbvars-byza-railway.sh
envpg

## Change (manually) variables values on the web: postgress service:
    # set PGDATABASE : "ecupassdocsdb"
    # set PGUSER     : "postgres"
    # set PGPASSWORD : "postgresA."
    # set PGHOST     : public domain host (see Variables)
    # set PGPORT     : public domain port (see Variables)
