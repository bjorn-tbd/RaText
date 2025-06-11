import random
import uuid
import datetime
import json

def generate_tick_data(start=25, end=86):
    tick_data = {}
    index = start
    while index <= end:
        # 2 control compartments
        for _ in range(1):
            if index > end:
                break
            tick_data[f"{index}_No_of_Control_tic"] = 8
            index += 1
            if index > end:
                break
            tick_data[f"{index}_No_of_Control_tic"] = 0
            index += 1

        # 3 treatment compartments (alive + dead = 8)
        for _ in range(3):
            if index + 1 > end:
                break
            alive = random.randint(0, 8)
            dead = 8 - alive
            tick_data[f"{index}_No_of_ticks_alive"] = alive
            index += 1
            tick_data[f"{index}_No_of_ticks_dead_"] = dead
            index += 1
    return tick_data

def generate_location_south_america():
    # Random coordinate within South America
    latitude = random.uniform(-35.0, 5.0)
    longitude = random.uniform(-81.0, -34.0)
    return {
        "latitude": round(latitude, 6),
        "longitude": round(longitude, 6),
        "accuracy": random.randint(3, 50),
        "UTM_Northing": random.randint(9000000, 10000000),
        "UTM_Easting": random.randint(500000, 700000),
        "UTM_Zone": "18M"
    }

def generate_entry():
    now = datetime.datetime.utcnow()
    formatted_date = now.strftime("%d/%m/%Y")
    iso_date = now.isoformat() + "Z"
    
    entry = {
        "ec5_uuid": str(uuid.uuid4()),
        "created_at": iso_date,
        "uploaded_at": iso_date,
        "created_by": "auto.generator@tbdint.com",
        "title": "Auto Test",
        "2_name_of_the_villag": "Auto Village",
        "3_What_type_of_herd_": random.choice(["Individual herd", "Communal herd"]),
        "4_how_many_cattle_we": random.randint(1, 10),
        "5_what_other_animal_": random.sample(["Dogs", "Goats", "Sheeps", "Chickens"], k=2),
        "6_What_acaricide_cla": random.sample(["Organochlorine", "Benzolphenyl ureas", "Macrocyclic lactones", "Organophosphates"], k=2),
        "7_what_methods_of_ac": ["Brush local application"],
        "8_what_is_the_level_": random.choice(["Tethering", "Communal grazing"]),
        "9_How_many_tbd_cases": random.randint(1, 10),
        "10_How_many_cattle_h": random.randint(1, 5),
        "11_What_are_the_most": random.sample(["East coast fever", "Babesiosis", "Anaplasmosis", "Dermatophilosis"], k=2),
        "12_What_are_the_othe": "",
        "13_This_questionnair": "",
        "14_This_questionnair": formatted_date,
        "16_batch_number": f"RaT{random.randint(25000, 26000)}-{random.randint(1, 9)}",
        "17_location": generate_location_south_america(),
        "18_Tick_type": random.choice(["Rhipicephalus appendiculatus", "Rhipicephalus decoloratus"]),
        "19_Acaricidal_class": random.choice(["Deltamethrin", "Cypermethrin"]),
        "20_starting_date": formatted_date,
        "21_starting_time": now.strftime("%H:%M"),
        "22_reading_time_24_h": formatted_date,
        "23_reading_time_24_h": now.strftime("%H:%M"),
    }

    # Add tick counts from 25 to 86 (4x7 grid, alternating pattern)
    entry.update(generate_tick_data())
    return entry

# Generate multiple entries
def generate_dataset(num_entries=5):
    base_json = {
        "meta": {
            "total": num_entries,
            "per_page": 50,
            "current_page": 1,
            "last_page": 1,
            "from": 1,
            "to": num_entries,
            "newest": datetime.datetime.utcnow().isoformat() + "Z",
            "oldest": datetime.datetime.utcnow().isoformat() + "Z"
        },
        "data": {
            "id": "ratext-academy",
            "type": "entries",
            "entries": [],
            "mapping": {
                "map_name": "EC5_AUTO",
                "map_index": 0
            }
        },
        "links": {
            "self": "https://five.epicollect.net/api/export/entries/ratext-academy?...",
            "first": "...",
            "prev": None,
            "next": None,
            "last": "..."
        }
    }

    for _ in range(num_entries):
        base_json["data"]["entries"].append(generate_entry())
    return base_json

# Example usage
if __name__ == "__main__":
    result = generate_dataset(982)
    with open("test3.json", "w") as f:
        json.dump(result, f, indent=4)
