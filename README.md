# CSGO Player Number Analysis
This project uses the steam web api to collect aggregate player numbers on official servers and save it to an instance of InfluxDB.

## Usage
* Make a venv and install packages from requirements.txt
* create steamapitoken.txt and add a steam web api token in the first line
* create influxdb_cred.json with keys "token" "org" "bucket" and "url" and their respective values
* run getData.py
