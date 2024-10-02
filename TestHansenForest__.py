##Python program to determine any Forest or Tree Loss in a given Area - identified by a GeoJSON
#using the Hansen Data set: https://developers.google.com/earth-engine/datasets/catalog/UMD_hansen_global_forest_change_2023_v1_11
#and Google Earth Engine.  
#This is an EUDR requirement and this is an elementary attempt to create a program to determine the same.

#Credits: Hansen Global Forest Change Dataset, ChatGPT 

#Import the necessary libraries
import ee
import ssl
from datetime import datetime
import folium
from shapely.geometry import Point, Polygon
import geopandas as gpd
import random
import json

##ALERT!!! Hack to avoid any SSL errors that we faced initially.  Need to be addressed if this code is sent in production to customers
ssl._create_default_https_context = ssl._create_unverified_context

#Hack: Storing the Region Name as a global variable. Not Good
globalRegionName = ""
# To Store the Forest Loss Map Collection
forestLossMapCollection = []

def init():
    ee.Authenticate()
    # Initialize the Earth Engine API
    ee.Initialize(project='Your Google Earth Engine project')

def loadFileAndGetCoordinates():    
    #jsonFileName = input("Enter the Geo JSON FileName: ")
    jsonFileName = "SampleGeoJSONForHansenTest1.json"
    if not jsonFileName:
        print("Enter the Geo JSON FileName")
        exit()

    with open(jsonFileName, 'r') as file:
        data = json.load(file)

    if data:
        geoCoordinates = data['geometry']['coordinates']

    print(f"The Geo Coordinates are: {geoCoordinates}\n")

    if len(geoCoordinates) == 1 and isinstance(geoCoordinates[0], list):
        inputCoordinates = geoCoordinates[0]
    else:
        inputCoordinates = geoCoordinates    

    #Let us create an ee Geometry from our Coordinates
    eePolygon = ee.Geometry.Polygon(inputCoordinates)
    print("The eeGeometry aka Polygon is created successfully\n")
    return inputCoordinates, eePolygon

def printRegion(eePolygon):
    global globalRegionName
    # Load the administrative boundaries dataset
    admin_boundaries = ee.FeatureCollection("FAO/GAUL/2015/level2")

    # Find the intersection of the polygon with the administrative boundaries
    intersected_admin = admin_boundaries.filterBounds(eePolygon)

    # Get the name of the intersected administrative region
    region_name = intersected_admin.first().get('ADM1_NAME').getInfo()
    print('Region Identified by the Geometry/Coordinates (also called Administrative Region) is :', region_name)
    globalRegionName = region_name

def createMap(eePolygons, locationLatLon, year):
    print("createMap")
    randomFileName = random.randint(99, 9999)
    color=""
    if year == 0:
        mapFileName = f"MainMap-{globalRegionName}-{randomFileName}-Map.html"
        color="blue"
    else:    
        mapFileName = f"ForestLoss-{globalRegionName}-{year}-{randomFileName}-Map.html"
        color="red"

    location = [locationLatLon[1], locationLatLon[0]]
    m = folium.Map(location=location, zoom_start=16)
    for eePolygon in eePolygons:
        coords = eePolygon.coordinates().getInfo()[0]
        foliumPolygonCoords = [(coord[1], coord[0]) for coord in coords]
        folPoly = folium.Polygon(foliumPolygonCoords, color=color, weight=2, fill=True, fill_opacity=0.4).add_to(m)
        folium.map.Tooltip(mapFileName).add_to(folPoly)
    m.save(mapFileName)
    return m

def getLossAreaMap(loss_in_year, eePolygon, year):
    print("getLossAreaMap")
    lossArea = loss_in_year.updateMask(loss_in_year)
    vectorLoss = lossArea.reduceToVectors(geometry=eePolygon, scale=30, geometryType='polygon', 
                                             eightConnected=True, labelProperty=f'Forest Loss {year}', reducer=ee.Reducer.countEvery())
    lossCoordinates = vectorLoss.geometry().getInfo()
    locationLatLon = lossCoordinates['coordinates'][0][0][0]
    eePolygons = []
    for i in range(len(lossCoordinates['coordinates'])):
        eePolygons.append(ee.Geometry.Polygon(lossCoordinates['coordinates'][i]))

    return createMap(eePolygons, locationLatLon, year)    

def determineForestLoss(eePolygon):
    print("determineForestLoss")
    # Load the Hansen Global Forest Change dataset (2023 version)
    gfc = ee.Image("UMD/hansen/global_forest_change_2023_v1_11")
    # Select the 'lossyear' band
    loss_image = gfc.select('lossyear')
    # List the years of interest (e.g., 2021 to 2023)
    years = list(range(2021, 2024))  # This will give [2021, 2022, 2023]
    # Loop through the years and calculate forest loss for each year
    for year in years:
        # Convert the year to two-digit format (e.g., 2021 -> 21, 2022 -> 22)
        two_digit_year = year - 2000
        # Filter forest loss for the specific year
        loss_in_year = loss_image.eq(two_digit_year).clip(eePolygon)
        # Calculate the forest loss area in square meters
        loss_area_m2 = loss_in_year.multiply(ee.Image.pixelArea()).reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=eePolygon,
            scale=30,
            maxPixels=1e9
        ).get('lossyear').getInfo()
        # Convert the area from square meters to hectares (1 hectare = 10,000 m²)
        loss_area_ha = loss_area_m2 / 10000 if loss_area_m2 else 0
        # Print the results
        print(f'Forest loss area in {year} (ha):', loss_area_ha)
        if loss_area_ha > 0:
            map = getLossAreaMap(loss_in_year, eePolygon, 2000+two_digit_year)
            forestLossMapCollection.append([map, 2000+two_digit_year])

def createOverlayMaps(mainMap, locationLatLon):    
    print("createOverlayMaps for all years where there is Forest Loss")
    # Create Feature Groups for Main map
    fg1 = folium.FeatureGroup(name='Overall Farm Plot Area')
    fg2 = folium.FeatureGroup(name='Forest Loss Area')

    # Add features from the Main map to Feature Group 1
    for feature in mainMap._children:
        fg1.add_child(mainMap._children[feature])

    for object in forestLossMapCollection:
        lossMap = object[0]
        year = object[1]
        # Add features from the second map to Feature Group 2
        for feature in lossMap._children:
            fg2.add_child(lossMap._children[feature])
        location = [locationLatLon[1], locationLatLon[0]]
        overlayMap = folium.Map(location=location, zoom_start=16)
        overlayMap.add_child(fg1)
        overlayMap.add_child(fg2)
        # Add Layer Control
        folium.LayerControl().add_to(overlayMap)
        randFileNum = random.randint(599, 5999)
        mapFile = f"OverlayMap-ForestLoss-{globalRegionName}-{year}-{randFileNum}.html"
        overlayMap.save(mapFile)


#Starts here
if __name__=="__main__":
    init()#Initialize the EE Project
    inputCoordinates, eePolygon = loadFileAndGetCoordinates() #Load the GeoJSON File and get the Coordinates and the Polygon
    printRegion(eePolygon)

    eePolygons = []
    eePolygons.append(eePolygon)
    print("Create the Main Map")
    mainMap = createMap(eePolygons, inputCoordinates[0][0], 0) #Create the Main Map

    determineForestLoss(eePolygon) #Determine the Forest Loss using the Hansen Data set: Refer: https://developers.google.com/earth-engine/datasets/catalog/UMD_hansen_global_forest_change_2023_v1_11

    createOverlayMaps(mainMap, inputCoordinates[0][0]) #Use the Main Map and Overlay the Forest Loss Maps on top of the Main Map

