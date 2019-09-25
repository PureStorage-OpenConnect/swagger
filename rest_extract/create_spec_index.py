import yaml
import json
import sys
import os


def main():
    print ("creating spec index")

    specs_path = os.path.join("../html/specs")

    results=[]
    for file_name in os.listdir(specs_path):
        item = {}
        if 'DS_Store' in file_name:
            continue
        
        with open(os.path.join(specs_path, file_name)) as f:

            print("loading: "+file_name)
            spec_file = yaml.safe_load(f)
            
            if "FlashArray" in spec_file["info"]["title"]:
                item["model"] = "FlashArray"
            elif "FlashBlade" in spec_file["info"]["title"]:
                item["model"] = "FlashBlade"
            elif "Pure1" in spec_file["info"]["title"]:
                item["model"] = "Pure1"
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
