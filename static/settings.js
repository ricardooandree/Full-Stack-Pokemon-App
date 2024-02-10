document.addEventListener('DOMContentLoaded', () => {    
    // Listen for clicks on submit changes for profile info and credentials
    document.querySelectorAll('button[name="action"]').forEach(button => {
        button.addEventListener('click', () => {
            document.getElementById('pokemonForm').submit();
        });
    });
    
    // Check if there's an error message from the backend
    if (errorMessage && errorMessage !== "None") {
        displayErrorMessage(errorMessage);
        console.log(errorMessage);
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