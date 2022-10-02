

def grid(ds, Nchunks, slice_size, fluid, stable_start, stable_end, pump_start, pump_end):
    return f"pwd ; mpirun --bind-to core --map-by core -report-bindings proc_nc.py {ds}.nc \
        {Nchunks} 1 {slice_size} {fluid} {stable_start} {stable_end} {pump_start} {pump_end} ;\
        mpirun --bind-to core --map-by core -report-bindings proc_nc.py {ds}.nc \
        1 {Nchunks} {slice_size} {fluid} {stable_start} {stable_end} {pump_start} {pump_end}"

def merge(ds, Nchunks):
    return f"if [ ! -f {ds}_{Nchunks}x1_001.nc ]; then \n
      mv {ds}_{Nchunks}x1_000.nc {ds}_{Nchunks}x1.nc ; \n
      mv {ds}_1x{Nchunks}_000.nc {ds}_1x{Nchunks}.nc ; \n
    else \n
      cdo mergetime {ds}_{Nchunks}x1_*.nc {ds}_{Nchunks}x1.nc ; rm {ds}_{Nchunks}x1_* ;\
      cdo mergetime {ds}_1x{Nchunks}_*.nc {ds}_1x{Nchunks}.nc ; rm {ds}_1x{Nchunks}_* ;\
    fi"
