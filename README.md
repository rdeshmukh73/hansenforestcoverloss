EUDR - EU Deforestation Regulation specifies that any product produced or imported into Europe has any Deforestation or Forest degradation in its production process.  
As a consequence it is imperative that companies that ship raw, semi-finshed and finished goods into Europe demonstrate Traceability and Compliance to this regulation.
https://environment.ec.europa.eu/topics/forests/deforestation/regulation-deforestation-free-products_en

There are several Datasets available to help determine if there was any Deforestation in areas where the raw materials were grown/produced.  Prominent among them:
a. Global Forest Watch
b. Hansen Global Forest Change
c. MODIS
d. Sentinel
and more

In this program written in Python, I am using Google Earth Engine (EE) and Hansen Global Forest Change Dataset to determine if a Land mass (represented by a GeoJSON)
has had any Forest Loss from 2021 Jan till Dec 2023 and if yes, plot the same on a Map.

Technologies used:
a. Python
b. Hansen Global Forest Change data set (https://developers.google.com/earth-engine/datasets/catalog/UMD_hansen_global_forest_change_2023_v1_11)
c. Folium Maps
d. Google Earth Engine (ee)

High level Steps:
a. Create a Project on Google Earth Engine and Link it with your Google ID
b. Accept, Parse and determine the Co-Ordinates as a Polygon.  Create a Folium Map of the overall area. 
c. Use FAO/GAUL/2015/level2 dataset to determine the name of place/region represented by the Co-Odinates.  This can be achieved with OpenStreetMap APIs as well
d. Determine the Forest Loss using the Hansen Dataset for the years 2021, 2022 and 2023
e. If there is Forest Loss, get the Co-ordinates for the Land which is deforested
f. Create a Folium Map of the Loss Area
g. Overlay the Loss Area Map on top of the Overall Map and Save it to disk
h. Open the Overlay map to show the Overall area and the forest loss area

