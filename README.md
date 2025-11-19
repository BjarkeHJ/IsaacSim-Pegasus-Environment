# IsaacSim-PegasusSim Environment for Aerial Vehicle Simulation
- Repository for quick setup of IsaacSim world for UAV simulations
- Works with IsaacSim 5.1 and PegasusSim v5.1
- Tested on Ubuntu 22.04
- ROS2 Humble Compatible

## IsaacSim Installation
Based on: https://pegasussimulator.github.io/PegasusSimulator/source/setup/installation.html#installing-nvidia-isaac-sim

```bash
# Go to home directory 
cd ~

# Create new directory for the IsaacSim installation
mkdir -p isaacsim
cd isaacsim

# Download the zip file containing the IsaacSim installation
wget https://download.isaacsim.omniverse.nvidia.com/isaac-sim-standalone-5.1.0-linux-x86_64.zip

# Unzip the file
unzip isaac-sim-standalone-5.1.0-linux-x86_64.zip

# Run the post-installation scripts
./post_install.sh

# Run the sim selector and click start
./isaac-sim.selector.sh

# Delete the zip file
rm isaac-sim-standalone-5.1.0-linux-x86_64.zip
```

NVIDIA provides IsaacSim with its own Python interpreter. To use PegasusSim usage of the same Python interpreter is required when starting simulations. 
The following ~/.bashrc lines simplifies this:
```
# ---------------------------
# ISAAC SIM SETUP
# ---------------------------
# Isaac Sim root directory
export ISAACSIM_PATH="${HOME}/isaacsim"
# Isaac Sim python executable
export ISAACSIM_PYTHON="${ISAACSIM_PATH}/python.sh"
# Isaac Sim app
export ISAACSIM="${ISAACSIM_PATH}/isaac-sim.sh"

# Define an auxiliary function to launch Isaac Sim or run scripts with Isaac Sim's python
# This is done to avoid conflicts between ROS 2 and Isaac Sim's Python environment
isaac_run() {

    # ------------------
    # === VALIDATION ===
    # ------------------
    if [ ! -x "$ISAACSIM_PYTHON" ]; then
        echo "❌ IsaacSim python.sh not found at: $ISAACSIM_PYTHON"
        return 1
    fi
    if [ ! -x "$ISAACSIM" ]; then
        echo "❌ IsaacSim launcher not found at: $ISAACSIM"
        return 1
    fi

    # -------------------------
    # === CLEAN ENVIRONMENT ===
    # -------------------------
    # Unset ROS 2 environment variables to avoid conflicts with Isaac's Python 3.11
    unset ROS_VERSION ROS_PYTHON_VERSION ROS_DISTRO AMENT_PREFIX_PATH COLCON_PREFIX_PATH PYTHONPATH CMAKE_PREFIX_PATH

    # Remove ROS 2 paths from LD_LIBRARY_PATH if present
    local ros_paths=("/opt/ros/humble" "/opt/ros/jazzy" "/opt/ros/iron")
    for ros_path in "${ros_paths[@]}"; do
        export LD_LIBRARY_PATH=$(echo "$LD_LIBRARY_PATH" | tr ':' '\n' | grep -v "^${ros_path}" | paste -sd':' -)
    done

    # -----------------------------
    # === UBUNTU VERSION CHECK ===
    # -----------------------------

    if [ -f /etc/os-release ]; then
        UBUNTU_VERSION=$(grep "^VERSION_ID=" /etc/os-release | cut -d'"' -f2)
    fi

    # If Ubuntu 24.04 -> use the Isaac Sim internal ROS2 Jazzy (ROS2 Jazzy bridge)
    if [[ "$UBUNTU_VERSION" == "24.04" ]]; then
        export ROS_DISTRO=jazzy
        export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
        export LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:${ISAACSIM_PATH}/exts/isaacsim.ros2.bridge/jazzy/lib"
        echo "🧩 Detected Ubuntu 24.04 -> Using ROS_DISTRO=jazzy"
    # If Ubuntu 22.04 -> use the Isaac Sim internal ROS2 Humble (ROS2 Humble bridge)
    else
        export ROS_DISTRO=humble
        export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
        export LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:${ISAACSIM_PATH}/exts/isaacsim.ros2.bridge/humble/lib"
        echo "🧩 Detected Ubuntu ${UBUNTU_VERSION:-unknown} -> Using ROS_DISTRO=humble"
    fi

    # ---------------------
    # === RUN ISAAC SIM ===
    # ---------------------
    if [ $# -eq 0 ]; then
        # No args → Launch full Isaac Sim GUI
        echo "🧠 Launching Isaac Sim GUI..."
        "${ISAACSIM}"

    elif [[ "$1" == --* ]]; then
        # Arguments start with "--" → pass them to Isaac Sim executable
        echo "⚙️  Launching Isaac Sim with options: $*"
        "${ISAACSIM}" "$@"

    elif [ -f "$1" ]; then
        # First argument is a Python file → run with Isaac Sim's Python
        local SCRIPT_PATH="$1"
        shift
        echo "🚀 Running Python script with Isaac Sim: $SCRIPT_PATH"
        "${ISAACSIM_PYTHON}" "$SCRIPT_PATH" "$@"

    else
        # Unrecognized input
        echo "❌ Unknown argument or file not found: '$1'"
        echo "Usage:"
        echo "  isaac_run                 → launch GUI"
        echo "  isaac_run my_script.py    → run script with IsaacSim Python"
        echo "  isaac_run --headless ...  → launch IsaacSim with CLI flags"
        return 1
    fi
}
# Allow running from shell scripts
export -f isaac_run
```

IsaacSim can now be run using the Alias:
```
isaac_run
```

## PegasusSim Installation
Based on: https://pegasussimulator.github.io/PegasusSimulator/source/setup/installation.html#installing-the-pegasus-simulator

Clone the PegasusSim repository:
```
git clone https://github.com/PegasusSimulator/PegasusSimulator.git
```

Installing the IsaacSim extension as a library. This is required to use the PegasusSimulator API from python scripts and standalone apps.
```
# Navigate to the extensions directory
cd PegasusSimulator
cd extensions

# Run the pip command using the IsaacSim Python interpreter
$ISAACSIM_PYTHON -m pip install --editable pegasus.simulator
```

Note: For interactive GUI setup refer to original PegasusSimulator setup guide. 

## PX4-Autopilot Installation
Based on: https://docs.px4.io/main/en/ros2/user_guide

Clone the PX4-Autopilot repository:
```
cd ~
git clone https://github.com/PX4/PX4-Autopilot.git
```

Install the PX4-Autopilot:
```
# Run setup script
bash ./PX4-Autopilot/Tools/setup/ubuntu.sh

# Navigate to the PX4 directory
cd PX4-Autopilot

# Compile the code in SITL mode
make px4_sitl
```
Note: This also installs gazebo modules which are not used but this is the safest way to install the software. 

Install and Setup Micro XRCE-DDS Agent and Client:
```
# Clone repository
git clone -b v2.4.3 https://github.com/eProsima/Micro-XRCE-DDS-Agent.git

# Build the uXRCE-DDS Agent from source
cd Micro-XRCE-DDS-Agent
mkdir build
cd build
cmake ..
make
sudo make install
sudo ldconfig /usr/local/lib
```

The installation can be verified by starting an agent in a terminal:
```
# Start a uXRCE Agent (port 8888)
MicroXRCEAgent udp4 -p 8888
```

## World Configuration

## Quick Launch
```
```









