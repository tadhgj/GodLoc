# let's reinvent the wheel
import urllib.request as urllib
from urllib.request import urlopen
from urllib.error import HTTPError, URLError
from socket import timeout
import time
import datetime
import iso8601
import os
import logging
import pytz
import sys
import ujson as json

# globals

# 5:30
# 5*60*60 + 30*60 = 19800
startTimeSec = 19800
# 3:45
# 3*60*60 + 45*60 = 13500
endTimeSec = 13500

rutgersAgencyCode = 1323

# Set up logging
def setupLogging():
    # return logging object

    # create logger
    l = logging.getLogger()
    l.setLevel(logging.DEBUG)

    # create file handler and set level to debug

    #if running in vm:
    # outputDir = '/root/bus/'
    # outputDirAdd = 'logs/'

    #if running locally:
    outputDir = ''
    outputDirAdd = 'logs/'

    # realtime log: test.log
    realtimeLog = logging.FileHandler(outputDir+outputDirAdd+'test.log', 'w', 'utf-8')
    realtimeLog.setFormatter(logging.Formatter('%(name)s %(message)s'))

    # output log: GMT_day_time_busThird.log
    start_time = int(time.time())
    GMTTime = datetime.datetime.now()
    eastern = pytz.timezone('US/Eastern')
    ESTTime = GMTTime.astimezone(eastern)
    generalLog = logging.FileHandler(outputDir+outputDirAdd+ESTTime.strftime("EST_%Y-%m-%d_%H-%M-%S")+'_busThird.log', 'w', 'utf-8')

    # add two outputs to log system
    l.addHandler(realtimeLog)
    l.addHandler(generalLog)
        
    #if local
    l.addHandler(logging.StreamHandler(sys.stdout))

    # debug
    l.debug('debug message')
    

    return l

def genericNetworkRequest(url):
    # create request object
    request = urllib.Request(url)

    # poke the bear
    # (retry up to 3 times before throwing error. return response object after success or failure)
    failReason = ""
    for i in range(3):
        try:
            response = urllib.urlopen(request, timeout=5)
            return response
        except HTTPError as e:
            logging.warning("HTTPError: "+str(e.code))
            failReason = "HTTPError: "+str(e.code)
        except URLError as e:
            logging.warning("URLError: "+str(e.reason))
            failReason = "URLError: "+str(e.reason)
        except timeout:
            logging.warning("Timeout")
            failReason = "Timeout"
        except Exception as e:
            logging.warning("Exception: "+str(e))
            failReason = "Exception: "+str(e)
        time.sleep(5)

    # if we get here, we failed 3 times
    logging.critical("Failed 3 times. Exiting.")
    raise Exception("Failed 3 times. Exiting. Reason: "+failReason)

# get routes
def getRoutes():
    l.info("Getting routes.")
    # return route object

    # get routes
    # https://feeds.transloc.com/3/routes?agencies=1323
    url = "https://feeds.transloc.com/3/routes?agencies="+str(rutgersAgencyCode)
    try:
        response = genericNetworkRequest(url)
    except Exception as e: 
        logging.critical(e, exc_info=True)
        raise Exception("Failed to get routes"+str(e))

    routes = response.read().decode('utf-8') # not sure if decode is necessary. to test later
    routes = json.loads(routes)

    # parse?

    return routes

# get stops
def getStops():
    l.info("Getting stops.")
    # return stop object

    # get stops
    # https://feeds.transloc.com/3/stops?agencies=1323
    url = "https://feeds.transloc.com/3/stops?agencies="+str(rutgersAgencyCode)
    try:
        response = genericNetworkRequest(url)
    except Exception as e: 
        logging.critical(e, exc_info=True)
        raise Exception("Failed to get stops"+str(e))

    stops = response.read().decode('utf-8') # not sure if decode is necessary. to test later
    stops = json.loads(stops)

    # parse?

    return stops

def windDown():
    # wind down
    l.info("Exiting.")
    sys.exit()

# get vehicles
def getVehicles():
    l.info("Getting vehicles.")
    # return vehicle object

    # get vehicles
    # https://feeds.transloc.com/3/vehicle_statuses?agencies=1323
    url = "https://feeds.transloc.com/3/vehicle_statuses?agencies="+str(rutgersAgencyCode)
    try:
        response = genericNetworkRequest(url)
    except Exception as e:
        logging.critical(e, exc_info=True)
        raise Exception("Failed to get vehicles"+str(e))

    vehicles = response.read().decode('utf-8') # not sure if decode is necessary. to test later
    vehicles = json.loads(vehicles)

    # parse?

    return vehicles

# parse vehicles
def parseVehicles(vehicles):
    # check if empty
    if vehicles['vehicles'] == []:
        return []

    # create list to store buses
    buses = []

    def processBus(vehicle):
        # create dict
        busDict = {}

        # add bus id
        busDict['busnumber'] = vehicle['call_name']

        # add route id
        busDict['routeid'] = vehicle['route_id']

        # 

    # loop through vehicles
    for vehicle in vehicles['vehicles']:
        processBus(vehicle)


    return vehicles

# update "currently stopped" list
def updateCurrentlyStopped(pVehicles):
    # make api calls in this function
    pass

#  update general bus list (use old format, add new parameters)
def updateGeneralBusList(pVehicles):
    pass


# loop
def startLoop(routes, stops):
    l.info("Starting loop.")
    # wait for next 5s interval
    tim = datetime.datetime.now()
    tims = (tim - tim.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()
    timsr = round(tims)
    time.sleep(5 - (timsr % 5))

    # start loop
    while timsr > endTimeSec or timsr < startTimeSec:

        # get vehicles from transloc
        # https://feeds.transloc.com/3/vehicle_statuses?agencies=1323
        vehicles = getVehicles()
        # parse vehicles
        pVehicles = parseVehicles(vehicles)
        # update "currently stopped" list
        updateCurrentlyStopped(pVehicles)
        # update general bus list (use old format, add new parameters)
        updateGeneralBusList(pVehicles)
        # repeat


        # until the next one
        tim = datetime.datetime.now()
        tims = (tim - tim.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()
        timsr = round(tims)
        time.sleep(5 - (timsr % 5))

    # done
    windDown()




def startReading():
    l.info("Start reading")
    # 1. get routes
    # 2. get stops
    # 3. start 5s loop

    tim = datetime.datetime.now()
    tims = (tim - tim.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()
    timsr = round(tims)

    # litmus check to see if it is between 3:45am and 5:30am. startReading is usually called right at 5:30am
    if timsr > endTimeSec and timsr < startTimeSec:
        logging.info("strange start time. exiting.")
        windDown()
        return

    # get routes
    try:
        routes = getRoutes()
    except Exception as e:
        logging.critical(e, exc_info=True)
        logging.info("could not get routes. exiting.")
        windDown()
        return

    # get stops
    try:
        stops = getStops()
    except Exception as e:
        logging.critical(e, exc_info=True)
        logging.info("could not get stops. exiting.")
        windDown()
        return

    # start 5 second interval loop
    try:
        startLoop(routes, stops)
    except Exception as e:
        logging.critical(e, exc_info=True)
        logging.info("could not start loop. exiting.")
        windDown()
        return


    
    




l = None
# on script start:
def init():
    global l

    # Set up logging
    l = setupLogging()
    l.info("Init")

    # determine time
    now = datetime.datetime.now()
    sinceMidnight = now - datetime.datetime.combine(now.date(), datetime.time())
    sinceMidnightSeconds = sinceMidnight.seconds

    try: 
        if sinceMidnightSeconds > startTimeSec:
            # it is after 5:30am
            startReading()
        elif sinceMidnightSeconds < endTimeSec:
            # it is before 3:45am
            startReading()
        else:
            # it is between 3:45am and 5:30am. Wait until 5:30am
            logging.info("waiting to start script. ("+str(startTimeSec - sinceMidnightSeconds)+")")
            time.sleep(startTimeSec - sinceMidnightSeconds)
            startReading()
    except Exception as e:
        logging.critical(e, exc_info=True)
        logging.info("finished with error (see above).")

init()