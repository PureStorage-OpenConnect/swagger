import os
import shutil
import rest_extract


for item in sorted(os.listdir('pdfs/')):
    #pick an item for debug purposes:
    #if item != "REST_API_1.14.pdf":
    #    continue
    
    if os.path.exists("../html/rest.pdf"):
        os.remove("../html/rest.pdf")
    shutil.copy("pdfs/"+item,"../html/rest.pdf")
    rest_extract.main(True)
    os.remove("../html/rest.pdf")
