import os
from ruamel.yaml import YAML
import dtoolcore
from dtool_create.dataset import _get_readme_template

def create_dataset(dataset_name):
    """
    Creates a parent dataset
    """

    # global yaml setting
    yaml = YAML()
    yaml.explicit_start = True
    yaml.indent(mapping=4, sequence=4, offset=2)

    ds = dtoolcore.DataSetCreator(dataset_name, os.getcwd(), creator_username='mtelewa')

    read_from = os.path.join(os.path.expanduser('~'), '.dtool', 'custom_dtool_readme.yml')
    readme_template = _get_readme_template(read_from)
    # load readme template and update
    metadata = yaml.load(readme_template)

    # metadata = update_readme(**kwargs)
    sim_uri = os.path.join(os.getcwd(),dataset_name)
    template = os.path.join(sim_uri, 'README.yml')

    # write the readme of the dataset
    with open(template, "w") as f:
        yaml.dump(metadata, f)
