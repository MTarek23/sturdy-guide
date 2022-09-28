import os
import dtoolcore
from ruamel.yaml import YAML


def create_dataset(dataset_name, **kwargs):
    """
    Creates a parent dataset
    """
    
    # global yaml setting
    yaml = YAML()
    yaml.explicit_start = True
    yaml.indent(mapping=4, sequence=4, offset=2)

    ds = dtoolcore.DataSetCreator(dataset_name, os.getcwd(), creator_username='mtelewa')
    metadata = manipulate_ds(dataset_name).update_readme(**kwargs)
    sim_uri = os.path.join(os.getcwd(),dataset_name)
    template = os.path.join(sim_uri, 'README.yml')

    # write the readme of the dataset
    with open(template, "w") as f:
        yaml.dump(metadata, f)
