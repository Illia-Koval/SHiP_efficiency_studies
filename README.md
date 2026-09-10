# SHiP_efficiency_studies
Codes from the research project under S3P3 program

In order to run the generation scripts, you need to install [Event Calculator](https://github.com/matclim/EventCalc-SHiP/) and FairShip (specifically, Valerii's fork with [the branch encompassing fixed reco and proprer EventCalc readout](https://github.com/kholoimov/FairShip/tree/dev_vkholoim_EvtCalc_import_v2)).

The generation scripts ```generation_script_{FIP}.sh``` are designed to work on the [LPHE cluster](https://www.epfl.ch/labs/lphe/en/cluster/guide/new-cluster-instructions/) as a matter of running various mass FIP generation and simulation in parallel. The paths to the Event Calculator, FairShip and the preferred directory for the (many) output files should be entered at the beginning of each file for now.

The efficiency analysis scripts also require the paths to the particular directories. Also, they have the hardcoded masses (same as in scripts) which should be modified in case some files are missing.