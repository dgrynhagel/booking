from flask import Flask, render_template, request, jsonify
import os
import json
import schedule
import threading
import time
from subprocess import Popen

app = Flask(__name__)

DATA_DIR = "data"
MAX_RECORDS = 20

# Define the function to execute booking.py for each JSON file
def execute_booking_script(email, refresh_token, space_id, data_path):
    script_path = os.path.join(os.path.dirname(__file__), "booking.py")
    Popen(["python", script_path, email, refresh_token, space_id, data_path])

# Schedule the execution of booking.py for each JSON file once a day at 00:01
def read_and_process_files():
    files = os.listdir(DATA_DIR)
    for file in files:
        file_path = os.path.join(DATA_DIR, file)
        file_content = open(file_path)
        record = json.load(file_content)
        email = record.get('email')
        refresh_token = record.get('token')
        space_id = record.get('space_id')
        file_content.close()
        execute_booking_script(email, refresh_token, space_id, file_path)


# Schedule the execution of reading files and processing bookings once a day at 00:01
def schedule_file_reading_and_booking_process():
    schedule.every().day.at("00:01").do(read_and_process_files)

# Run the scheduled jobs in a separate thread
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

# Start the scheduler in a separate thread
scheduler_thread = threading.Thread(target=run_scheduler)
scheduler_thread.start()

# Your Flask routes and functions below

def save_data(data):
    email = data.get('email')
    space_id = data.get('space_id')
    token = data.get('token')

    filename = f"{email}_{space_id}.json"
    filepath = os.path.join(DATA_DIR, filename)

    if len(os.listdir(DATA_DIR)) >= MAX_RECORDS:
        return jsonify({'error': 'Maximum number of records reached'}), 400

    with open(filepath, 'w') as f:
        f.write(json.dumps(data))
    return jsonify({'message': 'Data saved successfully'})

def update_data(data):
    email = data.get('email')
    space_id = data.get('space_id')
    token = data.get('token')

    filename = f"{email}_{space_id}.json"
    filepath = os.path.join(DATA_DIR, filename)

    if os.path.exists(filepath):
        with open(filepath, 'w') as f:
            f.write(json.dumps(data))
        return jsonify({'message': 'Data updated successfully'})
    return jsonify({'error': 'Record not found'}), 404

@app.route('/')
def index():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    files = os.listdir(DATA_DIR)
    records = []
    for file in files:
        with open(os.path.join(DATA_DIR, file)) as f:
            record = json.load(f)
            records.append(record)

    return render_template('index.html', records=records)

@app.route('/save', methods=['POST'])
def save_record():
    if request.method == 'POST':
        data = request.get_json()
        return save_data(data)

@app.route('/update', methods=['POST'])
def update_record():
    if request.method == 'POST':
        data = request.get_json()
        return update_data(data)

@app.route('/remove', methods=['POST'])
def remove_record():
    if request.method == 'POST':
        filename = request.form.get('filename')
        filepath = os.path.join(DATA_DIR, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            return jsonify({'message': 'Record removed successfully'})
        else:
            return jsonify({'error': 'Record not found'}), 404




if __name__ == "__main__":
    app.run(debug=True)


