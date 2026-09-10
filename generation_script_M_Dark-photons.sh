#!/bin/bash
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=4096M
#SBATCH -J Multibody_decay
#SBATCH -t 24:00:00
#SBATCH -o logs/launcher_%j.out
#SBATCH -e logs/launcher_%j.err

decay_mode_idx=20  

#range = Range of masses for EventCalc generations where the job is not killed by small/zero Br
case "$decay_mode_idx" in
    1)
        # e+e-; range - [0.03; 4.0] (in principle can be generated beyond, but unstable)
        mass_array=(0.05 0.10 0.15 0.20 0.25 0.30 0.35 0.40 0.45 0.50 0.55 0.60 0.65 0.70 0.75)
        ;;
    12)
        # K+K-; range [1.0; 1.75]
        mass_array=(1.0 1.1 1.2 1.3 1.4 1.5 1.6 1.7)
        ;;
    15)
        # Pi+Pi-; range [0.285; 1.944]
        mass_array=(0.3 0.5 0.7 0.9 1.1 1.3 1.5 1.7 1.9)
        ;;
    18)
        # 2Pi+2Pi-; range - [0.83; 1.944]
        mass_array=(0.9 1.1 1.3 1.5 1.7 1.9)
        ;;
    20)
        # mu+mu-; range - [0.211; 4.0] (in principle can be generated beyond, but unstable)
        mass_array=(0.5 0.75 1.0 1.25 1.5 1.75 2.0 2.25 2.5 2.75 3.0 3.25 3.5 3.75 4.0)
        #mass_array=(1.234 2.345)
        ;;
    *)
        echo "Error: no mass_array defined for decay_mode_idx=$decay_mode_idx" >&2
        exit 1
        ;;
esac

if [[ -z "${SLURM_ARRAY_TASK_ID:-}" ]]; then
    n=${#mass_array[@]}
    echo "Submitting self as array job with --array=0-$((n-1))"
    sbatch --array=0-$((n-1)) \
           -o "logs/mass_Dark-photons_%a.out" \
           -e "logs/mass_Dark-photons_%a.err" \
           "$0"
    exit 0
fi

set -euo pipefail

EVENTCALC="/panfs/ikoval/EventCalc-SHiP"
FAIRSHIP="/panfs/ikoval/FairShip"
SIM_SIGNAL="/panfs/ikoval/FairShip/my_work/signal/sim_signal"

LLP_NAMES=("" "ALP-SU2L" "ALP-photon" "Dark-photons" "HNL" "Scalar-mixing" "Scalar-quartic")
llp_name_from_index() { echo "${LLP_NAMES[$1]}"; }

DECAY_MODES_DARK_PHOTON=("All" "e+e-" "" "" "" "" "KL_KS" "KS_K-pi+" "KS_K+pi-" "" "10" "" "K+K-" "" "" "Pi+Pi-" "" "" "2Pi+2Pi-" "" "mu+mu-" "tau+tau-")
decay_mode_from_index() { echo "${DECAY_MODES_DARK_PHOTON[$1]}"; }

llp_exact_filename() {
    local name="$1" mass="$2" c_tau="$3" 
    local mass_fmt c_tau_fmt
    mass_fmt=$(printf "%.3e" "$mass")
    c_tau_fmt=$(printf "%.3e" "$c_tau")
    echo "${EVENTCALC}/outputs/${name}/eventData/${name}_${mass_fmt}_${c_tau_fmt}_central_data.dat" #assuming central uncertainty, hard-coded
}

#setting one of the masses from the array
mass="${mass_array[$SLURM_ARRAY_TASK_ID]}"
echo "Processing mass=$mass on array task $SLURM_ARRAY_TASK_ID"

#hard-coded particle index - given by the script
particle_idx=3
llp_name=$(llp_name_from_index "$particle_idx")
echo "Selected LLP: $llp_name"

#hard-coded uncertainty - suitable only for Dark photon
uncertainty=2
uncertainty_name="central"

decay_mode_name=$(decay_mode_from_index "$decay_mode_idx")
echo "Selected Decay Mode: $decay_mode_name"

n_events=11000 #ask EventCalc to generate 2x more events than simulated - the actual output will have just enough 
c_tau=10 #hard-coded

#files with logs
mv "logs/mass_Dark-photons_${SLURM_ARRAY_TASK_ID}.out" "logs/Dark-photons_${mass}_${uncertainty_name}_${decay_mode_name}.out"
mv "logs/mass_Dark-photons_${SLURM_ARRAY_TASK_ID}.err" "logs/Dark-photons_${mass}_${uncertainty_name}_${decay_mode_name}.err"

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
	    echo "$uncertainty"
        echo "$decay_mode_idx"   # e.g. decay mode selection, adjust as needed
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
    export QT_QPA_PLATFORM=offscreen #should remove QT attempts from GEANT

    cd "$SIM_SIGNAL"

    echo "### simulation ###"
    #.dat file is not moved -> can be overwritten by differnt modes. Not important anyway

    filename=$(llp_exact_filename "$llp_name" "$mass" "$c_tau")
    filename_core="${filename%.dat}"
    root_filename="${filename_core}.root"
    root_filename_with_mode="${filename_core}_${decay_mode_name}.root"

    #avoids overwriting EventCalc root file with same mass and different modes -> used for geometrical acceptance
    mv "$root_filename" "$root_filename_with_mode"
    
    #particle tracking
    pixi run python ${FAIRSHIP}/macro/run_simScript.py --tag signal_"$llp_name"_"$uncertainty_name"_"$mass"_GeV_"$c_tau"_m_"$decay_mode_name" -n 5000 --evtcalc -f "$root_filename_with_mode"
    #->sim_signal_"$llp_name"_"$mass"_GeV_"$c_tau"_m_"$decay_mode_name".root

    #reconstruction
    pixi run python ${FAIRSHIP}/macro/ShipReco.py -f sim_signal_"$llp_name"_"$uncertainty_name"_"$mass"_GeV_"$c_tau"_m_"$decay_mode_name".root -g geo_signal_"$llp_name"_"$uncertainty_name"_"$mass"_GeV_"$c_tau"_m_"$decay_mode_name".root #--noVertexing
    #->sim_signal_"$llp_name"_"$mass"_GeV_"$c_tau"_m_"$decay_mode_name"_rec.root
)

#pixi run python tracking_analysis_M_shell_script.py
