#!/bin/bash

# Set conda environment
# export ISAAC_CONDA_ENV="isaac_env"

# Set IsaacSim root directory
# export ISAACSIM_PATH="$HOME/isaacsim"

# Activate conda environment
# source ~/miniconda3/etc/profile.d/conda.sh
# conda activate $ISAAC_CONDA_ENV

# Source IsaacSim setup file
# source $ISAACSIM_PATH/setup_conda_env.sh

# Start uXRCE-DDS Agent 
echo "Starting uXRCE-DDS Agent..."
MicroXRCEAgent udp4 -p 8888 &

# Start IsaacSim-Pegasus simulation environment
# python src/IsaacSim-Pegasus-Environment/environment/environment.py
# python environment/environment.py
isaac_run environment/environment.py

# Deactivate conda environment
conda deactivate

pkill MicroXRCEAgent

# End of file