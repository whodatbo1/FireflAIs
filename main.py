import requests
import datetime
import pandas as pd
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import glob
import time

# From https://waarneming.nl/api/docs/misc.md#species-groups
INSECT_GROUP_IDS = [
    4,  # Butterflies
    8,  # Moths
    5,  # Dragonflies
    14, # Locusts and Crickets
    17, # Bees, Wasps and Ants
    18, # Flies
    16, # Beetles
    15, # Bugs, Plant Lice and Cicadas
    6,  # Other Insects
]

INSECT_GROUP_NAMES = {
    4: "Butterflies",
    8: "Moths",
    5: "Dragonflies",
    14: "Locusts and Crickets",
    17: "Bees, Wasps and Ants",
    18: "Flies",
    16: "Beetles",
    15: "Bugs, Plant Lice and Cicadas",
    6: "Other Insects",
}

def fetch_and_append_to_csv(species_group_id, target_date, filename):
    """
    Fetches all observations for a single species group on a specific day
    and appends them to the given CSV file, page by page.
    """
    print(f"Fetching observations for group {species_group_id} on {target_date.strftime('%Y-%m-%d')}")
    url = "https://waarneming.nl/api/v1/observations/"
    params = {
        'species_group': species_group_id,
        'date_after': target_date.strftime("%Y-%m-%d"),
        'date_before': (target_date + datetime.timedelta(days=1)).strftime("%Y-%m-%d"),
        'limit': 100,
        'offset': 0
    }

    print(f"Fetching observations for group {species_group_id} on {target_date.strftime('%Y-%m-%d')} with params: {params}")

    total_fetched = 0
    write_header = not os.path.exists(filename)

    while True:
        response = None
        for attempt in range(3): # Retry up to 3 times
            try:
                response = requests.get(url, params=params)
                response.raise_for_status()
                break  # Success
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429 and attempt < 2:
                    wait_time = 2 ** attempt
                    print(f"Rate limited for group {species_group_id} on {target_date}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"Request error for group {species_group_id} on {target_date}: {e}")
                    response = None
                    break
            except requests.exceptions.RequestException as e:
                print(f"Request error for group {species_group_id} on {target_date}: {e}")
                response = None
                break

        if response is None:
            break

        try:
            data = response.json()
        except ValueError:
            print(f"JSON decode error for group {species_group_id} on {target_date}.")
            break
            
        results = data.get('results', [])
        if not results:
            break

        total_fetched += len(results)
        
        parsed_data = []
        for obs in results:
            species_detail = obs.get('species_detail', {})
            point = obs.get('point', {})
            coordinates = point.get('coordinates', [None, None])
            location_detail = obs.get('location_detail', {})
            user_detail = obs.get('user_detail', {})
            parsed_data.append({
                'id': obs.get('id'),
                'common_name': species_detail.get('name'),
                'scientific_name': species_detail.get('scientific_name'),
                'date': obs.get('date'),
                'time': obs.get('time'),
                'count': obs.get('number'),
                'longitude': coordinates[0] if coordinates else None,
                'latitude': coordinates[1] if coordinates else None,
                'location': location_detail.get('name'),
                'observer': user_detail.get('name')
            })
        
        df = pd.DataFrame(parsed_data)
        df.to_csv(filename, mode='a', index=False, header=write_header)
        write_header = False

        if data.get('next') is None:
            break
        params['offset'] += len(results)

    print(f"Fetched {total_fetched} observations for group {species_group_id} on {target_date}")
    return total_fetched

def process_day(target_date):
    """
    Worker function for a thread. Fetches data for all insect groups for a single day
    and saves it to a single CSV file for that day.
    """
    print(f"Processing date: {target_date}")
    
    total_obs_for_day = 0
    for group_id in INSECT_GROUP_IDS:
        filename = f'observations_{target_date.strftime("%Y-%m-%d")}_{group_id}.csv'
        count = fetch_and_append_to_csv(group_id, target_date, filename)
        total_obs_for_day += count
        
    return f"Finished processing for date: {target_date}. Total observations: {total_obs_for_day}"

if __name__ == "__main__":
    print("Cleaning up old observation files...")
    for f in glob.glob("observations_*.csv"):
        os.remove(f)

    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=30)
    dates_to_process = [start_date + datetime.timedelta(days=i) for i in range((today - start_date).days)]

    with ThreadPoolExecutor(max_workers=7) as executor:
        print(f"Starting fetching for {len(dates_to_process)} days...")
        futures = [executor.submit(process_day, date) for date in dates_to_process]
        
        for future in as_completed(futures):
            try:
                result = future.result()
                print(result)
            except Exception as exc:
                print(f"A thread generated an exception: {exc}")
    
    print("\nAll finished.")
