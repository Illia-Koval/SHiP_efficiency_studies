# SHiP_efficiency_studies
Codes from the research project under S3P3 program

## Setup
In order to run the generation scripts, you need to install [Event Calculator](https://github.com/matclim/EventCalc-SHiP/) and FairShip (specifically, [the branch encompassing fixed reco and proprer EventCalc readout](https://github.com/kholoimov/FairShip/tree/dev_vkholoim_EvtCalc_import_v2)).

### Event Calculator prerequisites
The geometry of SHiP is misaligned in EventCalc and FairShip. You must access the file ```EventCalc-SHiP/funcs/ship_setup.py``` and paste following limits at the top of the file:

```
z_min = 33.12    # Minimum z-coordinate in meters
z_max = 83.12    # Maximum z-coordinate in meters
Delta_x_in = 1   # Delta x at z_min in meters
Delta_x_out = 4  # Delta x at z_max in meters
Delta_y_in = 2.7 # Delta y at z_min in meters
Delta_y_out = 6  # Delta y at z_max in meters
```

## Generation

The generation scripts are located in the folder ```generation/```. For each studied FIP model (dark scalar, dark photon and HNL) there is a corresponding file ```generation_script_{FIP}.sh```. They are designed to work on the [LPHE cluster](https://www.epfl.ch/labs/lphe/en/cluster/guide/new-cluster-instructions/) as a matter of running various mass FIP generation and simulation in parallel.

The paths to the Event Calculator, FairShip and the preferred directory for the (many) output files should be entered at the beginning of each file.

In order to run generation, you must manually enter the decay mode in the variable ```decay_mode_idx``` according to the numbering scheme in the Event Calculator (can also be found in the generation files). The lists of FIP masses were chosen arbitrarily, so the customisation according to computational access is welcome.



## Analysis

The efficiency analysis scripts also require the paths to the particular directories. Also, they have the hardcoded masses (same as in scripts) which should be modified in case some files are missing.