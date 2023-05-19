import requests
from bs4 import BeautifulSoup
from xml.etree import ElementTree
import pytz
import json
import numpy as np
import datetime
import pandas as pd
import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS

headers = {
    'Content-Type': 'text/xml; charset=utf-8'
}

url= 'http://20.43.144.12/CQInterface/CQInterface.asmx'

def getCurData(username,password,buildingID):

    curData_request_payload = """<?xml version="1.0" encoding="utf-8"?>
    <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Header>
        <AuthHeader xmlns="http://tempuri.org/">
            <Username>"""+username+"""</Username>
            <Password>"""+password+"""</Password>
        </AuthHeader>
    </soap:Header>
    <soap:Body>
        <GetCurData xmlns="http://tempuri.org/">
            <BuildingID>"""+buildingID+"""</BuildingID>
        </GetCurData>
    </soap:Body>
    </soap:Envelope>"""

    # POST request
    response = requests.request("POST", url, headers=headers, data=curData_request_payload)
    soup = BeautifulSoup(response.text,features='xml')
    curResults = str(soup.GetCurDataResult).replace('<GetCurDataResult>','').replace('</GetCurDataResult>','')
    jsonContent =  json.loads(curResults)
    print(jsonContent)


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
    
    price = 0
    load =  0
    SOCcur= 0 
    battery1SOC = 0
    battery2SOC = 0
    battery1Voltage = 0
    battery2Voltage = 0
    solarPV1Generation = 0
    solarPV2Generation = 0
    temperature = 0
    irradiance = 0
    powernow = 0
    
    for item in jsonContent:

        if (item['EquipName']=='USEP'):
            price = item['Data']
        
        if (item['EquipName']=='Load'):
            load = item['Data']

        if (item['EquipName']=='Temperature'):
            temperature = item['Data']

        if (item['EquipName']=='Irradiance_Min15Avg'):
            irradiance = item['Data']
            
        if (item['EquipName']=='PowerNow'):
            powernow = item['Data']

        if (item['EquipName']=='SolarPVGeneration1'):
            solarPV1Generation = item['Data']
        
        if (item['EquipName']=='SolarPVGeneration2'):
            solarPV2Generation = item['Data']

        if (item['EquipName']=='BatterySOC1'):
            battery1SOC = item['Data']

        if (item['EquipName']=='BatterySOC2'):
            battery2SOC = item['Data']
            
        if (item['EquipName']=='BatteryVoltage1'):
            battery1Voltage = item['Data']

        if (item['EquipName']=='BatteryVoltage2'):
            battery2Voltage = item['Data']

    influx_data = []
    for item in jsonContent:
        timestamp_str = item['TimeStamp']
        timestamp_obj = datetime.datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S')
        # Convert to UTC timezone
        local_tz = pytz.timezone('Asia/Singapore')
        utc_tz = pytz.timezone('UTC')
        utc_time = local_tz.localize(timestamp_obj).astimezone(utc_tz)

        # Format the timestamp in RFC3339 format
        iso_timestamp = utc_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        # iso_timestamp = timestamp_obj.isoformat() + "Z"
        influx_item = {
            "measurement": "iEMS",
            "tags": {"tags":7000180501},
            "time": iso_timestamp,
            "fields":  {"USEP_price": float(price),
				"Load": float(load),
				"Temperature": float(temperature),
				"Irradiance_Min15Avg": float(irradiance),
				"PowerNow": float(powernow),
				"SolarPVGeneration1":float(solarPV1Generation),
				"SolarPVGeneration2":float(solarPV2Generation),
				"BatterySOC1":float(battery1SOC),
				"BatterySOC2":float(battery2SOC),
				"BatteryVoltage1": float(battery1Voltage),
				"BatteryVoltage2":float(battery2Voltage)
		    }
        }

        influx_data.append(influx_item)

    write_api.write(bucket=bucket, org=org, record=influx_data)

data = getCurData('murata','murata','7000180501')

