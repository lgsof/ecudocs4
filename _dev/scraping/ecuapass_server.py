#!/usr/bin/env python3

VERSION="0.930"
"""
LOG: 
Jul/19 : 0.930 : Binary settings. Admin settings. Azure synchronous Feedback.
Jul/08 : 0.921 : BOT4: Modified to work with PERU for NTA
Jul/04 : 0.920 : BOT4: Working bot control panel with messages and speed options
Jun/26 : 0.913 : BOT3: Added sleeps
Jun/21 : 0.912 : V3. BOT,INFO: Modified to work with LOGITRANS
Jun/19 : 0.911 : V3. Runs webdriver first, then flask server
Jun/14 : 0.910 : V3. Runs flask and webdriver servers
Jun/13 : 0.903 : Fixed return value for responding to Java.
Jun/06 : 0.900 : Redesigned as three independent process: GUI, Server, webdrive
May/16 : 0.860 : Improved Codebin conection (back) and error handling.
"""

import os, sys, time
import multiprocessing as mp

# Threads
from threading import Thread 
import queue

# For server
from flask import Flask, make_response
from flask import request as flask_request 
from werkzeug.serving import make_server

# For ecuapassdocs functions
from ecuapassdocs.info.ecuapass_utils import Utils

# Codebin, Ecuapassdocs Bot
from bot_codebin import CodebinBot
from bot_codebin import startCodebinBot
from bot_ecuapassdocs import startEcuapassdocsBot

# doc, document bots
from ecuapass_doc import EcuDoc
from ecuapass_bot import EcuBot
from ecuapass_bot_cartaporte import EcuBotCartaporte
from ecuapass_bot_manifiesto import EcuBotManifiesto
from ecuapass_exceptions import EcudocBotStopException, EcudocEcuapassException
from ecuapass_feedback import EcuFeedback
from ecuapass_settings import EcuSettings

# Driver for web interaction
driver = None
def main ():
	args = sys.argv 
	if len (args) > 1:
		portNumber = args [1]
		EcuServer.start (portNumber)
	else:
		result = EcuServer.run_server_forever (None)
		return (result)

#-----------------------------------------------------------
# Ecuapass server: listen GUI messages and run processes
#-----------------------------------------------------------
class FlaskServer (Flask):
	def __init__(self, result_queue):
		super().__init__(__name__)
		self.queue = result_queue
	def getWebdriver (self):
		#self.webdriver = self.queue.get () 
		#self.webdriver = self.queue [0]
		self.webdriver = CodebinBot.loadWebdriver ()
		return self.webdriver
	def stopWebdriver (self):
		Utils.printx ("+++ Deteniendo app webdriver:")
		if not hasattr (CodebinBot, "webdriver"):
			return
		if CodebinBot.webdriver:
			print ("+++ Cerrando app webdriver:", CodebinBot.webdriver)
			CodebinBot.webdriver.quit ()

#-----------------------------------------------------------
# Global vars
#-----------------------------------------------------------
result_queue = list ()   # To put/get webdriver
stdin_list   = list ()   # To put/get java GUI stdin and used by python Server
app = FlaskServer (result_queue)

def message (response_text):
	response = make_response(response_text)
	response.headers['Content-Type'] = 'text/plain; charset=utf-8'
	return response

#-----------------------------------------------------------
#-----------------------------------------------------------
class EcuServer:
	#-- Start the server with a port number
	def run_server_forever (portNumber):
		Utils.printx ("+++ Cargando servidores ...")
		try:
			#-- DEBUG: ommited webdriver load
			webdriver  = CodebinBot.loadWebdriver ()
			#webdriverProcess = Thread (target=CodebinBot.loadWebdriver).start ()

			portNumber = EcuServer.getPortNumber (portNumber)
			server     = make_server('127.0.0.1', portNumber, app)

			Utils.printx (f">>>>>>>>>>>>>>>> Server version: {VERSION} <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
			Utils.printx (f">>>>>>>>>>>>>>>> Server is running on port::{portNumber}::<<<<<<<<<<<<<<<<<<")
			server.serve_forever()
		except SystemExit:
			print ("-------------------------- Server Exit -------------------------------")
		except WebDriverException as e:
			Utils.printx ("ERROR: Intente nuevamente. Problemas conectandose con CODEBIN")
			return (Utils.printx ("Finalizando servidor Ecuapass"))
		return (Utils.printx ("--- Server Exit ---"))

	#-- Start server searching a port number from file
	def start ():
		portNumber  = EcuServer.getPortNumber ()
		run_server_forever (porNumber)

	#----------------------------------------------------------------
	# Listen for remote calls from Java GUI
	#----------------------------------------------------------------
	@app.route('/start_processing', methods=['GET', 'POST'])
	def start_processing ():
		try:
			Utils.printx ("-------------------- Iniciando Procesamiento -------------------------")
			#webdriver = None
			webdriver = app.getWebdriver ()

			# Get the file name from the request
			service = flask_request.json ['service']
			param1   = flask_request.json ['param1']
			param2   = flask_request.json ['param2']
			param3   = flask_request.json ['param3']

			Utils.printx ("Servicio  : ", service, flush=True)
			Utils.printx ("Parametro 1    : ", param1, flush=True)
			Utils.printx ("Parametro 2    : ", param2, flush=True)
			Utils.printx ("Parametro 3    : ", param3, flush=True)

			# Call your existing script's function to process the file
			result = None
			if (service == "doc_processing"):
				result = EcuDoc.analyzeDocument (docFilepath=param1, runningDir=param2)

			elif (service == "bot_activate_window"):
				result = EcuServer.botActivateWindow (jsonFilepath=param1, runningDir=param2)

			elif (service == "bot_processing"):
				result = EcuServer.botProcessing (ecuFieldsFilepath=param1, runningDir=param2, speedOption=param3)

			elif (service == "codebin_transmit"):
				result = EcuServer.codebin_transmit (workingDir=param1, codebinFieldsFile=param2)

			elif (service == "ecuapassdocs_transmit"):
				result = EcuServer.ecuapassdocs_transmit (workingDir=param1, ecuapassdocsFieldsFile=param2)

			elif (service == "open_ecuapassdocs_URL"):
				EcuServer.openEcuapassdocsURL (url=param1)

			elif (service == "stop_server"):
				Utils.printx ("...Attending 'stop_server'...") 
				EcuServer.stop_server (runningDir=param1)

			elif (service == "send_feedback"):
				EcuFeedback.sendFeedback (zipFilepath=param1, docFilepath=param2)
				result = "true"

			elif (service == "is_running"):
				result = "true"

			else:
				print (f"Servicio '{service}' no existe")
				result = f">>> Servicio '{service}' no disponible."

			return result

		except EcudocBotStopException as ex:
			return message ("BOTERROR: Digitación interrumpida")

		except EcudocEcuapassException as ex:
			return message ("BOTERROR: " + str(ex))

		except Exception as ex:
			Utils.printException (ex)
			return f"BOTERROR: No se pudo digitar documento"

	#----------------------------------------------------------------
	# Stop server
	#----------------------------------------------------------------
	def stop_server (runningDir):
		print ("Finalizando servidor...")
		print ("...Finalizando CODEBIN")
		app.stopWebdriver ()
		sys.exit (0)

	#----------------------------------------------------------------
	#----------------------------------------------------------------
	#----------------------------------------------------------------
	#----------------------------------------------------------------
	#----------------------------------------------------------------
	# Open Ecuapassdocs URL in Chrome browser
	#----------------------------------------------------------------
	#----------------------------------------------------------------
	#----------------------------------------------------------------
	#----------------------------------------------------------------
	#----------------------------------------------------------------
	def openEcuapassdocsURL (url):
		import pyautogui as py

		windows = py.getAllWindows ()
		Utils.printx (">> Todas las ventanas:", [x.title for x in windows])
		for win in windows:
			if "EcuapassDocs" in win.title and "Google" in win.title:
				win.minimize()
				win.restore (); py.sleep (1)
				return

		global driver
		if driver:
			driver.quit ()
		print (">> Inicializando webdriver...")
		driver = selenium.webdriver.Chrome()
		driver.get (url)

		#Utils.printx (f">> Abriendo sitio web de EcuapassDocs: '{url}'")
		#driver.execute_script("window.open('" + url + "','_blank');")

#		# Check if the URL is already open in another window
#		url_open = False
#		Utils.printx (f">> Buscando una ventana abierta de EcuapassDocs : '{url}'")
#		for handle in driver.window_handles:
#			driver.switch_to.window (handle)
#			print (f">>>> Ventana : '{driver.current_url}'")
#			current_url = driver.current_url
#			if url == current_url:
#				url_open = True
#				break
#
#
#		# Optionally, switch to the last opened window
#		driver.switch_to.window(driver.window_handles[-1])
		
		
	#----------------------------------------------------------------
	#-- Execute bot according to the document type
	#-- Doctype is in the first prefix of the ecuFieldsFilepath
	#----------------------------------------------------------------
	def botProcessing (ecuFieldsFilepath, runningDir, speedOption):
		docType = EcuServer.getDoctypeFromFilename (ecuFieldsFilepath)
		message = ""
		if docType == "CARTAPORTE":
			bot = EcuBotCartaporte (ecuFieldsFilepath, runningDir, speedOption)
		elif docType == "MANIFIESTO":
			bot = EcuBotManifiesto (ecuFieldsFilepath, runningDir, speedOption)
		else:
			message = Utils.printx ("ERROR: Tipo de documento desconocido: '{filename}'")

		bot.initSettings ()
		bot.start ()
		message = Utils.printx (f"MENSAJE: Documento digitado")
		return message

	#----------------------------------------------------------------
	# Activate ECUAPASS window
	#----------------------------------------------------------------
	def botActivateWindow (jsonFilepath, runningDir):
		Utils.printx ("+++ SERVER: Activando ventana del ECUAPASS")

		bot = EcuBot (jsonFilepath, runningDir, "CARTAPORTE", None)
		bot.initSettings ()
		bot.activateEcuapassWindow ()

		return ("Ventana de ECUAPASS activada!")

	#----------------------------------------------------------------
	#-- Transmit document fields to CODEBIN web app using Selenium
	#----------------------------------------------------------------
	def codebin_transmit (workingDir, codebinFieldsFile):
		filepath = os.path.join (workingDir, codebinFieldsFile)
		docType = EcuServer.getDoctypeFromFilename (codebinFieldsFile)
		startCodebinBot (docType, filepath)

	#----------------------------------------------------------------
	#-- Transmit document fields to ECUAPASSDOCS web app using Selenium
	#----------------------------------------------------------------
	def ecuapassdocs_transmit (workingDir, ecuapassdocsFieldsFile):
		filepath = os.path.join (workingDir, ecuapassdocsFieldsFile)
		docType = EcuServer.getDoctypeFromFilename (ecuapassdocsFieldsFile)
		startEcuapassdocsBot (filepath)

	#----------------------------------------------------------------
	#-- Get document type from filename
	#----------------------------------------------------------------
	def getDoctypeFromFilename (filename):
		docType = os.path.basename (filename).split("-")[0].upper()
		filename = filename.upper ()
		if "CPI" in filename or "CARTAPORTE" in filename:
			return ("CARTAPORTE")
		elif "MCI" in filename or "MANIFIESTO" in filename:
			return ("MANIFIESTO")
		elif "DCL" in filename or "DECLARACION" in filename:
			return ("DECLARACION")
		else:
			Utils.printx (f"ERROR: Tipo de documento desconocido: '{docType}'")
			sys.exit (1)

	#------------------------------------------------------
	# If no port then runned with a user port
	# else get port by defoult or adding 1 to the last open port
	#------------------------------------------------------
	def getPortNumber (portNumber=None):
		portFilename     = "url_port.txt"
		lastPortFilename = "last_url_port.txt"

		# If port from file or default
		if not portNumber:
			if not os.path.exists (lastPortFilename):
				# Default port
				portNumber = 5000
			else:
				# Last port from file
				with open (lastPortFilename, "r", encoding='utf-8') as portFile: 
					portString = portFile.readline ()
					portNumber = 1 + int (portString)

		# Write new port
		print ("+++ Escribiendo nuevo puerto: ", portNumber)
		with open (portFilename, "w", encoding='utf-8') as portFile: 
			portFile.write ("%d" % int(portNumber))

		return portNumber

#--------------------------------------------------------------------
# Call main 
#--------------------------------------------------------------------
if __name__ == '__main__':
	mp.freeze_support ()
	main ()
