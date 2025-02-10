import os
import yaml


def main():
    print ("creating spec index")
    specs_path = os.path.abspath(os.path.join("../html/specs"))

    results=[]
    for file_name in os.listdir(specs_path):
        item = {}
        if 'DS_Store' in file_name:
            continue

        name = file_name.replace('.spec.yaml','')
        name = name.replace('.yaml','') # makes it work for the FlashArray Files too.
        version = None
        model = None
        priority = 1

        if name.startswith('FA'):
            model = "FlashArray"
            version = name.replace('FA', '')
            
        elif name.startswith('FB'):
            model = "FlashBlade"
            version = name.replace('FB', '')
            priority = 2000
        elif name.startswith('Pure1-'):
            model = "Pure1"
            version = name.replace('Pure1-', '')
            priority = 3000
        elif name.startswith('FlashArray REST'):
            model = "FlashArray"
            version = name.replace('FlashArray REST v', '')
            priority = 4000

        if model:
            item['model'] = model
            item['version'] = version
            version_split = item["version"].split('.')
            if version_split[1] == 'X':
                version_split[1] = 99
            
            item['version_sort'] = priority + int(version_split[0])*100 + int(version_split[1])
            item['filename'] = file_name
            item['url'] = 'specs/'+file_name
            item['name'] = f"{item['model']} v{item['version']}"
            results.append(item)

    sorted_results = sorted(results, key=lambda k: (k['version_sort']))

    with open(os.path.abspath(os.path.join("../html/spec_index.yaml")),"w", encoding='utf-8') as f:
        f.write(yaml.dump(sorted_results))

if __name__=='__main__':   
    main()
