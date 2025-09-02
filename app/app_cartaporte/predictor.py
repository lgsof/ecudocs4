import os, pickle
import pandas as pd
from django.conf import settings
from django.forms.models import model_to_dict
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from ecuapassdocs.info.ecuapass_extractor import Extractor
from app_docs.models_Entidades import Vehiculo, Conductor


modelsDic, encodersDic = None, None

print (f"+++ ...Loading predictor module...'")
#----------------------------------------------------------
# Load the saved models and encoders
#----------------------------------------------------------
def loadModelsEncoders ():
	mlPath = os.path.join (Path (settings.BASE_DIR), "app_cartaporte", "ml_models")
	print (f"+++ mlPath '{mlPath}'")
	modelsPath = os.path.join (mlPath, 'randomforest-cartaporte-models.pkl')
	#modelsPath = os.path.join (os.path.dirname(__file__), 'ml_models', modelsFile)

	with open (modelsPath, 'rb') as f:
		models = pickle.load(f)

	encodersPath = os.path.join (mlPath, 'randomforest-cartaporte-encoders.pkl')
	#encodersPath = os.path.join (os.path.dirname(__file__), 'ml_models', encodersFile)
	with open (encodersPath, 'rb') as f:
		encoders = pickle.load(f)

	return models, encoders

# Load models in the background
def load_models_in_background():
	global modelsDic, encodersDic
	with ThreadPoolExecutor() as executor:
		future = executor.submit(loadModelsEncoders)
		modelsDic, encodersDic = future.result()

# Start the background loading
executor = ThreadPoolExecutor(max_workers=1)
executor.submit(load_models_in_background)

modelsDic, encodersDic = loadModelsEncoders ()
#----------------------------------------------------------
#----------------------------------------------------------
class Predictor:
	def __init__ (self):
		global modelsDic, encodersDic
		#self.modelsDic = apps.get_app_config('app_cartaporte').modelsDic
		#self.encodersDic = apps.get_app_config('app_cartaporte').encodersDic
		self.modelsDic, self.encodersDic = modelsDic, encodersDic

	#----------------------------------------------------------
	# Predicts Manifiesto info given cartaporte form values
	#-----------------------------------------c-----------------
	def predictManifiestoInfo (self, cartaporteForm):
		print (f"+++ Doing predictions for manifiesto:")
		# Get values from form raw text values
		formFields = model_to_dict (cartaporteForm)
		inputsValuesAll  = self.getInputsValues (formFields)

		# Filter to main fields used for prediction	
		cpiMainFields  = ["txt02","txt03","txt04","txt05","txt06","txt07","txt08","txt09"] 
		inputsValues   = {}
		for key in cpiMainFields:
			inputsValues [key] = inputsValuesAll [key]
		
		# Predict value for manifiesto fields ["mtxt06", "mtxt23", "mtxt24"]
		prdPlacaVehiculo = self.doPrediction ("txt80", inputsValues)
		prdLugarCarga    = self.doPrediction ("txt81", inputsValues)
		prdLugarDescarga = self.doPrediction ("txt82", inputsValues)

		# Complete info from predictions
		vehiculoInfo   = self.getVehiculoInfoFromPlaca (prdPlacaVehiculo)
		cargaInfo      = self.getCargaInfo (prdLugarCarga, prdLugarDescarga)

		manifiestoInfo = {}
		manifiestoInfo.update (vehiculoInfo)
		manifiestoInfo.update (cargaInfo)

		return manifiestoInfo

	#----------------------------------------------------------
	# Predicts value for 'txtId' field based on input values 
	#----------------------------------------------------------
	def doPrediction (self, txtId, inputsValues):
		print (f"+++ Doing predictions for txtId:", txtId)

		# Skip fields with prices 
		if txtId in ["txt02","txt14","txt15"] or "13" in txtId or "17" in txtId:
			return None

		#modelsDic, encodersDic = self.loadModelsEncoders ()
		encodedValues          = self.getEncodedValues (inputsValues, self.encodersDic)
		inputs                 = pd.DataFrame ([encodedValues]); 
		prdEncValue            = self.modelsDic [txtId].predict (inputs); 
		prdValue               = self.encodersDic [txtId].inverse_transform (prdEncValue)[0]; 
		return prdValue

	#----------------------------------------------------------
	# encode simple and complex string values to numbers
	#----------------------------------------------------------
	def getEncodedValues (self, inputsValues, encodersDic):
		encodedValues = {}
		for key, value in inputsValues.items ():
			try:
				encoder = encodersDic [key]
				encodedValues [key] = encoder.transform ([value])[0]
			except:
				print (f"+++ No encode value for key:value '{key}':'{value}'")
				encodedValues [key] = None

		return encodedValues

	#----------------------------------------------------------
	# Get values used for prediction from raw text values in form
	#----------------------------------------------------------
	def getInputsValues (self, inputsTextValues):
		inputsValues = inputsTextValues
		for key,value in inputsTextValues.items():
			if key in ["txt02", "txt03", "txt04"]:  # 03_Destinatario, 04_Consignatario
				value = Extractor.getSubjectId (value)
			elif key in ["txt05"]:          # 05_Notificado
				value = Extractor.delLow (Extractor.getSubjectNombre (value))
			elif key in ["txt06", "txt07", "txt08"]:          # 05_Notificado
				resourcesPath = os.path.join (os.getcwd(), "resources", "data_ecuapass")
				value = Extractor.getCiudadPais (value, resourcesPath)
			inputsValues [key] = value
			return inputsValues

	#----------------------------------------------------------
	# Get predic
	#----------------------------------------------------------
	def getVehiculoInfoFromPlaca (self, placa):
		info = {}
		vehiculo = Vehiculo.objects.filter (placa=placa).first()
		if not vehiculo:
			vehiculo = Vehiculo ()     # Create an empty vehiculo

		info ["marcaVehiculo"]  = vehiculo.marca 
		info ["anhoVehiculo"]   = vehiculo.anho
		info ["placaPaisVehiculo"]  = vehiculo.placa 
		info ["chasisVehiculo"] = vehiculo.chasis

		remolque = vehiculo.remolque if vehiculo else None
		info ["marcaRemolque"]  = remolque.marca if remolque else None
		info ["anhoRemolque"]   = remolque.anho if remolque else None
		info ["placaPaisRemolque"]  = remolque.placa if remolque else None
		info ["chasisRemolque"] = remolque.chasis if remolque else None

		conductor = vehiculo.conductor if vehiculo else None
		info ["nombreConductor"]    = conductor.nombre if conductor else None
		info ["documentoConductor"] = conductor.documento if conductor else None
		info ["paisConductor"]      = conductor.pais if conductor else None
		info ["licenciaConductor"]  = conductor.licencia if conductor else None

		info ["nombreAuxiliar"]    = conductor.auxiliar.nombre if conductor and conductor.auxiliar else None
		info ["documentoAuxiliar"] = auxiliar.documento if conductor and conductor.auxiliar else None
		info ["paisAuxiliar"]      = auxiliar.pais if conductor and conductor.auxiliar else None
		info ["licenciaAuxiliar"]  = auxiliar.licencia if conductor and conductor.auxiliar else None

		return info

	#-- Datos sobre la carga
	def getCargaInfo (self, prdLugarCarga, prdLugarDescarga):
		info = {}
		info ["ciudadPaisCarga"]    = prdLugarCarga
		info ["ciudadPaisDescarga"] = prdLugarDescarga
		info ["otroTipoCarga"]      = "X"
		info ["descripcionCarga"]   = "FACIL MANEJO"
		
		return info

#	#----------------------------------------------------------
#	# encode simple and complex string values to numbers
#	#----------------------------------------------------------
#	def encodeData (df):
#		dfe         = pd.DataFrame (columns=df.columns)
#		encodersDic = {}
#		for name in df.columns:
#			#if name == ["12Dsc", "18Dcm", "21Ins", "22Obs"]:  # Complex text
#			encoder = LabelEncoder ()   # Default, for simple text
#			if name == ["txt12", "txt16", "txt18", "txt21", "txt22"]:  # Complex text
#				encoder = TextClusterEncoder ()
#
#			encodersDic [name] = encoder
#			dfe [name] = encoder.fit_transform (df [name])		
#
#		return encodersDic
#
#	#----------------------------------------------------------
#	#-- From Cartaporte form get fields used for predicion (main fields)
#	#----------------------------------------------------------
#	def getPredictionFieldsFromForm  (self, cartaporteForm): 
#		# Get values from form raw text values
#		inputsTextValues = model_to_dict (cartaporteForm)
#		inputsValuesAll  = self.getInputsValues (inputsTextValues)
#
#		# Filter to values used for prediction	
#		cpiMainFields    = ["txt02","txt03","txt04","txt05","txt06","txt07","txt08","txt09"] # Main fields used for prediction 
#		inputsValues = {}
#		for key in cpiMainFields:
#			inputsValues [key] = inputsValuesAll [key]
#		
#		# Predict value for manifiesto fields
#		mciMainFields   = ["mtxt06", "mtxt23", "mtxt24"]
#		predictedValues = [self.doPrediction (txtId, inputValues) for txtId in mciMainFields]
#
#		runningDir     = os.getcwd ()
#		ecudocFields   = Utils.getEcudocFieldsFromFormFields ("CARTAPORTE", formFields)
#		cartaporteInfo = Cartaporte_BYZA (None, runningDir, ecudocFields)
#		ecuapassFields = cartaporteInfo.extractEcuapassFields (analysisType="PREDICTION")
#
#		# Process ecuapassFields
#		df       = pd.DataFrame (ecuapassFields)
#		df       = self.renameColumns (df)
#		df       = self.preprocessData (df)
#		encoders = self.encodeData (df)
#
#
#		cpiMainFields  = ["txt03","txt04","txt05","txt06","txt07","txt08","txt09"] # Main fields used for prediction 
#		inputsValues = {}
#		for key in cpiMainFields:
#			inputsValues [key] = 
#		
#
#	#----------------------------------------------------------
#	# Preprocess data by organizing/joining columns
#	#----------------------------------------------------------
#	def preprocessData (df):
#		def removeNumberLowSufix (df):
#			def removeNumbers (input_str):
#				return re.sub(r'\d+', '', input_str) if isinstance(input_str, str) else input_str
#
#			df ["68"] = df ["68"].apply (removeNumbers)  # 10_Cantidad_Clase_Bultos
#			return df.map (Extractor.delLow)     # Remove "||LOW"
#
#		def joinColumns (df):
#			df ["30"] = df ["30"] + "-"  + df ["29"]; del df ["29"]   # Ciudad-Pais Recepcion
#			df ["33"] = df ["33"] + "-"  + df ["32"]; del df ["32"]   # Ciudad-Pais Embarque
#			df ["36"] = df ["36"] + "-"  + df ["35"]; del df ["35"]   # Ciudad-Pais Entrega
#			df ["39"] = df ["38"] + ". " + df ["39"]; del df ["38"]   # Condiciones Tranporte-Pago
#			df ["49"] = df ["46"] + ": " + df ["49"] + "-" + df ["48"]; del df ["46"]; del df ["48"]   # Ciudad-Pais Mercancia
#			return df
#
#		def selectRenameColumns (df):
#			selCols = [12,18,23,26,30,33,36,39,68,69,79,49,60,64,65]
#			docCols = [ 2, 3, 4, 5, 6, 7, 8, 9,10,11,12,16,18,21,22]
#			new_df = pd.DataFrame()
#			for selcol, doccol in zip (selCols, docCols):
#				selcolname = str (selcol).zfill (2)
#				doccolname = "txt" + str (doccol).zfill (2)
#				for colname in df.columns:
#					if colname.startswith (selcolname):
#						new_df [doccolname] = df [selcolname]
#						break
#			return new_df
#
#		df = removeNumberLowSufix (df)
#		df = joinColumns (df)
#		df = selectRenameColumns (df)
#		return (df)
#
#
#	def selRenameCols (df):
#		#docNamesList = ["02Rmt","03Dst","04Cns","05Ntf", "06Rcp","07Emb","08Ent","09Cnd", "10Cnt","11Mrc","12Dsc","16Mrc", "18Dcm","21Ins","22Obs"]
#		formNamesList = ["02","03","04","05","06","07","08","09","10","11","12","16", "18","21","22"]
#		formNamesList = [f"txt{x}" for x in formNamesList]
#		docNames = dict (zip (df.columns, formNamesList))
#		for k,v in docNames.items():
#			print (k,v)
#		df = df.rename (columns=docNames)
#		return df
#
#	df = pd.read_csv (dataFilename)
#	df = removeNumberLowSufix (df)
#	df = joinColumns (df)
#	df = selectRenameColumns (df)
#
#	outFilename  = dataFilename.split (".")[0] + "-PRP.csv"
#	df = df.where (pd.notna(df), '')
#	df.to_csv (outFilename, na_rep=None, index=False, header=True)
#	return (outFilename)
#
#	#----------------------------------------------------------
#	#-- Rename columns to short names
#	#----------------------------------------------------------
#	def renameColumns (self, df, type="SHORTNAMES"):
#		newColnames = {}
#		for i, colname in enumerate (df.columns):
#			if type == "SHORTNAMES":
#				newColnames [colname] = colname [:2]
#			else:
#				newColnames [colname] = str (i+2).zfill(2)
#
#		df = df.rename (columns=newColnames)
#		return df
#
#
#
#	#-- Get complete document info for 'txtId' field from predicted values
#	def getDocInfoFromPredictedValue (self, txtId, prdValue):
#		if txtId in ["txt03", "txt04"]: # Destinatario, Consignatario
#			cliente = Scripts.getClienteInstanceByNumeroId (prdValue)
#			prdValue = cliente.toDocFormat () if cliente else ""
#		elif txtId in ["txt05"]:        # Notificado
#			cliente = Scripts.getClienteInstanceByNombre (prdValue)
#			prdValue = cliente.toDocFormat () if cliente else ""
#		elif txtId in ["txt06"]:        # Recepcion: add cur date
#			prdValue = prdValue + ". " + Utils.getCurrentDate ()
#			
#		#prdValue         = None if np.isnan (prdValue) else prdValue
#
#		print (f" Input '{txtId}' - Prediction: '{prdValue}'")
#		return prdValue
#

