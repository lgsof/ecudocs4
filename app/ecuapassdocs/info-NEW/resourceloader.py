
import os, re, sys, json, traceback
import importlib
from importlib import resources

# External packages
from PyPDF2 import PdfReader
from PIL import Image 

class ResourceLoader:
	def loadText (resourcePackage, resourceName):
		text = None
		resourcePackage = "resources." + resourcePackage
		try:
			with resources.open_text (resourcePackage, resourceName, encoding="utf-8") as fp:
				text = fp.readlines()
		except:
			print (traceback.format_exc())

		return text

	def loadJson (resourcePackage,  resourceName):
		jsonDic = None
		resourcePackage = "resources." + resourcePackage
		try:
			with resources.open_text (resourcePackage, resourceName, encoding="utf-8") as fp:
				jsonDic = json.load (fp)
		except:
			print (traceback.format_exc())
		return jsonDic

	def loadPdf (resourcePackage, resourceName):
		pdfObject = None
		resourcePackage = "resources." + resourcePackage
		try:
			fp = resources.open_binary (resourcePackage, resourceName)
			pdfObject = PdfReader (fp)
		except:
			print (traceback.format_exc())

		return pdfObject

	def loadImage (resourcePackage, resourceName):
		imgObject = None
		resourcePackage = "resources." + resourcePackage
		try:
			with resources.open_binary (resourcePackage, resourceName) as fp:
				imgObject = Image.open (fp)
		except:
			print (traceback.format_exc())

		return imgObject

	def get_resource_path (resource_name):
		return os.path.join('resources', resource_name)

	#-------------------------------------------------------------------
	#-- Get ECUAPASS data items as dic taking resources from package (no path)
	#-------------------------------------------------------------------
	def getEcuapassData (dataFilename, TYPE="VALUES"): # DICT or KEYS or VALUES
		dataLines = ResourceLoader.loadText ("data_ecuapass", dataFilename + ".txt")

		data = {} 
		for line in dataLines [1:]:
			res = re.search (r"\[(.+)\]\s+(.+)", line)
			data [res.group(1)] = res.group(2)

		if TYPE=="VALUES":
			return data.values ()
		elif TYPE=="KEYS":
			return data.keys ()
		elif TYPE=="ITEMS":
			return data
		else:
			return none
	#-------------------------------------------------------------------
	#-- Return a piped string of ECUPASS data used in regular expression
	#-- From join "values" or join "keys"
	#-------------------------------------------------------------------
	def getDataString (dataFilename, resourcesPath, From="values"):
		dataPath   = os.path.join (resourcesPath, dataFilename)
		dataDic    = Extractor.getDataDic (dataFilename, resourcesPath)
		dataString = None
		if From=="values":
			#dataString = "|".join (map (re.escape, dataDic.values())) #e.g. 'New York' to 'New\\ York'
			dataString = "|".join (dataDic.values()) #e.g. 'New York' to 'New\\ York'
		else:
			dataString = "|".join (dataDic.keys())
		return (dataString)

	#-------------------------------------------------------------------
	# Dynamically loads a module from a package and retrieves a class from it.
	# Works both in a script and in a PyInstaller bundle.
	#-------------------------------------------------------------------
	def load_class_from_module (package_name, module_name, class_name):
		# Determine the base path based on whether the script is frozen (e.g., PyInstaller)
		if getattr(sys, 'frozen', False):
			# Running in a PyInstaller bundle
			base_path = sys._MEIPASS
		else:
			# Running as a script
			base_path = os.path.dirname(os.path.abspath(__file__))

		# Add the base path to sys.path to ensure the package can be imported
		if base_path not in sys.path:
			sys.path.append(base_path)

		# Dynamically import the module
		full_module_name = f"{package_name}.{module_name}"
		try:
			module = importlib.import_module(full_module_name)
		except ImportError as e:
			raise ImportError(f"Could not import module: {full_module_name}. Error: {e}")

		# Retrieve the class from the module
		if hasattr(module, class_name):
			return getattr(module, class_name)
		else:
			raise AttributeError(f"The module {full_module_name} does not have class: {class_name}")

# Example usage
if __name__ == "__main__":
    try:
        # Load a class from a module in the package
        MyClass = load_class_from_module("info", "moduleA", "MyClassA")
        instance = MyClass()  # Create an instance of the dynamically loaded class
        instance.some_method()  # Call a method on the instance
    except Exception as e:
        print(f"Error: {e}")
