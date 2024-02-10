document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('searchBtn').addEventListener('click', function() {
        document.getElementById('actionInput').value = 'search';
        document.getElementById('pokemonForm').submit();
    });

    document.getElementById('previousBtn').addEventListener('click', function() {
        document.getElementById('actionInput').value = 'previous';
        document.getElementById('pokemonForm').submit();
    });

    document.getElementById('nextBtn').addEventListener('click', function() {
        document.getElementById('actionInput').value = 'next';
        document.getElementById('pokemonForm').submit();
    });

    // Check if there's an error message from the backend
    if (errorMessage && errorMessage !== "None") {
        displayErrorMessage(errorMessage);
    }

    // Function to display error message
    function displayErrorMessage(message) {
        let messageContainer = document.getElementById('message-container');
        messageContainer.innerHTML = `<div class="alert alert-danger text-center">${message}</div>`;

        // Clear the message after 4 seconds
        setTimeout(() => {
            messageContainer.innerHTML = '';
        }, 4000);
    }
});