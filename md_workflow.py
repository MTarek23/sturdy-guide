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


# SSH key file

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
prefix = os.getcwd()

# FireWorks config directory
local_fws = os.path.expanduser('~/.fireworks')

# Test connection with Fabric
# connection = fabric.connection.Connection(host, user=user, connect_kwargs=
#                                 {"key_filename": key_file})

# set up the LaunchPad and reset it
lp = LaunchPad.auto_load()

qadapter = CommonAdapter.from_file(QUEUEADAPTER_LOC)

# FilePad behaves analogous to LaunchPad
# fp = FilePad.auto_load()

project_id = 'EOS'

# Initialize ----------------------------------------

parametric_dimension_labels = ['nUnitsX', 'nUnitsY', 'density']

parametric_dimensions = [ {
    'press':               [285],         #atm
    'temp':                [326],                             #  , 423, 520 temp
    'nUnitsX':             [72],
    'nUnitsY':             [10],
    'density':             [0.7],
    'Np'     :             [2880],
    'fluid'  :             ['pentane'],
    'code'   :             ['moltemp']
    }
]

parameter_sets = list(
    itertools.chain (*[
            itertools.product(*list(
                    p.values())) for p in parametric_dimensions ]) )

parameter_dict_sets = [ dict(zip(parametric_dimension_labels, s)) for s in parameter_sets ]

fw_list = []

# ft = ScriptTask.from_str('echo "Start the Workflow"')
# root_fw = Firework([ft],
#     name = 'Load the files',
#     spec = {'_category': 'cmsquad35',
#             'metadata': {'project': project_id,
#                         'datetime': datetime.datetime.now()}
#             })
#
# fw_list.append(root_fw)



# Fetch the files to be used in multiple simulatios with different parameters
fetch_input = ScriptTask.from_str(f" git clone -n git@github.com:mtelewa/md-input.git --depth 1 ;\
                            cd md-input/ ; git checkout HEAD pentane/equilib-rigid-walls; cd ../;\
                            mv {os.getcwd()}/md-input/pentane/equilib-rigid-walls equilib ;\
                            rm -rf {os.getcwd()}/md-input/ ; mkdir {os.getcwd()}/equilib/out")

fetch_firework = Firework([fetch_input],
                                name = 'Fetch Input',
                                spec = {'_category': 'uc2.scc.kit.edu', #f'{host}',
                                        '_dupefinder': DupeFinderExact(),
                                        '_launch_dir': f'{os.getcwd()}',#f'{workspace_equilib}',
                                        'metadata': {'project': project_id,
                                                    'datetime': datetime.datetime.now()}})

fw_list.append(fetch_firework)



# ds_remote = PyTask(func='fw_funcs.create_remote_ds', args=[host, user, key_file,
#                                                            workspace,'equilib-ds'])
#
# firework_create_ds = Firework([ds_remote],
#                          name = 'Create Dataset',
#                          spec = {'_category' : 'cmsquad35',
#                                  '_dupefinder': DupeFinderExact()},
#                          parents = [fetch_firework])
#
# fw_list.append(firework_create_ds)

# Create the datasets and copy the files from the fetched src
create_dataset = PyTask(func='dtool_dataset.create_dataset', args=['equilib-ds'])

transfer_from_src = FileTransferTask({'files': glob.glob(os.path.join('equilib','*')),
                                      'dest': 'equilib-ds',
                                      'mode': 'copy')

firework_create_ds = Firework([create_dataset, transfer_from_src],
                         name = 'Create Dataset',
                         spec = {'_category' : 'uc2.scc.kit.edu',
                                 '_dupefinder': DupeFinderExact()},
                         parents = [fetch_firework])

fw_list.append(firework_create_ds)


# Select the independent variable
# for k, v in parametric_dimensions[0].items():
#     if len(v) > 1: indep_var = v


# for idx, val in enumerate(indep_var):

    # Create the local datasets
    # subprocess.call([f'if [ ! -d "{sys.argv[1]}-{val}" ]; \
    #                     then echo Creating directory ;\
    #                     mkdir {sys.argv[1]}-{val};\
    #                     cp -r {sys.argv[1]}/* {sys.argv[1]}-{val};\
    #                     else cp -r {sys.argv[1]}/* {sys.argv[1]}-{val}; \
    #                     fi'], shell=True)

    # ds_local = PyTask(func='fw_funcs.create_local_ds', args=[f'{sys.argv[1]}',
    #                                                           f'{sys.argv[1]}-{val}'])


    # Initialization FW----------------

    # init = ScriptTask.from_str(f"cd {local_moltemp} ; initialize_bulk.py \
    #         {parametric_dimensions[0]['density'][0]} {parametric_dimensions[0]['Np'][0]} \
    #         {parametric_dimensions[0]['fluid'][0]} {parametric_dimensions[0]['code'][0]}")
    # # init = ScriptTask.from_str(f'cd {local_moltemp} ; ./setup.sh')#, {'stdout_file': 'a.out'})
    #
    # firework_init = Firework([init],
    #                          name = 'Initialize',
    #                          spec = {'_category' : 'cmsquad35',
    #                                  '_dupefinder': DupeFinderExact()},
    #                          parents = [firework_create_ds])
    #
    # fw_list.append(firework_init)


    # Transfer to the cluster ----------------------------------
    # remote_transfer = FileTransferTask({'files': sorted(glob.glob(os.path.join(local_blocks,'*'))),
    #                                     'dest': workspace_blocks,
    #                                     'mode': 'rtransfer',
    #                                     'server': host,
    #                                     'user': user})
    #
    # remote_transfer2 = FileTransferTask({'files': [os.path.join(local_equilib, f)
    #                                             for f in os.listdir(local_equilib)
    #                                             if os.path.isfile(os.path.join(local_equilib, f))],
    #                                     'dest': workspace_equilib,
    #                                     'mode': 'rtransfer', 'server': host,
    #                                     'user': user})
    #
    # firework_transfer = Firework([remote_transfer, remote_transfer2],
    #                              name = 'Transfer',
    #                              spec = {'_category': 'cmsquad35',
    #                                      '_dupefinder': DupeFinderExact()},
    #                              parents = [firework_create_ds])
    #
    # fw_list.append(firework_transfer)
    #
    # # Equilibrate ----------------------------------------------
    #
    # equilibrate = ScriptTask.from_str(f"pwd ; mpirun --bind-to core --map-by core -report-bindings \
    #         lmp_mpi -in $(pwd)/equilib.LAMMPS -v press '{parametric_dimensions[0]['press'][idx]}'")
    #
    # firework_equilibrate = Firework(equilibrate,
    #                                 name = 'Equilibrate',
    #                                 spec = {'_category': f'{host}',
    #                                         '_dupefinder': DupeFinderExact(),
    #                                         '_launch_dir': f'{workspace_equilib}'},
    #                                 parents = [firework_transfer])
    #
    # fw_list.append(firework_equilibrate)


    # Post_process ----------------------------------------------

    # parameters = [{'infile': 'equilib',
    #                'fluid': 'pentane',
    #                'Nchunks': 144,
    #                'stable_start': 0.4,
    #                'stable_end': 0.8,
    #                'pump_start': 0,
    #                'pump_end': 0.2,}]
    #
    # # USE template
    # postproc1 = ScriptTask.from_str(f"mpirun --bind-to core --map-by core -report-bindings \
    #                         proc.py {parameters[0]['infile']}.nc {parameters[0]['Nchunks']} 1 1000 {parameters[0]['fluid']}\
    #                         {parameters[0]['stable_start']} {parameters[0]['stable_end']} \
    #                         {parameters[0]['pump_start']} {parameters[0]['pump_end']}")
    # postproc2 = ScriptTask.from_str(f"mpirun --bind-to core --map-by core -report-bindings \
    #                         proc.py {parameters[0]['infile']}.nc 1 {parameters[0]['Nchunks']} 1000 {parameters[0]['fluid']}\
    #                         {parameters[0]['stable_start']} {parameters[0]['stable_end']} \
    #                         {parameters[0]['pump_start']} {parameters[0]['pump_end']}")
    # postproc3 = ScriptTask.from_str(f"if [ ! -f {parameters[0]['infile']}_{parameters[0]['Nchunks']}x1_001.nc ]; then \
    #                       mv {parameters[0]['infile']}_{parameters[0]['Nchunks']}x1_000.nc \
    #                       {parameters[0]['infile']}_{parameters[0]['Nchunks']}x1.nc \
    #                       mv {parameters[0]['infile']}_1x{parameters[0]['Nchunks']}_000.nc \
    #                       {parameters[0]['infile']}_1x{parameters[0]['Nchunks']}.nc \
    #                     else \
    #                       cdo mergetime {parameters[0]['infile']}_{parameters[0]['Nchunks']}x1_*.nc \
    #                       {parameters[0]['infile']}_{parameters[0]['Nchunks']}x1.nc ;\
    #                       #rm {parameters[0]['infile']}_{parameters[0]['Nchunks']}x1_* \
    #                       cdo mergetime {parameters[0]['infile']}_1x{parameters[0]['Nchunks']}_*.nc \
    #                       {parameters[0]['infile']}_1x{parameters[0]['Nchunks']}.nc ;\
    #                       #rm {parameters[0]['infile']}_1x{parameters[0]['Nchunks']}_* \
    #                     fi")
    # command = [{'export': 'ALL',
    #             'EXECUTABLE': './$HOME/tools/md/proc.py'}]

    # firework_postproc = Firework([postproc1,postproc2,postproc3],
    #                              name = 'Post-process',
    #                              spec = {'_category': f'{host}',
    #                                      '_dupefinder': DupeFinderExact()},
    #                                     #'_queueadapter': command},
    #                              parents = [firework_equilibrate])
    #
    # fw_list.append(firework_postproc)


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

# rocket_launcher.rapidfire(lp, FWorker(f'{local_fws}/fworker_cms.yaml'))
# for i in indep_var:
#     # Launch the fireworks on the local machine
#     # First rocket is simple echo
#     rocket_launcher.launch_rocket(lp, FWorker(f'{local_fws}/fworker_cms.yaml'))
#     # Create the empty datasets remotely
#     rocket_launcher.launch_rocket(lp, FWorker(f'{local_fws}/fworker_cms.yaml'))
#     # Initialize the structure and related parameters
#     # rocket_launcher.launch_rocket(lp, FWorker(f'{local_fws}/fworker_cms.yaml'))
#     # Transfer to the cluster
#     rocket_launcher.launch_rocket(lp, FWorker(f'{local_fws}/fworker_cms.yaml'))

    # Submit the simulation to the cluster (still not working properly)
    # A. QueueLauncher-------------------------------------
    #
    # queue_launcher.launch_rocket_to_queue(lp, FWorker('$HOME/.fireworks/fworker_cms.yaml'),
    #         queue_adapter.QueueAdapterBase())
    #queue_launcher.launch_rocket_to_queue(lp, FWorker('$HOME/.fireworks/fworker_cms.yaml'), qadapter)
    #
    # Remote fireworks will be FIZZLED so rerun them
    # subprocess.call(['source $HOME/fireworks/bin/activate; \
    #                  lpad rerun_fws -s FIZZLED'], shell=True)

    # B. Remote Commands------------------------------------
    # connection.run(f"cd {workspace}/{sys.argv[1]}-{i}/data;\
    #                source $HOME/fireworks/bin/activate ;\
    #                qlaunch singleshot")
    # Submit the post-processing
    #connection.run(f"cd {workspace}/{sys.argv[1]}-{i}/data/out;\
    #               source $HOME/fireworks/bin/activate ;\
    #               qlaunch -q $HOME/.fireworks/qadapter_uc2_postproc.yaml singleshot")

# Queries to the data base are simple dictionaries
# query = {
#     'metadata.project': project_id,
#         }
#
# print(fp.filepad.count_documents(query))
