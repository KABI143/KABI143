import RPi.GPIO as GPIO
import time
from datetime import datetime, timedelta
from flask import Flask, request, render_template, jsonify
import json

app = Flask(__name__)

# Configuration
LIGHT_PIN = 17  # Change this to the GPIO pin connected to the relay module

BUFFER_TIME = 10  # Buffer time in seconds

# Load the last set times from a JSON file
try:
    with open('last_set_times.json', 'r') as file:
        last_set_times = json.load(file)
except (FileNotFoundError, json.JSONDecodeError):
    last_set_times = {'time_on': None, 'time_off': None}

def save_last_set_times():
    with open('last_set_times.json', 'w') as file:
        json.dump(last_set_times, file)

def setup():
    GPIO.setwarnings(False)  # Disable runtime warnings
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(LIGHT_PIN, GPIO.OUT)
    GPIO.output(LIGHT_PIN, GPIO.LOW)

def turn_on_light():
    print("Turning the light ON")
    GPIO.output(LIGHT_PIN, GPIO.HIGH)

def turn_off_light():
    print("Turning the light OFF")
    GPIO.output(LIGHT_PIN, GPIO.LOW)

@app.route('/')
def index():
    global last_set_times
    return render_template('set.html', time_on=last_set_times['time_on'], time_off=last_set_times['time_off'])

@app.route('/set_times', methods=['POST'])
def set_times():
    global last_set_times
    last_set_times['time_on'] = request.form['time_on']
    last_set_times['time_off'] = request.form['time_off']
    save_last_set_times()
    return render_template('set.html', time_on=last_set_times['time_on'], time_off=last_set_times['time_off'])

@app.route('/get_light_state')
def get_light_state():
    light_state = GPIO.input(LIGHT_PIN)
    return jsonify({'light_state': light_state})

def check_time():
    while True:
        current_time = datetime.now().strftime("%H:%M")

        if last_set_times['time_on'] and last_set_times['time_off']:
            time_on_dt = datetime.strptime(last_set_times['time_on'], "%H:%M")
            time_off_dt = datetime.strptime(last_set_times['time_off'], "%H:%M")
            buffer_time = timedelta(seconds=BUFFER_TIME)

            if time_on_dt - buffer_time <= datetime.strptime(current_time, "%H:%M") <= time_on_dt + buffer_time:
                turn_on_light()
            elif time_off_dt - buffer_time <= datetime.strptime(current_time, "%H:%M") <= time_off_dt + buffer_time:
                turn_off_light()
    # Check the time every minute

if __name__ == "__main__":
    setup()
    try:
        import threading
        t = threading.Thread(target=check_time)
        t.start()
        app.run(host='0.0.0.0',) # Run the Flask app on port 80
    except KeyboardInterrupt:
        GPIO.cleanup()
