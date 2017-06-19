# Google Maps distance matrix API: script to group up origins and destinations.

# The Google Maps distance matrix API takes a list of origins and destinations and returns a JSON object with journey information in.  You are limited to 2500 requests per day, and each request can include up to 100 journeys.  To maximise the number of journeys per day, the origins and destinations should be grouped appropriately. This script takes a list of origins (postcodes or lat-lon coordinates) and a list of destinations, groups them into 25 origins and 4 destinations, then sends them together to the API, and runs through all combinations.  # 

# I wrote this as part of a project to look at travel times in London. This is by no means perfect, but might save someone some time, so I'm making it available.  

# Call from command line: TravelTimesGoogleMaps.py list-origins.csv list-destinations.csv
# Outputs to output.csv

import requests, os, csv, sys, configparser, datetime, time

# read in the files - assumes we pass it a list of files, and then returns a list of lists
def get_files(files):
    pc = [[], []]
    for i in range(len(files)):
        input = open(files[i], 'r')
        for line in input:
            line = line.strip('\n').strip().strip('\"') # strip out new line chars and trim spaces
            pc[i].append(line)
        pc[i] = list(filter(bool, pc[i])) # filter out blank lines
    return pc


# various functions to do with building the API call
def call_api(origins, destinations, mode, counter_request):
    url = url_builder(makepostcodestring(origins), makepostcodestring(destinations), mode)
    r = requests.get(url).json()
    counter_request += 1
    return url, r, counter_request

# form URL for API call, given orgin and desination as strings of encoded postcodes 
def url_builder(origins, destinations, mode):

    # read API key from config file
    config = configparser.ConfigParser()
    config.read('../etc/credentials.txt')
    key = config.get('googledistancematrixapi','key')
    url_key = '&key=' + key    
    url_base = 'https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial'
    url_origins = '&origins=' + origins
    url_destinations = '&destinations=' + destinations
    url_mode = '&mode=' + mode #'&mode=walking'
    url = url_base + url_origins + url_destinations + url_mode + url_key
    return url

# take a list of postcodes, turn them into a string to send to API
def makepostcodestring(postcodelist):
    l = [] # list
    for i in range(len(postcodelist)):
        #l.append(enc(postcodelist[i]))
        l.append(postcodelist[i].replace(' ', ''))
    s = '|'.join(l) # string
    return s

# group postcodes
def group_postcodes(A, B):
    # list sizes
    L1 = len(A)
    L2 = len(B)
    # block sizes
    b1 = 3
    b2 = 5

    postcodes_grouped = []

    # could probably do this in a lambda function within the range() below:
    def get_range(L,b):
        if L % b == 0:
            return L//b
        else:
            return L//b + 1

    for j in range(get_range(L1,b1)):
        for l in range(get_range(L2,b2)):
            row = ([A[i] for i in range(b1*j, min(b1*(j+1), b1*j + (L1-b1*j)))],                   [B[k] for k in range(b2*l, min(b2*(l+1), b2*l + (L2-b2*l)))]  )
            postcodes_grouped.append(row)
            
    return postcodes_grouped

# go through output array and pick out each pair of postcodes and the right travel time
def parse_results(origins, destinations, mode, results, url, counter_request):
    errors = []
    output = []
    for i in range(len(origins)):
        for j in range(len(destinations)):
            if results['rows'][i]['elements'][j]['status'] == 'OK':
                row = [origins[i], destinations[j], mode,
                   int(results['rows'][i]['elements'][j]['duration']['value']), 
                       counter_request]
                output.append(row)
            else: 
                row = [origins[i], destinations[j], mode, 'failed', counter_request]
                errors.append(row)
    return output, errors


# Main part of the script:
if __name__ == '__main__':

    # temporarily inserting this to wait 24 hours before beginning as I've used quota for today!
    print('Timestamp: {:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()))
    # wait 24 hours
    #time.sleep(86400)


    # variables
    mode = 'walking' # options: walking, driving, bicycling, transit https://developers.google.com/maps/documentation/distance-matrix/intro#travel_modes

    # INPUT - read in files from command line - we are going to find travel times for each pair in A and B
    files = [sys.argv[1], sys.argv[2]]
    postcodes = get_files(files)
    groups = group_postcodes(postcodes[0], postcodes[1])
    n_pairs = len(postcodes[0])*len(postcodes[1])

    # OUTPUT - where to save the files
    ofile = 'output.csv'
    errorfile = 'errorlog.csv'

    filemode = 'w' # w = overwite, a = append

    # initialise counters
    counter_requests = 0
    counter_pairs = 0
    counter_errors = 0

    counter_pairs_max = n_pairs # size of array
    counter_requests_max = 2450 # we are allowed 2500 per day, but I have already made some today

    messages = []

    while counter_pairs < counter_pairs_max:
        try: 
            with open(ofile, mode = filemode) as ofile:        
                with open(errorfile, mode = filemode) as efile:        
                    wro = csv.writer(ofile)#, dialect='excel')
                    wre = csv.writer(efile)

                    for row in groups:
                        origins = row[0]
                        destinations = row[1]
                        # Increment counter of pairs of postcodes
                        counter_pairs += len(origins)*len(destinations)              
                        # Send request to API (request counter incremented)
                        url, results, counter_requests = call_api(origins, destinations, mode, counter_requests)
                        # Parse the results - returns a list of lists, so we need to go through each list
                        output, errors = parse_results(origins, destinations, mode, results, url, counter_requests)

                        # Output line by line
                        for row in output:
                            wro.writerow(row)
                        # Output errors
                        for e in errors:
                            wre.writerow(e)
                            counter_errors += 1

                        # print output
                        print('Number of requests made:', counter_requests, 'Number of pairs sent to API:', counter_pairs,
                             'Number of errors:', counter_errors, 
                             'Timestamp: {:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()))

                        if counter_requests == counter_requests_max:
                            print('Waiting a while, until quota is reset')
                            time.sleep(86400)
                            counter_requests = 0

        except Exception as e:
            messages.append(e)
            break