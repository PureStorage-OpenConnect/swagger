import os
from flask import Flask, request, redirect, url_for, send_from_directory, flash, Response
import rest_extract
import requests
import urllib3
from urllib import parse

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


ROOT_DIR = '/usr/share/pureswagger/html'
ALLOWED_EXTENSIONS = set(['pdf', 'json'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = ROOT_DIR
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def root():
  return send_from_directory(ROOT_DIR,"index.html")

def print_request(req):
    print( 'HTTP/1.1 {method} {url}\n{headers}\n\n{body}'.format(
        method=req.method,
        url=req.url,
        headers='\n'.join('{}: {}'.format(k, v) for k, v in req.headers.items()),
        body=req.body))

def print_response(res):
    print('HTTP/1.1 {status_code}\n{headers}\n\n{body}'.format(
        status_code=res.status_code,
        headers='\n'.join('{}: {}'.format(k, v) for k, v in res.headers.items()),
        body=res.content,
    ))

#Proxy API calls to the array to bypass CORS
@app.route('/api', defaults={'path': ''}, methods=['GET', 'PUT','POST','DELETE','OPTIONS','HEAD'])
@app.route("/api/<path:path>", methods=['GET', 'PUT','POST','DELETE','OPTIONS','HEAD'])
def proxy_to_fa(*args, **kwargs):
    if "flasharray" not in request.cookies or request.cookies["flasharray"] == "change-me":
        return "Error: Please set FlashArray IP / Hostname at top of page before making API Calls"

    url = parse.urlparse(request.url)
    url = url._replace(scheme="https",netloc=request.cookies["flasharray"])   
    
    resp = requests.request(
        str(request.method),
        url.geturl(),
        headers={key: value for (key, value) in request.headers if key != 'Host'},
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=False,
        verify=False)
    print ("flask request: {}".format(request.method))
    
    print_request(resp.request)
    print_response(resp)

    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = [(name, value) for (name, value) in resp.raw.headers.items()
               if name.lower() not in excluded_headers]

    return Response(resp.content, resp.status_code, headers)

@app.route('/<path:file>/')
def get_file(file):
    return send_from_directory(ROOT_DIR,file)

@app.route('/swagify', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            if "pdf" in file.filename:
                filename = "rest.pdf"
            else:
                filename = "swagger.json"

            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.exists(filepath):
                os.remove(filepath)
            
            
            file.save(filepath)
    
            rest_extract.main()
            return redirect('/')

    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form action=/swagify method=post enctype=multipart/form-data>
      <p><input type=file name=file>
         <input type=submit value=Upload>
    </form>
    '''

@app.after_request
def add_header(r):
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r


if __name__ == "__main__":
    app.run(host='0.0.0.0')