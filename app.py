from flask import Flask, request, jsonify
from flask_mysqldb import MySQL
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Allow CORS for requests from specific origin
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})

# MySQL Configuration
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Password@123'
app.config['MYSQL_DB'] = 'scheduling_platform'

mysql = MySQL(app)

# Directory where uploaded files will be stored
UPLOAD_FOLDER = 'uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the directory exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# User Registration Route
@app.route('/register', methods=['POST'])
def register_user():
    try:
        data = request.json
        name = data.get('name')
        username = data.get('userid')  # Make sure to align with 'userid' from frontend
        email = data.get('email')
        phone = data.get('phone')
        password = data.get('password')

        # Check for missing fields
        if not all([name, username, email, phone, password]):
            return jsonify({'error': 'Missing required fields'}), 400

        hashed_password = generate_password_hash(password)
        user_unique_id = str(uuid.uuid4())

        cursor = mysql.connection.cursor()

        # Check if email or username already exists
        cursor.execute('''SELECT * FROM users WHERE email = %s OR username = %s''', (email, username))
        existing_user = cursor.fetchone()
        
        if existing_user:
            return jsonify({'error': 'Email or Username already exists!'}), 409

        # Insert new user into the database
        cursor.execute('''INSERT INTO users (name, username, email, phone, password, user_unique_id) 
                          VALUES (%s, %s, %s, %s, %s, %s)''', 
                          (name, username, email, phone, hashed_password, user_unique_id))
        mysql.connection.commit()

        cursor.close()

        return jsonify({'message': 'User registered successfully!', 'user_unique_id': user_unique_id}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# User Login Route
@app.route('/login', methods=['POST'])
def login_user():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT id, name, username, email, phone, password, user_unique_id FROM users WHERE email=%s', [email])
        user = cursor.fetchone()
        cursor.close()

        if user and check_password_hash(user[5], password):
            return jsonify({
                'id': user[0],
                'name': user[1],
                'username': user[2],
                'email': user[3],
                'phone': user[4],
                'user_unique_id': user[6]
            }), 200
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Profile Update Route (Create or Update Profile)
@app.route('/profile/<user_unique_id>', methods=['POST', 'PUT'])
def update_profile(user_unique_id):
    try:
        cursor = mysql.connection.cursor()

        # Check if the user_unique_id exists in the users table
        cursor.execute("SELECT * FROM users WHERE user_unique_id = %s", (user_unique_id,))
        user = cursor.fetchone()

        if not user:
            return jsonify({'error': 'User does not exist for the provided user_unique_id'}), 400

        # Proceed with updating or creating the profile as previously implemented
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        address = request.form.get('address')
        bio = request.form.get('bio')

        profile_picture = request.files.get('profile_picture')
        profile_picture_url = None

        if profile_picture:
            filename = secure_filename(profile_picture.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            profile_picture.save(filepath)
            profile_picture_url = filepath

        cursor.execute('''SELECT * FROM profiles WHERE user_unique_id = %s''', (user_unique_id,))
        existing_profile = cursor.fetchone()

        if existing_profile:
            # Update the profile if it exists
            cursor.execute(
                '''UPDATE profiles SET name=%s, email=%s, phone=%s, address=%s, bio=%s, profile_picture=%s, updated_at=CURRENT_TIMESTAMP 
                WHERE user_unique_id=%s''', 
                (name, email, phone, address, bio, profile_picture_url, user_unique_id)
            )
            message = 'Profile updated successfully!'
        else:
            # Insert a new profile if it doesn't exist
            cursor.execute(
                '''INSERT INTO profiles (user_unique_id, name, email, phone, address, bio, profile_picture) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)''', 
                (user_unique_id, name, email, phone, address, bio, profile_picture_url)
            )
            message = 'Profile created successfully!'

        mysql.connection.commit()
        cursor.close()

        return jsonify({'message': message}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Schedule Appointment Route
@app.route('/appointments', methods=['POST'])
def schedule_appointment():
    try:
        data = request.json
        user_id = data.get('user_id')
        date = data.get('date')
        description = data.get('description')

        if not user_id or not date:
            return jsonify({'error': 'Missing required fields'}), 400

        cursor = mysql.connection.cursor()
        cursor.execute('INSERT INTO appointments (user_id, date, description) VALUES (%s, %s, %s)', 
                       (user_id, date, description))
        mysql.connection.commit()
        cursor.close()

        return jsonify({'message': 'Appointment scheduled successfully!'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
