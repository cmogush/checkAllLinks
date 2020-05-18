import sys, csv, time, re, socket, urllib.request, concurrent.futures, queue, os
from urllib.error import URLError, HTTPError
from urllib.request import urlopen, Request

def readCSV(csvFile):
    """ Extracts urls from a CSV file; returns results as a list"""
    urlList = []
    with open(csvFile, 'r') as csv_f:
        reader = csv.DictReader(csv_f)
        headers = reader.__next__()  # get the headers
        url_header = list(headers)[0]
        print(url_header)
        for row in reader:
            urlList.append(row[url_header])
    return urlList, url_header

""" Setup global variables """
rows = []
# inputs
csv_file = input("Enter full path to csv to be read in: ")
urls, url_column = readCSV(csv_file)

# urls, url_column = getUrls(r'C:\Users\Chris\Desktop\Python Scripts\checkAllLinks\CPUniqueDomains_medium.csv') # testing


def getErrorDetails(response):
    """returns the corresponding details for the Error Code"""
    responses = {
        100: ('Continue', 'Request received, please continue'),
        101: ('Switching Protocols',
              'Switching to new protocol; obey Upgrade header'),

        200: ('OK', 'Request fulfilled, document follows'),
        201: ('Created', 'Document created, URL follows'),
        202: ('Accepted',
              'Request accepted, processing continues off-line'),
        203: ('Non-Authoritative Information', 'Request fulfilled from cache'),
        204: ('No Content', 'Request fulfilled, nothing follows'),
        205: ('Reset Content', 'Clear input form for further input.'),
        206: ('Partial Content', 'Partial content follows.'),

        300: ('Multiple Choices',
              'Object has several resources -- see URI list'),
        301: ('Moved Permanently', 'Object moved permanently -- see URI list'),
        302: ('Found', 'Object moved temporarily -- see URI list'),
        303: ('See Other', 'Object moved -- see Method and URL list'),
        304: ('Not Modified',
              'Document has not changed since given time'),
        305: ('Use Proxy',
              'You must use proxy specified in Location to access this '
              'resource.'),
        307: ('Temporary Redirect',
              'Object moved temporarily -- see URI list'),

        400: ('Bad Request',
              'Bad request syntax or unsupported method'),
        401: ('Unauthorized',
              'No permission -- see authorization schemes'),
        402: ('Payment Required',
              'No payment -- see charging schemes'),
        403: ('Forbidden',
              'Request forbidden -- authorization will not help'),
        404: ('Not Found', 'Nothing matches the given URI'),
        405: ('Method Not Allowed',
              'Specified method is invalid for this server.'),
        406: ('Not Acceptable', 'URI not available in preferred format.'),
        407: ('Proxy Authentication Required', 'You must authenticate with '
                                               'this proxy before proceeding.'),
        408: ('Request Timeout', 'Request timed out; try again later.'),
        409: ('Conflict', 'Request conflict.'),
        410: ('Gone',
              'URI no longer exists and has been permanently removed.'),
        411: ('Length Required', 'Client must specify Content-Length.'),
        412: ('Precondition Failed', 'Precondition in headers is false.'),
        413: ('Request Entity Too Large', 'Entity is too large.'),
        414: ('Request-URI Too Long', 'URI is too long.'),
        415: ('Unsupported Media Type', 'Entity body in unsupported format.'),
        416: ('Requested Range Not Satisfiable',
              'Cannot satisfy request range.'),
        417: ('Expectation Failed',
              'Expect condition could not be satisfied.'),

        500: ('Internal Server Error', 'Server got itself in trouble'),
        501: ('Not Implemented',
              'Server does not support this operation'),
        502: ('Bad Gateway', 'Invalid responses from another server/proxy.'),
        503: ('Service Unavailable',
              'The server cannot process the request due to a high load'),
        504: ('Gateway Timeout',
              'The gateway server did not receive a timely response'),
        505: ('HTTP Version Not Supported', 'Cannot fulfill request.'),
    }
    if response in responses:
        return responses[response]
    return ""


def pingURL(url):
    """pings the given url and, if redirected, returns a redirected URL"""
    redirectedURL = None
    req = urllib.request.Request(url, headers={'User-Agent': "Mozilla/5.0 (Windows NT 6.1; Win64; x64)"})
    r = urllib.request.urlopen(req)
    ogURL = req.get_full_url()
    finalURL = r.geturl()
    if ogURL != finalURL and ogURL != finalURL + "/":
        redirectedURL = finalURL
    return redirectedURL


def formatRow(redirected, ogURL, url, urlFormatted, https):
    """format the row based on the resulting variables"""
    print("{} / {} {} ".format(urls.index(ogURL)+1, len(urls), url), end="")  # OG url
    if redirected is None and https and not urlFormatted:  # successful condition
        print('Success')
        result = 'Success'
        details = ''
    elif redirected is None and https and urlFormatted:  # successful but original URL needs reformatted
        print('Bad Syntax | Update URL | {}'.format(url))
        result = 'Failed - Bad Syntax'
        details = 'Failed because of capitalization, spacing, or other bad syntax; Successful as reformatted'
        redirected = url
    elif redirected is None:   # successful but original URL needs to be changed from https to http
        print('Change to http | {}'.format(url))
        result = 'Failed - https'
        details = 'Failed with https; Successful as http'
        redirected = url
    else:
        print('Redirected | Update URL | {}'.format(redirected))  # successful but URL needs updated to RedirectedURL
        result = 'Redirected'
        details = 'URL should be updated to match Redirected URL'
    return result, details, redirected


def testUrl(url):
    """function that tests the url using several conditions; returns a formatted dictionary list to use as a CSV row"""
    socket.setdefaulttimeout(30)
    row = {url_column: url, 'Result': "", 'Details': "", 'UpdatedURL': ""}
    # setup the url for testing, make note if it had to be reformatted
    urlFormatted = False
    ogURL = url
    if not url == url.strip().lower():
        url = url.strip().lower()
        urlFormatted = True
    # begin testing the url
    try: # test url with no changes
        redirected = pingURL(url)
        row['Result'], row['Details'], row['UpdatedURL'] = formatRow(redirected, ogURL, url, urlFormatted, True)
    except urllib.error.HTTPError as e:  # catch the HTTPError (response code)
        url = re.sub('https', 'http', url)
        try:  # try again with http, instead of https
            redirected = pingURL(url)
            row['Result'], row['Details'], row['UpdatedURL'] = formatRow(redirected, ogURL, url, urlFormatted, False)
        except:  # failed with error code
            print("{} / {} {} {} | {}".format(urls.index(ogURL)+1, len(urls), ogURL, e.code, getErrorDetails(e.code)))
            row['Result'] = e.code
            row['Details'] = getErrorDetails(e.code)
    except:  # catch all other errors
        url = re.sub('https', 'http', url)
        try:  # try again with http, instead of https
            redirected = pingURL(url)
            row['Result'], row['Details'], row['UpdatedURL'] = formatRow(redirected, ogURL, url, urlFormatted, False)
        except:  # failed without error code
            print("{} / {} {} Failed ".format(urls.index(ogURL)+1, len(urls), ogURL))  # OG url
            row['Result'] = 'Failed to connect'
    return row

def feed_the_workers(q, urls, spacing):
    """ Simulate outside actors sending in work to do """
    time.sleep(spacing)
    for url in urls:
        q.put(url)
    return "DONE FEEDING"

def testUrlsParallel(urls):
    """ Test a list of urls in parallel; returns a list of dictionaries used for writing a CSV """
    q = queue.Queue()
    count = 0
    # We can use a with statement to ensure threads are cleaned up promptly
    with concurrent.futures.ThreadPoolExecutor(max_workers=None) as executor:

        # start a future for a thread which sends work in through the queue
        future_to_url = {
            executor.submit(feed_the_workers, q, urls, 0.25): 'FEEDER DONE'}

        while future_to_url:
            # check for status of the futures which are currently working
            done, not_done = concurrent.futures.wait(
                future_to_url, timeout=0.25,
                return_when=concurrent.futures.FIRST_COMPLETED)

            # if there is incoming work, start a new future
            while not q.empty():
                # fetch a url from the queue
                url = q.get()

                # Start the load operation and mark the future with its URL
                future_to_url[executor.submit(testUrl, url)] = url

            # process any completed futures
            for future in done:
                url = future_to_url[future]
                try:
                    row = future.result()
                    if not url == 'FEEDER DONE':
                        global rows # pull in the global variable
                        rows.append(row)
                        # # checkpoint to write to CSV
                        if (urls.index(row[url_column])+1) % 100 == 0: # write every 100 rows
                            tempRows = rows
                            tempRows = sorted(rows, key=lambda i: i[url_column])
                            writeCSV(tempRows)
                except Exception as exc:
                    print('%r generated an exception: %s' % (url, exc))
                else:
                    if url == 'FEEDER DONE':
                        print(url)

                # remove the now completed future
                del future_to_url[future]
        rows = sorted(rows, key = lambda i: i[url_column])
    return rows

def testUrls(urls):
    """functions to test a list of urls; returns a list of dictionaries used for writing a CSV"""
    rows = []
    count = 0
    for url in urls:
        count += 1
        print("{}/{} : ".format(count, len(urls)), end="")
        row = testUrl(url)
        rows.append(row)
        if count % 299 == 0:
            writeCSV(rows)  # writing to CSV
        if count % 50 == 0:
            print("sleeping 5 seconds...opportunity to pause")
            time.sleep(5)
    return rows

def writeCSV(rows):
    """functions to write dictionary list 'rows' to a CSV"""
    keys = [url_column, 'Result', 'Details', 'UpdatedURL']
    with open('CPUniqueDomains_result.csv', 'w', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=keys)
        print ("writing to CSV")
        writer.writeheader()  # will create first line based on keys
        writer.writerows(rows)  # turns the dictionaries into csv

def restoreProgress(partial_csv):
    """ Restore the progress from a partially finished CSV output """
    with open(partial_csv, 'r') as csv_f:
        reader = csv.DictReader(csv_f)
        header = reader.__next__() # get the headers
        count = 0
        for row in reader:
            if list(header)[1]: # see if the row is completed, if so, add it to finished list of dictionaries
                rows.append({url_column: row[list(header)[0]], 'Result': row[list(header)[1]],
                'Details': row[list(header)[2]], 'UpdatedURL': row[list(header)[3]]})
                urls.remove(row[url_column]) # remove the finished url from the list to check
                count += 1
    print("{} rows read in from {}".format(count, os.path.basename(partial_csv)))
    time.sleep(1)

def main():
    """main method"""
    print("Restore progress from a partially completed CSV?)")
    print("Note: columns must match this exact order: url | result | details | updated url")
    if(input("Input (y/n): ") == 'y'):
        partial_csv = input("Enter full path to partial csv: ")
        # partial_csv = r'C:\Users\Chris\Desktop\Python Scripts\checkAllLinks\CPUniqueDomains_result_parallel.csv' # testing
        restoreProgress(partial_csv)


    # single process
    # print("Started {}".format(time.ctime()))
    # timer = time.time()
    # rows = testUrls(urls)
    # print("Ended {} | {} seconds elapsed".format(time.ctime(), time.time() - timer))
    # writeCSV(rows)

    # parallel process
    print("Started {}".format(time.ctime()))
    timer = time.time()
    rows = testUrlsParallel(urls)
    writeCSV(rows)
    print("Ended {} | {} seconds elapsed".format(time.ctime(), time.time() - timer))

    # testUrl("https://www.architecturaldigest.com")  # for testing purposes


if __name__ == "__main__":
    main()
