from django.conf import settings
from pprint import pprint
from railtracker.mapfeed.models import MapStation, MapLine, MapCity, MapPath
import httplib, urllib, base64, json

#Functions
def loadCity():
    try:
        MapCity.objects.get(city_name="Washington D.C.")
    except Exception as e:
        c_model = MapCity(
                city_name="Washington D.C.",
                rail_name="Metro",
                twitter_id="MetroRailInfo"
        )
        c_model.save()

def loadLines():
    colors = {'Orange': 'CC6600',
            'Blue': '0033CC',
            'Silver': 'B2CCCC',
            'Red': 'FF0000',
            'Yellow': 'FFFF00',
            'Green': '00CC00',
            }
    try:
        conn.request("GET", "/Rail.svc/json/jLines?%s" % params, "", headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()
    except Exception as e:
        pprint("[Errno {0}] {1}".format(e.errno, e.strerror))
    decoded_lines = json.loads(data)
    #Go through line list and load into database
    for line in decoded_lines['Lines']:
        print line['DisplayName']
        city = MapCity.objects.get(city_name="Washington D.C.").id
        l_model = MapLine(
                map_id=city,
                line_name=line['DisplayName'],
                line_code=line['LineCode'],
                color=colors[line['DisplayName']],
        )
        l_model.save()

def loadStations():
    city = MapCity.objects.get(city_name="Washington D.C.").id
    try:
        conn.request("GET", "/Rail.svc/json/jStations?%s" % params, "", headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()
    except Exception as e:
        pprint("[Errno {0}] {1}".format(e.errno, e.strerror))
    decoded_stations = json.loads(data)
    #Go through station list and load into database
    for station in decoded_stations['Stations']:
        print station['Name']
        try:
            s_model = MapStation.objects.get(station_code=station['Code'])
        except MapStation.DoesNotExist as dne:
            s_model = MapStation(
                    station_name=station['Name'],
                    lat=station['Lat'],
                    lon=station['Lon'],
                    station_code=station['Code'],
            )
        try:
            s_model.through_station = MapStation.objects.get(station_code=station['StationTogether1'])
            print "Found through station."
            print s_model.through_station
        except MapStation.DoesNotExist as dne:
            if station['StationTogether1']:
                print "Through station indicated but station not found in database. Creating station..."
                s_model.save()
                copy_model = MapStation(
                        station_name=station['Name'],
                        lat=station['Lat'],
                        lon=station['Lon'],
                        station_code=station['StationTogether1'],
                )
                copy_model.through_station = s_model
                copy_model.save()
                s_model.through_station = copy_model
                s_model.save()
            else:
                print "No through station found."
                s_model.save()
        for x in range(1, 5):
            try:
                line = MapLine.objects.get(line_code=station['LineCode' + str(x)], map=city)
                s_model.lines.add(line)
            except Exception:
                print "Line " + str(x) + " is invalid!"

def loadPaths():
    city = MapCity.objects.get(city_name="Washington D.C.").id
    lines = MapLine.objects.filter(map=city)
    #Go through all lines and fill in stations by order
    for line in lines:
        print line
        params = urllib.urlencode({
            'api_key': settings.DC_PRIMARY_KEY,
            'LineCode': line
        })
        try:
            conn.request("GET", "/Rail.svc/json/jStations?%s" % params, "", headers)
            response = conn.getresponse()
            data = response.read()
            conn.close()
        except Exception as e:
            pprint("[Errno {0}] {1}".format(e.errno, e.strerror))
        decoded_path = json.loads(data)
        #Go through path list and load into database
        for i, path in enumerate(decoded_path['Stations']):
            print path['Name']
            s_path = MapPath(
                    seq_num=i
            )
            s_path.line = MapLine.objects.get(line_name=line, map=city)
            s_path.station = MapStation.objects.get(station_code=path['Code'])
            s_path.save()

#Vars
headers = {
}

params = urllib.urlencode({
    'api_key': settings.DC_PRIMARY_KEY
})

conn = httplib.HTTPSConnection('api.wmata.com')

#Calls
loadCity()
loadLines()
loadStations()
loadPaths()
