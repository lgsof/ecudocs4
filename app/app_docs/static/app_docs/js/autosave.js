// Function to automatically save form data to the server
function autoSaveFormData() {
    const form = $('#forma_pdf');

    // Serialize form data into a JSON string
    const formData = {};
    form.serializeArray().forEach(item => {
        formData[item.name] = item.value;
    });

    // Send the data to the server using AJAX
    $.ajax({
        type: 'POST',
        url: '/save-data-endpoint/',  // Replace with your actual Django view URL
        dataType: 'json',
        data: formData,
        success: function(response) {
            console.log('Data saved successfully:', response);
        },
        error: function(error) {
            console.error('Error saving data:', error);
        }
    });
}

// Automatically save form data every 5 seconds (adjust as needed)
setInterval(autoSaveFormData, 5000);

