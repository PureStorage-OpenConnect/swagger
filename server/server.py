import os
from flask import Flask, request, redirect, send_from_directory, Response, abort
import requests
import urllib3
from urllib import parse
import json
import yaml
import pprint
from Crypto.PublicKey import RSA
from time import time
import jwt
import time


import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


ROOT_DIR = '/usr/share/pureswagger/html'
ALLOWED_EXTENSIONS = set(['pdf', 'yaml'])
USER_AGENT = 'PureStorage-OpenConnect/swagger'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = ROOT_DIR
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


app.url_map.strict_slashes = False


@app.route('/')
def root():
    return send_from_directory(ROOT_DIR, "index.html")


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

    print(bcolors.CMD + 'HTTP/1.1 {method} {url}\n'.format(
        method=req.method,
        url=req.url) + bcolors.ENDC)

    print(bcolors.BLUE + '{headers}\n'.format(
        headers='\n'.join('{}: {}'.format(k, v)
                          for k, v in req.headers.items()),
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
    ) + bcolors.ENDC)

    print(bcolors.BLUE + '{headers}\n'.format(
        headers='\n'.join('{}: {}'.format(k, v)
                          for k, v in res.headers.items())
    ) + bcolors.ENDC)

    try:
        obj = json.loads(res.content)
        print(bcolors.GREEN)
        pprint.pprint(obj)
        print(bcolors.ENDC)
    except:
        print(res.content)


# Proxy API calls to the array to bypass CORS
@app.route('/api', defaults={'path': ''}, methods=['GET', 'PUT', 'POST', 'DELETE', 'OPTIONS', 'HEAD', 'PATCH'])
@app.route("/api/<path:path>", methods=['GET', 'PUT', 'POST', 'DELETE', 'OPTIONS', 'HEAD', 'PATCH'])
@app.route("/oauth2/<path:path>", methods=['GET', 'PUT', 'POST', 'DELETE', 'OPTIONS', 'HEAD', 'PATCH'])
def proxy_to_fa(*args, **kwargs):
    # this is how we are passing the IP on the webpage to here, useing an additional cookie
    # just to make swagger proxy work using the flasharray ip cookie.
    if "flasharray" not in request.cookies or request.cookies["flasharray"] == "change-me":
        return "Error: Please set FlashArray IP / Hostname at top of page before making API Calls"

    header_exclude = ['host', 'set-cookie', 'cookie', 'User-Agent']
    swagger_headers = {key: value for (
        key, value) in request.headers if key.lower() not in header_exclude}
    cookie_exclude = ['flasharray', 'x-auth-token', 'Authorization']
    swagger_cookies = {key: value for (
        key, value) in request.cookies.items() if key not in cookie_exclude}
    # print(swagger_cookies)
    # print(type(swagger_cookies))

    # this is used by FA 2.x & FB
    if "x-auth-token" not in swagger_headers and "Authorization" not in swagger_headers:
        if "x-auth-token" in request.cookies and request.cookies['x-auth-token'].strip():
            # don't want to replace a header explicity passed by the swagger UI
            # but if it doesn't exist and we have one as a cookie
            swagger_headers['x-auth-token'] = request.cookies['x-auth-token']

    swagger_headers['User-Agent'] = USER_AGENT

    # rewrite url to change to https and the remote array IP address
    url = parse.urlparse(request.url)
    host = request.cookies["flasharray"]
    url = url._replace(scheme="https", netloc=host)

    # Make actual API call
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

    # print ("flask request: {}".format(request.method))

    excluded_headers = ['content-encoding',
                        'content-length', 'transfer-encoding', 'connection']
    response_headers = [(name, value) for (name, value) in resp.raw.headers.items()
                        if name.lower() not in excluded_headers]

    print_request(resp.request)
    print_response(resp)

    proxy_response = Response(resp.content, resp.status_code, response_headers)

    # we are going to store x-auth-token in the web browser cookie,
    # instead of doing it server side is in browser cookies
    auth_token = ""
    for header, value in response_headers:
        if 'x-auth-token' in header:
            auth_token = value
    if auth_token != "":
        proxy_response.set_cookie("x-auth-token", auth_token, path='/')

    return proxy_response


# This either lists the directory, or returns the actual file
@app.route('/<path:req_path>')
def get_specs(req_path):
    abs_path = os.path.join(ROOT_DIR, req_path)

    # Return 404 if path doesn't exist
    if not os.path.exists(abs_path):
        return abort(404)

    # Check if path is a file and serve
    if os.path.isfile(abs_path):
        # changing to send_from_directory to avoid path traversal attacks
        return send_from_directory(ROOT_DIR, req_path, as_attachment=True)

    # List Directroy
    if req_path == "specs" or req_path == "specs/":
        # Show directory contents
        results = []
        for item in get_spec_index():
            results.append({
                'name': item['name'],
                'url': item['url']})

        return json.dumps(results)

    return abort("Unknown error")


def get_spec_index():
    with open(os.path.join(ROOT_DIR, "spec_index.yaml")) as f:
        spec_index = yaml.load(f, Loader=yaml.FullLoader)
    return spec_index


# Automatically identify array and load Api
@app.route('/identify', methods=['GET'])
def identify(*args, **kwargs):
    if "flasharray" not in request.cookies or request.cookies["flasharray"] == "change-me":
        return "Error: Please set FlashArray/FlashBlade IP / Hostname at top of page before making API Calls"

    host = "https://{}/api/".format(request.cookies["flasharray"])

    try:
        api_version_response = requests.get(
            host + "api_version",
            verify=False)
    except:
        return "Failed to communicate with IP"

    if api_version_response.status_code != 200:
        # Error this is probably not FA or FB
        return "This doesn't look like a FlashArray or FlashBlade with REST API support"

    versions_response = json.loads(api_version_response.text)
    if 'version' in versions_response:
        versions = versions_response['version']
        array_type = "FlashArray"
    elif 'versions' in versions_response:
        # this is FlashBlade
        array_type = "FlashBlade"
        versions = versions_response['versions']
    else:
        return "This doesn't look like a FlashArray or FlashBlade with REST API support"

    # because different version vs versions don't need this way to detect, but save in case
    # ident_response = requests.get(
    #    host+"1.0/file-systems",
    #    verify=False)

    # array_type = ""
    # if ident_response.status_code == 404:
    #    array_type = "FlashArray"
    # elif ident_response.status_code == 403:
    #    array_type = "FlashBlade"

    # load spec index
    spec_index = get_spec_index()
    # find highest match
    matches = []
    for spec in spec_index:
        if spec['model'] == array_type and spec['version'] in versions:
            matches.append(spec)

    # return a reverse sorted list of matching spec files.
    sorted_list = sorted(
        matches, key=lambda k: k['version_sort'], reverse=True)
    if len(sorted_list) > 0:
        return redirect('/?urls.primaryName=' + sorted_list[0]['name'])
    return "Sorry, Could not find matching spec."

# Generate RSA Key Pair
@app.route('/oauth2_pub_priv_key_pair', methods=['GET'])
def pub_priv_key_pair(*args, **kwargs):
    data = "RSA 2048 bit key pair, save the private key, and create an \n" \
           "API Client with the public key. Not recommended for use in \n" \
           "production, private key is not encrypted.\n"
    key = RSA.generate(2048)
    data += key.export_key().decode("UTF-8")
    data += '\n'
    data += key.publickey().export_key().decode("UTF-8")

    print("======================== Generating an RSA 2048 Bit Key Pair =========================")
    print(data)

    return Response(data, mimetype="text/plain")

# Authenticate
@app.route('/oauth2_token_from_private_key', methods=['POST'])
def id_token_from_private_key(*args, **kwargs):
    if "flasharray" not in request.cookies or request.cookies["flasharray"] == "change-me":
        return "Error: Please set FlashArray/FlashBlade IP / Hostname at top of page before making API Calls"

    host = "https://{}/oauth2/1.0/token".format(request.cookies["flasharray"])

    required_values = ["issuer_name", "client_id", "key_id", "username"]
    private_key = str(request.get_data(), 'utf-8')
    try:
        data = request.headers
        missing = []
        for k in required_values:
            if k not in data:
                missing.append(k)
        if missing:
            return "Missing required values {}".format(",".join(missing))

        token = generate_id_token(data['issuer_name'], data['client_id'],
                                  data['key_id'], data['username'], private_key)

        print("\n==================== Authenticating to /oauth2/1.0/token =====================")
        oauth_request = {'grant_type': 'urn:ietf:params:oauth:grant-type:token-exchange',
                         'subject_token': token,
                         'subject_token_type': 'urn:ietf:params:oauth:token-type:jwt'}
        r = requests.post(host, data=oauth_request, verify=False)

        print_request(r.request)
        print_response(r)
        r = r.json()
        if 'access_token' in r:
            data = {
                'Authorization': 'Bearer ' + r['access_token'],
                'description': "Use the SwaggerUI Authorize button at the top of the page and copy in the Authorization token to use other API endpoints."}

            r = Response(json.dumps(data, indent=4))
            r.set_cookie('x-auth-token', path='/', expires=0)
            return r
        return('Failed to get proper access token:\n{}'.format(r))

    except ValueError as e:
        print(e)
        return "Unable to json decode payload. {}".format(e)

# Token Exchange requires a JWT in the Authorization Bearer header with this format
# client_id, key_id, client_name, username


def generate_id_token(issuer, client_id, key_id, sub, private_key, expire_hours=24):
    private_key = private_key.strip()
    issuer = issuer.strip()
    client_id = client_id.strip()
    key_id = key_id.strip()
    sub = sub.strip()

    addtl_header = {
        "kid": key_id,
    }
    payload = {
        "aud": client_id,
        "sub": sub,
        "iss": issuer,
        "iat": int(time()),
        "exp": int(time()) + expire_hours * 3600
    }
    print("\n================================== Genrating a JWT =============================================")
    print("\nPayload:")
    pprint.pprint(payload)
    print("\nAddtl_header:")
    pprint.pprint(addtl_header)
    print("Private Key: \n{}".format(private_key))
    print("Creating jwt using Python jwt library:")

    print("\njwt.encode(payload, private_key, algorithm='RS256', headers=addtl_header)")

    new_jwt = jwt.encode(payload, private_key,
                         algorithm='RS256', headers=addtl_header)

    # python3 jwt returns bytes, so we need to decode to string
    # print("ID Token: {}".format(new_jwt.decode()))
    return new_jwt


# Generate a token_id to use for authorization
@app.route('/oauth2_token_id', methods=['POST'])
def token_id(*args, **kwargs):

    data = {}

    return json.dumps(data)


@app.after_request
def add_header(r):
    r.headers["Cache-Control"] = "no-cache, no-store, max-age=0, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    return r

def oecho(text):
    # ANSI escape code for orange and reset
    O = "\033[38;5;208m"
    NC = "\033[0m"
    print(f"{O}{text}{NC}")

if __name__ == "__main__":
    os.environ["FLASK_DEBUG"] = "1"

    # Delay to ensure everything is loaded as before
    time.sleep(1)

    # Display the message
    oecho("Open your browser to http://127.0.0.1, use Ctrl+C to end close PureSwagger")
    
    app.run(host='0.0.0.0')
