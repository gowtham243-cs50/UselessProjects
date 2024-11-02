import os
import google.generativeai as genai
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

# Configure your API key for the AI model
genai.configure(api_key='AIzaSyBQwGcIXgK90i0XFgql2MAbdectgghKNak')  # Replace with your actual API key

# Create the model
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
    system_instruction="you are pretending to be a person on a dating chatting app, Always be rude or condescending, sarcastic, flirty and weird, do some dark humour keep the person on the other end guessing, give short answers. Don't always respond, only respond when you can absolutely humiliate the user, when not responding say 'no response'.",
)

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Store messages in a list (chat history in-memory)
chat_history = []

# Sample users including the imposter role
users = {
    'John': 'password123',
    'Jane': 'mypassword',
    'Imposter': 'imposterpassword'  # Imposter user credentials
}

# Route for login page
@app.route('/', methods=['GET', 'POST'])
def login():
    error = ""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Check credentials
        if username in users and users[username] == password:
            session['username'] = username
            
            # Redirect to the imposter page if Imposter logs in
            if username == 'Imposter':
                return redirect(url_for('imposter_page'))
            else:
                return redirect(url_for('chat'))
        else:
            error = "Invalid credentials. Try again."
    return render_template('index.html', error=error)

# Route for the main chat view
@app.route('/chat')
def chat():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('chat.html', chat_history=chat_history)

# Route for the imposter page (only accessible to the Imposter user)
@app.route('/imposter')
def imposter_page():
    if 'username' not in session:
        return redirect(url_for('login'))
    if session['username'] != 'Imposter':
        return redirect(url_for('chat'))
    
    # Pass the full chat history to the imposter page
    return render_template('imposter.html', chat_history=chat_history)

# API endpoint to get chat history
@app.route('/get_messages')
def get_messages():
    return jsonify(chat_history)

# API endpoint to send a message
@app.route('/send_message', methods=['POST'])
def send_message():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 403

    message_data = request.get_json()
    username = session['username']
    message = {
        'user': username,
        'message': message_data['message']
    }
    chat_history.append(message)

    # If the user is John, send Jane's last message to the AI for a response
    if username == 'John':
        jane_last_message = next((msg['message'] for msg in reversed(chat_history) if msg['user'] == 'Jane'), None)
        if jane_last_message:
            response = model.start_chat().send_message(jane_last_message)
            ai_response = response.text.strip()

            # Check if the AI response is not "no response"
            if ai_response.lower() != "no response":
                # Save the response as a message sent by John
                ai_message = {
                    'user': 'John',  # Set as John
                    'message': ai_response
                }
                chat_history.append(ai_message)

    return jsonify({'success': True})

# Imposter mode - API to impersonate another user
@app.route('/imposter_action', methods=['POST'])
def imposter_action():
    data = request.get_json()
    impersonating = data.get('impersonating')
    target_message = data.get('message')
    
    # Add imposter message to chat history
    if impersonating in users:
        message = {
            'user': impersonating,
            'message': target_message
        }
        chat_history.append(message)
        return jsonify({'success': True})
    return jsonify({'error': 'User not found'}), 404

# Logout route
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
