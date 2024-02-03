// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', () => {
    // Get the modal and sprites
    let modal = document.getElementById('pokemon-modal');
    let sprites = document.querySelectorAll('.clickable-sprite');

    // Loop through sprites and add click event listener
    sprites.forEach(sprite => {
        sprite.addEventListener('click', async () => {
            // Get the Pokemon ID from the data attribute
            let pokemonId = sprite.dataset.pokemonId;
            console.log(pokemonId);

            // Check if pokemonId is valid
            if (pokemonId) {
                // Fetch Pokemon details asynchronously using AJAX
                try {
                    let response = await fetch(`/get_pokemon_details/${pokemonId}`);
                    let pokemonData = await response.json();

                    // Format types
                    let formattedTypes = pokemonData.types.join(', ');

                    // Format abilities
                    let formattedAbilities = pokemonData.abilities.join(', ');

                    // Format stats
                    let formattedStats = pokemonData.stats.map(stat => `${stat.name}: ${stat.value}`).join('\n');

                    // Create a string with various details
                    let detailsString = `ID: ${pokemonData.id}\n`;
                    detailsString += `Name: ${pokemonData.name}\n`;
                    detailsString += `Types: ${formattedTypes}\n`;
                    detailsString += `Abilities: ${formattedAbilities}\n`;
                    detailsString += `Stats:\n${formattedStats}`;

                    // Set the details in the modal
                    document.getElementById('pokemon-details').innerText = detailsString;

                    // Display the modal
                    modal.style.display = 'block';

                } catch (error) {
                    console.error('Error fetching Pokemon details:', error);
                }
            } else {
                console.error('Invalid Pokemon ID');
            }
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

    // Listen for the change event on the type dropdown
    $('#type').change(function() {
        // Submit the form when the type changes
        $('#pokemonForm').submit();
    });

    // Listen for the click event on the search button
    $('button[name="action"]').click(function() {
        // Submit the form when the search button is clicked
        $('#pokemonForm').submit();
    });
});
