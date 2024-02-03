// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', () => {
    let modal = document.getElementById('pokemon-modal');
    let sprites = document.querySelectorAll('.clickable-sprite');
    let alert_message = document.getElementById('message-container');

    sprites.forEach(sprite => {
        sprite.addEventListener('click', async () => {
            let pokemonId = sprite.dataset.pokemonId;
    
            if (pokemonId) {
                try {
                    let response = await fetch(`/get_pokemon_details/${pokemonId}`);
                    let pokemonData = await response.json();
    
                    let formattedTypes = pokemonData.types.join(', ');
                    let formattedAbilities = pokemonData.abilities.join(', ');
                    let formattedStats = pokemonData.stats.map(stat => `${stat.name}: ${stat.value}`).join('\n');
    
                    let detailsString = `ID: ${pokemonData.id}\n`;
                    detailsString += `Name: ${pokemonData.name}\n`;
                    detailsString += `Types: ${formattedTypes}\n`;
                    detailsString += `Abilities: ${formattedAbilities}\n`;
                    detailsString += `Stats:\n${formattedStats}`;
    
                    document.getElementById('pokemon-details').innerText = detailsString;
    
                    // Remove existing buttons
                    document.querySelectorAll('.add-to-party-button').forEach(button => {
                        button.remove();
                    });

                    // Create and append "Add to Party" button
                    let addButton = document.createElement('button');
                    addButton.className = 'btn btn-primary mx-2 w-auto add-to-party-button';
                    addButton.type = 'button';
                    addButton.innerText = 'Add to Party';
                    addButton.dataset.pokemonId = pokemonId; // Set the dataset for later retrieval
                    addButton.addEventListener('click', async () => {
                        // Send AJAX request to add to party
                        try {
                            let response = await fetch(`/add_to_party/${pokemonId}`);
                            let result = await response.json();
                            
                            // Get the message container element
                            let messageContainer = document.getElementById('message-container');

                            // Create a new div element to hold the message
                            let messageDiv = document.createElement('div');

                            // Add classes to the div
                            messageDiv.classList.add('alert', 'alert-dark');
                            
                            // Set the role attribute
                            messageDiv.setAttribute('role', 'alert');

                            // Set the message text
                            messageDiv.innerText = result.message;

                            // Append the message div to the container
                            messageContainer.appendChild(messageDiv);

                            // Hide the message after a few seconds
                            setTimeout(() => {
                                messageDiv.style.display = 'none';
                                alert_message.style.display = 'none';

                            }, 5000);  // Hide after 5 seconds

                            // Hide the modal when successfully added to the party
                            modal.style.display = 'none';

                        } catch (error) {
                            console.error('Error adding to party:', error);
                        }
                    });
    
                    document.querySelector('.modal-content').appendChild(addButton);
    
                    modal.style.display = 'block';
                } catch (error) {
                    console.error('Error fetching Pokemon details:', error);
                }
            } else {
                console.error('Invalid Pokemon ID');
            }
        });
    });
    
    // Listen for the close button click
    document.querySelector('.close').addEventListener('click', () => {
        modal.style.display = 'none';
    });
    
    // Listen for clicks outside the modal to close it
    window.addEventListener('click', event => {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
    
    // Listen for the change event on the type dropdown
    $('#type').change(function () {
        $('#pokemonForm').submit();
    });
    
    // Listen for clicks on previous, next, or search buttons
    $('button[name="action"]').click(function () {
        $('#pokemonForm').submit();
    });
});
