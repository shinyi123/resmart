import requests
from bs4 import BeautifulSoup
import json
import pytz
import numpy as np
import datetime
import pandas as pd
import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS

headers = {
    'Content-Type': 'text/xml; charset=utf-8'
}

url = 'http://20.43.144.12/UIInterface/UIInterface.asmx'
data =[]

def getHistorialData(username, password, buildingID, metric, startDate, endDate):
        curData_request_payload = """<?xml version="1.0" encoding="utf-8"?>
        <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
        <soap:Header>
            <AuthHeader xmlns="http://tempuri.org/">
            <Username>""" + username + """</Username>
            <Password>""" + password + """</Password>
            </AuthHeader>
        </soap:Header>
        <soap:Body>
            <GetHistoricalDataEx xmlns="http://tempuri.org/">
            <BuildingID>""" + buildingID + """</BuildingID>
            <metric>""" + metric + """</metric>
            <startDate>""" + startDate + """</startDate>
            <endDate>""" + endDate + """</endDate>
            </GetHistoricalDataEx>
        </soap:Body>
        </soap:Envelope>"""

        # POST request
        response = requests.request("POST", url, headers=headers, data=curData_request_payload)
        soup = BeautifulSoup(response.text, features='xml')
        curResults = str(soup.GetHistoricalDataExResult).replace('<GetHistoricalDataExResult>', '').replace('</GetHistoricalDataExResult>', '')
        jsonContent = json.loads(curResults)

        # Define Bucket
        bucket = "e5e536bd1a214e56"
        org = "47008c0dbbd1ecc5"
        token = "k1-AsOkI9sT6Rqx13y-lI9ud2XOgO74bxDfag6a6orOKtM6o5DP-FTq38mihHK5xxdXf8GjKqStLPaMtPGZiUg=="
        # Store the URL of your InfluxDB instance
        influx_url="http://203.117.54.2:8086"

        # Insert data into InfluxDB
        client = influxdb_client.InfluxDBClient(
        url=influx_url,
        token=token,
        org=org
        )

        write_api = client.write_api(write_options=SYNCHRONOUS)
        influx_data = []
        for item in jsonContent:
            timestamp_str = item['data']
            for d in timestamp_str:
                  timestamp = d['timeStamp']
                  timestamp_obj = datetime.datetime.strptime(timestamp, '%d%m%Y %H:%M:%S')
                
                  # create timezone object for Singapore
                  sg_tz = pytz.timezone('Asia/Singapore')

                 # convert datetime object to Singapore timezone
                  timestamp_sg = timestamp_obj.replace(tzinfo=pytz.utc).astimezone(sg_tz)
                  # Format the timestamp in RFC3339 format
                  iso_timestamp = timestamp_sg.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
                  influx_item = {
                    "measurement": "iEMS",
                    "tags": {"tags":7000180501},
                    "time": iso_timestamp,
                    "fields":{
                        "Cmd for Inverter 2": float(d['value'])
                    }
                }
                  influx_data.append(influx_item)

        write_api.write(bucket=bucket, org=org, record=influx_data)

        return data

# metric = ['Irradiance','PV100 Active Power','PV100 Energy Generation Today','PV100 Total Energy Generation','PV2000 Active Power','PV2000 Energy Generation Today',
#           'PV2000 Total Energy Generation','USEP','Load','Battery 1 Voltage','Battery 2 Voltage','Battery 1 SOC','Battery 2 SOC','Battery 1 Charging','Battery 1 Discharging',
#           'Battery 1 Charged Today','Battery 1 Discharged Today','Battery 2 Charging','Battery 2 Discharging','Battery 2 Charged Today','Battery 2 Discharged Today','Inverter 1 State',
#           'Inverter 1 Active Power','Inverter 1 Energy Generation Today','Inverter 1 Total Energy Generation','Inverter 2 State','Inverter 2 Active Power',
#           'Inverter 2 Energy Generation Today','Inverter 2 Total Energy Generation','Cmd for Inverter 1','Cmd for Inverter 2']


data = getHistorialData('murata', 'murata', '7000180501', 'Cmd for Inverter 2', '30062022', '31122022')
