import chevron
import os
import re
from functools import total_ordering


@total_ordering
class Version:
  def __init__(self, bu, version, filename):
    self.bu = bu
    self.version = version
    self.filename = filename
    self.bu_pretty = self.get_pretty_bu(bu)

  def get_pretty_bu(self, bu):
    if (bu == 'fa'):
      return 'FlashArray'
    elif (bu == 'fb'):
      return 'FlashBlade'
    else:
      return 'Pure1'

  def __eq__(self, other):
    return self.version == other.version

  def __lt__(self, other):
    this = self.version.split('.')
    that = other.version.split('.')
    if this[0] == that[0]:
      # Same major version
      return True if int(this[1]) < int(that[1]) else False
    else:
      return True if int(this[0]) < int(that[0]) else False

def parse_versions(bu):
  SPECS_DIR = './redoc'
  specs_found = []
  spec_regex = re.compile(f'{bu}[-]?(?P<version>.*)-api-reference.html')
  for spec in os.listdir(SPECS_DIR):
    match = spec_regex.match(spec)
    if match:
      specs_found.append(Version(bu, match.groupdict()['version'], spec))
  return sorted(specs_found)

def generate(template_path, output_path, data):
  with open(template_path) as template:
    with open(output_path, 'w') as output:
      output.write(chevron.render(template, data))

class VersionTriplets:
  def __init__(self, fa, fb, pure1):
    self.lines = []
    for i in range(0, len(fa)):
      rows = []
      rows.append(fa[i])
      if len(fb) > i:
        rows.append(fb[i])
      if len(pure1) > i:
        rows.append(pure1[i])
      self.lines.append({'rows': rows})

if __name__ == '__main__':
  fa = parse_versions('fa')
  fb = parse_versions('fb')
  pure1 = parse_versions('pure1')

  # Generate content for BU-specific pages
  def generate_for_bu(bu, versions): 
    for file_type in ['links', 'select']:
      template_path = os.path.join('_templates', f'{file_type}.mustache')
      output_path = os.path.join('_includes', f'{bu}_{file_type}.html')
      generate(template_path, output_path, {'links': versions})
  generate_for_bu('fa', fa)
  generate_for_bu('fb', fb)
  generate_for_bu('pure1', pure1)

  # Generate the joint table for index.html
  version_triplets = VersionTriplets(fa, fb, pure1)
  template_path = os.path.join('_templates', 'table.mustache')
  output_path = os.path.join('_includes', 'table_with_links.html')
  generate(template_path, output_path, {'lines': version_triplets.lines})













