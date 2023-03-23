import urllib.request as urllib
from urllib.request import urlopen
import time
import datetime
import iso8601
import os
import logging
import pytz
import sys

import secretHeader

#regular json
import json

#alternative json
import ujson as json


headers = secretHeader.headers

# outputFile: busData.json

# fetch data function:

#if running in vm:
# outputDir = '/root/bus/'
outputDirAdd = 'logs/'

#if running in mac:
outputDir = ''
outputDirAdd = 'logs/'

#log please!
loggerThing = logging.getLogger()
loggerThing.setLevel(logging.DEBUG)

# realtime log: test.log
realtimeLog = logging.FileHandler(outputDir+outputDirAdd+'test.log', 'w', 'utf-8')
realtimeLog.setFormatter(logging.Formatter('%(name)s %(message)s'))

# output log: GMT_day_time_busThird.log
start_time = int(time.time())
GMTTime = datetime.datetime.now()
eastern = pytz.timezone('US/Eastern')
ESTTime = GMTTime.astimezone(eastern)
generalLog = logging.FileHandler(outputDir+outputDirAdd+ESTTime.strftime("EST_%Y-%m-%d_%H:%M:%S")+'_busThird.log', 'w', 'utf-8')

# add two outputs to log system
loggerThing.addHandler(realtimeLog)
loggerThing.addHandler(generalLog)
    
#if mac
loggerThing.addHandler(logging.StreamHandler(sys.stdout))

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
        # print("Error receiving data", response.getcode())
        logging.error("66 Error receiving data", response.getcode())

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

        #SHOULD I ROUND LOCATION?
        #4	0.0001	    11.1 m
        #5	0.00001	    1.11 m
        #6	0.000001	0.111 m
        #7	0.0000001	1.11 cm
        #so, 5 or 6 is probably good enough

        #add lat to dict
        latRound = round(bus["location"]["lat"], 6)
        busDict["lat"] = latRound

        #add lng to dict
        lngRound = round(bus["location"]["lng"], 6)
        busDict["lng"] = lngRound

        #add heading to dict
        # honestly, this is only useful for visualization
        # segment tangent line could display this just as well
        busDict["heading"] = bus["heading"]

        #add speed to dict
        busDict["speed"] = bus["speed"]

        # optional stuff here

        # I should definitely round capacity, there is literally no reason to need 10 decimals.
        #add capacity to dict
        capacityRound = round(bus["passenger_load"], 3)
        busDict["capacity"] = capacityRound

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
                                        # print("Error: bus location lat or lng is not a number")
                                        logging.error("Error: bus location lat or lng is not a number")
                                        return 'Error: bus location lat or lng is not a number'
                                else:
                                    #if not, skip it
                                    # print("Error: bus location is missing lat or lng")
                                    logging.error("Error: bus location is missing lat or lng")
                                    return 'Error: bus location is missing lat or lng'
                            else:
                                #if not dict, skip it
                                # print("Error: bus location is not a dict")
                                logging.error("Error: bus location is not a dict")
                                return 'Error: bus location is not a dict'
                        else:
                            #no location, skip it
                            # print("Error: bus has no location")
                            logging.error("Error: bus has no location")
                            return 'Error: bus has no location'
                    else:
                        #no route_id, skip it
                        # print("Error: bus has no route_id, so it's route cannot be determined")
                        logging.error("Error: bus has no route_id, so it's route cannot be determined")
                        return "Error: bus has no route_id, so it's route cannot be determined"
                else:
                    #no vehicle_id, skip it
                    # print("Error: bus has no vehicle_id")
                    logging.error("Error: bus has no vehicle_id")
                    return 'Error: bus has no vehicle_id'
            else:
                #if not dict, skip it
                # print("Error: bus is not a dict")
                logging.error("Error: bus is not a dict")
                return 'Error: bus is not a dict'
    else:
        #if it's not a list, it's not the right data
        # print("Error: busData is not a list")
        logging.error("Error: busData is not a list")
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
                "stat": inputvalue['status'],
                "seg": inputvalue['segment'],
            }
        ],
        "temp": {
            inputvalue['timestamp']: {
                "l": [inputvalue['lat'], inputvalue['lng']],
                "h": inputvalue['heading'],
                "s": inputvalue['speed'],
                "c": inputvalue['capacity'],
            }
        }
    }

def newFileObj():
    # create new file object
    return {
        "metadata": {
            "lastUpdated": 0
        },
        "data": {
            "busList": {}
        },
        "timestamps": {}
    }

def newSemiPerm(inputvalue):
    # create new semiperm object
    return {
        "t": inputvalue['timestamp'],
        "r_id": inputvalue['route_id'],
        "stat": inputvalue['status'],
        "seg": inputvalue['segment'],
    }

def newTemp(inputvalue):
    # create new temp object
    return {
        "l": [inputvalue['lat'], inputvalue['lng']],
        "h": inputvalue['heading'],
        "s": inputvalue['speed'],
        "c": inputvalue['capacity'],
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
                semiPermLength = len(currentBusData['semiperm'])-1
                if currentBusData['semiperm'][semiPermLength]['r_id'] != value['route_id'] or \
                currentBusData['semiperm'][semiPermLength]['stat'] != value['status'] or \
                currentBusData['semiperm'][semiPermLength]['seg'] != value['segment']:
                    # if so, add new semiperm
                    currentBusData['semiperm'].append(newSemiPerm(value))

                # add new temp
                currentBusData['temp'][value['timestamp']] = newTemp(value)

            else:
                # adding new bus object
                data['data']['busList'][key] = newBusObject(value)

        data['timestamps'][unixtimestamp] = 'good'

    else:
        # print("Error: inputdata is not a string or dict")
        logging.error("287 Error: inputdata is not a string or dict")

        data['timestamps'][unixtimestamp] = 'Error: writeFunc inputdata is not a string or dict'

    data['metadata']['lastUpdated'] = unixtimestamp

    return data


# write data function
def writeFunc(inputdata, unixtimestamp):
    global outputDir
    global dayStr

    #track time of each step
    writeStart = time.time()

    # print("Writing data...")
    loggerThing.info("Writing data...")

    # print(inputdata)

    #get fileName
    date_str = dayStr
    outDir = outputDir + "busData-" + date_str + ".json"

    try:
        # Check if the file exists
        if not os.path.isfile(outDir):
            # If the file doesn't exist, create it and write an empty JSON object to it
            with open(outDir, 'w') as file:
                json.dump({
                    "metadata": {
                        "lastUpdated": 0
                    },
                    "data": {
                        "busList": {}
                    },
                    "timestamps": {}
                }, file)

            logging.info("New file created: {"+outDir+"}")
        
        else:
            # file exists then
            thing = True

        with open(outDir, 'r+') as file:
            try:
                # Load the JSON data from the file
                data = json.load(file)
                loadTime = time.time()
                # print("Load time: "+str(loadTime-writeStart))
                loadtime = loadTime-writeStart
                loadtimeround = round(loadtime, 5)
                loggerThing.info("Load  time: "+str(loadtimeround))

            except json.decoder.JSONDecodeError as e:
                # print("Error decoding JSON: {e}")
                logging.error("331 Error decoding JSON: {"+str(e)+"}")

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

                logging.info("File reset to default values: {"+outDir+"}")

            # print("Data from file:")
            # print(data)

            # Modify the data
            data = modifyData(data, inputdata, unixtimestamp)
            modifyTime = time.time()
            modifytime = modifyTime-loadTime
            modifytimeround = round(modifytime, 5)
            loggerThing.info("Modif time: "+str(modifytimeround))

            # print("Data to write:")
            # print(data)


            # Move the file cursor to the beginning of the file
            file.seek(0)

            # Write the modified data back to the file
            json.dump(data, file)

            # Close the file
            file.close()
            fileWriteTime = time.time()
            filewritetime = fileWriteTime-modifyTime
            filewritetimeround = round(filewritetime, 5)
            loggerThing.info("File write: "+str(filewritetimeround))


    except IOError as e:
        # print("Error reading or writing to the file.")
        logging.error("366 Error reading or writing to the file.")
        # print(e)
        logging.debug(e)

    writeEnd = time.time()
    # print("Time to write: " + str(writeEnd - writeStart))
    writeTetalTime = writeEnd - writeStart
    # round
    writeTetalTime = round(writeTetalTime, 5)
    logging.info("Write  int: " + str(writeTetalTime))

    # print("Done writing data.")
    logging.info("Written.")


# start reading function
def startReading():
    # print("Starting reading...")
    logging.info("Starting reading...")
    #without using .sleep, run at 4:00:00, 4:00:05, 4:00:10, ...

    # get current time (I don't care about timezones, use local time)
    tempcurrenttime = datetime.datetime.now()

    # get seconds since midnight
    tempsecondsSinceMidnight = (tempcurrenttime - tempcurrenttime.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()
    # print("seconds since midnight: " + str(tempsecondsSinceMidnight))
    logging.info("reading: seconds since midnight: " + str(tempsecondsSinceMidnight))

    # round to int
    rounded = int(tempsecondsSinceMidnight)
    # print("rounded: " + str(rounded))
    logging.info("rounded: " + str(rounded))

    # get unix time:

    # check if after 2:00am but before 4:00am
    if rounded > twoam and rounded < fouram:
        # end of "bus day"
        # stop scanning
        # maybe run last function to transfer this somewhere else

        # print("End of bus day. Stopping.")
        logging.info("End of bus day. Stopping.")

        #INSERT END FUNC HERE#

        return

    #if time is integer multiple of 5, run fetchBusDataNow()
    if rounded % 5 == 0:
        # print("is integer multiple of 5")
        logging.info("is integer multiple of 5")

        try:
            while True:
                try:
                    unixtime = int(time.time())

                    # print("Fetching bus data...")
                    logging.info("Fetching ...")
                    startFuncTime = time.time()

                    # fetch data
                    data = fetchBusDataNow()
                    fetchtime = time.time()
                    # print("Fetched bus data.")
                    logging.info("Fetched.")

                    # parse data
                    parsedData = parseData(data, unixtime)
                    parsetime = time.time()

                    # write data to file
                    writeFunc(parsedData, unixtime)
                    writetime = time.time()

                    endFuncTime = time.time()

                    # debug print times
                    fetchTimeRound = round(fetchtime - startFuncTime, 5)
                    logging.info("fetch time: " + str(fetchTimeRound))

                    # logging.info("parse time: " + str(parsetime - fetchtime))

                    writeTimeRound = round(writetime - parsetime, 5)
                    logging.info("write time: " + str(writeTimeRound))

                    totalTimeRound = round(endFuncTime - startFuncTime, 5)
                    logging.info("total time: " + str(totalTimeRound))

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
                    # this catches too many errors. does not help debug
                    # maybe I should just let it catastrophically fail.
                    writeFunc('466 Error: ' + str(e), unixtime)

                    logging.error("466 Error: " + str(e))

                    time.sleep(5 - (time.time() % 5))


        except KeyboardInterrupt:
            pass


        #display to user that the script has stopped
        logging.info("Stopping startReading()... and script.")
        exit()

        #end of script
        

    else:
        #wait until 4:00:00, 4:00:05, 4:00:10, ...
        logging.info("waiting until next 5 second interval - " + str(5 - (tempsecondsSinceMidnight % 5)) + " seconds")

        time.sleep(5 - (tempsecondsSinceMidnight % 5))
        startReading()

# script can be run at any time prior to 4:00am. determine if it is before 4:00am

# get current time (I don't care about timezones, use local time)
currenttime = datetime.datetime.now()

# get seconds since midnight
secondsSinceMidnight = (currenttime - currenttime.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()
# logging.info("seconds since midnight: " + str(secondsSinceMidnight))

# print date in yyyy-mm-dd
# exit()
dayStr = currenttime.strftime("%Y-%m-%d")
logging.info("day: " + dayStr)
logging.info("time: " + currenttime.strftime("%H:%M:%S"))

# 4*60*60 = 14400
fouram = 14400
twoam = 7200

# if it is after 4am, start process
try: 

    if secondsSinceMidnight > fouram:
        startReading()
    elif secondsSinceMidnight < twoam:
        startReading()
    else:
        #wait until 4am
        logging.info("waiting until 4am - " + str(fouram - secondsSinceMidnight) + " seconds")
        time.sleep(fouram - secondsSinceMidnight)
        # that's pretty smart actually...
        startReading()
except Exception as e:
    logging.critical(e, exc_info=True)
    logging.info("finished with error (see above).")
