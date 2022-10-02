#!/usr/bin/env python

from fireworks import Firework, FWorker, LaunchPad, ScriptTask, TemplateWriterTask, FileTransferTask, PyTask, Workflow
from fireworks.utilities.filepad import FilePad
import fireworks.core.rocket_launcher as rocket_launcher
import fireworks.queue.queue_launcher as queue_launcher # launch_rocket_to_queue, rapidfire
import fireworks.queue.queue_adapter as queue_adapter
from fireworks.user_objects.queue_adapters.common_adapter import CommonAdapter
from fireworks.fw_config import QUEUEADAPTER_LOC
from fireworks.user_objects.dupefinders.dupefinder_exact import DupeFinderExact
import os, glob, sys, datetime, subprocess, itertools
import numpy as np

import dtool_dataset
import init_walls, init_bulk
import post_commands

# remote = input('Remote server: ')
remote = 'uc2'

if remote == 'nemo':
    key_file = os.path.expanduser('~/.ssh/id_rsa')
    host = 'login1.nemo.uni-freiburg.de'
    user = 'ka_lr1762'
    workspace = f'/work/ws/nemo/{user}-my_workspace-0/'

elif remote == 'uc2':
    key_file = os.path.expanduser('~/.ssh/id_rsa_uc2')
    host = 'uc2.scc.kit.edu'
    user = 'lr1762'
    workspace = f'/pfs/work7/workspace/scratch/{user}-flow_sims'

else:
    print('Remote server unknown!')
    exit()

# Current Working directory
# prefix = os.getcwd()
# FireWorks config directory
# local_fws = os.path.expanduser('~/.fireworks')

# set up the LaunchPad and reset it
lp = LaunchPad.auto_load()
qadapter = CommonAdapter.from_file(QUEUEADAPTER_LOC)

# FilePad behaves analogous to LaunchPad
# fp = FilePad.auto_load()

project_id = 'EOS'

md_system = sys.argv[1]

# Define the input parameters ----------------------------------------
# --------------------------------------------------------------------

# For the simulations ----------
parametric_dimensions = [{
    'press':               [2467],
    'temp':                [326],
    'nUnitsX':             [72],
    'nUnitsY':             [10],
    'nUnitsZ':             [1],
    'density':             [0.7],
    'height':              [40],
    'Np'     :             [2880],
    'fluid'  :             ['pentane'],
    'code'   :             ['moltemp']
    }]

# For the post-processing ----------
proc_params = {
    'Nchunks':       144,
    'slice_size':    1000,
    'stable_start':  0.4,
    'stable_end':    0.8,
    'pump_start':    0.0,
    'pump_end':      0.2}


# Define the fireworks and the firetasks within ----------------------
# --------------------------------------------------------------------

fw_list = []

# Fetch the equilibrium src files (to be used in multiple simulations with different parameters) -----------
fetch_eq_input = ScriptTask.from_str(f" git clone -n git@github.com:mtelewa/md-input.git --depth 1 ;\
    cd md-input/ ; git checkout HEAD {parametric_dimensions[0]['fluid'][0]}/equilib-{md_system}; cd ../;\
    mv md-input/{parametric_dimensions[0]['fluid'][0]}/equilib-{md_system} equilib ;\
    rm -rf md-input/ ; mkdir equilib/out")

fetch_eq_firework = Firework([fetch_eq_input],
                                name = 'Fetch Equilibration Input',
                                spec = {'_category': f'{host}',
                                        '_dupefinder': DupeFinderExact(),
                                        '_launch_dir': f'{os.getcwd()}',
                                        'metadata': {'project': project_id,
                                                    'datetime': datetime.datetime.now()}})

fw_list.append(fetch_eq_firework)


# Create the datasets and copy the files from the fetched src --------------
create_eq_dataset = PyTask(func='dtool_dataset.create_dataset',
                        args=[f"equilib-{parametric_dimensions[0]['press'][0]}"])
transfer_from_src = ScriptTask.from_str(f"cp -r equilib/* equilib-{parametric_dimensions[0]['press'][0]}/data/ ; rm -r equilib")

create_eq_ds_firework = Firework([create_eq_dataset, transfer_from_src],
                         name = 'Create Equilibrium Dataset',
                         spec = {'_category' : 'uc2.scc.kit.edu',
                                 '_launch_dir': f'{os.getcwd()}',
                                 '_dupefinder': DupeFinderExact()},
                         parents = [fetch_eq_firework])

fw_list.append(create_eq_ds_firework)


# Initialize system with moltemplate ----------------
if parametric_dimensions[0]['fluid'][0] == 'pentane':
    mFluid = 72.15
    tolX, tolY, tolZ = 10 , 4 , 3
elif parametric_dimensions[0]['fluid'][0] == 'propane':
    mFluid = 44.09
    tolX, tolY, tolZ = 5 , 3 , 3
elif parametric_dimensions[0]['fluid'][0] == 'heptane':
    mFluid = 100.21
    tolX, tolY, tolZ = 10 , 4 , 3
elif parametric_dimensions[0]['fluid'][0] == 'lj':
    mFluid = 39.948
    tolX, tolY, tolZ = 5 , 5 , 5

if 'bulk' in md_system:
    initialize = PyTask(func='init_bulk.init_moltemp',
                        args=[parametric_dimensions[0]['density'][0],
                        parametric_dimensions[0]['Np'][0],
                        parametric_dimensions[0]['fluid'][0],
                        mFluid, tolX, tolY, tolZ])

if 'walls' in md_system:
    initialize = PyTask(func='init_walls.init_moltemp',
                        args=[parametric_dimensions[0]['nUnitsX'][0],
                        parametric_dimensions[0]['nUnitsY'][0],
                        parametric_dimensions[0]['nUnitsZ'][0],
                        parametric_dimensions[0]['height'][0],
                        parametric_dimensions[0]['density'][0],
                        parametric_dimensions[0]['fluid'][0],
                        mFluid, tolX, tolY, tolZ])

setup = ScriptTask.from_str("./setup.sh")

init_firework = Firework([initialize, setup],
                         name = 'Initialize',
                         spec = {'_category' : f'{host}',
                                 '_launch_dir': f"{os.getcwd()}/equilib-{parametric_dimensions[0]['press'][0]}/data/moltemp",
                                 '_dupefinder': DupeFinderExact()},
                         parents = [create_eq_ds_firework])

fw_list.append(init_firework)


# Equilibrate with LAMMPS ----------------------------------------------
equilibrate = ScriptTask.from_str(f"pwd ; mpirun --bind-to core --map-by core singularity run --bind {workspace} \
    --bind /scratch --bind /tmp --pwd=$PWD $HOME/programs/lammps.sif -i $(pwd)/equilib.LAMMPS ")


equilibrate_firework = Firework(equilibrate,
                                name = 'Equilibrate',
                                spec = {'_category': f'{host}',
                                        '_launch_dir': f"{os.getcwd()}/equilib-{parametric_dimensions[0]['press'][0]}/data/",
                                        '_dupefinder': DupeFinderExact(),
                                        '_files_out': {'equilib_data':'data.equilib'}},
                                parents = [init_firework])

fw_list.append(equilibrate_firework)


# Post-process with Python-netCDF4 ----------------------------------------------

post_eq = ScriptTask.from_str(post_commands.grid('equilib', proc_params['Nchunks'], proc_params['slice_size'],
                        parametric_dimensions[0]['fluid'][0], proc_params['stable_start'],
                        proc_params['stable_end'], proc_params['pump_start'], proc_params['pump_end']))

merge_nc =  ScriptTask.from_str(post_commands.merge('equilib', proc_params['Nchunks']))

print_to_flags = ScriptTask.from_str(f"echo '-i equilib -N {proc_params['Nchunks']}\
    -f {parametric_dimensions[0]['fluid'][0]} -s {proc_params['stable_start']}\
    -e {proc_params['stable_end']} -p {proc_params['pump_start']} -x {proc_params['pump_end']}' > $(pwd)/flags.txt")

post_equilib_firework = Firework([post_eq, merge_nc, print_to_flags],
                                name = 'Post-process Equilibration',
                                spec = {'_category': f'{host}',
                                        '_launch_dir': f"{os.getcwd()}/equilib-{parametric_dimensions[0]['press'][0]}/data/out",
                                        '_queueadapter': {'walltime':'00:10:00'},
                                        '_dupefinder': DupeFinderExact()},
                                        # '_priority': '2'},
                                parents = [equilibrate_firework])

fw_list.append(post_equilib_firework)


# Create the post equilibrium dataset (this will also copy the output files from the simulation dataset) ------------
create_post_eq_dataset = PyTask(func='dtool_dataset.create_post',
                        args=[f"equilib-{parametric_dimensions[0]['press'][0]}"])
# transfer_from_src = ScriptTask.from_str(f"cp -r equilib/* equilib-{parametric_dimensions[0]['press'][0]}/data/ ; rm -r equilib")

create_post_eq_ds_firework = Firework([create_post_eq_dataset],
                         name = 'Create Post Equilibrium Dataset',
                         spec = {'_category' : 'uc2.scc.kit.edu',
                                 '_launch_dir': f'{os.getcwd()}',
                                 '_dupefinder': DupeFinderExact()},
                         parents = [post_equilib_firework])

fw_list.append(create_post_eq_ds_firework)


# Fetch the loading src files (to be used in multiple simulations with different parameters) -----------
fetch_load_input = ScriptTask.from_str(f" git clone -n git@github.com:mtelewa/md-input.git --depth 1 ;\
    cd md-input/ ; git checkout HEAD {parametric_dimensions[0]['fluid'][0]}/load-{md_system}; cd ../;\
    mv md-input/{parametric_dimensions[0]['fluid'][0]}/load-{md_system} load ;\
    rm -rf md-input/ ; mkdir load/out")

copy_eq_data = FileTransferTask({'files': [{'src': f"equilib-{parametric_dimensions[0]['press'][0]}/data/out/data.equilib",
                                            'dest': 'load/blocks'}], 'mode': 'copy'})

create_load_dataset = PyTask(func='dtool_dataset.create_derived',
                        args=[f"equilib-{parametric_dimensions[0]['press'][0]}",f"load-{parametric_dimensions[0]['press'][0]}"])

transfer_from_src = ScriptTask.from_str(f"cp -r load/* load-{parametric_dimensions[0]['press'][0]}/data/ ; rm -r load")

fetch_load_firework = Firework([fetch_load_input, copy_eq_data, create_load_dataset, transfer_from_src],
                                name = 'Fetch Loading Input',
                                spec = {'_category': f'{host}',
                                        '_dupefinder': DupeFinderExact(),
                                        '_launch_dir': f'{os.getcwd()}',
                                        'metadata': {'project': project_id,
                                                    'datetime': datetime.datetime.now()}},
                                parents = [create_post_eq_ds_firework])

fw_list.append(fetch_load_firework)


# Load the upper wall with LAMMPS ----------------------------------------------

load = ScriptTask.from_str(f"pwd ; mpirun --bind-to core --map-by core singularity run --bind {workspace} \
    --bind /scratch --bind /tmp --pwd=$PWD $HOME/programs/lammps.sif -i $(pwd)/load.LAMMPS ")

load_firework = Firework(load,
                            name = 'Load',
                            spec = {'_category': f'{host}',
                                    '_launch_dir': f"{os.getcwd()}/load-{parametric_dimensions[0]['press'][0]}/data/",
                                    '_dupefinder': DupeFinderExact()},
                            parents = [fetch_load_firework])

fw_list.append(load_firework)


# Post-process with Python-netCDF4 ----------------------------------------------

post_load = ScriptTask.from_str(post_commands.grid('load', proc_params['Nchunks'], proc_params['slice_size'],
                        parametric_dimensions[0]['fluid'][0], proc_params['stable_start'],
                        proc_params['stable_end'], proc_params['pump_start'], proc_params['pump_end']))

merge_nc =  ScriptTask.from_str(post_commands.merge('load', proc_params['Nchunks']))

print_to_flags = ScriptTask.from_str(f"echo '-i equilib -N {proc_params['Nchunks']}\
    -f {parametric_dimensions[0]['fluid'][0]} -s {proc_params['stable_start']}\
    -e {proc_params['stable_end']} -p {proc_params['pump_start']} -x {proc_params['pump_end']}' > $(pwd)/flags.txt")

post_load_firework = Firework([post_load, merge_nc, print_to_flags],
                                name = 'Post-process Loading',
                                spec = {'_category': f'{host}',
                                        '_launch_dir': f"{os.getcwd()}/load-{parametric_dimensions[0]['press'][0]}/data/out",
                                        '_queueadapter': {'walltime':'00:30:00'},
                                        '_dupefinder': DupeFinderExact()},
                                        # '_priority': '2'},
                                parents = [load_firework])

fw_list.append(post_load_firework)







# Launch the Workflow ---------------------------------------

wf = Workflow(fw_list,
    name = 'test_wf',
    metadata = {
        'project': 'EOS',
        'fluid'  : 'pentane',
        'datetime': datetime.datetime.now(),
        'type':    'benchmark'
    })


#Store the workflow to the db
lp.add_wf(wf)

#Write out the Workflow to a flat file
wf.to_file('wf.yaml')



# Select the independent variable
# for k, v in parametric_dimensions[0].items():
#     if len(v) > 1: indep_var = v

# for idx, val in enumerate(indep_var):


# rocket_launcher.rapidfire(lp, FWorker(f'{local_fws}/fworker_cms.yaml'))
# for i in indep_var:

# # Launch the fireworks on the local machine
# # Fetch Input
# rocket_launcher.launch_rocket(lp, FWorker(f'{local_fws}/fworker_cms.yaml'))
#
# # Create the datasets
# rocket_launcher.launch_rocket(lp, FWorker(f'{local_fws}/fworker_cms.yaml'))
#
# # Initialize the structure and related parameters
# # rocket_launcher.launch_rocket(lp, FWorker(f'{local_fws}/fworker_cms.yaml'))
# # Transfer to the cluster
# rocket_launcher.launch_rocket(lp, FWorker(f'{local_fws}/fworker_cms.yaml'))
#
# ## Submit the simulation to the cluster (still not working properly)
# #A. QueueLauncher-------------------------------------
#
# queue_launcher.launch_rocket_to_queue(lp, FWorker('$HOME/.fireworks/fworker_cms.yaml'),
#         queue_adapter.QueueAdapterBase())
# queue_launcher.launch_rocket_to_queue(lp, FWorker('$HOME/.fireworks/fworker_cms.yaml'), qadapter)
#
#
# #B. Remote Commands------------------------------------
# connection.run(f"cd {workspace}/{sys.argv[1]}-{i}/data;\
#                source $HOME/fireworks/bin/activate ;\
#                qlaunch singleshot")
#
# #Submit the post-processing
# connection.run(f"cd {workspace}/{sys.argv[1]}-{i}/data/out;\
#               source $HOME/fireworks/bin/activate ;\
#               qlaunch -q $HOME/.fireworks/qadapter_uc2_postproc.yaml singleshot")
#
# #Queries to the data base are simple dictionaries
# query = {
#     'metadata.project': project_id,
#         }
#
# print(fp.filepad.count_documents(query))
