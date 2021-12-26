import requests
import json
import pandas as pd
import numpy as np
from datetime import datetime

from influxdb_client import InfluxDBClient, Point, WriteOptions


def getServerStats(filter):
    steamAPIKey = ""
    with open("steamapitoken.txt") as f:
        steamAPIKey = f.readline().strip()
    endpoint = "https://api.steampowered.com/IGameServersService/GetServerList/v1/"
    params = {
        "key":steamAPIKey,
        "limit": 20000,
        "filter": filter
    }
    response = requests.get(endpoint,params)
    if response.status_code != 200:
        print(f"Failed to request data: {response.text}")
        return None
    responseJSON = json.loads(response.text)
    if "response" not in responseJSON:
        print(f"Failed to request data: {response.text}")
        return None
    if "servers" not in responseJSON["response"]:
        print(f"Failed to request data: {response.text}")
        return None
    return responseJSON["response"]["servers"]

def getPlayerNumbers():
    baseFilter = "\\appid\\730\\white\\1\\empty\\1"
    otherMapFilter = "\\nand\\1\\map\\de_dust2,de_mirage,de_inferno"
    dust2 = "\\map\\de_dust2"
    mirage = "\\map\\de_mirage"
    inferno = "\\map\\de_inferno"

    dust2Stats = getServerStats(baseFilter+dust2)
    mirageStats = getServerStats(baseFilter+mirage)
    infernoStats = getServerStats(baseFilter+inferno)
    othermapStats = getServerStats(baseFilter+otherMapFilter)

    mapStats = [dust2Stats,mirageStats,infernoStats,othermapStats]
    combinedStats = []
    for stat in mapStats:
        if stat is None:
            continue
        if len(combinedStats) == 0:
            combinedStats = stat
        else:
            combinedStats += stat
    mapStats = pd.DataFrame(combinedStats)
    maps = mapStats[mapStats["map"].notna()]["map"].unique()
    maps.sort()

    region_us = [1,2,22,23,27]
    region_eu = [3,8,9,21,28]
    region_sa = [10,14,15,38]
    region_asia = [5,6,16,19,24,26,39]
    region_china = [12,17,25]
    region_other = [11,7]

    all_regions = region_us+region_eu+region_sa+region_asia+region_china+region_other

    region_dict = {
        "north_america":region_us,
        "europe": region_eu,
        "south_america": region_sa,
        "other": region_other,
        "asia": region_asia,
        "china": region_china
    }

    data = []
    for map in maps:
        current = mapStats[mapStats["map"]==map]
        max_players = current["max_players"].unique()
        max_players.sort()
        for max_player in max_players:
            currentMP = current[current["max_players"]==max_player]
            regions = currentMP["region"].unique()
            regions.sort()
            for k, v in region_dict.items():
                players = currentMP[currentMP["region"].isin(v)]["players"].sum()
                if players == 0:
                    continue
                data.append([map, k, max_player,players])
            otherplayers = currentMP[~currentMP["region"].isin(all_regions)]["players"].sum()
            if otherplayers != 0:
                data.append([map, "other", max_player,players])

    playerStatistics = pd.DataFrame(columns=["map", "region","max_players","players"],data=data)
    playerStatistics = playerStatistics.set_index(pd.DatetimeIndex(np.full(playerStatistics.index.size, datetime.utcnow())))
    return playerStatistics

def insertIntoDB(playerStatistics):
    credentials = []
    with open("influxdb_cred.json") as f:
        credentials = json.load(f)
    token = credentials["token"]
    org = credentials["org"]
    bucket = credentials["bucket"]
    url = credentials["url"]

    with InfluxDBClient(url=url, token=token, org=org) as _client:
        with _client.write_api(write_options=WriteOptions(batch_size=500,
                                                          flush_interval=10_000,
                                                          jitter_interval=2_000,
                                                          retry_interval=5_000,
                                                          max_retries=5,
                                                          max_retry_delay=30_000,
                                                          exponential_base=2)) as _write_client:
            _write_client.write(bucket, org, record=playerStatistics, data_frame_measurement_name='player_count',
                                data_frame_tag_columns=['map','max_players','region'])

def main():
    statisticsDF = getPlayerNumbers()
    insertIntoDB(statisticsDF)




if __name__ == "__main__":
    main()