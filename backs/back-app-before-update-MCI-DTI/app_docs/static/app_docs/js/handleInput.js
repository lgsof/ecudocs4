/* Handle char inpus in textareas:
    Convert to uppercase
    Control maxlines
*/

function handleInput (textArea, maxChars, maxLines) {
	textArea.addEventListener ('input', controlMaxChars (textArea, maxChars));
	textArea.addEventListener ('keydown', controlMaxLines (textArea, maxLines));
}

// Check max lines considering when AUTOCOMPLETE is working
function controlMaxLines (textArea, maxLines) {
	return function (event) {
		if (event.key === 'Enter') {
			const numLines = textArea.value.split('\n').length;
			if (numLines >= maxLines) {
				event.preventDefault();
				//alert ('Límite de líneas alcanzado.')
			}
		}
	}
}

function controlMaxChars (textArea, maxChars) {
    return function (event) {
        const lines = textArea.value.split('\n');
    	convertToUpperCase (textArea);
        let cursorPosition = textArea.selectionStart;
        let currentLine = 0;
        let charCount = 0;

        for (let i = 0; i < lines.length; i++) {
            charCount += lines[i].length + 1; // +1 for the newline character
            if (charCount > cursorPosition) {
                currentLine = i;
                break;
            }
        }

        if (lines[currentLine].length > maxChars) {
            const excessChars = lines[currentLine].length - maxChars;
            textArea.value = textArea.value.substring(0, cursorPosition - excessChars) + textArea.value.substring(cursorPosition);
            textArea.selectionStart = textArea.selectionEnd = cursorPosition - excessChars;
			message = "Límite de caracteres alcanzado"
            alert (message)
        }
    }
  //});    
}

// Save the current cursor position
function convertToUpperCase (textArea) {
    var start = textArea.selectionStart;
    var end = textArea.selectionEnd;
    // Convert the text to uppercase and set it back to the textArea
    textArea.value = textArea.value.toUpperCase();
    // Restore the cursor position
    textArea.setSelectionRange (start, end);
}

