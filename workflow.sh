# Fetch equilibrium input files from remote repo, create dataset and initialize (root)
rlaunch singleshot
rlaunch singleshot
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

