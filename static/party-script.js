// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', () => {
    // Get the modal and sprites
    let modal = document.getElementById('pokemon-modal');
    let sprites = document.querySelectorAll('.clickable-sprite');

    // Loop through sprites and add click event listener
    sprites.forEach(sprite => {
        sprite.addEventListener('click', () => {
            // Get the Pokemon ID from the data attribute
            //let pokemonId = sprite.dataset.pokemonId;

            // Set the details in the modal (replace with actual details)
            document.getElementById('pokemon-details').innerText = `Details for Pokemon ID`;

            // Display the modal
            modal.style.display = 'block';
        });
    });

    // Close the modal when the close button is clicked
    document.querySelector('.close').addEventListener('click', () => {
        modal.style.display = 'none';
    });

    // Close the modal if the user clicks outside of it
    window.addEventListener('click', event => {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
});
