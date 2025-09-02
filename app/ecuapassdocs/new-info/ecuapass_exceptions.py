
from info.ecuapass_utils import Utils

import sys, traceback
from datetime import datetime

#-----------------------------------------------------------
# Custom Ecupasssdocs exceptions
#-----------------------------------------------------------
class EcudocException (Exception):
	def __init__ (self, message=None):
		Utils.printException (message)

#---------------- Bot Exceptions --------------------
class EcuerrorImageNotFound (EcudocException):
	pass

class EcudocBotStopException (EcudocException):
	pass

class EcudocBotCartaporteNotFound (EcudocException):
	pass
#---------------------------------------------------

class EcudocPdfCoordinatesError (EcudocException):
	def __init__ (self, message):
		super().__init__(message)

class EcudocWebException (EcudocException):
	pass

class EcuerrorNetworkConnection (EcudocException):
	pass

class EcudocDocumentNotFoundException (EcudocException):
	pass

class EcudocConnectionNotOpenException (EcudocException):
	defaultMessage = "No se pudo conectar a CODEBINI"

	def __init__(self, message=None):
		self.message = message or self.defaultMessage

class EcudocEcuapassException (EcudocException):
	pass

class EcudocExtractionException (EcudocException):
	pass

class EcudocDocumentNotValidException (EcudocException):
	pass

class IllegalEmpresaException (EcudocException):
	pass

class EcudocCloudException (EcudocException):
	pass

class EcudocDocTypeException (EcudocException):
	pass

class EcudocSettingsError (EcudocException):
	pass

class EcudocTypingError (EcudocException):
	pass

class EcudocCheckError (EcudocException):
	pass

