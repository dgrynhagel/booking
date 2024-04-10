import sys
from datetime import datetime, timedelta, timezone
import urllib.request
import json

logs_dir = './logs.txt'

def write_to_log(text):
    with open(logs_dir, 'a') as file:
        file.write(f"{text}\n")

def obtain_auth_token(refresh_token, email):
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
        'refreshToken': refresh_token
    }
    data = json.dumps(data).encode('utf-8')

    req = urllib.request.Request(url, data=data, headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req) as response:
            response_data = response.read().decode('utf-8')
            json_response = json.loads(response_data)
            write_to_log(f"Refresh token for account {email} succeed")
            return json_response['token'], json_response['refreshToken']
    except urllib.error.HTTPError as e:
        print(f"Error code: {e.code}")
        write_to_log(f"Refresh token for account {email} failed - please provide new one")
        print(e.reason)
        return None, None


def process_booking(email, auth_token, space_id):
    start_date = datetime.now() + timedelta(days=82, hours=8)  # Example: Use current date and time
    excluded_days = [False, False, False, False, False, True, True]

    def is_excluded_day(day):
        return excluded_days[day]

    if is_excluded_day(start_date.weekday()):
        write_to_log(f"Booking skipped (weekend) for space ID {space_id} - {email}")
        return

    url = f'https://fiserv.serraview.com/engage_api/v1/spaces/{space_id}/book'
    headers = {
        'Accept': 'application/json',
        'Accept-Language': 'pl,en;q=0.9,en-GB;q=0.8,en-US;q=0.7',
        'Authorization': f'Bearer {auth_token}',
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

    def iso_format(dt):
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    start_time_utc = start_date.astimezone(timezone.utc)
    end_time_utc = (start_date + timedelta(hours=10)).astimezone(timezone.utc)

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
            print(f"Booking successful for space ID {space_id}.")
            write_to_log(f"Booking successful for space ID {space_id} - {email}")
    except urllib.error.HTTPError as e:
        print(f"Failed to book for space ID {space_id}. Error code: {e.code}")
        write_to_log(f"Booking failure for space ID {space_id} - {email}")
        print(e.reason)


def update_refresh_token_in_file(file_path, new_refresh_token):
    with open(file_path, 'r+') as file:
        data = json.load(file)
        data['token'] = new_refresh_token
        file.seek(0)
        json.dump(data, file, indent=4)
        file.truncate()


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python booking.py <email> <refresh_token> <space_id> <file_path>")
        sys.exit(1)

    email = sys.argv[1]
    refresh_token = sys.argv[2]
    space_id = sys.argv[3]
    file_path = sys.argv[4]
    write_to_log("")

    auth_token, new_refresh_token = obtain_auth_token(refresh_token, email)
    if auth_token:
        process_booking(email, auth_token, space_id)
        if new_refresh_token:
            update_refresh_token_in_file(file_path, new_refresh_token)
    else:
        print("Failed to obtain authentication token.")
        sys.exit(1)
