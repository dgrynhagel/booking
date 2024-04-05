from flask import Flask, render_template, request, jsonify, send_file
import os
import json
import schedule
import threading
import time
import subprocess

port = 7171
app = Flask(__name__)

DATA_DIR = "data"
MAX_RECORDS = 5

# Define the function to execute booking.py for each JSON file
def execute_booking_script(email, refresh_token, space_id, data_path):
    script_path = os.path.join(os.path.dirname(__file__), "additional/booking.py")
    process = subprocess.Popen(["python", script_path, email, refresh_token, space_id, data_path],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)

    time.sleep(0.5)
    stdout, stderr = process.communicate()
    print("Output:", stdout.decode())
    print("Errors:", stderr.decode())


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
    schedule_file_reading_and_booking_process()
    while True:
        schedule.run_pending()
        time.sleep(1)


# Start the scheduler in a separate thread
scheduler_thread = threading.Thread(target=run_scheduler)
scheduler_thread.daemon = True
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
        filename = request.get_json().get('filename')
        filepath = os.path.join(DATA_DIR, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            return jsonify({'message': 'Record removed successfully'})
        else:
            return jsonify({'error': 'Record not found'}), 404

@app.route('/source')
def download_source():
    try:
        return send_file('additional/source.zip', as_attachment=True)
    except Exception as e:
        return str(e)

@app.route('/program')
def download_program():
    try:
        return send_file('additional/booking-tool.zip', as_attachment=True)
    except Exception as e:
        return str(e)

if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=port)
