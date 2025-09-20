// Functions for autocomplete in document forms
//

// Get last CSRF token (after redirects)
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Create autocomplete for an entity
function createAutocomplete (entity) {
	const csrftoken = getCookie('csrftoken');
	let inputSelector = entity.inputSelector
	let sourceUrl     = "/" + entity.sourceUrl
	
	$(inputSelector).autocomplete({
		// List of autocomplete options
		source: function (request, response) {
			$.ajax({ url: sourceUrl, type:'POST', dataType: 'json', data: {query: request.term},

				beforeSend: function (xhr, settings) {
					// Include the CSRF token in the request headers
					xhr.setRequestHeader("X-CSRFToken", csrftoken);
				},

				success: function (data) {
                    //responseData = entity.onAjaxSuccess (data)
					response (data)
				}
			});
		},
		minLength: 2, 
		position: { my: "left top", at: "center top", collision: "none" }, // Customize the position
		select: function (event, ui) {
			entity.onItemSelected (ui)
            // Mark that a proper selection was made
            $(this).data('properlySelected', true);
			// Prevent the default behavior of filling the input with the selected value
			return false;
		}
	});

//    // Clear input when focus is lost without proper selection
//    $(inputSelector).on('blur', function(event) {
//        if (!$(this).data('properlySelected')) {
//            // Clear the input if not properly selected
//            $(this).val('');
//            // Also close the menu if it's open
//            $(this).autocomplete('close');
//        }
//        // Reset the flag for next time
//        $(this).data('properlySelected', false);
//    });
    
    // Also handle escape key to clear without selection
    $(inputSelector).on('keydown', function(event) {
        if (event.keyCode === 27 ||  event.keyCode === 37) { // Escape key
            $(this).val('');
            $(this).autocomplete('close');
            event.preventDefault();
        }
    });
}

// Return array of selected textAreas according to className
function getTextAreasByClassName (className) {
	let selectedTextAreas = []
	textAreas.forEach (textArea => {
		if (textArea.className === className) {
			selectedTextAreas.push (textArea)
		}
	});
	return (selectedTextAreas);
}

// Set autocomplete for document according to doc type
// Doc types: "cartaporte", "manifiesto", "declaración
function setAutocompleteForDocument (documentType) {
		// Clientes
		let clienteInputs = getTextAreasByClassName ("input_cliente")
		clienteInputs.forEach (inputName => {
			createAutocomplete(new AutoComplete (inputName, 'opciones-cliente')) 
		});
	
		// Ciudad-Pais. Fecha
		let inputsLugarFecha = getTextAreasByClassName ("input-lugar-fecha")
		inputsLugarFecha.forEach (inputName => {
			createAutocomplete(new AutoComplete (inputName, 'opciones-lugar-fecha' )) 
		});

		// Ciudad-Pais
		let inputsLugar = getTextAreasByClassName ("input_lugar")
		inputsLugar.forEach (inputName => {
			createAutocomplete(new AutoComplete (inputName, 'opciones-lugar' )) 
		});

		// Cartaportes
		let cartaporteInputs = getTextAreasByClassName ("input_cartaporte")
		cartaporteInputs.forEach (inputName => {
			createAutocomplete(new AutoCompleteCartaporte (inputName, 'opciones-cartaporte', documentType)) 
		});

		// Placa-Pais (Used in Declaracion)
		let placaPaisInputs = getTextAreasByClassName ("input_placaPais")
		placaPaisInputs.forEach (inputName => {
			createAutocomplete(new AutoComplete (inputName, 'opciones-placa')) 
		});

		// Vehiculo (Used in Manifiesto)
		let vehiculoInputs = getTextAreasByClassName ("input_vehiculo")
		vehiculoInputs.forEach (inputName => {
			createAutocomplete(new AutoCompleteVehiculo (inputName, 'opciones-vehiculo')) 
		});

		// Conductor Info (Used in Manifiesto)
		let conductorInputs = getTextAreasByClassName ("input_conductor")
		conductorInputs.forEach (inputName => {
			createAutocomplete(new AutoCompleteConductor (inputName, 'opciones-conductor')) 
		});

		// Numero Manifiesto (Used in Declaracion)
		let manifiestoInputs = getTextAreasByClassName ("input_manifiesto")
		manifiestoInputs.forEach (inputName => {
            console.log ("...In manifiestoInputs...")
			createAutocomplete(new AutoCompleteManifiesto (inputName, 'opciones-manifiesto')) 
		});
}

//----------------------------------------------------------------------
//----------------------------------------------------------------------

//-- General class for autocomplete only with the value of the option
class AutoComplete {
	// Init with input element and source URL which is handles in views
	constructor (inputSelector, sourceUrl, documentType=null) {
        console.log ("... In constructor ...")
		let inputId        = "#" + inputSelector
		this.inputSelector = inputSelector;
		this.sourceUrl     = sourceUrl;
		this.fullData      = null;
		this.documentType  = documentType; 
	}

	// When an item is selected, populate the textarea 
	onItemSelected (ui) {
		$(this.inputSelector).val (ui.item.info);
	}
}

//-------------------------------------------------------------------
//-- Autocomplet for "cartaporte" -----------------------------------
//-------------------------------------------------------------------
class AutoCompleteCartaporte extends AutoComplete {
	// When a cartaporte number is selected, populate related inputs
	onItemSelected (ui) {
		let values = ui.item.info.split ("||");
		
		let docInputsIds = null;
		if (this.documentType === "MANIFIESTO")
			docInputsIds = ["28","29","30","31","32_1","32_3","33_1","34","32_2","32_4","33_2", "40"];
		else if (this.documentType === "DECLARACION")
			docInputsIds = ["15","16","17","18","19_1","19_3","20_1","21","19_2","19_4","20_2"];
		else { 
			return null
		}

		for (let i=0; i < docInputsIds.length; i++) {
			let txtId = "txt" + docInputsIds [i]
			document.getElementById (txtId).value = values [i]
		}
	}
}

//-------------------------------------------------------------------
//-- Autocomplete for "manifiesto" 
//-------------------------------------------------------------------
class AutoCompleteManifiesto extends AutoComplete {
	// When a cartaporte number is selected, populate related inputs
	onItemSelected (ui) {
        let values = ui.item.info.split ("||")
		
		let docInputsIds = ["12","13","14","15","16","17","18","19_1","19_3","20_1","21","22","23"]

		for (let i=0; i < docInputsIds.length; i++) {
			let txtId = "txt" + docInputsIds [i]
			document.getElementById (txtId).value = values [i]
		}
	}
}

//-- AutoComplete for Vehiculo inputs
class AutoCompleteVehiculo extends AutoComplete {
	// When an item is selected, populate the textarea 
	onItemSelected (ui) {
        console.log ("...In AutoCompleteVehiculo...")
		let values = ui.item.info.split ("||");
		let input  = this.inputSelector
		if (input.id === "txt06") {
            //-- Vehiculo
			document.getElementById("txt04").value = getValidValue (values [2])
			document.getElementById("txt05").value = getValidValue (values [1])
			document.getElementById("txt06").value = getValidValue (values [0])
			document.getElementById("txt07").value = getValidValue (values [3])
            //-- Remolque
			document.getElementById("txt09").value = getValidValue (values [6])
			document.getElementById("txt10").value = getValidValue (values [5])
			document.getElementById("txt11").value = getValidValue (values [4])
			document.getElementById("txt12").value = getValidValue (values [7])
            //-- Conductor
			document.getElementById("txt13").value = getValidValue (values [8])
			document.getElementById("txt14").value = getValidValue (values [9])
			document.getElementById("txt15").value = getValidValue (values [10])
			document.getElementById("txt16").value = getValidValue (values [11])

		}else {
			document.getElementById("txt09").value = getValidValue (values [2])
			document.getElementById("txt10").value = getValidValue (values [1])
			document.getElementById("txt11").value = getValidValue (values [0])
			document.getElementById("txt12").value = getValidValue (values [3])
		}
	}
}

//-- Autocomplete Conductor inputs
class AutoCompleteConductor extends AutoComplete {
	// When an item is selected, populate the textarea 
	onItemSelected (ui) {
		let input = this.inputSelector
        let values = ui.item.info.split ("||")
		if (input.id === "txt13") {
			document.getElementById("txt13").value = values [0]
			document.getElementById("txt14").value = values [1]
			document.getElementById("txt15").value = values [2]
			document.getElementById("txt16").value = values [3]
			document.getElementById("txt17").value = values [4]
		}else {
			document.getElementById("txt18").value = values [0]
			document.getElementById("txt19").value = values [1]
			document.getElementById("txt20").value = values [2]
			document.getElementById("txt21").value = values [3]
			document.getElementById("txt22").value = values [4]
		}
	}
}
