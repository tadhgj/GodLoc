import urllib.request as urllib
from urllib.request import urlopen
import json
import time
import datetime
import iso8601
import os

import secretHeader

headers = secretHeader.headers

# outputFile: busData.json

# fetch data function:

def fetchBusDataNow():
    #set url var
    rutgersAgencyCode = 1323
    url = 'https://transloc-api-1-2.p.rapidapi.com/vehicles.json?agencies='+str(rutgersAgencyCode)+'&callback=call'

    #set headers
    global headers
    

    #fetch data
    request = urllib.Request(url, headers=headers)
    requestTime = time.time()
    response = urlopen(request, timeout=10)
    responseTime = time.time()

    # if response is not 200, return error
    if response.getcode() != 200:
        print("Error receiving data", response.getcode())
        return {
            "error": "Error receiving data",
            "code": str(response.getcode()),
            "errorContent": str(response.read()),
        }
    
    # if response is 200, return data
    else:
        data = response.read()

        # convert data to json
        data = json.loads(data)

        # run another function with this data...
        return data


def parseData(data, unixtimestamp):
    #1323 comes from the agency code for Rutgers
    try:
        busData = data["data"]["1323"]
    except:
        # return error object
        return 'Error: key "data" or key "1323" not found in data:' + str(data)

    #create list to store buses
    buses = {}

    #define function to process each bus
    def processBus(bus):
        #create dict to store bus data
        busDict = {}

        #add vehicle_id to dict
        busDict["busnumber"] = bus["call_name"]

        #add route_id to dict
        busDict["route_id"] = bus["route_id"]

        #add status to dict
        busDict["status"] = bus["tracking_status"]

        #add lat to dict
        busDict["lat"] = bus["location"]["lat"]

        #add lng to dict
        busDict["lng"] = bus["location"]["lng"]

        #add heading to dict
        busDict["heading"] = bus["heading"]

        #add speed to dict
        busDict["speed"] = bus["speed"]

        # optional stuff here

        #add capacity to dict
        busDict["capacity"] = bus["passenger_load"]

        #add segment to dict
        busDict["segment"] = bus["segment_id"]

        #add timestamp to dict
        # busDict["timestamp"] = bus["last_updated"]
        busDict['timestamp'] = unixtimestamp

        # add busDict to buses
        buses[bus["vehicle_id"]] = busDict
    
    #run a littany of checks to make sure the data is valid
    #check if this is a list
    if type(busData) is list:
        #for each item...
        for bus in busData:
            #check if it's a dict
            if type(bus) is dict:
                #check if it has a vehicle_id
                if "vehicle_id" in bus:
                    #check if it has a route_id
                    if "route_id" in bus:
                        #check if it has a location
                        if "location" in bus:
                            #check if location is a dict
                            if type(bus["location"]) is dict:
                                #check if location has lat and lng
                                if "lat" in bus["location"] and "lng" in bus["location"]:
                                    #check if lat and lng are numbers
                                    if type(bus["location"]["lat"]) is float and type(bus["location"]["lng"]) is float:
                                        #if so, process this bus and add it to the list
                                        processBus(bus)
                                    else:
                                        #if not, skip it
                                        print("Error: bus location lat or lng is not a number")
                                        return 'Error: bus location lat or lng is not a number'
                                else:
                                    #if not, skip it
                                    print("Error: bus location is missing lat or lng")
                                    return 'Error: bus location is missing lat or lng'
                            else:
                                #if not dict, skip it
                                print("Error: bus location is not a dict")
                                return 'Error: bus location is not a dict'
                        else:
                            #no location, skip it
                            print("Error: bus has no location")
                            return 'Error: bus has no location'
                    else:
                        #no route_id, skip it
                        print("Error: bus has no route_id, so it's route cannot be determined")
                        return "Error: bus has no route_id, so it's route cannot be determined"
                else:
                    #no vehicle_id, skip it
                    print("Error: bus has no vehicle_id")
                    return 'Error: bus has no vehicle_id'
            else:
                #if not dict, skip it
                print("Error: bus is not a dict")
                return 'Error: bus is not a dict'
    else:
        #if it's not a list, it's not the right data
        print("Error: busData is not a list")
        return 'Error: busData is not a list'

    #return the list of buses
    return buses


def newBusObject(inputvalue):
    # create new bus object
    return {
        "perm": {
            "busnumber": inputvalue['busnumber']
        },
        "semiperm": [
            {
                "t": inputvalue['timestamp'],
                "r_id": inputvalue['route_id'],
                "stat": inputvalue['status']
            }
        ],
        "temp": {
            inputvalue['timestamp']: {
                "l": [inputvalue['lat'], inputvalue['lng']],
                "h": inputvalue['heading'],
                "s": inputvalue['speed'],
                "c": inputvalue['capacity'],
                "p": inputvalue['segment'],
            }
        }
    }

def newSemiPerm(inputvalue):
    # create new semiperm object
    return {
        "t": inputvalue['timestamp'],
        "r_id": inputvalue['route_id'],
        "stat": inputvalue['status']
    }

def newTemp(inputvalue):
    # create new temp object
    return {
        "l": [inputvalue['lat'], inputvalue['lng']],
        "h": inputvalue['heading'],
        "s": inputvalue['speed'],
        "c": inputvalue['capacity'],
        "p": inputvalue['segment'],
    }


def modifyData(toWrite, inputdata, unixtimestamp):
    data = toWrite

    busList = data['data']['busList']

    # print(busList)

    busKeyList = list(busList.keys())

    # print(busKeyList)

    # if inputdata is a string:
    if type(inputdata) is str:
        # is an error... just add to timestamps
        data['timestamps'][unixtimestamp] = inputdata

    elif type(inputdata) is dict:

        # for each bus in inputdata (key and value)
        for key, value in inputdata.items():
            # check if key in busKeyList
            if key in busKeyList:
                # cool
                currentBusData = data['data']['busList'][key]
                # check if anything has changed in semiperm
                if currentBusData['semiperm'][0]['r_id'] != value['route_id'] or currentBusData['semiperm'][0]['stat'] != value['status']:
                    # if so, add new semiperm
                    currentBusData['semiperm'].append(newSemiPerm(value))

                # add new temp
                currentBusData['temp'][value['timestamp']] = newTemp(value)

            else:
                # adding new bus object
                data['data']['busList'][key] = newBusObject(value)

        data['timestamps'][unixtimestamp] = 'good'

    else:
        print("Error: inputdata is not a string or dict")
        data['timestamps'][unixtimestamp] = 'Error: writeFunc inputdata is not a string or dict'

    data['metadata']['lastUpdated'] = unixtimestamp

    return data


# write data function
def writeFunc(inputdata, unixtimestamp):
    print("Writing data...")

    # print(inputdata)

    try:
        # Check if the file exists
        if not os.path.isfile('busData.json'):
            # If the file doesn't exist, create it and write an empty JSON object to it
            with open('busData.json', 'w') as file:
                json.dump({
                    "metadata": {
                        "lastUpdated": 0
                    },
                    "data": {
                        "busList": {}
                    },
                    "timestamps": {}
                }, file)

        with open('busData.json', 'r+') as file:
            try:
                # Load the JSON data from the file
                data = json.load(file)
            except json.decoder.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
                # If the file is empty or doesn't contain valid JSON data, reset the data to default values
                data = {
                    "metadata": {
                        "lastUpdated": 0
                    },
                    "data": {
                        "busList": {}
                    },
                    "timestamps": {}
                }

            # print("Data from file:")
            # print(data)

            # Modify the data
            data = modifyData(data, inputdata, unixtimestamp)

            # print("Data to write:")
            # print(data)


            # Move the file cursor to the beginning of the file
            file.seek(0)

            # Write the modified data back to the file
            json.dump(data, file)

            # Close the file
            file.close()


    except IOError as e:
        print("Error reading or writing to the file.")
        print(e)


# start reading function
def startReading():
    print("Starting reading...")
    #without using .sleep, run at 4:00:00, 4:00:05, 4:00:10, ...

    # get current time (I don't care about timezones, use local time)
    tempcurrenttime = datetime.datetime.now()

    # get seconds since midnight
    tempsecondsSinceMidnight = (tempcurrenttime - tempcurrenttime.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()
    print("seconds since midnight: " + str(tempsecondsSinceMidnight))

    # round to int
    rounded = int(tempsecondsSinceMidnight)
    print("rounded: " + str(rounded))

    # get unix time:

    # check if after 2:00am but before 4:00am
    if rounded > twoam and rounded < fouram:
        # end of "bus day"
        # stop scanning
        # maybe run last function to transfer this somewhere else

        print("End of bus day. Stopping.")

        #INSERT END FUNC HERE#

        return

    #if time is integer multiple of 5, run fetchBusDataNow()
    if rounded % 5 == 0:
        print("is integer multiple of 5")
        try:
            while True:
                try:
                    unixtime = int(time.time())

                    print("Fetching bus data...")
                    startFuncTime = time.time()

                    # fetch data
                    data = fetchBusDataNow()
                    fetchtime = time.time()
                    print("Fetched bus data.")

                    # parse data
                    parsedData = parseData(data, unixtime)
                    parsetime = time.time()

                    # write data to file
                    writeFunc(parsedData, unixtime)
                    writetime = time.time()

                    endFuncTime = time.time()

                    # debug print times
                    print("fetch time: " + str(fetchtime - startFuncTime))
                    print("parse time: " + str(parsetime - fetchtime))
                    print("write time: " + str(writetime - parsetime))
                    print("total time: " + str(endFuncTime - startFuncTime))

                    # wait until 4:00:05, 4:00:10, ...
                    # time.sleep(5 - (endFuncTime - startFuncTime))

                    #wait until time is another integer multiple of 5
                    # now = time.time()
                    #ex. it's 5:03:01, wait until 5:03:05.00
                    #ex. it's 5:03:06, wait until 5:03:10.00
                    #ex. it's 5:03:13, wait until 5:03:15.00
                    # nowModFive = now % 5
                    # so 5:03:01.023 became 1.023
                    # subtract 1.023 from 5 to get 3.977
                    # wait 3.977 seconds
                    # delay = 5 - nowModFive
                    # print("waiting " + str(delay) + " seconds")

                    # time.sleep(delay)

                    #in one line:
                    time.sleep(5 - (time.time() % 5))

                except Exception as e:
                    exceptionTime = time.time()
                    writeFunc('Error: ' + str(e), unixtime)

                    print("Error: " + str(e))

                    time.sleep(5 - (time.time() % 5))


        except KeyboardInterrupt:
            pass


        #display to user that the script has stopped
        print("Stopping startReading()... and script.")

        #end of script
        

    else:
        #wait until 4:00:00, 4:00:05, 4:00:10, ...
        print("waiting until next 5 second interval - " + str(5 - (tempsecondsSinceMidnight % 5)) + " seconds")
        time.sleep(5 - (tempsecondsSinceMidnight % 5))
        startReading()

# script can be run at any time prior to 4:00am. determine if it is before 4:00am

# get current time (I don't care about timezones, use local time)
currenttime = datetime.datetime.now()

# get seconds since midnight
secondsSinceMidnight = (currenttime - currenttime.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()
print("seconds since midnight: " + str(secondsSinceMidnight))

# 4*60*60 = 14400
fouram = 14400
twoam = 7200

# if it is after 4am, start process
if secondsSinceMidnight > fouram:
    startReading()
elif secondsSinceMidnight < twoam:
    startReading()
else:
    #wait until 4am
    print("waiting until 4am - " + str(fouram - secondsSinceMidnight) + " seconds")
    time.sleep(fouram - secondsSinceMidnight)
    # that's pretty smart actually...
    startReading()

