#!/usr/bin/env python3

"""
Populate PG Database with few data only for testing
"""

import os
from traceback import format_exc

import psycopg2
from psycopg2 import sql

# PostgreSQL database connection parameters
# Railway or local based on env vars
db_params= {
	'dbname'  : os.environ.get ('PGDATABASE'),
	'user'	  : os.environ.get ('PGUSER'),
	'password': os.environ.get ('PGPASSWORD'),
	'host'	  : os.environ.get ('PGHOST'),
	'port'	  : os.environ.get ('PGPORT'),
}
#--------------------------------------------------------------------
# Populate clientes, conductores, vehiculos
#--------------------------------------------------------------------
def main ():
	populate_database (clientes_data, "cliente")
	populate_database (conductores_data, "conductor")
	populate_database (vehiculos_data, "vehiculo")


#--------------------------------------------------------------------
def execute_sql_query(query, values=None):
	print (f"+++ DEBUG: query '{query}'")
	print (f"+++ DEBUG: values '{values}'")
	conn = psycopg2.connect(**db_params)
	with conn.cursor() as cursor:
		cursor.execute(query, values)
	conn.commit()
	conn.close()

#--------------------------------------------------------------------	 
#-- Vehiculos
#--------------------------------------------------------------------	 
clientes_data = [
	(1001, '1020', "CHEVROLET S.A", "AV. COLON", "CALI", "COLOMBIA", "NIT"),
	(1002, '1030', "MAZDA S.A.", "AV. RIO", "IBARRA",  "ECUADOR", "RUC"),
	(1003, '1040', "RENAULT S.A.", "AV. CIRC", "QUITO", "ECUADOR", "RUC")
]

conductores_data = [
	(1001, '11030', "LUIS GARRETA", "ECUADOR", "1103011", "1990-12-31", ),
	(1002, '11020', "JAIRO MORA", "COLOMBIA", "1102011", "1990-10-25", 1001 ),
	(1003, '99040', "JAIRO GARRETA", "PERU", "9904011", "1995-05-22",   ),
	(1004, '11040', "LUIS DIAZ", "COLOMBIA", "1104011", "2000-05-22", 1003 )
]

vehiculos_data = [
	(1001, 'PNA12A', "CHEVROLET", "COLOMBIA", "1020", "2000", 1001 ),
	(1002, 'PNB12B', "MAZDA", "ECUADOR", "1030", "1999", 1003 ),
	(1003, 'PNC12C', "RENAULT", "ECUADOR", "1040", "1995", )
]


def populate_database (data, table):
	try:
		for entry in data:
			query = sql.SQL(f"INSERT INTO {table} VALUES {entry};")
				#sql.SQL(', ').join(map(sql.Identifier, entry.keys())),
				#sql.SQL(', ').join(map(sql.Placeholder, entry.values()))
			#)
			execute_sql_query(query)
	except:
		print (">>> Registro existente:", table, data)

if __name__ == '__main__':
	main ()
