import requests
import yaml
import json
import queue
import threading
import os
import urllib
import sys
import argparse

fb_max_version = { 0:0, 1:12, 2:8 }      #this is a list of major:minor_max version pairs
pure1_max_version = { 0:-1, 1:1 }
fa_2_max_version = { 2:20 }
thread_count = 8
baseURL = 'http://purest.dev.purestorage.com'
spec_url = baseURL + '/pure-urls.js'
cache = {}
overwrite_local_files = False

class SpecWorker(threading.Thread):
    def __init__(self, s, q, file_download_root, io_lock, cache_lock):
        threading.Thread.__init__(self)
        self.s = s
        self.q = q
        self.file_download_root = file_download_root
        self.io_lock = io_lock
        self.cache_lock = cache_lock

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


    #Dowload and return the file
    def get_spec_file(self, spec_url, head, model):
      

        # figure out local path
        url_parse_result = urllib.parse.urlparse(spec_url)
        url_path = url_parse_result.path
        url_path = url_path.replace("/purest","")  #pull out the purest
        #print(self.file_download_root)
        #print(url_path)

        if head:
            save_to_path = self.file_download_root + '/original_spec' + url_path
        else:
            save_to_path = self.file_download_root + url_path

        # print("Spec URL:{}   Local File:{}".format(spec_url,save_to_path))
        # don't used cached file for head file.
        # also, don't use if we want to overwrite local files.
        if not (head or overwrite_local_files):
            # try and pull yaml file locally
            try:
                with self.io_lock:
                    with open(save_to_path,"r") as f:
                        spec_file = f.read()
                #print("Returning Local file")
                return spec_file

            except FileNotFoundError:
                pass
        
        # file not found, lets download it
        # print("downloading spec ")
        self.response = self.s.get(spec_url)
        spec_file = self.response.text
        path, _ = os.path.split(save_to_path)
        os.makedirs(path, exist_ok=True)

        if '.yaml' in spec_url:
            spec_yaml = yaml.safe_load(spec_file)

            #remove host references because of security concern.
            if 'host' in spec_yaml:
                del spec_yaml['host']

            spec_file = yaml.dump(spec_yaml, sort_keys=False)

        with self.io_lock:
            with open(save_to_path,"w") as f:
                f.write(spec_file)
        
        return spec_file


    def run(self):
        global cache

        while True:
            item = self.q.get()
            spec_url = item['url']

            with self.cache_lock:
                if spec_url in cache:
                    #it  means another thread is already working on getting this item
                    self.q.task_done()
                    continue
                else:
                    cache[spec_url] = 'working'

            head = item['head']
            model = item['model']

            try:
                 spec_file = self.get_spec_file(spec_url, head, model)
            except:
                print("Unexpected error:", sys.exc_info()[0])
                self.q.task_done()
                raise
            if '.yaml' in spec_url:
                #means another  yaml file and need to look for more references.
                spec_dict = yaml.safe_load(spec_file)

                #There is at least one file with .yaml extension, but is not yaml...
                if isinstance(spec_dict, dict):
                    for rel_path in self.parse_spec(spec_dict):
                        new_abs_path = urllib.parse.urljoin(spec_url,rel_path)

                        #print("source: {}  rel: {}  abs: {}".format(spec_url,rel_path,new_abs_path))
                        self.q.put({'url':new_abs_path,'head':False, 'model':model })
                else:
                    print("Yaml file: {} does not appear to be yaml !".format(spec_url))

            with self.cache_lock:
                cache[spec_url] = 'finished'
            self.q.task_done()


def main():
    global overwrite_local_files

    parser = argparse.ArgumentParser()
    parser.add_argument("--overwrite-local-files", help="overwrite local files", action="store_true")
    args = parser.parse_args()

    if args.overwrite_local_files:
        
        overwrite_local_files = True

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
    # someone put a typo in the json list with a double ,,
    json_compat = json_compat.replace(',,',',')
    #print(json_compat)

    spec_list = json.loads(json_compat)

    with open("fb_template.yaml") as f:
        fb_template_yaml = yaml.safe_load(f)
    with open("fa2_template.yaml") as f:
        fa_template_yaml = yaml.safe_load(f)
    with open("pure1_template.yaml") as f:
        pure1_template_yaml = yaml.safe_load(f)

    for spec in spec_list:
        max_version = {}
        lower_name = spec['name'].lower()

        if ".x" in lower_name:
            continue

        elif "flashblade" in lower_name:
            max_version = fb_max_version
            template = fb_template_yaml
            model = 'fb'
        
        elif "pure1" in lower_name:
            max_version = pure1_max_version
            template = pure1_template_yaml
            model = 'pure1'
    
        elif "flasharray" in lower_name:
            max_version = fa_2_max_version
            template = fa_template_yaml
            model = 'fa2'
        else:
            continue

        try:
            version = spec['name'].split()[1]
            version_major = int(version.split(".")[0])
            version_minor = int(version.split(".")[1])
            if version_major in max_version and version_minor <= max_version[version_major]:
                #actually go and pull down this file.
                #get_spec_file(spec,s) 
                q.put({"url":baseURL+spec['url'],"head":True, "model":model, "template": template})
                print("Working on {}".format(spec['name']))
        except (ValueError):
            pass
    
    #Start threads to do the work.
    io_lock = threading.Lock()
    cache_lock = threading.Lock()
    for _ in range(thread_count):
        t = SpecWorker(s,q,file_download_root,io_lock,cache_lock)
        t.setDaemon(True)
        t.start()
    
    # wait till all threads finish    
    q.join()


if __name__=='__main__':   
    try:
        main()
    except KeyboardInterrupt:
        print()
