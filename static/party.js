// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', () => {
    let modal = document.getElementById('pokemon-modal');
    let sprites = document.querySelectorAll('.clickable-sprite');
    let alertMessage = document.getElementById('message-container');

    sprites.forEach(sprite => {
        sprite.addEventListener('click', async () => {
            let pokemonId = sprite.dataset.pokemonId;
            let imageId = sprite.id;
    
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
                    document.querySelectorAll('.add-to-party-button, .remove-from-party-button').forEach(button => {
                        button.remove();
                    });
    
                    let addButton = document.createElement('button');
                    let buttonText, buttonClass;
    
                    if (imageId === 'party-sprite') {
                        buttonText = 'Remove from Party';
                        buttonClass = 'btn btn-danger mx-auto w-auto remove-from-party-button';
                    } else {
                        buttonText = 'Add to Party';
                        buttonClass = 'btn btn-primary mx-auto w-auto add-to-party-button';
                    }
    
                    addButton.className = buttonClass;
                    addButton.type = 'button';
                    addButton.innerText = buttonText;
                    addButton.dataset.pokemonId = pokemonId; // Set the dataset for later retrieval
    
                    addButton.addEventListener('click', async () => {
                        // Send AJAX request to add/remove from party
                        try {
                            let response = await fetch(`/${imageId === 'party-sprite' ? 'remove_from_party' : 'add_to_party'}/${pokemonId}`);
                            let result = await response.json();

                            // Store the alert message in session storage
                            sessionStorage.setItem('alertMessage', result.message);

                            // Close the modal
                            modal.style.display = 'none';

                            // Sets timeout to redirect after 0.15 seconds
                            setTimeout(() => {
                                window.location.href = '/party';
                            }, 150);  // Redirect after 0.15 seconds

                        } catch (error) {
                            console.error(`Error ${imageId === 'party-sprite' ? 'removing from' : 'adding to'} the party:`, error);
                        }
                    });

                    // Append the button to the modal content
                    document.querySelector('.modal-content').appendChild(addButton);
                    
                    // Show the modal
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
    
    // Check for the existence of the alert message in session storage
    let storedAlertMessage = sessionStorage.getItem('alertMessage');
    if (storedAlertMessage) {
        // Display the alert message
        let messageContainer = document.getElementById('message-container');
        let messageDiv = document.createElement('div');
        messageDiv.classList.add('alert', 'alert-dark');
        messageDiv.setAttribute('role', 'alert');
        messageDiv.innerText = storedAlertMessage;
        messageContainer.appendChild(messageDiv);

        // Hide the message after a few seconds
        setTimeout(() => {
            messageDiv.style.display = 'none';
            alertMessage.style.display = 'none';
        }, 5000);  // Hide after 5 seconds

        // Clear the stored alert message in session storage
        sessionStorage.removeItem('alertMessage');
    }

    // Listen for the change event on the type dropdown
    $('#type').change(function () {
        $('#pokemonForm').submit();
    });
    
    // Listen for clicks on previous, next, or search buttons
    $('button[name="action"]').click(function () {
        $('#pokemonForm').submit();
    });
});
