#!/usr/bin/env python

# import fabric
import os


def create_local_ds(dir_in, dir_out):
    # Create the local datasets
    # subprocess.call([f'if [ ! -d "{dir}" ]; \
    #                     echo yes ;\
    #                     then cp -r equilib {dir}; \
    #                     else cp -r equilib/* {dir}; \
    #                 fi'], shell=True)

    subprocess.call([f'if [ ! -d "{dir_out}" ]; \
                        then echo Creating directory ;\
                        dtool create {dir_out};\
                        else cp -r {dir_in}/* {dir_out}/data;\
                        fi'], shell=True)
                        # cp -r {dir_in}/* {dir_out}/data;\


def create_remote_ds(host, user, key_file, workspace, dir):
    # Test connection with Fabric
    connection = fabric.connection.Connection(host, user=user, connect_kwargs=
                                    {"key_filename": key_file})

    connection.run(f'source $HOME/fireworks/bin/activate; \
                            if [ ! -d "/pfs/work7/workspace/scratch/{user}-{workspace}/EOS/{dir}" ]; \
                                then cd /pfs/work7/workspace/scratch/{user}-{workspace} ; \
                                mkdir EOS; cd EOS; \
                                dtool create {dir} ; \
                            fi')
                            # cd {dir} ; \
                            # cd data ; \
                            # mkdir out blocks; \
