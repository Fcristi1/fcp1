from flask import Flask, render_template, jsonify, redirect, request, url_for, session
import paho.mqtt.client as mqtt
import time
from datetime import datetime, timedelta

app = Flask(__name__)

# Secret key for session management
app.secret_key = 'your_secret_key'

# MQTT Broker setup
MQTT_BROKER = "192.168.0.110"  # Replace with your broker IP
MQTT_TOPIC_LED = "led/control"
MQTT_TOPIC_POT = "potentiometer/value"

pot_data = []  # Store potentiometer readings (timestamp, value)
led_status = "OFF"  # Initial LED status

# Correct credentials
USERNAME = "fcp1"
PASSWORD = "88888888"

# MQTT callback function to handle incoming messages
def on_message(client, userdata, message):
    global led_status
    if message.topic == MQTT_TOPIC_LED:
        led_status = message.payload.decode()
        print(f"LED Status: {led_status}")
    
    if message.topic == MQTT_TOPIC_POT:
        pot_value = int(message.payload.decode())
        timestamp = datetime.now()
        pot_data.append((timestamp, pot_value))
        
        # Keep only the last 24 hours of data
        cutoff_time = timestamp - timedelta(hours=24)
        pot_data[:] = [entry for entry in pot_data if entry[0] > cutoff_time]

# Setup MQTT client
client = mqtt.Client()
client.on_message = on_message
client.connect(MQTT_BROKER, 1883, 60)
client.subscribe(MQTT_TOPIC_LED)
client.subscribe(MQTT_TOPIC_POT)
client.loop_start()

@app.route('/')
def index():
    # If not logged in, redirect to the login page
    if 'logged_in' not in session or not session['logged_in']:
        return redirect(url_for('login'))
    
    return render_template('index.html', led_status=led_status)

@app.route('/get_pot_data')
def get_pot_data():
    timestamps = [entry[0] for entry in pot_data]
    values = [entry[1] for entry in pot_data]

    # Convert datetime to minutes from the start
    minutes = [(timestamp - timestamps[0]).total_seconds() / 60 for timestamp in timestamps]

    return jsonify({
        "timestamps": minutes,
        "values": values
    })

@app.route('/pot_graph')
def pot_graph():
    return render_template('pot_graph.html')

@app.route('/important_commands')
def important_commands():
    return render_template('important_commands.html')

@app.route('/system_diagram')
def system_diagram():
    return render_template('system_diagram.html')  # Render the system diagram page

@app.route('/control/<state>')
def control_led(state):
    if state == "on" or state == "off":
        client.publish(MQTT_TOPIC_LED, state)
        return f"LED {state.upper()}"
    return "Invalid command", 400

# Login page route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == USERNAME and password == PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))  # Redirect to the main page if login is successful
        else:
            return "Invalid credentials. Please try again.", 401

    return render_template('login.html')

# Logout route
@app.route('/logout')
def logout():
    session['logged_in'] = False
    return redirect(url_for('login'))  # Redirect to login page after logout

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
