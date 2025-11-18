#!/usr/bin/env python

import carb
from isaacsim import SimulationApp
sim_cfg = {
    "headless": False,
}
sim_app = SimulationApp(launch_config=sim_cfg) # MUST BE RIGHT AFTER SimulationApp IMPORT
# sim_app = SimulationApp({"headless": False}) # MUST BE RIGHT AFTER SimulationApp IMPORT

import os
import yaml
import numpy as np
from scipy.spatial.transform import Rotation

import omni.timeline
from omni.isaac.core.world import World

from isaacsim.core.utils.extensions import enable_extension
enable_extension("isaacsim.ros2.bridge")

# import omni.isaac.core.utils.numpy.rotations as rot_utils
import isaacsim.core.utils.numpy.rotations as rot_utils
from isaacsim.core.utils.stage import add_reference_to_stage
from isaacsim.core.prims import XFormPrim

# Import PegasusSim API
from pegasus.simulator.params import ROBOTS
from pegasus.simulator.logic.backends.px4_mavlink_backend import PX4MavlinkBackend, PX4MavlinkBackendConfig
from pegasus.simulator.logic.vehicles.multirotor import Multirotor, MultirotorConfig
from pegasus.simulator.logic.interface.pegasus_interface import PegasusInterface
from pxr import Gf, UsdLux, Sdf

from backend.sensor import StereoCamera, RTXLidar
from backend.ros2 import ClockPublisher, TfPublisher

sim_app.update()

class PegasusApp:
    def __init__(self):
        self.working_dir = os.path.dirname(os.path.abspath(__file__))
        self.default_body_children = {"body", "base_link", "Looks"}

        self.topic_prefix = "/isaac"
        self.timeline = omni.timeline.get_timeline_interface()
        self.pg = PegasusInterface()
        self.pg._world = World(**self.pg._world_settings)
        self.world = self.pg.world

        self.setup_scene()
        self.world.reset()
        self.stop_sim = False
    
    def setup_scene(self):
        self.world.scene.add_default_ground_plane()
        ClockPublisher()
        self._spawn_ground_plane(scale=[10.0, 10.0, 10.0])
        self._spawn_light()
        self._spawn_object(position=[10.0, 0.0, 0.0], filename="cube.usdc")
        self._spawn_quadrotor(position=[0,0,0], rotation=[0,0,0], vehicle_id=0, camera=False, lidar=True)
        
    @staticmethod
    def _spawn_ground_plane(scale=None):
        scale = np.array([scale])
        XFormPrim(prim_paths_expr="/World/defaultGroundPlane", name="GND", scales=scale)
        return
        
    def _spawn_light(self):
        light = UsdLux.SphereLight.Define(self.world.stage, Sdf.Path("/World/light"))
        light.CreateRadiusAttr(50.0)
        light.CreateIntensityAttr(1000.0)
        light.AddTranslateOp().Set(Gf.Vec3d(1000.0, 1000.0, 1000.0))
        return

    def _spawn_object(self, filename="cube.usdc", position=[0.0, 0.0, 0.0], orientation=[45.0, 45.0, 45.0]):
        # file w. filename must be put in data folder and be .usdc 
        data_dir = os.path.join(self.working_dir, "data/")
        object_path = data_dir + filename
        add_reference_to_stage(usd_path=object_path, prim_path="/World/Object")
        position = np.array([position])
        orientation = np.array([orientation])
        scale = np.array([[1.0, 1.0, 1.0]])
        XFormPrim(
            prim_paths_expr = "/World/Object",
            name = "CubeObject",
            positions=position,
            orientations=rot_utils.euler_angles_to_quats(orientation, degrees=True),
            scales=scale,
        )
        return
    
    def _spawn_quadrotor(self, position=[0.0,0.0,0.07], rotation=[0.0,0.0,0.0], vehicle_id: int=0, camera: bool=False, lidar: bool=False):
        if vehicle_id == 0:
            drone_prim_path = "/World/quadrotor"
        else:
            drone_prim_path = f"/World/quadrotor_{vehicle_id}"
        
        config_quadrotor = MultirotorConfig()
        mavlink_config = PX4MavlinkBackendConfig(
            {
                "vehicle_id": vehicle_id,
                "px4_autolaunch": True,
                "px4_dir": self.pg.px4_path,
                "px4_vehicle_model": self.pg.px4_default_airframe,
            }
        )
        config_quadrotor.backends = [PX4MavlinkBackend(mavlink_config)]

        Multirotor(
            drone_prim_path,
            ROBOTS["Iris"],
            vehicle_id,
            position,
            Rotation.from_euler("XYZ", rotation, degrees=True).as_quat(),
            config = config_quadrotor,
        )

        config_file = self._load_config_file("sensor_config.yaml")

        if camera:
            StereoCamera(
                camera_config=config_file["stereo_camera"],
                topic_prefix=self.topic_prefix,
                drone_prim_path=drone_prim_path,
                vehicle_id=vehicle_id,
                translation=(0.1, 0.0, 0.2),
            )
        
        if lidar:
            RTXLidar(
                lidar_config=config_file["rtx_lidar"],
                topic_prefix=self.topic_prefix,
                drone_prim_path=drone_prim_path,
                vehicle_id=vehicle_id,
                translation=(0.0,0.0,0.05),
            )
        
        TfPublisher(self.topic_prefix, drone_prim_path, self.default_body_children) #make tf tree publisher
        return
    
    def _load_config_file(self, filename):
        config_dir = os.path.join(self.working_dir, "config/")
        config_file_path = config_dir + filename
        try:
            with open(config_file_path, "r") as f:
                config = yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"File {config_file_path} not found")
        return config
    
    def run(self):
        self.timeline.play()

        while sim_app.is_running() and not self.stop_sim:
            self.world.step(render=True)
        
        carb.log_warn("PegasusApp Simulation: App is closing.")
        self.timeline.stop()
        sim_app.close()

def main():
    pg_app = PegasusApp()
    pg_app.run()

if __name__ == "__main__":
    main()
