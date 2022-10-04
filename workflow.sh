# Fetch equilibrium input files from remote repo and create dataset (root)
rlaunch singleshot

# Initialize the system with moltemp
rlaunch singleshot

# Run Equilibration (root/equilib/data)
cd equilib-2467/data ; qlaunch -q ~/.fireworks/qadapter_sim_uc2.yaml singleshot

# Run post-processing (root/equilib/data/out)
cd out ; qlaunch -q ~/.fireworks/qadapter_postproc_uc2.yaml singleshot

# Create post-equilib derived dataset (root)
cd ../../../ ; rlaunch singleshot

# Fetch the loading input files from remote repo, copy the LAMMPS data file from equilib/data/out and create dataset (root)
rlaunch singleshot

# Run Loading (root/loading/data)
cd load-2467/data ; qlaunch -q ~/.fireworks/qadapter_sim_uc2.yaml singleshot

# Run post-processing (root/load/data/out)
cd out ; qlaunch -q ~/.fireworks/qadapter_postproc_uc2.yaml singleshot

# Create post-loading derived dataset (root)
cd ../../../ ; rlaunch singleshot

# Fetch the NEMD input files from remote repo, copy the LAMMPS data file from load/data/out and create dataset (root)
rlaunch singleshot

# Run NEMD (root/nemd/data)
cd ff-050/data ; qlaunch -q ~/.fireworks/qadapter_sim_uc2.yaml singleshot

# Run post-processing (root/nemd/data/out)
cd out ; qlaunch -q ~/.fireworks/qadapter_postproc_uc2.yaml singleshot

# Create post-NEMD derived dataset (root)
cd ../../../ ; rlaunch singleshot

