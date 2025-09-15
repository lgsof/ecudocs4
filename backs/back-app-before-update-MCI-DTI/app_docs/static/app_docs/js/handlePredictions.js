// Handle field values predictions
// When field get the focus, it call view for predicting current value

function handlePredictions (docType, textareas) {
    if (docType === "CARTAPORTE") {
        const mainFields  = ["txt03","txt04","txt05","txt06","txt07","txt08","txt09"]
        const minorFields = ["txt10","txt11","txt12","txt16","txt18","txt21","txt22"]

        for (const ta of textareas) 
            if (mainFields.includes (ta.id) || minorFields.includes (ta.id)) 
                ta.addEventListener("focus", (event) => handleFocus(event, ta, mainFields));
    }
}

function handleFocus (event, textarea, mainFields) {
    console.log (">>> textarea: ", textarea)
	let originalTxtId = textarea.id
	numId = parseInt (originalTxtId.split ("txt")[1])

	// Iterate over all previous fields
	let inputsValues = {}
	for (let i=2; i < numId; i++) {
		loopTxtId = "txt" + String (i).padStart (2, '0');
        if (i < 10) // All main fields including "txt02"
		    inputsValues [loopTxtId] = document.getElementById (loopTxtId).value;
	}

	// console.log (">>> Values:", inputsValues)
	const csrftoken = getCookie('csrftoken');
	// Call view predict function
	$.ajax({
		type        : 'POST',
		url         : '/cartaporte/prediccion/' + originalTxtId,
		data        : JSON.stringify ({'txtId': originalTxtId, 'inputsTextValues': inputsValues}),
		contentType : 'application/json',
		headers     : { 'X-CSRFToken': csrftoken },  // Send token in headers
		success     : function (response) {
            if (textarea.value === "") {
			    textarea.value = response ["predictedValue"]
                textarea.select ()
            }
			//textarea.placeholder = response ["predictedValue"]
		},
		error       : function (xhr, status, error) {
			console.error ("Error prediciendo valor para input:", originalTxtId);
			console.error (error)
		}
	});
}

