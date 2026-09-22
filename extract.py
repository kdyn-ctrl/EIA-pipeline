import os #for accessing the environment variables
import json #handling json data
import requests #making API calls and sending http requests
from dotenv import load_dotenv #loading the environment variables from the .env file 

#get the key from the env file
load_dotenv()
# Crude oil inventories in the United States (Weekly)
API_URL = "https://api.eia.gov/v2/petroleum/stoc/wstk/data/"

#Define the parameters for the API call
params = {
    "api_key": os.getenv("EIA_API_KEY"),
    "frequency": "weekly",
    "data[0]": "value",
    "sort[0][column]": "period",
    "sort[0][direction]":"desc",
    "length": 50,
}

response = requests.get(API_URL, params=params, timeout=10)

if response.status_code == 200:
    with open("raw_data.json", "w") as f:
        json.dump(response.json(), f, indent=4) #indent=4 for better readability of the json file 
        print("Success: retrieved and saved 50 weeks of data.")
else: 
    print(f"Error Occured: {response.status_code}")
    print(response.text)
