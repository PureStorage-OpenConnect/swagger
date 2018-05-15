from pdfminer.pdfparser import PDFParser
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTTextBox,LTChar, LTFigure
import sys
import re
from string import digits
from pprint import pprint
import json
from datetime import datetime
import yaml
from genson import SchemaBuilder

baseDir = "/usr/share/pureswagger/"
webRoot = baseDir + "html/"

##uncomment below to run in CWD instead of hardcoded docker container directories.
#webRoot = ""
#baseDir = ""

class PdfMinerWrapper(object):
    """
    Usage:
    with PdfMinerWrapper('2009t.pdf') as doc:
        for page in doc:
           #do something with the page
    """
    def __init__(self, pdf_doc, pdf_pwd="",laparams=None):
        self.pdf_doc = pdf_doc
        self.pdf_pwd = pdf_pwd
        self.laparams = laparams
 
    def __enter__(self):
        #open the pdf file
        self.fp = open(self.pdf_doc, 'rb')
        # create a parser object associated with the file object
        parser = PDFParser(self.fp)
        # create a PDFDocument object that stores the document structure
        doc = PDFDocument(parser, password=self.pdf_pwd)
        # connect the parser and document objects
        parser.set_document(doc)
        self.doc=doc
        return self
    
    def _parse_pages(self):
        rsrcmgr = PDFResourceManager()
        if self.laparams == None:
            laparams = LAParams( all_texts = True)
        else:
            laparams=self.laparams
        device = PDFPageAggregator(rsrcmgr, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)
    
        for page in PDFPage.create_pages(self.doc):
            
            interpreter.process_page(page)
            # receive the LTPage object for this page
            layout = device.get_result()
            
            # layout is an LTPage object which may contain child objects like LTTextBox, LTFigure, LTImage, etc.
            yield layout
    def __iter__(self): 
        return iter(self._parse_pages())
    
    def __exit__(self, _type, value, traceback):
        self.fp.close()


def format_examples(examples):
    out=""
    for example in examples:
        out += example['name']
        out += "<br>URL: {}<br>".format(example['request']['url'])
        out += "Body:<br>{}".format(example['request']['body'])
        out += "<br>Response:{}<br><br>".format(example['response'])
    
    return out


            
def main():
    with PdfMinerWrapper(webRoot+"rest.pdf") as doc:
        
        resource_found = False
        machine = ["f","fd","e","ed",""]
        state = machine[0]
        line = ""
        fontname = ""
    
        x_coordinate = 0.0 #The distance from left edge of page
        middle_x=0.0

        open_oas = get_open_api_header()
        

        paths = open_oas['paths']
        path=""

        components = open_oas['components']
        
        example = {}
        examples = {}
        tags = open_oas['tags']
        tag=""

        param_index=0
        tag_index=0
        path_id=""
        version=""
        example=None
        start_page=1
        total_pages=120

        print("Parsing Rest API...")
        for page in doc:     
            #print 'Page no.', page.pageid, 'Size',  (page.height, page.width)
            if resource_found:
                print("{:.0f} Percent Complete".format((page.pageid-start_page)/total_pages*100),end='\r')
       
                

            items=[]
            for tbox in page:
                
                if not isinstance(tbox, LTTextBox):
                    continue
                #print ' '*1, 'Block', 'bbox=(%0.2f, %0.2f, %0.2f, %0.2f)'% tbox.bbox
                for obj in tbox:
                    #print ' '*2, obj.get_text().encode('UTF-8')[:-1] #,  '(%0.2f, %0.2f, %0.2f, %0.2f)'% tbox.bbox
                    line = obj.get_text().strip() #.encode('UTF-8')[:-1]

                    
                    for c in obj:
                        if not isinstance(c, LTChar):
                            continue 

                        fontname = c.fontname
                        #size = str(c.size) #.encode('UTF-8')
                        break
                    
                    items.append(
                        {'text':obj.get_text().strip(),
                        'box':tbox.bbox,
                        'font':fontname}
                        )

            sorted_items = pdf_sort(items)

            for row in sorted_items:
                for item in row['items']:


                    #### First Pass at changing state + initialization @ state change

                    line = item['text']
                    if page.pageid == 1 and version == "":
                        version = "/" + line.split(" ")[2] + "/"
                    
                    if line.startswith("Resources") and item['font'] == "Arial,Bold" :
                        start_page = page.pageid
                        resource_found = True
                    
                    
                    if resource_found:
                            
                        x_coordinate = item['box'][0]
                        #print line.encode('UTF-8')
                        #print '({}|{}|{}|{})'.format( c.fontname, c.size,type(c.size),tbox.bbox[0])

                        if 'PUT array' in line:
                            pass

                        if re.match(r"^[0-9]+\. ",line):
                            #Match section identifiers
                            # i.e.  1. Authentication
                            tag = line.split(" ")[1]
                            tags.append({"name":tag,"description":""})
                            tag_index = len(tags)-1

                            
                            
                            state="fd"
                            continue
                        
                        elif re.match(r"^[0-9]+\.[0-9]+ ",line):

                            #Match endpoint
                            # i.e. "2.1 GET array"
                            tag_index +=1
                            temp = line.split(" ")
                            method = temp[1].lower()
                            path = version+temp[2]
                            if path not in paths:
                                paths[path] = {}
                            paths[path][method] = {"tags":[tag],
                                                      "description":"",
                                                      "operationId":method+path,
                                                      "responses": {
                                                           '200':{
                                                               "content":{
                                                                   "application/json":{
                                                                       "schema":{
                                                                       }
                                                                   }
                                                               },
                                                               "description":""
                                                           }
                                                       }  
                                                    }
                                                

                            
                            examples = {}
                            param_index=0
                            if method=="get" or method == "delete" or "{" in path:
                                #Params go in parameters... see below for POST
                                #need to do this before to initilize the parameters dict
                                paths[path][method]['parameters'] = []
                            
                            #Need to create path param for each {id1} .. {id2} in path
                            for path_id in re.findall(r'\{(.*?)\}',path):
                                #adding in special path parameter volume/{volumeid}  example
                                paths[path][method]['parameters'].append({"name":path_id,"in":"path","required":True,"schema":{"type":"string"}})
                                param_index += 1

                            if not method=="get" and not method=="delete" :
                                #Params go in RequestBody for POST & PUT
                                paths[path][method]['requestBody'] = {'content':{"application/json":{"schema":{"properties":{},"type":"object"}}}}

                            state="ed"
                            continue
                        
                        elif line.startswith("Parameters"):
                            
                            state="parameters"
                            continue

                        elif line.startswith("Parameter"):
                            state="parameters"
                            continue

                        elif line.startswith("Example "):
                            state="example"
                            example_name = line
                            example = {}
                            
                            #create examples dict if it doesnt' exist
                            #if 'examples' not in paths[path][method]["responses"]["200"]["content"]["application/json"]:
                            #    paths[path][method]["responses"]["200"]["content"]["application/json"]["examples"]={}
                            #paths[path][method]["responses"]["200"]["content"]["application/json"]["examples"][example_name] = {"value":{"request":"","response":""}}
                            continue
                        
                        elif line.startswith("Request:"):
                            state="example_request"
                            continue
                        
                        elif line.startswith("Response:"):
                            state="example_response"
                            continue
                        
                        ############################################################################################
                        #### second pass, processing items in our current state
                        
                        if state == "fd":
                            tags[tag_index]['description'] += line

                        elif state == "ed":
                            paths[path][method]['description'] += line

                        elif state.startswith("parameters"):
                            if "Bold" in item['font']:
                                #This is a header, we will ignore these.
                                continue

                            if state == "parameters_3":
                                if x_coordinate < middle_x:
                                    #this means we wrapped around and are now on a new param.
                                    #the x coordinate is now left of that last text box we processed
                                    state = "parameters"
                                    param_index +=1

                            if state == "parameters":
                                #first param
                                param_name = line
                                if param_name != "None":
                                    if  method == "get" or  method == "delete":
                                        paths[path][method]['parameters'].append({"in":"query","name":param_name,"description":"","schema":{}})

                                    else :
                                        paths[path][method]['requestBody']['content']['application/json']['schema']['properties'][param_name] = {"description":""}
                                        

                                state = "parameters_2"
                                if " " not in line:
                                    #sometimes the type is concatenated with the param_name, we can detect if there is a space in name.
                                    continue
                                else:
                                    line = line.split(" ",1)[1]
                                    #now we will roll into param2 parsing.

                            if state == "parameters_2":
                                #type
                                if param_name != "None":
                                    #folders[title]['endpoints'][endpoint]['params'][param_name]['type'] = line
                                    if  method == "get" or  method == "delete":
                                        paths[path][method]['parameters'][param_index]['schema']['type']= getType(line)
                                        if getType(line) == "array":
                                            paths[path][method]['parameters'][param_index]['schema']['items'] = {"type":"object"}

                                    else:
                                        paths[path][method]['requestBody']['content']['application/json']['schema']['properties'][param_name]['type'] = getType(line)
                                        if getType(line) == "array":
                                            paths[path][method]['requestBody']['content']['application/json']['schema']['properties'][param_name]['items'] = {"type":"object"}

                                state = "parameters_3"
                                middle_x = x_coordinate
                                if  len(line) < 17:
                                    #means the descirptions was so close the pdf parser grouped it with the type text:
                                    continue
                                


                            if state == "parameters_3":
                                if param_name != "None":
                                    if line == "Required.":
                                        #folders[title]['endpoints'][endpoint]['params'][param_name]['required'] = True
                                        if  method == "get" or  method == "delete":
                                            paths[path][method]['parameters'][param_index]['required']= True
                                        else:
                                            if 'required' not in paths[path][method]['requestBody']['content']['application/json']['schema']:
                                                paths[path][method]['requestBody']['content']['application/json']['schema']['required'] = []
                                            paths[path][method]['requestBody']['content']['application/json']['schema']['required'].append(param_name)
                                    #elif line == "Optional.":
                                        #folders[title]['endpoints'][endpoint]['params'][param_name]['required'] = False
                                    else:
                                        if  method == "get" or  method == "delete":
                                            paths[path][method]['parameters'][param_index]['description'] += line
                                        else:
                                            paths[path][method]['requestBody']['content']['application/json']['schema']['properties'][param_name]['description'] += line
                        
                        #end elif state.startswith("parameters"):

                        elif state.startswith("example_request"):
                            if state == "example_request":
                                #Process first line of example
                                split = line.split()
                                example['request'] = {}
                                example['request']['method'] = split[0]
                                example['request']['url'] = split[1]
                                example['request']['body'] = ""
                                example['response'] = ""

                                state="example_request_2"
                                continue
                                
                                
                                
                            elif state == "example_request_2":
                                #body of request
                                example['request']['body'] += line
                                try:
                                    json.loads(example['request']['body'])
                                    example['request']['body'] = json.loads(example['request']['body'])
                                except :
                                    #we are still reading in the example, lets continue to the next line
                                    continue
                                continue
                                     

                        elif state == "example_response":
                            #folders[title]['endpoints'][endpoint]['examples'][example_name]['response'] += line
                            #paths[path][method]["responses"]["200"]['examples'][example_name]['response'] += line
                            
                            #paths[path][method]["responses"]["200"]["content"]["application/json"]["examples"][example_name]["value"]['response'] += line
                            response_obj = None
                            if "..." not in line:
                                example['response'] += line
                            try:
                                response_obj = json.loads(example['response'])
                                example['response'] = json.loads(example['response'])
                            except :
                                #we are still reading in the example, lets continue to the next line
                                continue

                            #this means we have valid json and reached end of response example.
                            #we can do our end of example processing here.
                            
                            #builder = SchemaBuilder()
                            #builder.add_schema({"type":"object","properties":{}})
                            #builder.add_object(response_obj)

                            
                            
                            schema_name = (method+path+"Examples").replace("/","_")
                            paths[path][method]["responses"]["200"]["content"]["application/json"]["schema"]["$ref"] = "#/components/schemas/"+schema_name

                            examples[example_name] = example

                            try:
                                #components['schemas'][schema_name] = builder.to_schema()
                                #forget trying to build an actual schema for the example... just put a placeholder schema in.
                                components['schemas'][schema_name] = {"properties":{"ex1":{"type":"object"}}}
                            except:
                                print("Unexpected error:", sys.exc_info()[0])
                                print("failed to parse schema")
                                
                                pprint(response_obj)
                                raise

                            #now add in our example
                            components['schemas'][schema_name]["example"] = examples
                            state = "done_with_example"
                            continue
                            
                        
                            
                        
                        

        #end pages

        #apply_fixes(paths)
        print("Finished parsing API...")
        

        open_oas["info"]["version"] = version
        open_oas['paths'] = paths
        open_oas['tags'] = tags 
        #print(json.dumps(open_oas,indent=3))
        with open(webRoot+'swagger.json','w') as outfile:
            json.dump(open_oas,outfile)
        with open(webRoot+"swagger.yaml","w") as outfile:
            yaml.dump(open_oas,outfile)
        return open_oas

                            
def add_security(paths):
    paths['/auth/session']['post']['responses']['200']['headers']={"Set-Cookie":{"schema":{"type":"string","example":"session=jlkdflaslfa8oijo;iifn4oainion"}}}

def get_open_api_header():
    with open(baseDir+"template.yaml") as f:
        return yaml.safe_load(f)

def getType(t):
    if t == "list":
        return "array"
    elif t == "number":
        return "integer"
    elif t == "uri":
        return "string"
    elif t =="int":
        return "integer"

    #if t not in ['array','string','integer','boolean','number','object']:
    #    return 'string'
    if "string" in t:
        return "string"
    
    return t

def pdf_sort(items):
    rows=[]
    #fuzzy matching rows by + or - their y coordinate, a new line is typically 20 ish points below
    fuzzy=3

    for item in items:
        found=False

        #search all rows for one this item might belong to.
        for  idx,row in enumerate(rows):
            if item['box'][1] > (row['y'] - fuzzy) and item['box'][1] < (row['y']+fuzzy):
                rows[idx]['items'].append(item)
                found=True

        if not found:
            #creating a new row and assigned item to that row.
            rows.append({'y':item["box"][1],"items":[item]})
    
    #This sorts the columns in each row by the X value
    for idx,row in enumerate(rows):
        rows[idx]['items'] =  sorted(row['items'],key=lambda k: k['box'][0])

    #this sorts all the rows by their y coordinate, in reverse order as 0,0 is bottom left of page and we want to read top down.
    sorted_rows = sorted(rows,key=lambda k: k['y'],reverse=True)
    return(sorted_rows)


if __name__=='__main__':   
    main()