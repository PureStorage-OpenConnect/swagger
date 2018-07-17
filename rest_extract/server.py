import os
from flask import Flask, request, redirect, url_for, send_from_directory, flash, Response, send_file, abort
import rest_extract
import requests
import urllib3
from urllib import parse
import json
import yaml
import pprint

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


ROOT_DIR = '/usr/share/pureswagger/html'
ALLOWED_EXTENSIONS = set(['pdf', 'yaml'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = ROOT_DIR
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


app.url_map.strict_slashes = False



@app.route('/')
def root():
  return send_from_directory(ROOT_DIR,"index.html")

class bcolors:
    CMD = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[1;32m'
    BLACK = '\033[39m'
    RED = '\033[31m'
    YELLOW = '\033[33m'
    ORANGE = '\033[38;5;208m'

    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'



def print_request(req):
    print("\n================================== API CALL =============================================")


    print( bcolors.CMD + 'HTTP/1.1 {method} {url}\n'.format(
        method=req.method,
        url=req.url ) + bcolors.ENDC)
    
    print( bcolors.BLUE + '{headers}\n'.format(
        headers='\n'.join('{}: {}'.format(k, v) for k, v in req.headers.items()),
        body=req.body) + bcolors.ENDC)

    try:
        obj = json.loads(req.body)
        print(bcolors.GREEN)
        pprint.pprint(obj)
        print(bcolors.ENDC)
    except:
        print(req.body)
    

def print_response(res):
    print("\n-----------------Response----------------------")
    print(bcolors.RED + 'Status Code: {status_code}\n'.format(
        status_code=res.status_code
    )+bcolors.ENDC)

    print(bcolors.BLUE + '{headers}\n'.format( 
        headers='\n'.join('{}: {}'.format(k, v) for k, v in res.headers.items())
    )+bcolors.ENDC)

    try:
        obj = json.loads(res.content)
        print(bcolors.GREEN)
        pprint.pprint(obj)
        print(bcolors.ENDC)
    except:
        print(res.content)

    
#Proxy API calls to the array to bypass CORS
@app.route('/api', defaults={'path': ''}, methods=['GET', 'PUT','POST','DELETE','OPTIONS','HEAD'])
@app.route("/api/<path:path>", methods=['GET', 'PUT','POST','DELETE','OPTIONS','HEAD'])
def proxy_to_fa(*args, **kwargs):
    #this is how we are passing the IP on the webpage to here, useing an additional cookie
    #just to make swagger proxy work using the flasharray ip cookie.
    if "flasharray" not in request.cookies or request.cookies["flasharray"] == "change-me":
        return "Error: Please set FlashArray IP / Hostname at top of page before making API Calls" 

    header_exclude = ['host','set-cookie','cookie']
    swagger_headers = {key: value for (key, value) in request.headers if key.lower() not in header_exclude}
    cookie_exclude = ['flasharray','x-auth-token']
    swagger_cookies = {key: value for (key, value) in request.cookies.items() if key not in cookie_exclude}
    #print(swagger_cookies)
    #print(type(swagger_cookies))

    if "x-auth-token" in request.cookies:
        swagger_headers['x-auth-token'] = request.cookies['x-auth-token']
        #remove this so it doesn't get passed to flash array



    url = parse.urlparse(request.url)
    host = request.cookies["flasharray"]
    url = url._replace(scheme="https",netloc=host)

    #Make actual API call
    try:
        resp = requests.request(
            str(request.method),
            url.geturl(),
            headers=swagger_headers,
            data=request.get_data(),
            cookies=swagger_cookies,
            allow_redirects=False,
            verify=False)
    except:
        abort(Response("Could not connect to {}".format(host)))
        
    #print ("flask request: {}".format(request.method))

    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    response_headers = [(name, value) for (name, value) in resp.raw.headers.items()
               if name.lower() not in excluded_headers]


    #we are going to store x-auth-token in the web browser cookie.... easiest way to save a 
    #token instead of doing it server side is in browser cookies
    auth_token=""
    for header,value in response_headers:
        if 'x-auth-token' in header:
            auth_token=value
    if auth_token != "":
        response_headers.append(("Set-Cookie","x-auth-token="+auth_token))
    

    print_request(resp.request)
    print_response(resp)


    return Response(resp.content, resp.status_code, response_headers)


#This either lists the directory, or returns the actual file
@app.route('/<path:req_path>')
def get_specs(req_path):
    abs_path = os.path.join(ROOT_DIR,req_path)
     

    # Return 404 if path doesn't exist
    if not os.path.exists(abs_path):
        return abort(404)
    
    # Check if path is a file and serve
    if os.path.isfile(abs_path):
        return send_file(abs_path,as_attachment=True)

    #List Directroy
    if req_path == "specs" or req_path == "specs/":
        # Show directory contents
        results=[]
        for item in get_spec_index():
            results.append({
                 'name':item['name'], 
                 'url':item['url'] })

        return json.dumps(results)
    
    return abort("Unknown error")


def get_spec_index():
    with open(os.path.join(ROOT_DIR,"spec_index.yaml")) as f:
        spec_index = yaml.load(f)
    return spec_index


#Automatically identify array and load Api
@app.route('/identify', methods=['GET'])
def identify(*args, **kwargs):
    if "flasharray" not in request.cookies or request.cookies["flasharray"] == "change-me":
        return "Error: Please set FlashArray/FlashBlade IP / Hostname at top of page before making API Calls"
    
    host = "https://{}/api/".format(request.cookies["flasharray"])

    api_version_response = requests.get(
        host+"api_version",
        verify=False)

    if api_version_response.status_code != 200:
        #Error this is probably not FA or FB
        return "This doesn't look like a FlashArray or FlashBlade with REST API support"
    
    versions_response = json.loads(api_version_response.text)
    if 'version' in versions_response:
        versions = versions_response['version']
        array_type = "FlashArray"
    elif 'versions' in versions_response:
        #this is FlashBlade
        array_type = "FlashBlade"
        versions = versions_response['versions']
    else:
        return "This doesn't look like a FlashArray or FlashBlade with REST API support"

    #because different version vs versions don't need this way to detect, but save in case
    #ident_response = requests.get(
    #    host+"1.0/file-systems",
    #    verify=False)
    
    #array_type = ""
    #if ident_response.status_code == 404:
    #    array_type = "FlashArray"
    #elif ident_response.status_code == 403:
    #    array_type = "FlashBlade"

    #load spec index
    spec_index = get_spec_index()
    #find highest match
    matches = []
    for spec in spec_index:
        if spec['model'] == array_type and spec['version'] in versions:
            matches.append(spec)

    #return a reverse sorted list of matching spec files.
    sorted_list =  sorted(matches,key=lambda k: k['version_sort'],reverse=True)
    if len(sorted_list) > 0:
        return redirect('/?urls.primaryName='+sorted_list[0]['name'])
    return "Sorry, Could not find matching spec."

@app.after_request
def add_header(r):
    r.headers["Cache-Control"] = "no-cache, no-store, max-age=0, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    return r


if __name__ == "__main__":
    app.run(host='0.0.0.0')