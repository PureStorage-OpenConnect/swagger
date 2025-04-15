import os
from os import listdir
from os.path import isfile
import argparse

import yaml
try:
    from yaml import CDumper as Dumper
except ImportError:
    from yaml import Dumper



def apply_template(spec_file, template, model):
    template_yaml = template
    spec_yaml = yaml.safe_load(spec_file)


    # Overwrite the description
    spec_yaml['info']['description'] = template_yaml['info']['description']

    if model == 'fb2':
        # Add template paths and tags to file
        for p in template_yaml['paths']:
            spec_yaml['paths'][p] = template_yaml['paths'][p]
        spec_yaml['tags'] = template_yaml['tags'] + spec_yaml['tags']

    elif model == 'fa2':

        spec_yaml['components']['securitySchemes'] = template_yaml['components']['securitySchemes']
        spec_yaml['security'] = template_yaml['security']
        spec_yaml['tags'] = template_yaml['tags'] + spec_yaml['tags']
        for p in template_yaml['paths']:
            spec_yaml['paths'][p] = template_yaml['paths'][p]
        
    elif model == 'pure1-1':
        #nothing specific, already set Info above.
        pass

    # some templates have servers set to "https://[array]/" and "http://[array]/"
    # we want just http, which it will use by default when not there, and we don't want the [array]
    if 'servers' in spec_yaml:
        del spec_yaml['servers']

    # Sort spec_yaml dict so the output text puts consistent information at the top
    sort_order = [
        'openapi', 'info', 'servers', 'security', 'paths', 'components', 'tags'
    ]
    
    sorted_spec_yaml = {key: spec_yaml[key] for key in sort_order if key in spec_yaml}
    
    # Add any other fields not in the sort order to the end
    for key in spec_yaml:
        if key not in sort_order:
            sorted_spec_yaml[key] = spec_yaml[key]
            
    # does the default yaml dump preserve the sort order? 

    return yaml.dump(sorted_spec_yaml, Dumper=Dumper, sort_keys=False)


def main():
    parser = argparse.ArgumentParser(description='Apply templates to OpenAPI specs.')
    parser.add_argument('--overwrite', action='store_true', help='Overwrite existing files in the spec directory')
    args = parser.parse_args()
    overwrite = args.overwrite


    script_path = os.path.dirname(os.path.realpath(__file__))
    project_dir = os.path.abspath(os.path.join(script_path, "../"))


    spec_directory = os.path.join(project_dir, "html", "specs")
    original_spec_directory = os.path.join(project_dir, "definitions", "oas3.x")

    with open(os.path.join(script_path, "fb_template.yaml"), encoding='utf-8') as f:
        fb_template_yaml = yaml.safe_load(f)
    with open(os.path.join(script_path, "fa2_template.yaml"), encoding='utf-8') as f:
        fa_template_yaml = yaml.safe_load(f)
    with open(os.path.join(script_path, "pure1_template.yaml"), encoding='utf-8') as f:
        pure1_template_yaml = yaml.safe_load(f)

    spec_list = listdir(original_spec_directory)
    for spec in spec_list:
        if spec == ".DS_Store":
            continue

        fullpath = os.path.join(original_spec_directory, spec)
        new_fullpath = os.path.join(spec_directory, spec)

        # check if destination already exists, and pass if not overwrite
        if not overwrite and isfile(new_fullpath):
            print(f"skipping {spec}")
            continue
    
        print(f"Proccing {spec}")


        if isfile(fullpath):
            lower_name = spec.lower()

            if lower_name.startswith('fa2'):
                template = fa_template_yaml
                model = 'fa2'

            elif lower_name.startswith('fb2'):
                template = fb_template_yaml
                model = 'fb2'

            elif lower_name.startswith('pure1-1'):
                template = pure1_template_yaml
                model = 'pure1-1'

            else:
                # don't need to apply template to fa as that is done during initial creation from the pdf
                continue

            with open(fullpath, "r", encoding='utf-8') as f:
                spec_file = f.read()

            output = apply_template(spec_file, template, model)

            with open(new_fullpath, "w", encoding='utf-8') as f:
                f.write(output)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print()
