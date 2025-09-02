import os, pickle, json, inspect, sys
import pandas as pd
import numpy as np

from django.views import View
from django.conf import settings         # BASE_DIR
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin

# For CSRF protection
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect

from ecuapassdocs.info.ecuapass_extractor import Extractor
from ecuapassdocs.info.ecuapass_utils import Utils 
from ecuapassdocs.utils.models_scripts import Scripts

#----------------------------------------------------------
# Print varname and varvalue
#----------------------------------------------------------
def debug (var_arg, type=None):
	try:
		caller_frame = inspect.getouterframes(inspect.currentframe())[1]
		caller_locals = caller_frame.frame.f_locals
		original_name = [k for k, v in caller_locals.items() if v is var_arg][0]
		print (f"+++ DEBUG:  {original_name}:")
		if not type:
			print (var_arg)
		elif type == "list":
			for v in var_arg:
				print (v)
		elif type == "dict":
			for k,v in var_arg.items ():
				print (f"{k} : {v}")
		print ("---")
	except:
		print ("++ DEBUG :", var_arg)

#----------------------------------------------------------
#----------------------------------------------------------
class CartaportePredictionsView (LoginRequiredMixin, View):
	@method_decorator (csrf_protect)
	def post (self, request, *args, **kwargs):
		print ("\n\n+++ POST : Predictions +++")

		# Retrieve the parameters from POST data
		# Use json.loads() to parse the JSON string from request.body (bytes)
		data             = json.loads (request.body.decode('utf-8'))
		txtId            = data.get ("txtId")

		inputsTextValues = data.get ("inputsTextValues", {})

		inputsValues     = self.getInputsValues (inputsTextValues)

		#predictedValue   = self.doPrediction (txtId, inputsValues) 
		predictedValue   = None

		return JsonResponse ({"predictedValue":predictedValue}, safe=False)

	#----------------------------------------------------------
	#-----------------------------------------c-----------------
	def doPrediction (self, txtId, inputsValues):
		print (f"+++ Doing predictions for txtId:", txtId)

		# Skip fields with prices 
		if txtId in ["txt02","txt14","txt15"] or "13" in txtId or "17" in txtId:
			return None

		modelsDic, encodersDic = self.loadModelsEncoders ()
		encodedValues          = self.getEncodedValues (inputsValues, encodersDic)
		print (f"+++ encodedValues '{encodedValues}'")
		inputs                 = pd.DataFrame ([encodedValues]); 
		print (f"+++ encodedValues::inputs '{inputs}'")
		prdEncValue            = modelsDic [txtId].predict (inputs); 
		print (f"+++ encodedValues::prdEncValue '{prdEncValue}'")
		prdValue               = encodersDic [txtId].inverse_transform (prdEncValue)[0]; 
		print (f"+++ encodedValues::prdValue '{prdValue}'")

		# Subjects: Given the id, get full company info from DB
		if txtId in ["txt03", "txt04"]: # Destinatario, Consignatario
			cliente = Scripts.getClienteInstanceByNumeroId (prdValue)
			prdValue = cliente.toDocFormat () if cliente else ""
		elif txtId in ["txt05"]:        # Notificado
			cliente = Scripts.getClienteInstanceByNombre (prdValue)
			prdValue = cliente.toDocFormat () if cliente else ""
		elif txtId in ["txt06"]:        # Recepcion: add cur date
			prdValue = prdValue + ". " + Utils.getCurrentDate ()
			
		#prdValue         = None if np.isnan (prdValue) else prdValue

		print (f" Input '{txtId}' - Prediction: '{prdValue}'")
		return prdValue

	#----------------------------------------------------------
	# Get values used for prediction from form inputs
	#----------------------------------------------------------
	def getInputsValues (self, inputsTextValues):
		inputsValues = inputsTextValues
		for key,value in inputsTextValues.items():
			if key in ["txt02", "txt03", "txt04"]:   # 03_Destinatario, 04_Consignatario
				value = Extractor.getSubjectId (value)
			elif key in ["txt05"]:                   # 05_Notificado
				value = Extractor.delLow (Extractor.getSubjectNombre (value))
			elif key in ["txt06", "txt07", "txt08"]: # 06_Recepcion,.., 08_Entrega
				resourcesPath = os.path.join (settings.BASE_DIR, "resources", "data_ecuapass")
				ciudad, pais = Extractor.getCiudadPais (value, resourcesPath)
				value = f"{ciudad}-{pais}"
			inputsValues [key] = value
		return inputsValues

	#----------------------------------------------------------
	# encode simple and complex string values to numbers
	#----------------------------------------------------------
	def getEncodedValues (self, inputsValues, encodersDic):
		encodedValues = {}
		for key, value in inputsValues.items ():
			try:
				print ("+++ key : value", key, value)
				encoder = encodersDic [key]
				encodedValues [key] = encoder.transform ([value])[0]
				print ("+++ encodedValues:", encodedValues [key])
			except:
				print (f"+++ No encode value for key:value '{key}':'{value}'")
				encodedValues [key] = None

		return encodedValues

	#----------------------------------------------------------
	# Load the saved models and encoders
	#----------------------------------------------------------
	def loadModelsEncoders (self):
		modelsFile = 'randomforest-cartaporte-models.pkl'
		modelsPath = os.path.join (os.path.dirname(__file__), 'ml_models', modelsFile)

		with open (modelsPath, 'rb') as f:
			models = pickle.load(f)

		encodersFile = 'randomforest-cartaporte-encoders.pkl'
		encodersPath = os.path.join (os.path.dirname(__file__), 'ml_models', encodersFile)
		with open (encodersPath, 'rb') as f:
			encoders = pickle.load(f)

		return models, encoders

