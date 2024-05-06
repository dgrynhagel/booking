import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta, timezone
import urllib.request
import json
import time
import os

CONFIG_FILE = os.path.join(os.path.expanduser("~"), "automatyczne-bookowanie.json")
token_refreshed = ''

def refresh_token():
    global token_refreshed
    url = 'https://fiserv.serraview.com/api/v1/phoenix/auth/refresh'
    headers = {
        'Accept': 'application/json',
        'Accept-Language': 'pl,en;q=0.9,en-GB;q=0.8,en-US;q=0.7',
        'Connection': 'keep-alive',
        'Content-Type': 'application/json',
        'Origin': 'https://engage.spaceiq.com',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'cross-site',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0',
        'sec-ch-ua': '"Microsoft Edge";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"'
    }
    data = {
        'refreshToken': refresh_token_var.get()
    }
    data = json.dumps(data).encode('utf-8')  # Encode data to JSON

    req = urllib.request.Request(url, data=data, headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req) as response:
            response_data = response.read().decode('utf-8')
            json_response = json.loads(response_data)
            refresh_token_var.set(json_response['refreshToken'])
            token_refreshed = json_response['token']
    except urllib.error.HTTPError as e:
        print(f"Error code: {e.code}")
        print(e.reason)  # If you want to print the error response


def process_booking():
    refresh_token()
    start_year = int(year_var.get())
    start_month = int(month_var.get())
    start_day = int(day_var.get())
    num_days = int(num_days_var.get())
    email = email_var.get()
    token = token_refreshed
    space_id = space_id_var.get()
    excluded_days = [monday_var.get(), tuesday_var.get(), wednesday_var.get(), thursday_var.get(),
                     friday_var.get(), saturday_var.get(), sunday_var.get()]

    start_date = datetime(start_year, start_month, start_day)

    url = f'https://fiserv.serraview.com/engage_api/v1/spaces/{space_id}/book'
    headers = {
        'Accept': 'application/json',
        'Accept-Language': 'pl,en;q=0.9,en-GB;q=0.8,en-US;q=0.7',
        'Authorization': f'Bearer {token}',
        'Connection': 'keep-alive',
        'Content-Type': 'application/json',
        'Origin': 'https://engage.spaceiq.com',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'cross-site',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0',
        'sec-ch-ua': '"Microsoft Edge";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"'
    }

    def is_excluded_day(day):
        return excluded_days[day]

    def iso_format(dt):
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    success_days = []
    failure_days = []

    for i in range(num_days):
        current_date = start_date + timedelta(days=i)
        if is_excluded_day(current_date.weekday()):
            continue

        start_time_local = current_date.replace(hour=8, minute=0, second=0)
        end_time_local = current_date.replace(hour=17, minute=59, second=0)
        start_time_utc = start_time_local.astimezone(timezone.utc)
        end_time_utc = end_time_local.astimezone(timezone.utc)

        data = {
            'start': iso_format(start_time_utc),
            'end': iso_format(end_time_utc),
            'startTimeZone': 'Europe/Warsaw',
            'endTimeZone': 'Europe/Warsaw',
            'isAllDayBooking': False,
            'organizer': email
        }

        data = json.dumps(data).encode('utf-8')

        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        try:
            with urllib.request.urlopen(req) as response:
                print(f"Day {start_time_utc}: {response.status}")
                success_days.append(start_time_utc)
        except urllib.error.HTTPError as e:
            print(f"Day {start_time_utc}: {e.code}")
            print(e.reason)
            failure_days.append(start_time_utc)

        success_output.config(text="Success Days:\n" + "\n".join(map(str, success_days)))
        failure_output.config(text="Failure Days:\n" + "\n".join(map(str, failure_days)))
        root.update_idletasks()

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    else:
        return {}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

def on_exit():
    config = {
        "year": year_var.get(),
        "month": month_var.get(),
        "day": day_var.get(),
        "num_days": num_days_var.get(),
        "email": email_var.get(),
        "token": token_refreshed,
        "refresh_token": refresh_token_var.get(),
        "space_id": space_id_var.get(),
        "monday": monday_var.get(),
        "tuesday": tuesday_var.get(),
        "wednesday": wednesday_var.get(),
        "thursday": thursday_var.get(),
        "friday": friday_var.get(),
        "saturday": saturday_var.get(),
        "sunday": sunday_var.get()
    }
    save_config(config)
    root.destroy()

root = tk.Tk()
root.title("Booking Process")

main_frame = ttk.Frame(root, padding="10")
main_frame.grid(column=0, row=0, sticky=(tk.W, tk.E, tk.N, tk.S))

config = load_config()

year_var = tk.StringVar(value=config.get("year", "YYYY"))
month_var = tk.StringVar(value=config.get("month", "MM or M"))
day_var = tk.StringVar(value=config.get("day", "D"))
num_days_var = tk.StringVar(value=config.get("num_days", "1"))
email_var = tk.StringVar(value=config.get("email", ""))
refresh_token_var = tk.StringVar(value=config.get("refresh_token", ""))
space_id_var = tk.StringVar(value=config.get("space_id", ""))
monday_var = tk.BooleanVar(value=config.get("monday", False))
tuesday_var = tk.BooleanVar(value=config.get("tuesday", False))
wednesday_var = tk.BooleanVar(value=config.get("wednesday", False))
thursday_var = tk.BooleanVar(value=config.get("thursday", False))
friday_var = tk.BooleanVar(value=config.get("friday", True))
saturday_var = tk.BooleanVar(value=config.get("saturday", True))
sunday_var = tk.BooleanVar(value=config.get("sunday", True))

start_date_label = ttk.Label(main_frame, text="Start Date:")
start_date_label.grid(column=0, row=0, sticky=tk.W)

year_entry = ttk.Entry(main_frame, textvariable=year_var)
year_entry.grid(column=1, row=0, sticky=(tk.W, tk.E))

month_entry = ttk.Entry(main_frame, textvariable=month_var)
month_entry.grid(column=2, row=0, sticky=(tk.W, tk.E))

day_entry = ttk.Entry(main_frame, textvariable=day_var)
day_entry.grid(column=3, row=0, sticky=(tk.W, tk.E))

num_days_label = ttk.Label(main_frame, text="Number of Days:")
num_days_label.grid(column=0, row=1, sticky=tk.W)

num_days_entry = ttk.Entry(main_frame, textvariable=num_days_var)
num_days_entry.grid(column=1, row=1, sticky=(tk.W, tk.E))

email_label = ttk.Label(main_frame, text="E-mail:")
email_label.grid(column=0, row=2, sticky=tk.W)

email_entry = ttk.Entry(main_frame, textvariable=email_var)
email_entry.grid(column=1, row=2, sticky=(tk.W, tk.E))

token_label = ttk.Label(main_frame, text="Refresh Token:")
token_label.grid(column=0, row=3, sticky=tk.W)

token_entry = ttk.Entry(main_frame, textvariable=refresh_token_var)
token_entry.grid(column=1, row=3, sticky=(tk.W, tk.E))

space_id_label = ttk.Label(main_frame, text="Space ID:")
space_id_label.grid(column=0, row=4, sticky=tk.W)

space_id_entry = ttk.Entry(main_frame, textvariable=space_id_var)
space_id_entry.grid(column=1, row=4, sticky=(tk.W, tk.E))

exclude_days_label = ttk.Label(main_frame, text="Exclude days from booking:")
exclude_days_label.grid(column=0, row=5, columnspan=2, sticky=tk.W)

monday_checkbox = ttk.Checkbutton(main_frame, text="Monday", variable=monday_var)
monday_checkbox.grid(column=0, row=6, sticky=tk.W)

tuesday_checkbox = ttk.Checkbutton(main_frame, text="Tuesday", variable=tuesday_var)
tuesday_checkbox.grid(column=1, row=6, sticky=tk.W)

wednesday_checkbox = ttk.Checkbutton(main_frame, text="Wednesday", variable=wednesday_var)
wednesday_checkbox.grid(column=2, row=6, sticky=tk.W)

thursday_checkbox = ttk.Checkbutton(main_frame, text="Thursday", variable=thursday_var)
thursday_checkbox.grid(column=0, row=7, sticky=tk.W)

friday_checkbox = ttk.Checkbutton(main_frame, text="Friday", variable=friday_var)
friday_checkbox.grid(column=1, row=7, sticky=tk.W)

saturday_checkbox = ttk.Checkbutton(main_frame, text="Saturday", variable=saturday_var)
saturday_checkbox.grid(column=2, row=7, sticky=tk.W)

sunday_checkbox = ttk.Checkbutton(main_frame, text="Sunday", variable=sunday_var)
sunday_checkbox.grid(column=0, row=8, sticky=tk.W)

process_button = ttk.Button(main_frame, text="Process Booking", command=process_booking)
process_button.grid(column=1, row=9, sticky=tk.E)

success_output = ttk.Label(main_frame, text="Success Days:", wraplength=300)
success_output.grid(column=0, row=10, columnspan=3, sticky=(tk.W, tk.E))

failure_output = ttk.Label(main_frame, text="Failure Days:", wraplength=300)
failure_output.grid(column=3, row=10, columnspan=3, sticky=(tk.W, tk.E))

for child in main_frame.winfo_children():
    child.grid_configure(padx=5, pady=5)

root.protocol("WM_DELETE_WINDOW", on_exit)

root.mainloop()

