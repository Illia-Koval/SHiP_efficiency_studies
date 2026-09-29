#!/bin/bash
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=12288M
#SBATCH -J Tracking
#SBATCH -t 04:00:00  

#source /cvmfs/sft.cern.ch/lcg/views/LCG_105/x86_64-el9-gcc13-opt/setup.sh

#python3 mother_mass_NEW.py
#python3 geometrical_acceptance_z_dependence_vs_MCTrack_vs_reco_NEW.py
#python3 vertexing_analysis_M_superimpose_modes_Scalar-mixing.py
#python3 vertexing_analysis_M_superimpose_modes_Dark-photons.py
#python3 vertexing_analysis_M_superimpose_modes_HNL.py
#python3 tracking_analysis_M_superimpose_modes_Scalar-mixing.py
#python3 tracking_analysis_M_superimpose_modes_Dark-photons.py
#python3 tracking_analysis_M_superimpose_modes_HNL.py
#
#python3 drawing_daughter_pointing_angle.py

unset PYTHONHOME
unset PYTHONPATH
unset LD_LIBRARY_PATH

pixi run python drawing_daughter_P.py

#pixi run python tracking_vertexing_analysis_M_Scalar-mixing.py
#pixi run python tracking_vertexing_analysis_M_Dark-photons.py
#pixi run python tracking_vertexing_analysis_M_HNL.py
#pixi run python tracking_analysis_particle_gun.py

#unbinds e.g. python from cvmfs -> job does not crash on the cluster
unset PYTHONHOME PYTHONPATH LD_LIBRARY_PATH ROOTSYS DISPLAY
#remove QT attempts from GEANT -> job does not crash
export QT_QPA_PLATFORM=offscreen #should remove QT attempts from GEANT

#nparticles=15

#pixi run python ../../macro/run_simScript.py --tag test_PG_multiple_PG_"$nparticles" -n 5000 PG --multiplePG --multiplicity "$nparticles" --Estart 10 --Eend 30 --Vz 5000 --pID 13 --bothCharges --thetaMax 3 --Dx 100 --Dy 100

#pixi run python ../../macro/ShipReco.py -f sim_test_PG_multiple_PG_"$nparticles".root -g geo_test_PG_multiple_PG_"$nparticles".root --noVertexing