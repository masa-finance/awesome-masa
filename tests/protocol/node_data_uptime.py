import json
import requests
from config import API_URL, FILTER_DATE
from datetime import datetime, timedelta, timezone

def parse_readable_uptime(uptime_str):
    """Convert readable uptime string to a timedelta object."""
    units = {'days': 0, 'hours': 0, 'minutes': 0}
    for part in uptime_str.split():
        if part.isdigit():
            value = int(part)
        else:
            if 'day' in part:
                units['days'] = value
            elif 'hour' in part:
                units['hours'] = value
            elif 'minute' in part:
                units['minutes'] = value
    return timedelta(days=units['days'], hours=units['hours'], minutes=units['minutes'])

def test_uptime_less_than_elapsed():
    response = requests.get(API_URL)
    if response.status_code == 200:
        data = response.json()['data']
    else:
        print(f"Failed to fetch data: HTTP {response.status_code}")
        return

    # Convert FILTER_DATE to a datetime object
    filter_date = datetime.strptime(FILTER_DATE, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp()

    failures = []
    successes = []
    total_uptime = timedelta()

    # Filter nodes by firstJoined after FILTER_DATE
    filtered_data = [node for node in data if node['firstJoined'] >= filter_date]

    # Calculate total uptime for all filtered nodes
    for node in filtered_data:
        readable_uptime_str = node['accumulatedUptimeStr']
        accumulated_uptime = parse_readable_uptime(readable_uptime_str)
        total_uptime += accumulated_uptime

    for node in filtered_data:
        # Convert Unix timestamp to timezone-aware datetime object
        first_joined = datetime.fromtimestamp(node['firstJoined'], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        elapsed_time = now - first_joined
        
        # Use accumulatedUptimeStr for comparison
        readable_uptime_str = node['accumulatedUptimeStr']
        accumulated_uptime = parse_readable_uptime(readable_uptime_str)
        
        if accumulated_uptime >= elapsed_time:
            failures.append((node['peerId'], f"Accumulated uptime {accumulated_uptime} is not less than elapsed time {elapsed_time}"))
        else:
            successes.append(node['peerId'])

    print("Test Results:")
    if successes:
        print(f"Success - {len(successes)} nodes passed the uptime less than elapsed time test.")
        for peerId in successes:
            print(f"Peer ID: {peerId} is within the correct bounds.")
    if failures:
        print(f"Failures - {len(failures)} nodes did not pass the uptime less than elapsed time test.")
        for peerId, message in failures:
            print(f"Failure - Peer ID: {peerId}, Error: {message}")

    # Calculate and print the weight of each node's uptime
    print("\nUptime Weights:")
    for node in filtered_data:
        readable_uptime_str = node['accumulatedUptimeStr']
        accumulated_uptime = parse_readable_uptime(readable_uptime_str)
        uptime_weight = (accumulated_uptime / total_uptime) * 100
        print(f"Peer ID: {node['peerId']}, Uptime Weight: {uptime_weight:.2f}%")

# Ensure to run the test
test_uptime_less_than_elapsed()