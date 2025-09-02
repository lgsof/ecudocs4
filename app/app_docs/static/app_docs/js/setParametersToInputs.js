// Convert to uppercase
//function handleInput (event) {
//		textArea = event.target;
//		convertToUpperCase (textArea);
//}
//
//// Save the current cursor position
//function convertToUpperCase (textArea) {
//	var start = textArea.selectionStart;
//	var end = textArea.selectionEnd;
//	// Convert the text to uppercase and set it back to the textArea
//	textArea.value = textArea.value.toUpperCase();
//	// Restore the cursor position
//	textArea.setSelectionRange(start, end);
//}

// Handle the event went user leaves out textareas
function handleBlur (textareaId, docType, textAreasDict, textarea) {
	if (docType == "CARTAPORTE")
		handleBlurForCartaporte (textareaId, docType, textAreasDict, textarea) 
	//else if (docType == "MANIFIESTO")
	//	handleBlurForManifiesto (textareaId, docType, textAreasDict, textarea) 
}

function handleBlurForCartaporte (textareaId, docType, textAreasDict, textarea) {
	//-- Copy "ciudad-pais. fecha" to other inputs (BYZA)
	if (textareaId == "txt06") {
		textAreasDict ["txt07"].value = textAreasDict ["txt06"].value
		textAreasDict ["txt19"].value = textAreasDict ["txt06"].value
	}
	//-- Calculate totals when change gastos table values
	remitenteInputs = {"txt17_11":"txt17_21","txt17_12":"txt17_22","txt17_13":"txt17_23"}
	if (Object.keys (remitenteInputs).includes (textareaId)) {
		if (textarea.value != "") {
			textarea.value = checkFormatNumber (textarea.value)
			textAreasDict [remitenteInputs [textareaId]].value = "USD"
		}

		setTotal (Object.keys (remitenteInputs), "txt17_14", textAreasDict);
		textAreasDict ["txt17_24"].value = "USD"
	}

	destinatarioInputs = {"txt17_31":"txt17_41","txt17_32":"txt17_42","txt17_33":"txt17_43"}
	if (Object.keys (destinatarioInputs).includes (textareaId)) {
		if (textarea.value != "") {
			textarea.value = checkFormatNumber (textarea.value)
			textAreasDict [destinatarioInputs [textareaId]].value = "USD"
		}

		setTotal (Object.keys (destinatarioInputs), "txt17_34", textAreasDict);
		textAreasDict ["txt17_44"].value = "USD"
	}
}


function handleBlurForManifiesto (textareaId, docType, textAreasDict, textarea) {
	if (textareaId == "txt28") {
		const csrftoken = getCookie('csrftoken');
		$.ajax({
			type : 'POST',
			url  : 'actualizar-cartaporte/',
			data : {
				'cartaporteNumber': textAreasDict [textareaId].value,
				'csrfmiddlewaretoken': csrftoken 
			},
			success : function (response) {
				console.log ("BD actualizada");
			},
			error: function (xhr, status, error) {
				console.error ("Error actualizand lo BD:", error);
			}
		});
	}
}


// Calculates the total of the textArray values and set to txtTotal
function setTotal (textArray, txtTotal, textAreasDict) {
	let total = 0.0
	for (let item of textArray) {
		text = textAreasDict [item].value
		if (text != "") {
			value = parseFloat (textAreasDict [item].value, 10);
			if (isNaN(value)) {
				alert ("Por favor ingrese valores numéricos válidos");
				textAreasDict [item].value = ""
				return;
			}
			total += value

		}
	}
	totalFormatted = checkFormatNumber (total)
	textAreasDict [txtTotal].value = totalFormatted; // Use toFixed to format output
}

// Check and format numbers to two end decimals
function checkFormatNumber (number) {
	formatedNumber = parseFloat (number).toFixed (2)
	return formatedNumber
}

// Set restrictions and styles for each input textarea
function setParametersToInputs (textAreas, inputParameters, docType) {
	textAreas.forEach (function (textArea) {
		const input               = inputsParameters [textArea.id];
		textArea.value            = input ["value"]
		//textArea.value            = textArea.id
		textArea.style.fontSize   = input ["fontSize"];
		textArea.style.textAlign  = input ["align"];
		textArea.style.position   = "absolute";

		textArea.style.left       = input ["x"]  + "px";
		textArea.style.top        = input ["y"]  + "px";
		textArea.style.width      = input ["width"]  + "px";
		textArea.style.height     = input ["height"] + "px";
		textArea.style.whiteSpace = 'nowrap'; // Prevents text from wrapping

		// Handle input event for autocomplete
        maxChars = parseInt (input ["maxChars"])
        maxLines = parseInt (input ["maxLines"])
        handleInput (textArea, maxChars, maxLines)
		const textAreasDict = Object.fromEntries(
  			textAreas.map (textarea => [textarea.id, textarea])
		);

		// Handle blur (onExit) event for auto filling
		textArea.addEventListener ("blur", function (event) {
			handleBlur (event.target.id, docType, textAreasDict, this);
		});
	});
}

