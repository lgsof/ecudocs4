#!/usr/bin/env python3

import os, sys, csv, re, pickle
import pandas as pd
import psycopg2

from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import numpy as np

from sklearn.feature_extraction.text import TfidfVectorizer
#from sklearn.cluster import DBSCAN
import hdbscan

from TextClusterEncoder import TextClusterEncoder

from ecuapassdocs.info.ecuapass_utils import Utils
from ecuapassdocs.info.ecuapass_extractor import Extractor
from ecuapassdocs.info.ecuapass_info_BYZA import Cartaporte_BYZA

def main ():
	start_doc	  = "CO7405"

	# Set db vars
	pg       = readCheckDBVars ()
	filename = "data-byza-cartaportes.csv"
#
#	#-- Step 01: Get data
	getDataFromDB (pg, start_doc, 100, filename)
	
	filename  = renameColumns (filename, "SHORTNAMES")
	filename  = preprocessData (filename)
	filename, encoders = encodeData (filename)
	models = trainModels (filename)

#	models, encoders = loadModelsEncoders ()
	testModels (models, encoders)

	saveModelsEncoders (models, encoders)

#----------------------------------------------------------
# Load the saved models and encoders
#----------------------------------------------------------
def loadModelsEncoders ():
	with open('randomforest-cartaporte-models.pkl', 'rb') as f:
		models = pickle.load(f)

	with open('randomforest-cartaporte-encoders.pkl', 'rb') as f:
		encoders = pickle.load(f)

	return models, encoders

#----------------------------------------------------------
# Save the model and encoder to files
#----------------------------------------------------------
def saveModelsEncoders (models, encoders):
	with open('randomforest-cartaporte-models.pkl', 'wb') as f:
		pickle.dump (models, f)

	with open('randomforest-cartaporte-encoders.pkl', 'wb') as f:
		pickle.dump (encoders, f)

#----------------------------------------------------------
#----------------------------------------------------------
def testModels (models, encoders):
	value     = "891401705-8"
	#value     = "901473190-9"
	#value     = "860001999-7"
	#value      = "890916155-4"
	#value      = "810004621"
	print ("+++ Starting value txt02:", value)
	enc       = encoders ["txt02"]
	encValue  = enc.transform ([value])[0]
	inputsDic = {"txt02":encValue}     

	colnames  = models.keys()
	for name in colnames:
		inputs            = pd.DataFrame ([inputsDic])
		mdl               = models [name]
		prdEncValue       = mdl.predict (inputs)
		enc               = encoders [name]
		prdValue          = enc.inverse_transform (prdEncValue)
		print (f" Column '{name}': '{prdValue}'")

		if name < "txt10":
			inputsDic [name]  = prdEncValue
	
#----------------------------------------------------------
# encode simple and complex string values to numbers
#----------------------------------------------------------
def encodeData (dataFilename):
	df          = pd.read_csv (dataFilename)
	dfe         = pd.DataFrame (columns=df.columns)
	encodersDic = {}
	for name in df.columns:
		#if name == ["12Dsc", "18Dcm", "21Ins", "22Obs"]:  # Complex text
		encoder = LabelEncoder ()   # Default, for simple text
		if name == ["txt12", "txt16", "txt18", "txt21", "txt22"]:  # Complex text
			encoder = TextClusterEncoder ()

		encodersDic [name] = encoder
		dfe [name] = encoder.fit_transform (df [name])		

	outFilename  = dataFilename.split (".")[0] + "-ENC.csv"
	dfe.to_csv (outFilename, na_rep=None, index=False, header=True)
	return outFilename, encodersDic

#----------------------------------------------------------
#-- Create ML models for two set of cartaporte input fields:
#-- Main fields, depending of previous fields
#-- and Minor fields, depending of Main fields
#----------------------------------------------------------
def trainModels (dataFilename):
	df = pd.read_csv (dataFilename)

	colnames = df.columns

	models = {}
	xCols = []
	# Cartaporte main models
	mainColumns = ["txt02","txt03","txt04","txt05","txt06","txt07","txt08","txt09"]
	for i in range (len (mainColumns)-1):
		xCols.append (mainColumns [i])
		yCol = mainColumns [i+1]
		print (f"+++ Creating model y:{yCol} : X:{xCols}")

		X = df [xCols]
		y = df [yCol]
		mdl = RandomForestClassifier ()
		mdl.fit (X, y)
		models [yCol] = mdl
	
	xCols.append (mainColumns [i])

	# Cartaporte minor columns:  Alternate models depending only of fixed values
	minorColumns = ["txt10","txt11","txt12","txt16","txt18","txt21","txt22","txt80","txt81","txt82"]
	for col in minorColumns:
		xCols = mainColumns
		yCol = col
		print (f"+++ Creating model y:{yCol} : X:{xCols}")

		X = df [xCols]
		y = df [yCol]
		mdl = RandomForestClassifier ()
		mdl.fit (X, y)
		models [yCol] = mdl

	return models


#----------------------------------------------------------
# Preprocess data by organizing/joining columns
#----------------------------------------------------------
def preprocessData (dataFilename):
	def removeNumberLowSufix (df):
		def removeNumbers (input_str):
			return re.sub(r'\d+', '', input_str) if isinstance(input_str, str) else input_str

		df ["68"] = df ["68"].apply (removeNumbers)  # 10_Cantidad_Clase_Bultos
		return df.map (Extractor.delLow)     # Remove "||LOW"

	def joinColumns (df):
		df ["30"] = df ["30"] + "-"  + df ["29"]; del df ["29"]   # Ciudad-Pais Recepcion
		df ["33"] = df ["33"] + "-"  + df ["32"]; del df ["32"]   # Ciudad-Pais Embarque
		df ["36"] = df ["36"] + "-"  + df ["35"]; del df ["35"]   # Ciudad-Pais Entrega
		df ["39"] = df ["38"] + ". " + df ["39"]; del df ["38"]   # Condiciones Tranporte-Pago
		df ["49"] = df ["46"] + ": " + df ["49"] + "-" + df ["48"]; del df ["46"]; del df ["48"]   # Ciudad-Pais Mercancia
		return df

	def selectRenameColumns (df):
		selCols = [12,18,23,26,30,33,36,39,68,69,79,49,60,64,65]
		docCols = [ 2, 3, 4, 5, 6, 7, 8, 9,10,11,12,16,18,21,22]
		new_df = pd.DataFrame()
		for selcol, doccol in zip (selCols, docCols):
			selcolname = str (selcol).zfill (2)
			doccolname = "txt" + str (doccol).zfill (2)
			for colname in df.columns:
				if colname.startswith (selcolname):
					new_df [doccolname] = df [selcolname]
					break
		return new_df

	def selRenameCols (df):
		#docNamesList = ["02Rmt","03Dst","04Cns","05Ntf", "06Rcp","07Emb","08Ent","09Cnd", "10Cnt","11Mrc","12Dsc","16Mrc", "18Dcm","21Ins","22Obs"]
		formNamesList = ["02","03","04","05","06","07","08","09","10","11","12","16", "18","21","22"]
		formNamesList = [f"txt{x}" for x in formNamesList]
		docNames = dict (zip (df.columns, formNamesList))
		for k,v in docNames.items():
			print (k,v)
		df = df.rename (columns=docNames)
		return df

	df = pd.read_csv (dataFilename)
	df = removeNumberLowSufix (df)
	df = joinColumns (df)
	df = selectRenameColumns (df)

	outFilename  = dataFilename.split (".")[0] + "-PRP.csv"
	df = df.where (pd.notna(df), '')
	df.to_csv (outFilename, na_rep=None, index=False, header=True)
	return (outFilename)

#----------------------------------------------------------
# Clean data colums 
#----------------------------------------------------------
def cleanData (dataFilename):
	# Select main columns
	# Remove columns with low variance (mostly the same values)
	def filterLowVarianceCols (df):
		threshold = 0.90         # Set a threshold for low variance (e.g., 80%)
		low_variance_cols = [col for col in df.columns if df[col].value_counts(normalize=True).max() > threshold]
		single_value_cols = [col for col in df.columns if df[col].nunique() == 1]
		cols_to_drop = list (set(low_variance_cols + single_value_cols))
		return df.drop (cols_to_drop, axis=1)

	# Filter columns
	df          = pd.read_csv (dataFilename)
#	df          = filterMainCols (df)
	df          = filterLowVarianceCols (df)
	outFilename = dataFilename.split (".")[0] + "-CLN.csv"
	df.to_csv (outFilename, na_rep=None, index=False, header=True)
	return (outFilename)

#----------------------------------------------------------
#-- Rename columns to short names
#----------------------------------------------------------
def renameColumns (dataFilename, type="SHORTNAMES"):
	df = pd.read_csv (dataFilename)

	newColnames = {}
	for i, colname in enumerate (df.columns):
		if type == "SHORTNAMES":
			newColnames [colname] = colname [:2]
			outFilename  = dataFilename.split (".")[0] + "-RNMs.csv"
		else:
			newColnames [colname] = str (i+2).zfill(2)
			outFilename  = dataFilename.split (".")[0] + "-RNMd.csv"

	df = df.rename (columns=newColnames)
#		"12_NroIdRemitente": "12",
#		"18_NroIdDestinatario": "18",
#		"23_NroIdConsignatario":"23",
#		"26_NombreNotificado": "26"})

	df.to_csv (outFilename, na_rep=None, index=False, header=True)
	return outFilename

#----------------------------------------------------------
#-- Export document DB instances to a table
#----------------------------------------------------------
def getDataFromDB (pg, start_doc, limit, dataFilename):
	try:
		# Connect to the PostgreSQL database using environment variables
		conn = psycopg2.connect (dbname=pg ["db"], host= pg ["host"], 
						   port= pg ["port"], user= pg ["user"], password = pg ["pswd"])
		cursor = conn.cursor()

		# Query the database
		query = """ SELECT * FROM cartaporteform WHERE numero <= %s
			        ORDER BY numero LIMIT %s; """
		cursor.execute (query, (start_doc, limit))

		# Fetch all results
		records = cursor.fetchall ()
		# Get column names from cursor.description
		column_names = [desc[0] for desc in cursor.description]		
		print (column_names)

		# Write to the CSV file
		with open (dataFilename, 'w', newline='', encoding='utf-8') as csvfile:
			writer = csv.writer (csvfile, quoting=csv.QUOTE_MINIMAL)

			# Write data rows
			HEADERS_FLAG = True
			for record in records:
				formFields     = dict (zip (column_names, record))
				runningDir     = os.getcwd ()
				ecudocFields   = Utils.getDocFieldsFromFormFields ("CARTAPORTE", formFields)
				cartaporteInfo = Cartaporte_BYZA (None, runningDir, ecudocFields)
				ecuapassFields = cartaporteInfo.extractEcuapassFields (analysisType="PREDICTION")
				keys           = ecuapassFields.keys ()

				# Write the header row (column names)
				if HEADERS_FLAG:
					writer.writerow (keys)
					HEADERS_FLAG = False

				writer.writerow ([ecuapassFields[key] for key in keys])

		return (dataFilename)

		print(f"Data exported to {dataFilename}")

	except Exception as e:
		Utils.printException ("Error obteniendo datos de la BD")

	finally: # Close the database connection
		if conn:
			cursor.close()
			conn.close()

#----------------------------------------------------------
#-- Postgress env vars
#----------------------------------------------------------
def readCheckDBVars ():
	pg = {}
	pg ["user"] = os.environ.get ("PGUSER")
	pg ["pswd"] = os.environ.get ("PGPASSWORD")
	pg ["db"]	= os.environ.get ("PGDATABASE")
	pg ["host"] = os.environ.get ("PGHOST")
	pg ["port"] = os.environ.get ("PGPORT")

	print ("Postgres DB vars:")
	for k,v in pg.items ():
		print (f"\t{k}:{v}")
	print ("")

	#if input ("Desea continuar (yes/no): ")!="yes":
	#	sys.exit (0) 
	return pg

#----------------------------------------------------------
# Example usage
if __name__ == "__main__":
	main ()

