import urllib.request as urllib
from urllib.request import urlopen
import json
import time
import datetime
#polyline handles Google's polyline encoding format
#https://developers.google.com/maps/documentation/utilities/polylinealgorithm
import polyline

import secretHeader

headers = secretHeader.headers

routes_data = None


def fetchAPI(inputurl, timeout):
    #expecting url like:
    #https://transloc-api-1-2.p.rapidapi.com/routes.json?agencies=1323&callback=call

    #set url var
    # rutgersAgencyCode = 1323
    url = inputurl

    #set headers
    global headers

    #make request
    request = urllib.Request(url, headers=headers)

    #open request
    response = urllib.urlopen(request, timeout=timeout)

    #read response
    data = response.read()

    return data


def fetchRouteData():
    #this function will fetch the route data
        # print(rutgersData)

    serverResponse = fetchAPI('https://transloc-api-1-2.p.rapidapi.com/routes.json?agencies=1323&callback=call', 10)

    parsed = json.loads(serverResponse)

    rutgersData = parsed['data'][str(1323)]

    #first, make empty list of routes
    route_ids = {}
    #empty extra list
    route_extra = {}

    #for each item inside rutgers
    # for i in range(len(response.data[1323])):
    for currentRoute in rutgersData:
        # print("current route:")
        print(currentRoute)

        #for lookup table
        if currentRoute['short_name'] != "":
            route_ids[currentRoute['route_id']] = currentRoute['short_name'] + " - " + currentRoute['long_name']
        else:
            route_ids[currentRoute['route_id']] = currentRoute['long_name']

        #collect variables
        extendedRouteObject = {
            'bgcolor': currentRoute['color'],
            'textcolor': currentRoute['text_color'],
            'name': currentRoute['long_name'],
            'shortname': currentRoute['short_name'],

            # 'isactive': currentRoute['is_active'],
            # routes will not be fetched very often
            # whatever buses are running will determine
            # if a route is active or not

            'segments': currentRoute['segments'],
            'stops': currentRoute['stops'],
        }

        #add to extra list
        route_extra[currentRoute['route_id']] = extendedRouteObject




    #
    #output object
    outputObj = {
        'routes': route_ids,
        #more data below..
        'routeExtra': route_extra
    }
    # print(outputObj)
    return outputObj

routes_data = fetchRouteData()

segment_data = None

def fetchSegmentData():
    #this function will fetch the segment data
    # rutgersData = fetchAPI('https://transloc-api-1-2.p.rapidapi.com/segments.json', 10)

    serverResponse = fetchAPI('https://transloc-api-1-2.p.rapidapi.com/segments.json?agencies=1323&callback=call', 10)

    parsed = json.loads(serverResponse)

    segment_poly = {}
    
    #get keys and values
    for key, value in parsed['data'].items():
        segment_poly[key] = polyline.decode(value)

    return segment_poly

segment_data = fetchSegmentData()

stop_data = None

def fetchStopData():
    #this function will fetch the stop data
    serverResponse = fetchAPI('https://transloc-api-1-2.p.rapidapi.com/stops.json?agencies=1323&callback=call', 10)

    parsed = json.loads(serverResponse)

    rutgersData = parsed['data']

    #first, make empty list of stops
    stop_ids = {}

    #for each item inside rutgers
    for currentStop in rutgersData:
        stopCode = currentStop['code']
        stopLocation = [currentStop['location']['lat'], currentStop['location']['lng']]
        stopID = currentStop['stop_id']
        stopRouteList = currentStop['routes']
        stopName = currentStop['name']

        #collect variables
        extendedStopObject = {
            'code': stopCode,
            'location': stopLocation,
            'routes': stopRouteList,
            'name': stopName
        }

        #add to list
        stop_ids[stopID] = extendedStopObject

    return stop_ids

stop_data = fetchStopData()

with open('routes.json', 'w') as outfile:
    json.dump(routes_data, outfile)

with open('segments.json', 'w') as outfile:
    json.dump(segment_data, outfile)

with open('stops.json', 'w') as outfile:
    json.dump(stop_data, outfile)