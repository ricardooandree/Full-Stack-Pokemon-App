###################################################################################################
#######################################       IMPORTS       #######################################
###################################################################################################
import os
import pokebase as pb
import requests
import secrets
import tempfile

from flask import Flask, redirect, render_template, request, session, jsonify
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from werkzeug.exceptions import HTTPException
from datetime import datetime
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
from helperFunctions import validate_search_parameters, search_pokemon, validate_settings_parameters


###################################################################################################
###############################       APP CONFIGURATION/SETUP       ###############################
###################################################################################################
# Global variables for file uploads set up
UPLOAD_FOLDER = 'static/uploads/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}


# Flask-Session configuration - configure session to use filesystem (instead of signed cookies)
app = Flask(__name__)
app.config["SECRET_KEY"] = secrets.token_hex(16)  # Generates a 32-character hexadecimal string
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Database configuration + class-models
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.root_path, 'site.db')
db = SQLAlchemy(app)


class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    
    # Define the one-to-many relationship with PartyPokemon
    party_pokemons = db.relationship('PartyPokemon', backref='user', lazy=True)

    # Define the one-to-one relationship with UsersInfo
    user_info = db.relationship('UsersInfo', back_populates='user', uselist=False, lazy=True)

class PartyPokemon(db.Model):
    __tablename__ = 'partypokemon'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    pokemon_id = db.Column(db.Integer, nullable=False)
    pokemon_name = db.Column(db.String(80), nullable=False)

    
class UsersInfo(db.Model):
    __tablename__ = 'user_info'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    image_path = db.Column(db.String(255), nullable=True, default='DefaultValue')
    name = db.Column(db.String(60), nullable=True, default='DefaultValue')
    age = db.Column(db.Integer, nullable=True, default='DefaultValue')
    gender = db.Column(db.String(20), nullable=True, default='DefaultValue')
    country = db.Column(db.String(60), nullable=True, default='DefaultValue')
    city = db.Column(db.String(60), nullable=True, default='DefaultValue')
    join_date = db.Column(db.DateTime, nullable=True, default='DefaultValue')
    description = db.Column(db.Text, nullable=True, default='DefaultValue')

    user = db.relationship('Users', back_populates='user_info', lazy=True)


# Set the Pokebase cache location TODO: - local cache location
#pb.cache.set_cache('C:/Users/ricar/projects/cs50-final-project/.cache/pokebase')

# Get the temporary directory path
cache_directory = os.path.join(tempfile.gettempdir(), 'pokebase_cache')

# Ensure the cache directory exists
os.makedirs(cache_directory, exist_ok=True)

# Set the Pokebase cache location
pb.cache.set_cache(cache_directory)

# Global cache for Pokemon sprites and data
pokemon_sprites_cache = [pb.SpriteResource('pokemon', pokemon_id) for pokemon_id in range(1, 494)]
pokemon_data_cache = []


###################################################################################################
#############################       CACHING/FETCHING FUNCTIONS       ##############################
###################################################################################################
# Fetch pokemon data from the PokeAPI
def fetch_pokemon_data(url):
    # Send a GET request to the PokeAPI
    response = requests.get(url)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the JSON response
        pokemon_details = response.json()

        # Extract types, abilities, stats
        types = [type_data['type']['name'] for type_data in pokemon_details['types']]
        abilities = [ability_data['ability']['name'] for ability_data in pokemon_details['abilities']]
        stats = [{'name': stat_data['stat']['name'], 'value': stat_data['base_stat']} for stat_data in pokemon_details['stats']]
        
        # Create the Pokemon data dictionary
        pokemon_data = {
            'id': pokemon_details['id'],
            'name': pokemon_details['name'],
            'height': pokemon_details['height'],
            'weight': pokemon_details['weight'],
            'types': types,
            'abilities': abilities,
            'stats': stats,
        }
        
        # Check if the name is already in the cache
        for index, entry in enumerate(pokemon_data_cache):
            if entry['name'] == pokemon_data['name']:
                # Update existing entry
                pokemon_data_cache[index] = pokemon_data
                break
        
        # Return the pokemon data
        return pokemon_data
    else:
        # Print an error message if the request was not successful
        print(f"Failed to fetch Pokemon data. Status code: {response.status_code}")
        return None
    

# Pre-cache all pokemon names
def precache_pokemon_names():
    base_url = 'https://pokeapi.co/api/v2/pokemon/?limit=493'
 
    # Send a GET request to the PokeAPI to get a list of Pokemon names
    response = requests.get(f'{base_url}')
    
    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the JSON response
        data = response.json()

        # Extract Pokemon names from data
        for pokemon in data['results']:
            # Get pokemon name
            name = pokemon['name']
            
            # Create pokemon data dictionary with name
            pokemon_data = {
                'id': None,
                'name': name,
                'height': None,
                'weight': None,
                'types': None,
                'abilities': None,
                'stats': None,
            }
            
            # Add pokemon name to the global cache
            pokemon_data_cache.append(pokemon_data)
            
    else:
        # Print an error message if the request was not successful
        print(f"Failed to fetch Pokemon names. Status code: {response.status_code}")
        return None
    

# Batch fetch pokemon names and URLs from PokeAPI
def batch_fetch_pokemon(limit, i_party):
    base_url = 'https://pokeapi.co/api/v2/pokemon/'
    
    # Set limit if higher than 24
    limit = min(limit, 24)

    # Sets offset: 0 if first batch, 1 if second batch, etc.(offset = 24 -> data = 25 onwards)
    offset = i_party * limit

    # Create a set for all pokemon IDs
    pokemon_ids = set() 

    # Iterate pokemon_data_cache and get the pokemon IDs
    for pokemon_data in pokemon_data_cache:
        pokemon_id = pokemon_data.get('id')
        if pokemon_id is not None:
            pokemon_ids.add(pokemon_id)

    # Iterate pokemon_ids and cache pokemon if it doesn't exist
    for i in range(offset + 1, offset + limit + 1):
        # If pokemon not in cache
        if i not in pokemon_ids:
            pokemon_data = fetch_pokemon_data(f'{base_url}/{i}')
            
    return offset


# Fetch pokemon names by type
def fetch_pokemon_by_type(pokemon_type):
    url = f'https://pokeapi.co/api/v2/type/{pokemon_type}'
    pokemon_by_type = []
    
    # Send a GET request to the PokeAPI
    response = requests.get(url)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the JSON response
        data = response.json()

        # Extract pokemon names
        for pokemon in data['pokemon']:
            pokemon_name = pokemon['pokemon']['name']
            pokemon_by_type.append(pokemon_name)
        
        # Return the pokemon names
        return pokemon_by_type
    
    else:
        # Print an error message if the request was not successful
        print(f"Failed to fetch pokemons by type. Status code: {response.status_code}")
        return None


# Fetch pokemon data by ID
def fetch_pokemon_by_id(pokemon_id):
    # Check if data is already cached
    for pokemon_data in pokemon_data_cache:
        if pokemon_data['id'] == pokemon_id:
            return pokemon_data

    base_url = f'https://pokeapi.co/api/v2/pokemon/{pokemon_id}'
    
    return fetch_pokemon_data(base_url)


# Fetch pokemon data by name
def fetch_pokemon_by_name(pokemon_name):
    # Check if data is already cached
    for pokemon_data in pokemon_data_cache:
        if pokemon_data['name'] == pokemon_name:
            if pokemon_data['id'] is not None:
                return pokemon_data

    base_url = f'https://pokeapi.co/api/v2/pokemon/{pokemon_name}'
    
    return fetch_pokemon_data(base_url)


# Fetch user's party pokemon indexes
def fetch_user_party_pokemon_indexes(user_id):
    # Fetch pokemon IDs in the user's party from the database
    user_party_pokemons = PartyPokemon.query.filter_by(user_id=user_id).with_entities(PartyPokemon.pokemon_id).all()

    # Extract the pokemon IDs from the result set
    user_party_pokemon_ids = [pokemon_id for (pokemon_id,) in user_party_pokemons]
    
    # Transform the user pokemon IDs into sprite indexes
    user_party_indexes = []
    
    for id in user_party_pokemon_ids:
        user_party_indexes.append(id - 1)
        
    return user_party_indexes
        
        
# Checks if pokemon name exists
def pokemon_name_exists(pokemon_name):
    # Check if data is already cached
    for pokemon_data in pokemon_data_cache:
        if pokemon_data['name'] == pokemon_name:
            return True
        
    # Name doesn't exist
    return False


# Checks if pokemon ID exists
def pokemon_id_exists(pokemon_id):
    # Check if data is already cached
    for pokemon_data in pokemon_data_cache:
        if pokemon_data['id'] == pokemon_id:
            return True
        
    # ID doesn't exist
    return False
    
    
# Pre-cache all pokemon names
precache_pokemon_names()

# Pre-cache the first pokemon for the pokedex
fetch_pokemon_by_id(1)


###################################################################################################
#######################################       ROUTES        #######################################
###################################################################################################
@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


@app.errorhandler(HTTPException)
def page_not_found(e):
    return render_template("404.html"), 404

# TODO:
@app.route("/favicon.ico")
def favicon():
    return "", 204


@app.route("/", methods = ["GET"])
@login_required
def dashboard():
    # Fetch user's party pokemon indexes
    user_party_indexes = fetch_user_party_pokemon_indexes(session["user_id"])
    
    # Get user_info object
    user_info = UsersInfo.query.filter_by(user_id=session["user_id"]).first()
    
    # Get user object
    user = Users.query.filter_by(id=session["user_id"]).first()
    
    # Get user username
    username = user.username
    
    # Convert string to datetime object
    datetime_obj = datetime.strptime(str(user_info.join_date), "%Y-%m-%d %H:%M:%S.%f")

    # Format datetime object
    date = datetime_obj.strftime("%b %d, %Y")
    
    return render_template("dashboard.html", date=date, username=username, user_info=user_info, user_party_indexes=user_party_indexes, pokemon_sprites_cache=pokemon_sprites_cache)


@app.route("/login", methods=["GET", "POST"])
def login():
    # Forget any user_id
    session.clear()

    # Define message variables
    error_message = None

    # User reached route via POST
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Input validation
        if not username or not password:
            error_message = "Username and password are required"
        else:
            # Query database for user
            existing_user = Users.query.filter_by(username=username).first()

            # Ensure username exists and password is correct
            if not existing_user:
                error_message = "User doesn't exist"
            elif not check_password_hash(existing_user.password, password):
                error_message = "Incorrect password"
            else:
                # Remember which user has logged in
                session["user_id"] = existing_user.id

                # Redirect user to home page
                return redirect("/")

    # Render the login page with error message
    return render_template("homepage.html", login=True, error_message=error_message)


@app.route("/logout")
def logout():
    # Forget any user_id
    session.clear()
    
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    # Forget any user_id
    session.clear()

    # Define message variables
    error_message = None

    # User reached route via POST
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Input validation
        if not username:
            error_message = "Username is empty"
        elif not password:
            error_message = "Password is empty"
        elif not confirmation:
            error_message = "Password confirmation is empty"
        elif confirmation != password:
            error_message = "Passwords do not match"
        else:
            # Ensure username is available
            existing_user = Users.query.filter_by(username=username).first()
            if existing_user:
                error_message = "Username is taken"
            else:
                # Ensure password has at least 8 characters
                if len(password) < 8:
                    error_message = "Password must be at least 8 characters long"
                    
                else:
                    # Insert user into database
                    new_user = Users(username=username, password=generate_password_hash(password))
                    db.session.add(new_user)
                    db.session.commit()

                    # Add new entry of user_info to database
                    user_info = UsersInfo(user_id=new_user.id, join_date=datetime.now())
                    db.session.add(user_info)
                    db.session.commit()

                    # Log in the new user
                    session["user_id"] = new_user.id

                    # Redirect user to home page
                    return redirect("/")

    # Render the registration page with error message
    return render_template("homepage.html", register=True, error_message=error_message)


@app.route("/pokedex", methods=["GET", "POST"])
@login_required
def pokedex():
    # Initialize i in the session if it's not set
    if "i_pokedex" not in session:
        session["i_pokedex"] = 1
    
    pokemon_data = fetch_pokemon_by_id(session["i_pokedex"])
    
    # Define message variables
    error_message = None

    # User reached route via POST
    if request.method == "POST":
        action = request.form["action"]
        pokemon_name = request.form.get("pokemon_name")

        # If user clicks "Next"
        if action == "next":
            session["i_pokedex"] += 1
            pokemon_data = fetch_pokemon_by_id(session["i_pokedex"])

        # If user clicks "Previous"
        elif action == "previous":
            # If is not first pokemon
            if session["i_pokedex"] > 1:
                session["i_pokedex"] -= 1
            else:
                session["i_pokedex"] = 1 # IT ALREADY IS 1 - THIS IS EXTRA -
                
            pokemon_data = fetch_pokemon_by_id(session["i_pokedex"])

        # If user clicks "Search"
        elif action == "search":
            if not pokemon_name:
                error_message = "Pokemon name is empty"
            
            else:
                pokemon_name = pokemon_name.lower()
                if not pokemon_name_exists(pokemon_name):
                    error_message = "Pokemon name doesn't exist"
                else:
                    pokemon_data = fetch_pokemon_by_name(pokemon_name)
                    session["i_pokedex"] = pokemon_data['id']

    return render_template("pokedex.html", i=session["i_pokedex"] - 1, pokemon_sprites_cache=pokemon_sprites_cache, pokemon_data=pokemon_data, error_message=error_message)


@app.route("/add_to_party/<int:pokemon_id>", methods=["GET"])
@login_required
def add_to_party(pokemon_id):
    # Fetch pokemon data by ID
    pokemon_data = fetch_pokemon_by_id(pokemon_id)
    
    # Count number of entries in user's party
    count = PartyPokemon.query.filter_by(user_id=session["user_id"]).count()
    
    # Check if user's party is full
    if count < 6:
        # Add pokemon to user's party - insert into database
        new_pokemon = PartyPokemon(user_id=session["user_id"], pokemon_id=pokemon_id, pokemon_name=pokemon_data['name'])
        db.session.add(new_pokemon)
        db.session.commit()  
        
        return jsonify(success=True, message="Pokemon added to party successfully")
                             
    else:
        return jsonify(success=False, message="Party is full")


@app.route("/remove_from_party/<int:pokemon_id>", methods=["GET"])
@login_required
def remove_from_party(pokemon_id):
    # Fetch pokemon data by ID
    pokemon_data = fetch_pokemon_by_id(pokemon_id)
    
    # Count number of entries in user's party
    count = PartyPokemon.query.filter_by(user_id=session["user_id"]).count()
    
    # Check if user's party isn't empty
    if count > 0:
        # Remove pokemon from user's party - delete from database
        pokemon = PartyPokemon.query.filter_by(user_id=session["user_id"]).filter_by(pokemon_id=pokemon_id).first()
        db.session.delete(pokemon)
        db.session.commit()  
        
        return jsonify(success=True, message="Pokemon removed from party successfully")
                             
    else:
        return jsonify(success=False, message="Party is empty")
    
    
@app.route("/get_pokemon_details/<int:pokemon_id>", methods=["GET"])
@login_required
def get_pokemon_details(pokemon_id):
    # Fetch pokemon data by ID
    return fetch_pokemon_by_id(pokemon_id)


#HERE: def validate_search_parameters()


def search_by_type(pokemon_type):
    # Fetch pokemons with that type
    pokemon_names_by_type = fetch_pokemon_by_type(pokemon_type)
    
    # Check which pokemon names from id offset + 1 to offset + 1 + limit = 44 match with pokemon_names
    pokemon_ids = []
    limit = 493
    
    for i in range(0, limit):
        if pokemon_data_cache[i]['name'] in pokemon_names_by_type:
            pokemon_ids.append(i)
    
    return pokemon_ids


#HERE: def search_pokemon()
    
    
@app.route("/party", methods=["GET", "POST"])
@login_required
def party():
    error_message = None

    # Sets limit of sprites displayed
    limit = 44

    # Fetch user's party pokemon indexes
    user_party_indexes = fetch_user_party_pokemon_indexes(session["user_id"])

    # Initialize i in the session if it's not set
    if "i_party" not in session:
        session["i_party"] = 0
        offset = 0

    # If user reached route via POST
    if request.method == "POST":
        pokemon_type = request.form.get("pokemon_type")

        # User selected a "Type"
        if pokemon_type is not None:
            # Offset to search in the current page
            offset = session["i_party"] * limit
            i_type = search_by_type(pokemon_type)

            return render_template("party.html", pokemon_type=pokemon_type, i_type=i_type, pokemon_sprites_cache=pokemon_sprites_cache, user_party_indexes=user_party_indexes)

        # User had another action: previous, next or search
        else:
            action = request.form["action"]

            # User clicks "Next"
            if action == "next":
                session["i_party"] += 1

            # User clicks "Previous"
            elif action == "previous":
                # If is not first pokemon
                if session["i_party"] > 0:
                    session["i_party"] -= 1
                else:
                    session["i_party"] = 0  # IT ALREADY IS 1 - THIS IS EXTRA -

            # User clicks "Search"
            elif action == "search":
                pokemon_id = request.form.get("pokemon_id")
                pokemon_name = request.form.get("pokemon_name")

                # User input validation
                error_message = validate_search_parameters(pokemon_id, pokemon_name)
                if error_message:
                    # Offset to keep it on the same page
                    offset = session["i_party"] * limit
                    return render_template("party.html", error_message=error_message, pokemon_index=-1, pokemon_type='', i=offset, limit=limit, pokemon_sprites_cache=pokemon_sprites_cache, user_party_indexes=user_party_indexes)

                # Aux variables to store the pokemon ID by ID or name
                i_id = None
                i_name = None

                # Update aux variables
                if pokemon_id:
                    i_id = int(pokemon_id)

                if pokemon_name:
                    pokemon_name = pokemon_name.lower()
                    if pokemon_name_exists(pokemon_name):
                        pokemon_data = fetch_pokemon_by_name(pokemon_name)
                        i_name = pokemon_data['id']
                    else:
                        error_message = "Pokemon name doesn't exist"
                        return render_template("party.html", error_message=error_message, pokemon_index=-1, pokemon_type='', i=0, limit=limit, pokemon_sprites_cache=pokemon_sprites_cache, user_party_indexes=user_party_indexes)

                # Get searched pokemon index or error message
                search_result = search_pokemon(i_id, i_name)
                if isinstance(search_result, int):
                    pokemon_index = search_result
                    return render_template("party.html", pokemon_index=pokemon_index, pokemon_type='', i=0, limit=limit, pokemon_sprites_cache=pokemon_sprites_cache, user_party_indexes=user_party_indexes)
                else:
                    error_message = search_result

    # If user reached route via GET
    pokemon_index = -1
    pokemon_type = ''
    offset = session["i_party"] * limit

    return render_template("party.html", error_message=error_message, pokemon_index=pokemon_index, pokemon_type=pokemon_type, i=offset, limit=limit, pokemon_sprites_cache=pokemon_sprites_cache, user_party_indexes=user_party_indexes)


#HERE: def validate_settings_parameters()

    
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
           
           
@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    error_message = None
    
    # User reached route via POST
    if request.method == "POST":
        action = request.form["action"]

        if action == "avatar":
            # Check if the post request has the file part
            if 'file' not in request.files:
                error_message = "No file part"
                return render_template("settings.html", error_message=error_message)

            # Get the file
            file = request.files['file']

            # If no file selected
            if file.filename == '':
                error_message = "No selected file"
                return render_template("settings.html", error_message=error_message)

            if file and allowed_file(file.filename):
                # Generate a unique filename
                filename = secure_filename(file.filename)
                filename = str(session["user_id"]) + "_" + filename  # Example: 123_avatar.png

                # Save the file to the specified folder
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)

                # Update the user_info table with the file path or filename
                user_info = UsersInfo.query.filter_by(user_id=session["user_id"]).first()

                if user_info is not None:
                    user_info.image_path = file_path
                    db.session.commit()

                return redirect("/")
            else:
                error_message = "File type not allowed, allowed types: png, jpg, jpeg"
                return render_template("settings.html", error_message=error_message)

        elif action == "info":
            # Get user_info object
            user_info = UsersInfo.query.filter_by(user_id=session["user_id"]).first()

            # Get input form data
            name = request.form.get("name")
            age = request.form.get("age")
            gender = request.form.get("gender")
            country = request.form.get("country")
            city = request.form.get("city")
            description = request.form.get("description")

            # Input validation
            error_message = validate_settings_parameters(name, age, gender, country, city, description)
            
            if error_message:
                return render_template("settings.html", error_message=error_message)

            # Update the user_info table
            if name:
                user_info.name = name

            if age:
                user_info.age = age

            if gender:
                user_info.gender = gender

            if country:
                user_info.country = country

            if city:
                user_info.city = city

            if description:
                user_info.description = description

            # Commit the changes to the database
            db.session.commit()

        elif action == "credentials":
            # Get user object
            user = Users.query.filter_by(id=session["user_id"]).first()

            username = request.form.get("username")
            password = request.form.get("password")
            password_confirmation = request.form.get("password_confirmation")

            # Input validation
            if not username and not password and not password_confirmation:
                error_message = "Please input any info"
                return render_template("settings.html", error_message=error_message)

            # User wants to change username
            if username:
                existing_user = Users.query.filter_by(username=username).first()
                if existing_user:
                    error_message = "Username already exists"
                    return render_template("settings.html", error_message=error_message)

                # Update user's username
                user.username = username

                # Commit the changes to the database
                db.session.commit()

            # User wants to change password
            if password:
                if password_confirmation:
                    if password != password_confirmation:
                        error_message = "Passwords don't match"
                        return render_template("settings.html", error_message=error_message)

                    # Ensure password has at least 8 characters
                    if len(password) < 8:
                        error_message = "Password must be at least 8 characters long"
                        return render_template("settings.html", error_message=error_message)

                    # Update user's password with hash
                    user.password = generate_password_hash(password)

                    # Commit the changes to the database
                    db.session.commit()

                else:
                    error_message = "Insert password confirmation"
                    return render_template("settings.html", error_message=error_message)

            # User only input password confirmation
            elif password_confirmation:
                error_message = "Insert password both fields of password"
                return render_template("settings.html", error_message=error_message)

        # Redirect to the main page
        return redirect("/")

    else:
        return render_template("settings.html", error_message=error_message)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create tables before running the app
    #app.run(debug=True) # Development mode
    #app.run(debug=False, host='0.0.0.0', port=os.environ.get('PORT', 5000))
    app.run()