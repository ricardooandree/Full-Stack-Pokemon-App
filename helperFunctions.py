###################################################################################################
###################################       HELPER FUNCTIONS       ##################################
###################################################################################################
# Usage: /party
def validate_search_parameters(pokemon_id, pokemon_name):
    error_message = None

    if not pokemon_id and not pokemon_name:
        error_message = "Search parameters are empty"

    return error_message


# Usage: /party
def search_pokemon(i_id, i_name):
    error_message = None

    # Case 1: User inputs id and name
    if i_id and i_name:
        if i_id == i_name:
            return i_id - 1
        else:
            error_message = "Pokemon ID and Pokemon name don't match"

    # Case 2: User inputs id
    elif i_id:
        return i_id - 1

    # Case 3: User inputs name
    elif i_name:
        return i_name - 1

    # Default case: error
    else:
        error_message = "Invalid input"

    return error_message
    

# Usage: /settings
def validate_settings_parameters(name, age, gender, country, city, description):
    error_message = None

    if not name and not age and not gender and not country and not city and not description:
        error_message = "Please input any info"
    elif len(name) > 25:
        error_message = "Name is too long, 25 characters max please"
    elif len(country) > 25:
        error_message = "Country name is too long, 25 characters max please"
    elif len(city) > 25:
        error_message = "City name is too long, 25 characters max please"
    elif len(description) > 500:
        error_message = "Description is too long, 500 characters max please"

    return error_message
    