import re, os, sys, json, datetime, time

import pyautogui as py
import pywinauto

import pyperclip
from pyperclip import copy as pyperclip_copy
from pyperclip import paste as pyperclip_paste

from traceback import format_exc as traceback_format_exc

from ecuapassdocs.info.ecuapass_utils import Utils
from ecuapassdocs.info.ecuapass_info_cartaporte import CartaporteInfo
from ecuapassdocs.info.ecuapass_info_manifiesto import ManifiestoInfo
from ecuapass_exceptions import EcudocBotStopException, EcudocEcuapassException
from ecuapassdocs.info.ecuapass_extractor import Extractor

# For binary settings.bin
from ecuapass_settings import EcuSettings

#----------------------------------------------------------
# Globals
#----------------------------------------------------------
win   = None	 # Global Ecuapass window  object

#----------------------------------------------------------
# General Bot class with basic functions of auto completing
#----------------------------------------------------------
class EcuBot:
	#-- Load data, check/clear browser page
	def __init__(self, ecuFieldsFilepath, runningDir, docType, speedOption):
		self.ecuFieldsFilepath     = ecuFieldsFilepath   
		self.runningDir            = runningDir	   
		self.docType	           = docType
		self.speedOption           = speedOption

		self.ecuapassWinTitle      = 'ECUAPASS - SENAE browser'
		Utils.runningDir           = runningDir

	#-- Update fields with user's info and load settings
	def initSettings (self):
		# Update Ecuapass file to be transmitted to ECUAPASS
		self.fields = self.updateEcuapassFile (self.ecuFieldsFilepath)

		# Read settings 
		settingsPath	   = os.path.join (self.runningDir, "settings.txt")
		Utils.printx ("Leyendo settings desde: ", settingsPath)

		#settings		   = json.load (open (settingsPath, encoding="utf-8")) 
		ecuSettings        = EcuSettings (self.runningDir)
		settings           = ecuSettings.readBinSettings ()
		self.empresaName   = settings ["empresa"]

		self.NORMAL_PAUSE  = 0.05 #float (settings ["NORMAL_PAUSE"])
		self.SLOW_PAUSE    = 0.5 #float (settings ["SLOW_PAUSE"])
		self.FAST_PAUSE    = 0.01 #float (settings ["FAST_PAUSE"])
		py.PAUSE		   = self.NORMAL_PAUSE

		Utils.printx (f"+++ BOT Settings para la Empresa: <{settings ['empresa']}>")

	#-------------------------------------------------------------------
	# Executes general bot procedure
	#-------------------------------------------------------------------
	def start (self):
		Utils.printx (f"Iniciando digitación de documento '{self.ecuFieldsFilepath}'")
		self.initEcuapassWindow ()
		self.fillEcuapass ()

	#-- Check/init Ecuapass window
	def initEcuapassWindow (self):
		Utils.printx ("Iniciando ventana de ECUAPASS...")
		
		self.win = self.activateEcuapassWindow ()
		py.sleep (0.2)
		#self.moveMouseToEcuapassWinCenter ()
		#self.maximizeWindow (self.win)
		#py.sleep (0.2)

		#-- Detect and clear webpage
		self.scrollWindowToBeginning ()
		#self.detectEcuapassDocumentPage (self.docType)
		self.clearWebpageContent ()
		self.waitForInfo ()

	#-- Select first item from combo box
	def selFirstItemFromBox  (self):
		py.press ("down")
		py.press ("enter")

	#--------------------------------------------------------------------
	# Detect if is on find button using image icon
	#--------------------------------------------------------------------
	def isOnFindButton (self):
		Utils.printx ("Localizando botón de búsqueda...")
		filePaths = Utils.imagePath ("image-button-FindRUC")
		for fpath in filePaths:
			Utils.printx ("...Probando: ", os.path.basename (fpath))
			xy = py.locateCenterOnScreen (fpath, confidence=0.90, grayscale=False)
			if (xy):
				print ("...Detectado:", fpath)
				return True
	#--------------------------------------------------------------------
	# Check for error message box 'Seleccion Nula" 
	#--------------------------------------------------------------------
	def checkErrorDialogBox (self, imageName):
		Utils.printx (f"Verificando '{imageName}'...")
		filePaths = Utils.imagePath (imageName)
		for fpath in filePaths:
			Utils.printx (">>> Buscando la imágen: ", os.path.basename (fpath))
			xy = py.locateCenterOnScreen (fpath, confidence=0.80, grayscale=False)
			print ("--xy:", xy)
			if (xy):
				raise Exception (f"Se presentó errores en '{imageName}'")

	#--------------------------------------------------------------------
	# Fill subject fields waiting for RUC info for ecuadorian companies
	#--------------------------------------------------------------------

	def fillSubject (self, subjectType, fieldProcedimiento, fieldPais, fieldTipoId, 
					 fieldNumeroId, fieldNombre, fieldDireccion, fieldCertificado=None):
		#---------------- fill data about subject -------------------
		def processEcuapassId (fieldTipoId, fieldNumeroId):
			newType, newNumber = None, None
			if self.fields [fieldTipoId] == "NIT":
				self.fields [fieldTipoId]   = "OTROS"
				self.fields [fieldNumeroId] = self.fields [fieldNumeroId].split ("-")[0]

		def fillData (fieldPais, fieldTipoId, fieldNumeroId):
			self.fillBoxCheck (fieldPais)
			processEcuapassId (fieldTipoId, fieldNumeroId)
			self.fillBoxCheck (fieldTipoId)
			self.fillText (fieldNumeroId)
		#------------------------------------------------------------
		procedimiento = self.fields [fieldProcedimiento]
		Utils.printx (f"Procedimiento: '{procedimiento}', Sujeto: '{subjectType}'")
		fillData (fieldPais, fieldTipoId, fieldNumeroId); py.sleep (0.01)

		if self.fields [fieldPais] == "ECUADOR" and self.fields [fieldTipoId] == "RUC":
			Utils.printx ("Es una empresa ecuatoriana, verificando RUC")
			nTries = 0

			while True:
				self.checkStopFlag ()
				self.skipN (3, "LEFT"); 
				fillData (fieldPais, fieldTipoId, fieldNumeroId); py.sleep (0.1)
				Utils.printx ("...Esperando botón de búsqueda")
				if self.isOnFindButton (): 
					break
				elif nTries >= 3:
					raise EcudocEcuapassException (f"No se pudo digitar datos de '{subjectType}'")
				nTries +=1
				py.sleep (self.SLOW_PAUSE)	# Regresa para activar el boton de "find" 

			py.press ("space"); 
			py.sleep (1)
			self.waitForInfo ()
			#py.sleep (2)
		else:
			Utils.printx ("No es una empresa ecuatoriana, no verifica RUC")
			if subjectType == "REMITENTE":
				self.fillText (fieldCertificado)
			self.fillText (fieldNombre)

		self.fillText (fieldDireccion)

	#--------------------------------------------------------------------
	# Fill one of three radio buttons (PO, CI, PEOTP) according to input info
	#--------------------------------------------------------------------
	def fillRButton (self, fieldName):
		value = self.fields [fieldName]
		if (value == "1"):
			py.press ("Tab")
		else:
			py.press ("right")

	#--------------------------------------------------------------------
	#-- fill text field
	#--------------------------------------------------------------------
	def fillText (self, fieldName, TAB_FLAG="TAB"):
		self.checkStopFlag ()

		py.PAUSE = self.FAST_PAUSE

		value = self.fields [fieldName]
		Utils.printx (f"Llenando TextField '{fieldName}' : '{value}'...")
		if value != None:
			pyperclip_copy (value)
			py.hotkey ("ctrl", "v")
			py.sleep (self.SLOW_PAUSE)

		if TAB_FLAG == "TAB":
			py.press ("Tab")

		py.PAUSE = self.NORMAL_PAUSE

	#---------------------------------------------------------
	#---------------------------------------------------------
	def checkStopFlag (self):
		stopFlagFilename = os.path.join (self.runningDir, "flag-bot-stop.flag")
		#print ("+++ Checking flag:", stopFlagFilename)
		if os.path.exists (stopFlagFilename):
			raise EcudocBotStopException ()

	#--------------------------------------------------------------------
	#-- Fill combo box pasting text and selecting first value.
	#-- Without check. Default value, if not found. 
	#--------------------------------------------------------------------
	def fillBox (self, fieldName, TAB_FLAG="TAB"):
		py.PAUSE = self.FAST_PAUSE

		fieldValue = self.fields [fieldName]
		Utils.printx (f"Llenando CombolBox '{fieldName}' : '{fieldValue}'...")
		if fieldValue == None:
			return

		pyperclip_copy (fieldValue)
		py.hotkey ("ctrl", "v")
		py.sleep (self.SLOW_PAUSE)
		py.press ("down")
		py.sleep (self.SLOW_PAUSE)

		if TAB_FLAG == "TAB":
			py.press ("Tab")

		py.PAUSE = self.NORMAL_PAUSE


	#-- Fill box and wait if wait cursor appears
	def fillBoxDown (self, fieldName, TAB_FLAG="TAB_CHECK"):
		return self.fillBoxWait (fieldName, TAB_FLAG="TAB_CHECK")

	#-- Fill box for boxes requesting info
	def fillBoxWait (self, fieldName, TAB_FLAG="TAB_CHECK"):
		self.checkStopFlag ()
		try:
			py.PAUSE = self.NORMAL_PAUSE
			fieldValue = self.fields [fieldName]
			Utils.printx (f"Llenando ComboBox '{fieldName}' : '{fieldValue}'...")
			if fieldValue == None:
				py.press ("Enter") if "NOTAB" in TAB_FLAG else py.press ("Tab")
				return True

			pyperclip_copy (fieldValue)
			py.hotkey ("ctrl", "v"); 
			py.sleep (self.FAST_PAUSE)
			py.press ("down")
			py.press ("Enter")
			py.sleep (self.FAST_PAUSE)
			self.waitForInfo ()
			py.sleep (self.FAST_PAUSE)
			if "NOTAB" in TAB_FLAG:
				return
			else:
				py.press ("TAB")
		finally:
			py.PAUSE = self.NORMAL_PAUSE


	#--------------------------------------------------------------------
	# Wait until 'ready' cursor is present
	#--------------------------------------------------------------------
	def waitForInfo (self):
		import win32gui as w32     
		waitCursorId  = 244122955
		readyCursorId = 65539

		#-- DEBUG: Auto speed not implemented
		if self.speedOption == "FAST":
			py.sleep (0.1)
		elif self.speedOption == "SLOW":
			py.sleep (2)
		else: #AUTO
			while True:
				self.checkStopFlag ()
				info = w32.GetCursorInfo ()
				id	 = info [1]
				if id > 100000:
					print ("+++ Esperando datos desde el ECUAPASS...")
					time.sleep (self.NORMAL_PAUSE)
				else:
					break
		py.sleep (self.NORMAL_PAUSE)

	#--------------------------------------------------------------------
	# Select value in combo box by pasting, checking, and pasting
	# Return true if selected, raise an exception in other case.
	#--------------------------------------------------------------------
	def fillBoxCheck (self, fieldName, TAB_FLAG="TAB_CHECK"):
		try:
			fieldValue = self.fields [fieldName]
			Utils.printx (f"Llenando ComboBox '{fieldName}' : '{fieldValue}'...")
			if fieldValue == None:
				py.press ("Enter") if "NOTAB" in TAB_FLAG else py.press ("Tab")
				return True

			py.PAUSE = self.NORMAL_PAUSE
			for i in range (10):
				pyperclip_copy (fieldValue)
				py.hotkey ("ctrl", "v"); py.sleep (0.05);py.press ("down"); 
				pyperclip_copy ("")

				py.hotkey ("ctrl","c"); 
				text = pyperclip_paste().lower()
				Utils.printx (f"...Intento {i}: Buscando '{fieldValue}' en texto '{text}'")

				if fieldValue.lower() in text.lower():
					py.PAUSE = 0.3
					pyperclip_copy (fieldValue)
					py.hotkey ("ctrl", "v"); py.press ("enter"); py.sleep (0.01)
					#py.hotkey ("ctrl", "v"); 
					py.PAUSE = self.NORMAL_PAUSE

					#py.press ("TAB") if TAB_FLAG == "TAB" else py.press ("Enter")
					py.press ("Enter") if "NOTAB" in TAB_FLAG else py.press ("Tab")

					Utils.printx (f"...Encontrado '{fieldValue}' en '{text}'")
					return True
				else:
					py.PAUSE += 0.01

				py.hotkey ("ctrl", "a"); py.press ("backspace");

			# Check or not check
			if "NOCHECK" in TAB_FLAG:
				return True
			else:
				message = f"Problemas en el ECUAPASS sincronizando '{fieldName}':'{fieldValue}'"
				raise Exception (message)
		finally:
			py.PAUSE = self.NORMAL_PAUSE


	#--------------------------------------------------------------------
	# Skip N cells forward or backward 
	#--------------------------------------------------------------------
	def skipN (self, N, direction="RIGHT"):
		py.PAUSE = self.FAST_PAUSE

		if direction == "RIGHT":
			[py.press ("Tab") for i in range (N)]
		elif direction == "LEFT":
			[py.hotkey ("shift", "Tab") for i in range (N)]
		else:
			print (f"Direccion '{direction}' desconocida ")

		py.PAUSE = self.NORMAL_PAUSE
		py.sleep (0.1)

	#------------------------------------------------------------------
	#-- Fill box iterating, copying, comparing.
	#------------------------------------------------------------------
	def fillBoxIter (self, fieldValue, TAB_FLAG="TAB"):
		py.PAUSE = self.NORMAL_PAUSE
		fieldValue = fieldValue.upper ()
		Utils.printx (f"Buscando '{fieldValue}'...")

		for i in range (10):
			lastText = ""
			py.press ("home")
			while True:
				self.checkStopFlag ()
				py.press ("down"); py.sleep (0.1)
				py.hotkey ("ctrl", "a", "c"); py.sleep (0.1)
				text = pyperclip_paste().upper()
				if fieldValue in text:
					Utils.printx (f"...Intento {i}: Encontrado {fieldValue} en {text}") 
					[py.press ("Tab") if TAB_FLAG=="TAB" else py.press ("enter")] 
					return

				if (text == lastText):
					Utils.printx (f"...Intento {i}: Buscando '{fieldValue}' en {text}")
					break
				lastText = text 
			py.sleep (0.2)

		Utils.printx (f"...No se pudo encontrar '{fieldValue}'")
		py.PAUSE = self.NORMAL_PAUSE
		if TAB_FLAG == "TAB":
			py.press ("Tab")

	#-------------------------------------------------------------------
	#-- Fill Date box widget (month, year, day)
	#-------------------------------------------------------------------
	def fillDate (self, fieldName, GET=True):
		py.PAUSE = self.NORMAL_PAUSE
		try:
			Utils.printx (f"Llenando campo Fecha '{fieldName}' : {self.fields [fieldName]}'...")
			fechaText = self.fields [fieldName]
			if (fechaText == None):
				return

			items = fechaText.split("-")
			day, month, year = int (items[0]), int (items[1]), int (items[2])

			currentDate = datetime.datetime.now ()
			if GET:
				currentDate  = self.getBoxDate ()

			dayBox		= currentDate.day
			monthBox	= currentDate.month
			yearBox		= currentDate.year
			Utils.printx (f"...Fecha actual: {dayBox}-{monthBox}-{yearBox}.")

			py.hotkey ("ctrl", "down")
			#py.PAUSE = self.FAST_PAUSE
			self.setYear  (year, yearBox)
			self.setMonth (month, monthBox)
			self.setDay (day)
			#py.PAUSE = self.NORMAL_PAUSE
		except EcudocBotStopException as ex:
			return message ("BOTERROR: Digitación interrumpida")
		except Exception as ex:
			Utils.printException ("FECHA:")
			raise Exception ("No se pudo establecer fecha. \n" + str (ex)) 

	#-- Set year
	def setYear (self, yearDoc, yearOCR):
		diff = yearDoc - yearOCR
		pageKey = "pageup" if diff < 0 else "pagedown"
		pageSign = "-" if diff < 0 else "+"

		for i in range (abs(diff)):
			py.hotkey ("shift", pageSign)

	#-- Set month
	def setMonth (self, monthDoc, monthOCR):											 
		diff = monthDoc - monthOCR
		pageKey = "pageup" if diff < 0 else "pagedown"

		for i in range (abs(diff)):
			py.press (pageKey)

	#-- Set day
	def setDay (self, dayDoc):
			nWeeks = dayDoc // 7
			nDays  = dayDoc % 7 - 1

			py.press ("home")
			[py.press ("down") for i in range (nWeeks)]
			[py.press ("right") for i in range (nDays)]

			py.press ("enter")

	#-- Get current date fron date box widget
	def getBoxDate (self):
		count = 0
		while True:
			self.checkStopFlag ()
			count += 1
			py.hotkey ("ctrl", "down")
			py.press ("home")
			py.hotkey ("ctrl", "a")
			py.hotkey ("ctrl", "c")
			text	 = pyperclip_paste ()

			reFecha = r'\d{1,2}/\d{1,2}/\d{4}'
			if re.match (reFecha, text):
				boxDate  = text.split ("/") 
				boxDate  = [int (x) for x in boxDate]
				class BoxDate:
					day = boxDate[0]; month = boxDate [1]; year = boxDate [2]
				return (BoxDate())

			if (count > 112):
				raise Exception ("Sobrepasado el número de dias al buscar fecha.")

	#----------------------------------------------------------------
	#-- Function for windows management
	#----------------------------------------------------------------
	#-- Detect ECUAPASS window
	def detectWindowByTitle (self, titleString):
		Utils.printx (f"Detectando ventana '{titleString}'...")
		windows = py.getAllWindows ()
		for win in windows:
			if titleString in win.title:
				return win

		raise EcudocEcuapassException (f"No se detectó ventana '{titleString}' ")

	#-- Maximize window by minimizing and maximizing
	def maximizeWindow (self, win):
		SLEEP=0.3
		py.PAUSE = self.SLOW_PAUSE
		win.minimize (); py.sleep (SLEEP)
		win.restore (); py.sleep (0.1)
		py.hotkey ("win", "up")
		py.PAUSE = self.NORMAL_PAUSE
		#win.activate (); #py.sleep (SLEEP)
		#win.resizeTo (py.size()[0].size()[1]); py.sleep (SLEEP)

	def maximizeWindowByClickOnIcon (self, win):
		imagePath = Utils.imagePath ("image-icon-maximize.png")
		xy = py.locateCenterOnScreen (imagePath, confidence=0.70, grayscale=False)
		if (xy):
			Utils.printx ("+++ DEBUG:Maximizando ventana...")
			py.click (xy[0], xy[1], interval=1)    
			return True
		return False

	def activateWindowByTitle (self, titleString):
		SLEEP=0.2
		ecuWin = self.detectWindowByTitle (titleString)
		Utils.printx (f"Activando ventana '{titleString}'...", ecuWin)
		
		#ecuWin.activate (); py.sleep (SLEEP)
		if ecuWin.isMinimized:
			ecuWin.activate (); py.sleep (SLEEP)

		return (ecuWin)

	#-- Detect and activate ECUAPASS-browser/ECUAPASS-DOCS window
	def activateEcuapassWindow (self):
		try:
			Utils.printx ("Activando la ventana del ECUAPASS...")
			#return self.activateWindowByTitle ('ECUAPASS - SENAE browser')

			# Connect to an existing instance of an application by its title
			app = pywinauto.Application().connect(title=self.ecuapassWinTitle)

			# Get a reference to the main window and activate it
			ecuapass_window = app.window (title=self.ecuapassWinTitle)
			ecuapass_window.set_focus()
			return ecuapass_window
		except pywinauto.ElementNotFoundError:
			raise EcudocEcuapassException (f"No está abierta la ventana del ECUAPASS")

	#-- Move mouse to center of ecuapass window
	def moveMouseToEcuapassWinCenter (self):
		import win32gui as w32     
		hwnd = w32.FindWindow(None, self.ecuapassWinTitle)

		if hwnd == 0:
			print(f"No se encontrO ventana con tItulo'{self.ecuapassWinTitle}'!")
			return False

		winRect = w32.GetWindowRect(hwnd)
		x0, x1, y0, y1 = winRect[0], winRect [2], winRect [1], winRect [3]
		xc = x0 + (x1 - x0) / 2
		yc = y0 + (y1 - y0) / 2

		x, y = w32.GetCursorPos()
		py.moveTo (xc, yc)

	def activateEcuapassDocsWindow (self):
		return self.activateWindowByTitle ('Ecuapass-Docs')

	#-- Clear previous webpage content clicking on "ClearPage" button
	def clearWebpageContent (self):
		Utils.printx ("Localizando botón de borrado...")
		filePaths = Utils.imagePath ("image-button-ClearPage")
		for fpath in filePaths:
			print (">>> Probando: ", os.path.basename (fpath))
			xy = py.locateCenterOnScreen (fpath, confidence=0.80, grayscale=True)
			if (xy):
				print (">>> Detectado")
				py.click (xy[0], xy[1], interval=1)    
				return True

		raise EcudocEcuapassException ("No se detectó botón de borrado")
		
	#-- Scroll to the page beginning 
	def scrollWindowToBeginning (self):
		Utils.printx ("Desplazando página hasta el inicio...")
		filePaths = Utils.imagePath ("image-button-ScrollUp")
		for fpath in filePaths:
			print (">>> Probando: ", os.path.basename (fpath))
			xy = py.locateCenterOnScreen (fpath, confidence=0.80, grayscale=True)
			if (xy):
				Utils.printx (">>> Detectado")
				py.mouseDown (xy[0], xy[1])
				py.sleep (2)
				py.mouseUp (xy[0], xy[1])
				return True

		Utils.printx ("No se pudo desplazar la página ECUAPASS al inicio")

	#-- Scroll down/up N times (30 pixels each scroll)
	def scrollN (self, N, direction="down"):
		py.PAUSE = self.NORMAL_PAUSE
		sizeScroll = -10000 if direction=="down" else 10000
		#Utils.printx (f"\tScrolling {sizeScroll} by {N} times...")
		for i in range (N):
			#Utils.printx (f"\t\tScrolling {i} : {30*i}")
			py.scroll (sizeScroll)
			print ("...Scrolling: ", i)

	#-- Check if active webpage contains correct text 
	def detectEcuapassDocumentPage (self, docType):
		Utils.printx (f"Detectando página de '{docType}' activa...")
		docFilename = "";
		if docType == "CARTAPORTE":
			docFilename = "image-text-Cartaporte"; 
		elif docType == "MANIFIESTO":
			docFilename = "image-text-Manifiesto"; 
		elif docType == "DECLARACION":
			docFilename = "image-text-DeclaracionTransito.png"; 

		filePaths = Utils.imagePath (docFilename)
		for fpath in filePaths:
			Utils.printx (">>> Probando: ", os.path.basename (fpath))
			xy = py.locateCenterOnScreen (fpath, confidence=0.80, grayscale=True)
			if (xy):
				Utils.printx (">>> Detectado")
				return True

		message = Utils.printx (f"No se detectó la página de '{docType}'")
		raise EcudocEcuapassException (message)

	#-- Click on selected cartaporte
	def clickSelectedCartaporte (self, fieldName):
		Utils.printx ("Localizando cartaporte...")
		filePaths = Utils.imagePath ("image-blue-text-terrestre")
		for fpath in filePaths:
			print (">>> Probando: ", os.path.basename (fpath))
			xy = py.locateCenterOnScreen (fpath, confidence=0.70, grayscale=False)
			if (xy):
				Utils.printx ("...Cartaporte detectada")
				py.click (xy[0], xy[1], interval=1)    
				return True

		fieldValue = self.fields [fieldName]
		Utils.printx ("...No se detectó cartaporte.")
		return False

	#------------------------------------------------------
	#-- Updated Ecuapass document fields with values ready to transmit
	#-- Change names to codes for additional presition. Remove '||LOW'
	#------------------------------------------------------
	def updateEcuapassFile (self, ecuFieldsFilepath):
		ecuapassFields    = json.load (open (ecuFieldsFilepath, encoding="utf-8"))
		ecuapassFieldsUpd = self.updateEcuapassFields (ecuapassFields)
		print (f"+++ DEBUG: updateEcuapassFields: '{ecuFieldsFilepath}'")
		ecuJsonFileUpd    = Utils.saveFields (ecuapassFieldsUpd, ecuFieldsFilepath, "UPDATE")
		return ecuapassFieldsUpd

	def updateEcuapassFields (self, ecuapassFields):
		print ("-- Updating Ecuapass fields...")
		for key in ecuapassFields:
			if ecuapassFields [key] is None:
				continue

			# Vehiculo
			if "Tipo_Vehiculo" in key:
				vehiculos    = {"SEMIRREMOLQUE":"SR", "TRACTOCAMION":"TC", "CAMION":"CA"}
				ecuapassFields [key] = vehiculos [ecuapassFields[key]]

			# Moneda
			if "Moneda" in key:
				ecuapassFields [key] = "USD"

			# Embalaje
			if "Embalaje" in key: 
				embalaje = ecuapassFields [key].upper()
				ecuapassFields [key] = Extractor.getCodeEmbalaje (embalaje)

			# Remove confidence string ("||LOW")
			value        = ecuapassFields [key] 
			value        = value.split ("||")[0] if value else None
			ecuapassFields [key] = value if value != "" else None

		return ecuapassFields

if __name__ == "__main__":
	main()
