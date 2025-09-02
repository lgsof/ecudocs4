
"""
Globals variables used in all the app
"""

class Globals:
	empresa           = None
	version           = None
	APP_TYPE          = None                       # EBOT_APP or EDOCS_APP
	RUNNING_DIR       = None                       # Dir where app is running
	x,y,width,height  = None, None, None, None     # Coordinates Stop Transmission Button

	@classmethod
	def init (cls, empresa, version, APP_TYPE, RUNNING_DIR):
		cls.empresa     = empresa
		cls.version     = version
		cls.APP_TYPE    = APP_TYPE
		cls.RUNNING_DIR = RUNNING_DIR

