import argparse
import json
from collections import OrderedDict

import requests


__author__ = 'guglielmo'

"""
This script can be used to extract the details of a json schemas,
given its URL.
The script only requires the `requests` package


To install `requests`::
    
    pip install requests


In order to get the content of the schema (title, descr, properties) 
in a readable form::

    python schema_parser.py \
        --url http://www.popoloproject.com/schemas/event.json#


In order to generate the class definitions::

    python schema_parser.py \
        --url http://www.popoloproject.com/schemas/event.json# \
        --generate

"""

def main():
    parser = argparse.ArgumentParser(
        description='Parse a remote popolo schema.')
    parser.add_argument('--url', dest='url', type=str, nargs='?',
                        help='Json URL')
    parser.add_argument('--generate', action='store_true',
                        help='Generate class or fields definition')

    args = parser.parse_args()
    url = args.url
    generate = args.generate

    resp = requests.get(url)
    if resp.status_code != 200 or 'OpenDNS' in resp.headers['server']:
        print("URL not found")
        exit()

    try:
        schema = json.loads(
            resp.content,
            object_pairs_hook=OrderedDict
        )
    except ValueError:
        schema = None
        print("No JSON at {0}".format(url))
        exit()

    if generate:
        print("""
class {0}(models.Model):
    \"\"\"{1}

    \"\"\"
""".format(schema['title'], schema['description']))
        generate_fields(schema['properties'])
    else:
        print("Title: {0}".format(schema['title']))
        print("Description: {0}".format(schema['description']))
        print("Properties:")
        for p, v in schema['properties'].items():
            if isinstance(v, OrderedDict):
                v = json.loads(json.dumps(v))
            print(
                "  {0} => {1}".format(p, v)
            )


def generate_fields(properties):
    """
    Generate representations for all fields
    """
    for p, v in properties.items():
        generate_field(p, v)


def generate_field(key, value):
    """
    Generate representation for a single field
    """

    # determine object type
    obj_type = None
    default = None
    if 'type' in value:
        if isinstance(value['type'], list):
            obj_type = value['type'][0]
            default = value['type'][1]
        else:
            obj_type = value['type']
            default = None
    else:
        if '$ref' in value:
            print("    # reference to '{0}'".format(value['$ref']))

    # convert key into label ('_' => ' ')
    label = " ".join(key.split("_"))

    required = value['required'] if 'required' in value else False
    nullable = not required and (default is None or default == 'null')

    model_class = None
    field_validator = None
    if obj_type == 'string':
        if 'format' in value:
            if value['format'] == 'email':
                model_class = "models.EmailField"
            elif value['format'] == 'date-time':
                model_class = "models.DateTimeField"
            elif value['format'] == 'uri':
                model_class = "models.URLField"

        else:
            model_class = "models.CharField"
            if 'pattern' in value:
                field_validator = """
                    RegexValidator(
                        regex='{0}',
                        message='{1} must follow the given pattern: {2}',
                        code='invalid_{3}'
                    )
                """.format(value['pattern'], label, value['pattern'], key)

    elif obj_type == 'array':
        referenced_objects_type = value['items']['$ref']
        print(
            "    # add '{0}' property to get array of items "
            "referencing '{1}'".format(
                  key, referenced_objects_type
            )
        )

    if model_class:
        # build field representation
        field_repr = '    {0} = {1}(_("{2}")'.format(key, model_class, label)
        if model_class == 'models.CharField':
            field_repr += ', max_length=128'
        if nullable:
            field_repr += ', blank=True'
            if model_class != 'models.CharField':
                field_repr += ', null=True'
        if field_validator:
            field_repr += ', validators=[{0}]'.format(field_validator)

        field_repr += ', help_text=_("{0}")'.format(value['description'])
        field_repr += ')'
        print(field_repr)


if __name__ == "__main__":
    main()
