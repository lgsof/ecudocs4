"""
Class for handling document parameters info
"""
class SessionInfo:
	def __init__ (self, request, documentParams):
		self.request    = request
		self.request.session    = request.session

		print ("\n\n--------------")
		session_data = self.request.session.items()
		session_data_str = ', '.join([f'{key}: {value}' for key, value in session_data])
		print (session_data_str)
		print ("--------------\n\n")

		self.docType    = documentParams ["docType"]
		self.docId      = documentParams ["pk"]
		self.docParamId = f"{self.docType}_{self.docId}"
		if self.docParamId not in self.request.session:
			self.request.session [self.docParamId] = {}

	def __str__  (self):
		text = f"+++ SessionInfo: '{self.docParamId}'"
		session_data = self.request.session.items()
		session_data_str = text + ', '.join([f'{key}: {value}' for key, value in session_data])
		return session_data_str


	def set (self, paramName, paramValue):
		self.request.session [self.docParamId][paramName] = paramValue

	def get (self, paramName):
		paramValue = None
		if self.exists (paramName):
			paramValue = self.request.session [self.docParamId][paramName]
		else:
			print (f"+++ SessionInfo: No existe parámetro '{paramName}' para documento '{self.docParamId}'")

		return paramValue

	def exists (self, paramName):
		try:
			docParam      = self.request.session [self.docParamId]
			docParamValue = docParam [paramName]
			return True
		except KeyError as ex:
			print(f"KeyError: The key '{ex.args[0]}' does not exist in the dictionary.")
			return False
    


		
