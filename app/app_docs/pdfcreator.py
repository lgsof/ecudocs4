#!/usr/bin/env python

import io, sys, tempfile, json, re
from os.path import join

# External packages for creating PDF documents
from PyPDF2 import PdfReader, PdfWriter, PdfMerger
import reportlab
from reportlab.pdfgen import canvas

# External package for getting image size
from PIL import Image 

# For loading resources
from ecuapassdocs.utils.resourceloader import ResourceLoader 

print (f"+++ ...Loading CreadorPDF module")
#----------------------------------------------------------------
# Crea un documento PDF con background y textos
#----------------------------------------------------------------
class CreadorPDF:
	def __init__ (self, pdfType="ONE_PDF"):
		self.pdfType = pdfType

	#----------------------------------------------------------------
	# Set filenmaes of resources files for creating PDFs
	#----------------------------------------------------------------
	def setFilenamesForResources (self, docType):
		if docType.upper() == "CARTAPORTE":
			self.PdfDocument     = ResourceLoader.loadPdf ("docs", 'cartaporte-vacia-SILOG-BYZA.pdf')
			self.PdfDocument02   = ResourceLoader.loadPdf ("docs", 'cartaporte-contrato-BYZA.pdf')
			self.ImgDocument     = ResourceLoader.loadImage ("docs", 'image-cartaporte-vacia-SILOG-BYZA.png')
			self.paramFields     = ResourceLoader.loadJson ("docs", 'input_parameters_cartaporte.json')
			self.prefix          = "CPI"
		elif docType.upper() == "MANIFIESTO":
			self.PdfDocument     = ResourceLoader.loadPdf ("docs", 'manifiesto-vacio-NTA-BYZA.pdf')
			self.ImgDocument     = ResourceLoader.loadImage ("docs", 'image-manifiesto-vacio-NTA-BYZA.png')
			self.paramFields     = ResourceLoader.loadJson ("docs", 'input_parameters_manifiesto.json')
			self.prefix          = "MCI"
		elif docType.upper() == "DECLARACION":
			self.PdfDocument     = ResourceLoader.loadPdf ("docs", 'declaracion-vacia-NTA.pdf')
			self.ImgDocument     = ResourceLoader.loadImage ("docs", 'image-declaracion-vacia-NTA.png')
			self.paramFields     = ResourceLoader.loadJson ("docs", 'input_parameters_declaracion.json')
			self.prefix          = "DCL"
		else:
			print (f"Error: Tipo de documento '{docType}' no soportado")
			sys.exit (0)

		# Remove "id" field needed only for access DB
		self.paramFields.pop ("id")
		self.paramFields.pop ("numero")
		self.paramFields.pop ("fecha_creacion")
		self.paramFields.pop ("referencia")
		#self.paramFields.popitem ()      # OriginalCopia

	#----------------------------------------------------------------
	# Create multiPDF for values and docTypes
	#----------------------------------------------------------------
	def createMultiPdf (self, values, types):
		pdf_list = []
		docNumber = None
		for i, (formFields, docType) in enumerate (zip (values, types)):
			outPdfPath = self.createPdfDocument (docType, formFields, "COPIA")
			pdf_list.append (outPdfPath)

			if i == 0:
				docNumber = formFields ['txt00'] 

		tmpPath     = tempfile.gettempdir ()
		outPdfPath  = join (tmpPath, f"{self.prefix}-{docNumber}.pdf") 
		self.joinPdfFiles (pdf_list, outPdfPath)
		return outPdfPath

	#-------------------------------------------------------------------
	# Merges a list of PDFs into a single output file.
	#-------------------------------------------------------------------
	def joinPdfFiles (self, pdf_list, outPdfPath):
		merger = PdfMerger()
		for filename in pdf_list:
			# Open each PDF with PdfReader
			with open(filename, 'rb') as pdf_file:
				reader = PdfReader(pdf_file)
				merger.append (reader)
		# Write the merged content to a new PDF file
		with open (outPdfPath, 'wb') as output_file:
			merger.write(output_file)

	#----------------------------------------------------------------
	#-- Crea PDF con otro PDF como background y añade texto sobre este
	#-- pdfType: "original", "copia", "clon"
	#----------------------------------------------------------------
	def createPdfDocument (self, docType, formFields, pdfType):
		self.setFilenamesForResources (docType)

		pdfType     = pdfType.lower()
		tmpPath     = tempfile.gettempdir ()
		copyString  = "ORIGINAL" if "original" in pdfType else "COPIA"

		docNumber   = formFields ['txt00']
		#copyKey     = max (formFields.keys ())
		#formFields [copyKey] = copyString;

		if docType.upper () == "CARTAPORTE":
			formFields ["txt24"] = copyString
		elif docType.upper () == "MANIFIESTO":
			formFields ["txt41"] = copyString
		elif docType.upper () == "DECLARACION":
			formFields ["txt26"] = copyString
		else:
			print (f"ERROR. Tipo de documento desconocido: '{docType}'")
			
		outPdfPath  = join (tmpPath, f"{self.prefix}-{docNumber}.pdf") 
		outJsonPath = join (tmpPath, f"{self.prefix}-{docNumber}.json") 

		text_pdf, jsonFieldsDic = self.writeInputsToPdf (docType, self.paramFields, formFields)
		json.dump (jsonFieldsDic, open (outJsonPath, "w"), indent=4)
		self.merge_pdfs (docType, self.PdfDocument, text_pdf, outPdfPath)

		return outPdfPath

	#----------------------------------------------------------------
	# Write text values to output PDF
	#----------------------------------------------------------------
	def writeInputsToPdf (self, docType, paramFields, formFields):
		FONTSIZE = 9                  # Font "normal"
		LINESPACE = 2
		packet = io.BytesIO()
		can = canvas.Canvas(packet)

		for key, params in paramFields.items():
			if not key.startswith ("txt"):
				continue
			imgBounds = [params["x"], params["y"]-7, params ["width"], params ["height"]]
			pdfBounds = self.convertToImageToPdfBounds (imgBounds)

			fontTypes = {"hidden":0, "normal":8, "large":16, "small":7}
			FONTSIZE = fontTypes [params ["font"]]

			#can.setFont ("Times-Bold", FONTSIZE)
			#can.setFont("Helvetica", FONTSIZE)  # Set font size to 0 for hidden text
			can.setFont ("Courier-Bold", FONTSIZE)  # Set font size to 0 for hidden text

			#-- Set color to text 
			if "restrictions" in params.keys ():
				if any ("color" in x for x in params ["restrictions"]):
					can.setFillColorRGB (1,0,0)
				else:
					can.setFillColorRGB (0,0,0)

			text      = formFields [key]
			textLines = text.split ("\n")
			for i, line in enumerate (textLines):
				x = pdfBounds [0] - 2
				y = pdfBounds [1] - (i+1)*FONTSIZE + i+2  - i*LINESPACE

				drawFun = can.drawString
				if params ["align"] == "right":
					drawFun, x = can.drawRightString,   pdfBounds [0] + pdfBounds [2]
				elif params ["align"] == "center":
					drawFun, x = can.drawCentredString, pdfBounds [0] + pdfBounds [2]/2

				drawFun (x, y, line.strip())

		jsonFieldsDic = self.embedFieldsIntoPDF (docType, can, paramFields, formFields)
		can.save()

		packet.seek(0)
		return PdfReader(packet), jsonFieldsDic

	#----------------------------------------------------------------
	#-- Embed fields info (key:value) into PDF doc
	#-- Info is embedded according to Azure format
	#----------------------------------------------------------------
	def embedFieldsIntoPDF (self, docType, pdfCanvas, paramFields, formFields):
		print (">>> Embebiendo información del documento dentro del PDF...")
		if docType.upper() == "CARTAPORTE":
			return self.embedFieldsIntoPDFCartaporte (pdfCanvas, paramFields, formFields)
		elif docType.upper() == "MANIFIESTO":
			return self.embedFieldsIntoPDFManifiesto (pdfCanvas, paramFields, formFields)
		elif docType.upper() == "DECLARACION":
			print ("ALERTA: Aún no implementado la insersión de campos en declaraciones")
		else:
			print (f"ERROR. Tipo de documento desconocido: '{self.docType}´") 

		return None

	def embedFieldsIntoPDFCartaporte (self, pdfCanvas, paramFields, formFields):
		jsonFieldsDic = {}
		gastosDic = {"value": {"ValorFlete":{"value":{}}, 
		                       "Seguro":{"value":{}}, 
							   "OtrosGastos":{"value":{}}, 
							   "Total":{"value":{}}}}
		for key, params in paramFields.items():
			fieldName    = params ["ecudocsField"]
			#value        = formFields [key].replace ("\r\n", "\n")
			value        = formFields [key] 
			if "Gastos" in fieldName:
				res = re.findall ("\w+", fieldName)   #e.g ["ValorFlete", "MontoDestinatario"]
				tableName, rowName, colName = res [0], res [1], res[2]
				if value != "":
					gastosDic ["value"][rowName]["value"][colName] = {"value": value, "content": value}
					jsonFieldsDic [tableName] = gastosDic
			else:
				jsonFieldsDic [fieldName] = {"value": value, "content": value}

		embedded_jsonData = json.dumps (jsonFieldsDic, ensure_ascii=False)
		pdfCanvas.setFont("Helvetica", 0)  # Set font size to 0 for hidden text
		pdfCanvas.drawString(100, 150, f"Embedded_jsonData: {embedded_jsonData}")

		return jsonFieldsDic

	def embedFieldsIntoPDFManifiesto (self, pdfCanvas, paramFields, formFields):
		jsonFieldsDic = {}
		for key, params in paramFields.items():
			fieldName    = params ["ecudocsField"]
			#value        = formFields [key].replace ("\r\n", "\n")
			value        = formFields [key]
			jsonFieldsDic [fieldName] = {"value": value, "content": value}

		embedded_jsonData = json.dumps (jsonFieldsDic, ensure_ascii=False)
		pdfCanvas.setFont("Helvetica", 0)  # Set font size to 0 for hidden text
		pdfCanvas.drawString(100, 150, f"Embedded_jsonData: {embedded_jsonData}")

		return jsonFieldsDic

	#----------------------------------------------------------------
	#-- Convert image box bounds to pdf box bounds
	#----------------------------------------------------------------
	def convertToImageToPdfBounds (self, imageBoxBounds):
		try:
			class Img: # Internal image used as background
				x, y          = imageBoxBounds [0], imageBoxBounds [1]
				width, height = imageBoxBounds [2], imageBoxBounds [3]

			class Pdf: # Bounds for output PDF
				x, y, width, height = None, None, None, None

			imgSize = self.getImageSize (self.ImgDocument)
			pdfSize = self.getPdfSize (self.PdfDocument)

			pdfWidth, pdfHeight = pdfSize [0], pdfSize [1]
			imgWidth, imgHeight = imgSize [0], imgSize [1]

			conversionFactor = pdfWidth / float (imgWidth);
			Pdf.x = int (Img.x * conversionFactor);
			Pdf.y = pdfHeight - int (Img.y * conversionFactor) 
			#Pdf.y = 20 + pdfHeight - int (Img.y * conversionFactor);

			Pdf.width  = int (Img.width * conversionFactor);
			Pdf.width  = int (Pdf.width - 0.02*Pdf.width);
			Pdf.height = int (Img.height * conversionFactor);

			return (Pdf.x, Pdf.y, Pdf.width, Pdf.height)
		except:
			print (f"Error: No se pudo convertir coordenadas de la imagen a Pdf")
			raise

	#----------------------------------------------------------------
	#-- Merge pdf background image with text and add a second page
	#----------------------------------------------------------------
	def merge_pdfs (self, docType, PdfDocument, text_pdf, outputPdfPath):
		output_pdf_writer = PdfWriter()

		page0 = PdfDocument.pages [0]
		page0.merge_page (text_pdf.pages [0])
		output_pdf_writer.add_page (page0)

		# Add the contract page
		if (docType.upper() == "CARTAPORTE" and self.pdfType == "ONE_PDF"):
			page1 = PdfDocument.pages [1]
			output_pdf_writer.add_page (page1)

		with open(outputPdfPath, 'wb') as output_pdf:
			output_pdf_writer.write(output_pdf)

	#----------------------------------------------------------------
	#----------------------------------------------------------------
	def getInputBoundsFromJsonFile (self, inputsJsonPath):
		paramFields = {}
		with open (inputsJsonPath) as fp:
			paramFields = json.load (fp)

		return paramFields

	#----------------------------------------------------------------
	#----------------------------------------------------------------
	def getImageSize (self, imageObject):
		width, height = imageObject.size
		return width, height

	def getImageSizeFromFile (self, docPath):
		try:
			# Open the PNG image
			with Image.open(docPath) as img:
				return self.getImageSize (img)
		except Exception as e:
			print(f"Error: {e}")
			return None

	#----------------------------------------------------------------
	#----------------------------------------------------------------
	def getPdfSize (self, pdfObject):
		# Get the dimensions from the first page (assuming all pages have the same size)
		first_page = pdfObject.pages [0]
		width, height = first_page.mediabox.width, first_page.mediabox.height
		return width, height

	def getPdfSizeFromFile (self, pdfPath):
		try:
			# Open the PDF file in binary mode
			with open(pdfPath, 'rb') as pdf_file:
				# Create a PDF reader object
				pdf_reader = PdfReader(pdf_file)
				return self.getPdfSize (pdf_reader)
		except Exception as e:
			print(f"Error: {e}")
			return None

#--------------------------------------------------------------------
# Main
#--------------------------------------------------------------------
if __name__ == "__main__":
    backgroundPdfPath = "background.pdf"  # Provide the path to your background PDF
    outputPdfPath = "output.pdf"  # Provide the desired output PDF path

    # Define text and bounds (x, y) on the page
    paramFields = {
        "Text1": (100, 200),
        "Text2": (300, 400),
        # Add more text bounds as needed
    }

    creadorPDF = CreadorPDF ("CARTAPORTE")
    creadorPDF.crearPDF (backgroundPdfPath, paramFields, outputPdfPath)

