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
import random
from datetime import datetime


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
            
def main(laparams=None):
    with PdfMinerWrapper("REST_API_1.13.pdf",laparams) as doc:
        
        resource_found = False
        machine = ["f","fd","e","ed",""]
        state = machine[0]
        line = ""
        fontname = ""
    
        x_coordinate = 0.0 #The distance from left edge of page
        middle_x=0.0


        paths = {}
        path=""
        
        example_name=""
        tags=[]
        tag=""

        param_index=0
        tag_index=0

        path_id=""
        
        

        count=0
        for page in doc:     
            #print 'Page no.', page.pageid, 'Size',  (page.height, page.width)
            if page.pageid < 38:
                continue
            elif page.pageid > 39:
                exit()
            
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

            
            print("page: "+str(page.pageid))
            print(json.dumps(sort(items),indent=3))




def sort(items):
    rows=[]
    fuzzy=3

    for item in items:
        found=False
        for  idx,row in enumerate(rows):

            if item['box'][1] > (row['y'] - fuzzy) and item['box'][1] < (row['y']+fuzzy):
                rows[idx]['items'].append(item)
                found=True

        if not found:
            #creating a new row and assigned item to that row.
            rows.append({'y':item["box"][1],"items":[item]})
    
    #This sorts the columns in each row by the X
    for idx,row in enumerate(rows):
        rows[idx]['items'] =  sorted(row['items'],key=lambda k: k['box'][0])

    sorted_rows = sorted(rows,key=lambda k: k['y'],reverse=True)
    return(sorted_rows)

    
                
        



    


if __name__ == "__main__":
    options = {"line_overlap":1,
    "char_margin":1,
    "line_margin":1,
        "word_margin":
        1,
        "boxes_flow":1}
    laparams = LAParams( all_texts = True, **options)

    main(laparams)


