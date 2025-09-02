async function loadInputParameters (parametersFile) {
	try {
		const response = await fetch(parametersFile);
		const jsonData = await response.json ();
		return (jsonData);
	}catch (error) {
		console.error('Error fetching JSON:', error);
		return null;
	}
}

