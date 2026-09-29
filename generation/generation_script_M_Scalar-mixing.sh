#!/bin/bash
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=4096M
#SBATCH -J Multibody_decay
#SBATCH -t 24:00:00
#SBATCH -o logs/launcher_%j.out
#SBATCH -e logs/launcher_%j.err

EVENTCALC="/panfs/ikoval/EventCalc-SHiP"
FAIRSHIP="/panfs/ikoval/FairShip"
SIM_SIGNAL="/panfs/ikoval/my_work/signal/sim_signal"

#manually choose the decay mode for the generation
decay_mode_idx=6

#range = Range of masses for EventCalc generations where the job is not killed by small/zero Br
case "$decay_mode_idx" in
    1)
        # e+e-; range - [0.03; 0.35]
        mass_array=(0.04 0.07 0.10 0.13 0.16 0.19 0.22 0.25 0.28 0.31 0.34)
        ;;
    2)
        # mu+mu-; range - [0.212; 4.7]
        mass_array=(0.4 0.7 1.0 1.3 1.6 1.9 2.2 2.5 2.8 3.1 3.4 3.7 4.0 4.3 4.6)
        ;;
    4)
        # Pi+Pi-; range [0.284; 1.995]
        mass_array=(0.3 0.5 0.7 0.9 1.1 1.3 1.5 1.7 1.9)
        ;;
    6)
        # K+K-; range [1.0; 1.995]
        mass_array=(1.0 1.1 1.2 1.3 1.4 1.5 1.6 1.7 1.8 1.9)
        ;;
    8)
        # 2Pi+2Pi-; range - [0.58; 1.995]
        mass_array=(0.6 0.8 1.0 1.2 1.4 1.6 1.8)
        ;;
    *)
        echo "Error: no mass_array defined for decay_mode_idx=$decay_mode_idx" >&2
        exit 1
        ;;
esac

#job resubmission - enables parallelisation on the cluster instead of waiting for each mass to be processed sequentially
if [[ -z "${SLURM_ARRAY_TASK_ID:-}" ]]; then
    n=${#mass_array[@]}
    echo "Submitting self as array job with --array=0-$((n-1))"
    sbatch --array=0-$((n-1)) \
           -o "logs/mass_Scalar-mixing_%a.out" \
           -e "logs/mass_Scalar-mixing_%a.err" \
           "$0"
    exit 0
fi

#files with logs
mv "logs/mass_Scalar-mixing_${SLURM_ARRAY_TASK_ID}.out" "logs/Scalar-mixing_${mass}_${decay_mode_name}.out"
mv "logs/mass_Scalar-mixing_${SLURM_ARRAY_TASK_ID}.err" "logs/Scalar-mixing_${mass}_${decay_mode_name}.err"

set -euo pipefail

LLP_NAMES=("" "ALP-SU2L" "ALP-photon" "Dark-photons" "HNL" "Scalar-mixing" "Scalar-quartic")
llp_name_from_index() { echo "${LLP_NAMES[$1]}"; }

DECAY_MODES_SCALAR=("All" "e+e-" "mu+mu-" "" "Pi+Pi-" "" "K+K-" "" "2Pi+2Pi-")
decay_mode_from_index() { echo "${DECAY_MODES_SCALAR[$1]}"; }

llp_exact_filename() {
    local name="$1" mass="$2" c_tau="$3"
    local mass_fmt c_tau_fmt
    mass_fmt=$(printf "%.3e" "$mass")
    c_tau_fmt=$(printf "%.3e" "$c_tau")
    echo "${EVENTCALC}/outputs/${name}/eventData/${name}_${mass_fmt}_${c_tau_fmt}_data.dat"
}

#setting one of the masses from the array
mass="${mass_array[$SLURM_ARRAY_TASK_ID]}"
echo "Processing mass=$mass on array task $SLURM_ARRAY_TASK_ID"

#hard-coded FIP type index - given by the script
particle_idx=5
llp_name=$(llp_name_from_index "$particle_idx")
echo "Selected LLP: $llp_name"

decay_mode_name=$(decay_mode_from_index "$decay_mode_idx")
echo "Selected Decay Mode: $decay_mode_name"

n_events=11000 #ask EventCalc to generate 2x more events than simulated - the actual output will have just enough 
c_tau=10 #hard-coded FIP lifetime


########   Event Calculator bit   ########
(
    set +u
    source /cvmfs/sft.cern.ch/lcg/views/LCG_105/x86_64-el9-gcc13-opt/setup.sh
    set -u

    cd "$EVENTCALC"

    echo "=== Generating: mass=$mass ==="
    {
        echo "$n_events"
        echo "$particle_idx"
        echo "$decay_mode_idx"
        echo "$mass"
        echo "$c_tau"
    } | python3 simulate.py
    
    filename=$(llp_exact_filename "$llp_name" "$mass" "$c_tau")
   
    root -l -b -q "./convert.C(\"$filename\")"
)

########   FairShip bit - tracking + reco   ########
(
    #unbinds e.g. python from cvmfs -> job does not crash on the cluster
    unset PYTHONHOME PYTHONPATH LD_LIBRARY_PATH ROOTSYS DISPLAY
    #remove QT attempts from GEANT -> job does not crash
    export QT_QPA_PLATFORM=offscreen

    #.dat file is not moved -> can be overwritten by differnt modes. Not important anyway
    filename=$(llp_exact_filename "$llp_name" "$mass" "$c_tau")
    filename_core="${filename%.dat}"
    root_filename="${filename_core}.root"
    root_filename_with_mode="${filename_core}_${decay_mode_name}.root"

    #avoid overwriting EventCalc root file with same mass and different modes -> used for geometrical acceptance
    mv "$root_filename" "$root_filename_with_mode"

    cd "$SIM_SIGNAL"

    echo "### simulation ###"
    #particle tracking
    pixi run python ${FAIRSHIP}/macro/run_simScript.py --tag signal_"$llp_name"_"$mass"_GeV_"$c_tau"_m_"$decay_mode_name" -n 5000 --evtcalc -f "$root_filename_with_mode"
    #->sim_signal_"$llp_name"_"$mass"_GeV_"$c_tau"_m_"$decay_mode_name".root

    echo "### reconstruction ###"
    #digitisation and reconstruction
    pixi run python ${FAIRSHIP}/macro/ShipReco.py -f sim_signal_"$llp_name"_"$mass"_GeV_"$c_tau"_m_"$decay_mode_name".root -g geo_signal_"$llp_name"_"$mass"_GeV_"$c_tau"_m_"$decay_mode_name".root
    #->sim_signal_"$llp_name"_"$mass"_GeV_"$c_tau"_m_"$decay_mode_name"_rec.root
)
