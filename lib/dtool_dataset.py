import os
from ruamel.yaml import YAML
import dtoolcore
from dtool_create.dataset import _get_readme_template
from pathlib import Path

def create_dataset(dataset_name):
    """
    Creates a parent dataset with the nput files from the source (remote git repo)
    """

    # global yaml setting
    yaml = YAML()
    yaml.explicit_start = True
    yaml.indent(mapping=4, sequence=4, offset=2)

    ds = dtoolcore.DataSetCreator(dataset_name, os.getcwd(), creator_username='mtelewa')

    # load readme template and update metadata
    read_from = os.path.join(os.path.expanduser('~'), '.dtool', 'custom_dtool_readme.yml')
    readme_template = _get_readme_template(read_from)
    metadata = yaml.load(readme_template)

    # metadata = update_readme(**kwargs)
    sim_uri = os.path.join(os.getcwd(),dataset_name)
    template = os.path.join(sim_uri, 'README.yml')

    # write the readme of the dataset
    with open(template, "w") as f:
        yaml.dump(metadata, f)


def create_post(dataset_name, freeze=None, copy=None):
    """
    Creates a post-processing dataset derived from a simulation step
    """

    yaml = YAML()
    yaml.explicit_start = True
    yaml.indent(mapping=4, sequence=4, offset=2)

    sim_uri = os.path.join(os.getcwd(),dataset_name)
    sim_out_uri = os.path.join(sim_uri,'data','out')
    
    # Post-proc dataset path
    post_uri =  str(sim_uri) + '-post'
    # Post-proc dataset name
    post_name = dataset_name + '-post'
    # Post-proc dataset readme template
    post_template = os.path.join(post_uri, 'README.yml')

    read_from = os.path.join(os.getcwd(), dataset_name, 'README.yml')
    readme_template = _get_readme_template(read_from)
    metadata = yaml.load(readme_template)
    # Proto Dataset
    sim_dataset = dtoolcore.ProtoDataSet.from_uri(dataset_name)
    metadata['derived_from'][0]['uuid'] = sim_dataset.uuid

    # Create the derived dataset if not already existing
    if not os.path.isdir(post_name):
        dds = dtoolcore.create_derived_proto_dataset(post_name, os.getcwd(),
                    sim_dataset, creator_username='mtelewa')
    else:
        dds = dtoolcore.ProtoDataSet.from_uri(post_uri)

    # Copy the files to the post-proc dataset and remove them from the simulation dataset
    for root, dirs, files in os.walk(sim_out_uri):
        for i in files:
            if 'x' in i:
                dds.put_item(os.path.join(sim_out_uri,i), i)
                os.remove(os.path.join(sim_out_uri,i))
            if 'log.lammps' in i:
                dds.put_item(os.path.join(sim_out_uri,i), i)

    # write the readme of the post-proc dataset
    with open(post_template, "w") as f:
        yaml.dump(metadata, f)

    if freeze:
        print(f'Freezing Simulation dataset: {sim_uri} ----')
        sim_dataset.freeze()
    if copy:
        print(f'Copying dataset: {sim_uri} to S3 ----')
        dtoolcore.copy(sim_dataset.uri, 's3://frct-simdata',
                config_path=os.path.join(os.path.expanduser('~'),'.config/dtool/dtool.json'))


def create_derived(dataset_name, derived_name):
    """
    Creates a dataset derived from a previous simulation step
    """

    yaml = YAML()
    yaml.explicit_start = True
    yaml.indent(mapping=4, sequence=4, offset=2)

    derived_uri = os.path.join(os.getcwd(), derived_name)

    # Proto Dataset
    sim_dataset = dtoolcore.ProtoDataSet.from_uri(dataset_name)

    # Create the derived dataset if not already existing
    dds = dtoolcore.create_derived_proto_dataset(derived_name, os.getcwd(),
                sim_dataset, creator_username='mtelewa')

    # # derived dataset readme template
    derived_template = os.path.join(derived_uri, 'README.yml')
    # template = os.path.join(self.sim_uri, 'README.yml')

    metadata = self.update_readme(**kwargs)

    read_from = os.path.join(os.getcwd(), dataset_name, 'README.yml')
    readme_template = _get_readme_template(read_from)
    metadata = yaml.load(readme_template)
    # Proto Dataset
    sim_dataset = dtoolcore.ProtoDataSet.from_uri(dataset_name)
    metadata['derived_from'][0]['uuid'] = sim_dataset.uuid

    # if '-post' not in self.dataset_name:    # Take the UUID of the dataset itself not the post-processed one
    #     metadata['derived_from'][0]['uuid'] = self.sim_dataset.uuid

    # write the readme of the post-proc dataset
    with open(derived_template, "w") as f:
        yaml.dump(metadata, f)
