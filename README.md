# Google Maps distance matrix API: script to group up origins and destinations.

The Google Maps distance matrix API takes a list of origins and destinations and returns a JSON object with journey information in.  You are limited to 2500 requests per day, and each request can include up to 100 journeys.  To maximise the number of journeys per day, the origins and destinations should be grouped appropriately. This script takes a list of origins (postcodes or lat-lon coordinates) and a list of destinations, groups them into 25 origins and 4 destinations, then sends them together to the API, and runs through all combinations.  # 

I wrote this as part of a project to look at travel times in London. This is by no means perfect, but might save someone some time, so I'm making it available.  

Call from command line: `TravelTimesGoogleMaps.py list-origins.csv list-destinations.csv`
Outputs to `output.csv`

Reads API credentials from `../etc/credentials.txt`
