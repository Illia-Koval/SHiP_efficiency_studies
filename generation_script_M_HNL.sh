#!/bin/bash
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=4096M
#SBATCH -J Multibody_decay
#SBATCH -t 24:00:00
#SBATCH -o logs/launcher_%j.out
#SBATCH -e logs/launcher_%j.err

decay_mode_idx=34   # just change this one value to switch modes

#range = Range of masses for EventCalc generations where the job is not killed by small/zero Br
case "$decay_mode_idx" in
    34|35)
        # Ke(bar); range - [0.494; 1.44]
        mass_array=(0.5 0.6 0.7 0.8 0.9 1.0 1.1 1.2 1.3 1.4)
        #mass_array=(0.5 0.7 0.9 1.1 1.3)
        ;;
    36|37)
        # Kmu(bar); range [0.5994; 1.46]
        mass_array=(0.6 0.7 0.8 0.9 1.0 1.1 1.2 1.3 1.4)
        #mass_array=(0.6 0.8 1.0 1.2 1.4)
        ;;
    44|45)
        # Pie(bar); range [0.14; 1.44]
        mass_array=(0.2 0.35 0.5 0.65 0.8 0.95 1.1 1.25 1.4)
        #mass_array=(0.2 0.5 0.8 1.1 1.4)
        ;;
    46|47)
        # Pimu(bar); range - [0.246; 1.46]
        mass_array=(0.3 0.4 0.5 0.6 0.7 0.8 0.9 1.0 1.1 1.2 1.3 1.4)
        #mass_array=(0.3 0.5 0.7 0.9 1.1 1.3)
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
           -o "logs/mass_HNL_%a.out" \
           -e "logs/mass_HNL_%a.err" \
           "$0"
    exit 0
fi

set -euo pipefail

EVENTCALC="/panfs/ikoval/EventCalc-SHiP"
FAIRSHIP="/panfs/ikoval/FairShip"
SIM_SIGNAL="/panfs/ikoval/FairShip/my_work/signal/sim_signal"

LLP_NAMES=("" "ALP-SU2L" "ALP-photon" "Dark-photons" "HNL" "Scalar-mixing" "Scalar-quartic")
llp_name_from_index() { echo "${LLP_NAMES[$1]}"; }

DECAY_MODES_HNL=("All" "" "" "" "" "" "" "" "" "" "10" "" "" "" "" "" "" "" "" "" "20" "" "" "" "" "" "" "" "" "" "30" "" "" "" "K+e-" "K-e+" "K+mu-" "K-mu+" "" "" "40" "" "" "" "Pi+e-" "Pi-e+" "Pi+mu-" "Pi-mu+" "" "")
decay_mode_from_index() { echo "${DECAY_MODES_HNL[$1]}"; }

llp_exact_filename() {
    local name="$1" mass="$2" c_tau="$3" mixing_e="$4" mixing_mu="$5" mixing_tau="$6" 
    local mass_fmt c_tau_fmt mixing_e_fmt mixing_mu_fmt mixing_tau_fmt
    mass_fmt=$(printf "%.3e" "$mass")
    c_tau_fmt=$(printf "%.3e" "$c_tau")
    mixing_e_fmt=$(printf "%.3e" "$mixing_e")
    mixing_mu_fmt=$(printf "%.3e" "$mixing_mu")
    mixing_tau_fmt=$(printf "%.3e" "$mixing_tau")

    echo "${EVENTCALC}/outputs/${name}/eventData/${name}_${mass_fmt}_${c_tau_fmt}_${mixing_e_fmt}_${mixing_mu_fmt}_${mixing_tau_fmt}_data.dat"
}

#setting one of the masses from the array
mass="${mass_array[$SLURM_ARRAY_TASK_ID]}"
echo "Processing mass=$mass on array task $SLURM_ARRAY_TASK_ID"

#hard-coded particle index - given by the script
particle_idx=4
llp_name=$(llp_name_from_index "$particle_idx")
echo "Selected LLP: $llp_name"

#hard-coded mixings - suitable only for HNL
mixing_e=0.5
mixing_mu=0.5
mixing_tau=0

decay_mode_name=$(decay_mode_from_index "$decay_mode_idx")
echo "Selected Decay Mode: $decay_mode_name"

n_events=11000 #ask EventCalc to generate 2x more events than simulated - the actual output will have just enough 
c_tau=10 #hard-coded

#files with logs
mv "logs/mass_HNL_${SLURM_ARRAY_TASK_ID}.out" "logs/HNL_${mass}_${mixing_e}_${mixing_mu}_${mixing_tau}_${decay_mode_name}.out"
mv "logs/mass_HNL_${SLURM_ARRAY_TASK_ID}.err" "logs/HNL_${mass}_${mixing_e}_${mixing_mu}_${mixing_tau}_${decay_mode_name}.err"


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
	    echo "${mixing_e} ${mixing_mu} ${mixing_tau}"
        echo "$decay_mode_idx"
        echo "$mass"
        echo "$c_tau"
    } | python3 simulate.py
    
    filename=$(llp_exact_filename "$llp_name" "$mass" "$c_tau" "$mixing_e" "$mixing_mu" "$mixing_tau")
   
    root -l -b -q "./convert.C(\"$filename\")"
)

########   FairShip bit - tracking + reco   ########
(
    #unbinds e.g. python from cvmfs -> job does not crash on the cluster
    unset PYTHONHOME PYTHONPATH LD_LIBRARY_PATH ROOTSYS DISPLAY 
    #remove QT attempts from GEANT -> job does not crash
    export QT_QPA_PLATFORM=offscreen 
    
    cd "$SIM_SIGNAL"

    echo "### simulation ###"
    #.dat file is not moved -> can be overwritten by differnt modes. Not important anyway
    
    filename=$(llp_exact_filename "$llp_name" "$mass" "$c_tau" "$mixing_e" "$mixing_mu" "$mixing_tau")
    filename_core="${filename%.dat}"
    root_filename="${filename_core}.root"
    root_filename_with_mode="${filename_core}_${decay_mode_name}.root"

    #avoids overwriting EventCalc root file with same mass and different modes -> used for geometrical acceptance
    mv "$root_filename" "$root_filename_with_mode"
    
    #particle tracking
    pixi run python ${FAIRSHIP}/macro/run_simScript.py --tag signal_HNL_"$mixing_e"_"$mixing_mu"_"$mixing_tau"_"$mass"_GeV_"$c_tau"_m_"$decay_mode_name" -n 5000 --evtcalc -f "$root_filename_with_mode"
    #->sim_signal_"$llp_name"_"$mass"_GeV_"$c_tau"_m_"$decay_mode_name".root

    #reconstruction
    pixi run python ${FAIRSHIP}/macro/ShipReco.py -f sim_signal_HNL_"$mixing_e"_"$mixing_mu"_"$mixing_tau"_"$mass"_GeV_"$c_tau"_m_"$decay_mode_name".root -g geo_signal_HNL_"$mixing_e"_"$mixing_mu"_"$mixing_tau"_"$mass"_GeV_"$c_tau"_m_"$decay_mode_name".root #--noVertexing
    #->sim_signal_"$llp_name"_"$mass"_GeV_"$c_tau"_m_"$decay_mode_name"_rec.root
)

#pixi run python tracking_analysis_M_shell_script.py
