import requests
import yaml
import json
import queue
import threading
import os
import urllib
from urllib.parse import urlparse
import sys


fb_max_version = { 0:0, 1:8 }      #this is a list of major:minor_max version pairs
pure1_max_version = { 0:-1, 1:-1}
thread_count = 4
baseURL = 'http://purest.dev.purestorage.com'
spec_url = baseURL+'/pure-urls.js'
with open("fb_template.yaml") as f:
    template_yaml =  yaml.safe_load(f)


class SpecWorker(threading.Thread):
    def __init__(self,s,q,file_download_root,io_lock):
        threading.Thread.__init__(self)
        self.s = s
        self.q = q
        self.file_download_root = file_download_root
        self.io_lock = io_lock

    def find(self, key, dictionary):
        for k, v in dictionary.items():
            if k == key:
                yield v
            elif isinstance(v, dict):
                for result in self.find(key, v):
                    yield result
            elif isinstance(v, list):
                for d in v:
                    if isinstance(d, dict):
                        for result in self.find(key, d):
                            yield result 
        

    def parse_spec(self, spec_dict):
        
        for x in self.find("$ref", spec_dict):
            yield x

    def apply_template(self,spec_file):
        global template_yaml
        

        spec_yaml = yaml.safe_load(spec_file)
        spec_yaml['info']['description'] = template_yaml['info']['description']

        #remove host references because of security concern.
        if 'host' in spec_yaml:
            del spec_yaml['host']
        
        version = spec_yaml['info']['version']

        spec_yaml['basePath'] = "/api"

        #add api version into path
        #need to do this so we can add non version specific endpoints like get_version & login
        paths = list(spec_yaml['paths'])
        print(paths)
        for path in paths:
            new_path = '/' + str(version) + path
            spec_yaml['paths'][new_path] = spec_yaml['paths'][path]
            del spec_yaml['paths'][path]

        spec_yaml['paths']['/api_version'] = template_yaml['paths']['/api_version']
        spec_yaml['paths']['/login'] = template_yaml['paths']['/login']
        spec_yaml['tags'] = template_yaml['tags'] + spec_yaml['tags']


        return yaml.dump(spec_yaml)



    #Dowload and return the file
    def get_spec_file(self,spec_url,head):
        #spec_url is absolute path here
        #head means it's the first and we need to apply our template here.
        

        #figure out local path
        url_parse_result = urllib.parse.urlparse(spec_url)
        url_path = url_parse_result.path
        url_path = url_path.replace("/purest","")  #pull out the purest
        #print(self.file_download_root)
        #print(url_path)
        save_to_path = self.file_download_root+url_path

        #print("Spec URL:{}   Local File:{}".format(spec_url,save_to_path))
        
        #don't used cached file for head file.
        if not head:
            try:
                with self.io_lock:
                    with open(save_to_path,"r") as f:
                        spec_file = f.read()
                spec_dict = yaml.safe_load(spec_file)
                if not isinstance(spec_dict, dict):
                    abc=2

                #print("Returning Local file")

                return spec_file

            except FileNotFoundError:
                pass
        
        #file not found, lets download it

        
        #print("downloading spec ")
        self.response = self.s.get(spec_url)
        spec_file = self.response.text

        spec_dict = yaml.safe_load(spec_file)
        if not isinstance(spec_dict, dict):
            abc=2
        if '404 Not Found' in spec_file:
            abn = 99
        if self.response.status_code != 200 or '404' in spec_file:
            print(response)
        if spec_file == '':
            abj = ""

        path,_ = os.path.split(save_to_path)
        os.makedirs(path, exist_ok=True)

        if head:
            spec_file = self.apply_template(spec_file)
            
        with self.io_lock:
            with open(save_to_path,"w") as f:
                f.write(spec_file)
                f.close()
        
        with self.io_lock:
            with open(save_to_path,"r") as f:
                temp_check = f.read()

        spec_dict = yaml.safe_load(temp_check)
        if not isinstance(spec_dict, dict):
            abc=2
        if '404 Not Found' in temp_check:
            abn = 99
        if self.response.status_code != 200 or '404' in temp_check:
            print(response)
        if temp_check == '':
            abj = ""

        

        return spec_file


    def run(self):

        while True:
            item = self.q.get()
            spec_url = item['url']
            head = item['head']

            try:
                if spec_url == 'http://purest.dev.purestorage.com/purest/models/FB1.X/_fixed-reference.yaml':
                    abj = 2

                spec_file = self.get_spec_file(spec_url, head)
            except:
                print("Unexpected error:", sys.exc_info()[0])
                self.q.task_done()
                raise
            
            spec_dict = yaml.safe_load(spec_file)
            if not isinstance(spec_dict, dict):
                abc=2

            for rel_path in self.parse_spec(spec_dict):
                new_abs_path = urllib.parse.urljoin(spec_url,rel_path)
                if '1.X' in new_abs_path:
                    print("1.x in spec_url: {}".format(spec_url))

                #print("source: {}  rel: {}  abs: {}".format(spec_url,rel_path,new_abs_path))
                self.q.put({'url':new_abs_path,'head':False})
            self.q.task_done()


def main():

    script_path = os.path.dirname(os.path.realpath(__file__))
    
    file_download_root = os.path.abspath(os.path.join(script_path,"../html"))
    s = requests.Session()
    q = queue.Queue()
    resp = s.get(spec_url).text

    #need to convert it from javascript to valid json
    #strip just the list:
    step1 = resp[resp.find('['):resp.find(']')+1]
    #need to add quotes around the url&name 
    json_compat = step1.replace(' url: ',' "url": ').replace(' name: ',' "name": ')
    #print(json_compat)

    spec_list = json.loads(json_compat)

    for spec in spec_list:
        max_version = {} 
        if ".x" in spec['name']:
            continue

        elif "Flashblade" in spec['name']:
            max_version = fb_max_version
        
        elif "Pure1" in spec['name']:
            max_version = pure1_max_version


        try:
            version = spec['name'].split()[1]
            version_major = int(version.split(".")[0])
            version_minor = int(version.split(".")[1])
            if version_major in max_version and version_minor <= max_version[version_major]:
                #actually go and pull down this file.
                #get_spec_file(spec,s) 
                q.put({"url":baseURL+spec['url'],"head":True})
        except (ValueError):
            pass
    
    #Start threads to do the work.
    io_lock = threading.Lock()
    for _ in range(thread_count):
        t = SpecWorker(s,q,file_download_root,io_lock)
        t.setDaemon(True)
        t.start()
    
    #wait till all threads finish    
    q.join()
    #index the spec files and create on initial load
    create_spec_index()


def create_spec_index():
    print ("creating spec index")

    specs_path = os.path.join("../html/specs")

    results=[]
    for file_name in os.listdir(specs_path):
        item = {}
        
        with open(os.path.join(specs_path,file_name)) as f:
            print("loading: "+file_name)
            spec_file = yaml.load(f)
            if "FlashArray" in spec_file["info"]["title"]:
                item["model"] = "FlashArray"
            elif "FlashBlade" in spec_file["info"]["title"]:
                item["model"] = "FlashBlade"
            else:
                item["model"] = "Unknown"
            
            item["version"] = str(spec_file["info"]['version'])
            #print(item['version'])
            version_split = item["version"].split('.')
            item["version_sort"] = int(version_split[0])*1000 + int(version_split[1])
            item['filename'] = file_name
            item['url'] = 'specs/'+file_name
            item['name'] = "{} v{}".format(item['model'],item['version'])   

        
        results.append(item)


    sorted_results = sorted(results, key=lambda k: (k['model'], k['version_sort']))

    with open(os.path.join("../html/spec_index.yaml"),"w+") as f:
        f.write(yaml.dump(sorted_results))



if __name__=='__main__':   
    try:
        main()
    except KeyboardInterrupt:
        print()
