import yaml
import os
from os import listdir
from os.path import isfile


def apply_template(spec_file, template, model):
    template_yaml = template
    spec_yaml = yaml.safe_load(spec_file)
    spec_yaml['info']['description'] = template_yaml['info']['description']

    # version = spec_yaml['info']['version']

    # Need to remove this to expose the oauth2 token
    # spec_yaml['basePath'] = "/api"

    if model == 'fb':
        # add api version into path
        # need to do this so we can add non version specific endpoints like get_version & login
        # paths = list(spec_yaml['paths'])
        # print(paths)
        # removing in 2020 June, I think they added up stream api version number

        # make basepath /api as it's a bit cleaner
        # Update: removing because of Oauth
        # for path in paths:
        #    new_path = path.replace('/api/','/')
        #    spec_yaml['paths'][new_path] = spec_yaml['paths'][path]
        #    del spec_yaml['paths'][path]

        # spec_yaml['paths']['/api_version'] = template_yaml['paths']['/api_version']
        # overwrite existing to add authorization param
        spec_yaml['paths']['/api/login'] = template_yaml['paths']['/api/login']
        spec_yaml['tags'] = template_yaml['tags'] + spec_yaml['tags']

    elif model == 'fa2':

        spec_yaml['securityDefinitions'] = template_yaml['securityDefinitions']
        spec_yaml['security'] = template_yaml['security']
        spec_yaml['tags'] = template_yaml['tags'] + spec_yaml['tags']
        for p in template_yaml['paths']:
            spec_yaml['paths'][p] = template_yaml['paths'][p]

        # make basepath /api as it's a bit cleaner
        # Update: removing because of Oauth
        # paths = list(spec_yaml['paths'])
        # for path in paths:
        #    new_path = path.replace('/api/','/')
        #    spec_yaml['paths'][new_path] = spec_yaml['paths'][path]
        #    del spec_yaml['paths'][path]

    elif model == 'pure1':
        return yaml.dump(template_yaml)

    return yaml.dump(spec_yaml)


def one_off_fixes(file_download_root):
    # Change the offset param in
    def delete_example(filepath):
        file_full_path = file_download_root + filepath
        with open(file_full_path) as f:
            temp = yaml.safe_load(f)
        del(temp['example'])
        with open(file_full_path, "w") as f:
            f.write(yaml.dump(temp))

    delete_example('/queries/FA2.0/offset.query.yaml')
    delete_example('/queries/FA2.0/limit.query.yaml')
    delete_example('/queries/FB1.0/start.query.yaml')
    delete_example('/queries/FB1.0/limit.query.yaml')


def main():

    script_path = os.path.dirname(os.path.realpath(__file__))

    file_download_root = os.path.abspath(os.path.join(script_path, "../html"))
    original_spec_directory = file_download_root + '/original_spec/specs/'
    spec_directory = file_download_root + '/specs/'

    one_off_fixes(file_download_root)

    with open("fb_template.yaml") as f:
        fb_template_yaml = yaml.safe_load(f)
    with open("fa2_template.yaml") as f:
        fa_template_yaml = yaml.safe_load(f)
    with open("pure1_template.yaml") as f:
        pure1_template_yaml = yaml.safe_load(f)

    spec_list = listdir(original_spec_directory)
    for spec in spec_list:
        fullpath = os.path.join(original_spec_directory, spec)
        new_fullpath = os.path.join(spec_directory, spec)
        if isfile(fullpath):
            lower_name = spec.lower()

            if lower_name.startswith('fa2'):
                template = fa_template_yaml
                model = 'fa2'

            elif lower_name.startswith('fb'):
                template = fb_template_yaml
                model = 'fb'

            elif lower_name.startswith('pure1'):
                template = pure1_template_yaml
                model = 'pure1'

            else:
                # don't need to apply template to fa as that is done during initial creation from the pdf
                continue

            with open(fullpath, "r") as f:
                spec_file = f.read()

            output = apply_template(spec_file, template, model)

            with open(new_fullpath, "w") as f:
                f.write(output)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print()
