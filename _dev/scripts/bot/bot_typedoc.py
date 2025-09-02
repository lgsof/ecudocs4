#!/usr/bin/env python3
"""
Simple Bot for filling ECUAPASS documents from a JSON docFields document
"""
import sys, json
import subprocess

import pyautogui as py
import pywinauto
import pyperclip # copy, paste

def main ():
	args = sys.argv

	docFile = args [1]

	docFields = json.load (open (docFile))

	activateEcuapassDocsWindows ()
	createNuevaCartaporte ()
	docFields = prepareDocCartaporte (docFields)
	#docFields = prepareDocManifiesto (docFields)
	#createNuevaCartaporte ()
	typeDoc (docFields)

def typeDoc (docFields):
	subprocess.run(['setxkbmap', 'us'])
	py.sleep (1)
	skipN (5)
#	i = 0
	for i, key in enumerate (docFields):
		if isEmptyCurrentField ():
			value = docFields [key]
			py.write (value)
			py.sleep (0.005)
			print (f"{i} : {key} :: {docFields [key]}")
		py.press ("Tab")
#		i += 1
#		if i > 4:
#			break

	subprocess.run(['setxkbmap', 'latam'])

#-- Remove and clean info not used for typing
def prepareDoc (docFields):
	del docFields ["id"]
	del docFields ["00a_Pais"]
	#del docFields ["00a_Tipo"]
	del docFields ["00_Numero"]
	return docFields

#-- Remove and clean info not used for typing
def prepareDocManifiesto (docFields):
	docFields = prepareDoc (docFields)
	del docFields ["41_OriginalCopia"]
	return docFields

#-- Remove and clean info not used for typing
def prepareDocCartaporte (docFields):
	noFields = ["01_Transportista", "24_OriginalCopia"]
	monedaFields = [k for k in docFields.keys () if "Moneda" in k]
	noFields.extend (monedaFields)
	for k in noFields:
		del docFields [k]

	docFields = prepareDoc (docFields)

	for key in docFields:
		if any ([x in key for x in ["Total", "Emision", "Embarque"]]):
			docFields [key] = ""

	return docFields

def createNuevoManifiesto ():
	py.hotkey ("ctrl", "l")
	skipN (9)
	py.press ("Enter")
	#py.press ("Backspace")
	#py.write ("127.0.0.1:8000")

def createNuevaCartaporte ():
	py.hotkey ("ctrl", "l")
	skipN (6)
	py.press ("Enter")
	#py.press ("Backspace")
	#py.write ("127.0.0.1:8000")

def activateEcuapassDocsWindows ():
	# Replace 'window_name' with the title or partial title of the window you want to activate
	window_name = "EcuapassDocs 0.5"  # For example, if you want to activate a terminal window

	# Use wmctrl to activate the window with the specified title
	subprocess.run(['wmctrl', '-a', window_name])

#--------------------------------------------------------------------
# Skip N cells forward or backward 
#--------------------------------------------------------------------
def skipN (N, direction="RIGHT"):
	if direction == "RIGHT":
		[py.press ("Tab") for i in range (N)]
	elif direction == "LEFT":
		[py.hotkey ("shift", "Tab") for i in range (N)]
	else:
		print (f"Direccion '{direction}' desconocida ")
	py.sleep (0.5)

#-- Check if a form field is empty or contains any text
def isEmptyCurrentField ():
	pyperclip.copy ("")
	py.hotkey ("Ctrl","a")
	py.hotkey ("ctrl","c")
	text = pyperclip.paste ()
	if text == "":
		return True
	else:
		return False

main ()
