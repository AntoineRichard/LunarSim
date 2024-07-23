__author__ = "Antoine Richard"
__copyright__ = (
    "Copyright 2023, Space Robotics Lab, SnT, University of Luxembourg, SpaceR"
)
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = "Antoine Richard"
__email__ = "antoine.richard@uni.lu"
__status__ = "development"

from typing import List, Tuple, Union, Dict
import omni.kit.actions.core
import numpy as np
import omni
import carb

from omni.isaac.core.utils.stage import open_stage, add_reference_to_stage
from pxr import UsdGeom, Sdf, UsdLux, Gf, UsdShade, Usd

from src.configurations.procedural_terrain_confs import TerrainManagerConf
from src.terrain_management.terrain_manager import TerrainManager
from src.configurations.environments import LunalabConf
from src.configurations.rendering_confs import FlaresConf
from src.environments.rock_manager import RockManager
from src.physics.terramechanics_parameters import RobotParameter, TerrainMechanicalParameter
from src.physics.terramechanics_solver import TerramechanicsSolver
from WorldBuilders.pxr_utils import setDefaultOps
from assets import get_assets_path


class LunalabController:
    """
    This class is used to control the lab interactive elements."""

    def __init__(
        self,
        lunalab_settings: LunalabConf = None,
        rocks_settings: Dict = None,
        flares_settings: FlaresConf = None,
        terrain_manager: TerrainManagerConf = None,
        **kwargs,
    ) -> None:
        """
        Initializes the lab controller. This class is used to control the lab interactive elements.
        Including:
            - Projector position, intensity, radius, color.
            - Room lights intensity, radius, color.
            - Curtains open or closed.
            - Terrains randomization or using premade DEMs.
            - Rocks random placements.

        Args:
            lunalab_settings (LunalabLabConf): The settings of the lab.
            rocks_settings (Dict): The settings of the rocks.
            flares_settings (FlaresConf): The settings of the flares.
            terrain_manager (TerrainManagerConf): The settings of the terrain manager.
            **kwargs: Arbitrary keyword arguments."""

        self.stage = omni.usd.get_context().get_stage()
        self.stage_settings = lunalab_settings
        self.flare_settings = flares_settings
        self.T = TerrainManager(terrain_manager)
        self.RM = RockManager(**rocks_settings)
        self.TS = TerramechanicsSolver(
            robot_param=RobotParameter(),
            terrain_param=TerrainMechanicalParameter(),
        )
        self.dem = None
        self.mask = None
        self.scene_name = "/Lunalab"
        self.deformation_conf = terrain_manager.moon_yard.deformation_engine

    def load(self) -> None:
        """
        Loads the lab interactive elements in the stage.
        Creates the instancer for the rocks, and generates the terrain."""

        scene_path = get_assets_path() + "/USD_Assets/environments/Lunalab.usd"
        # Loads the Lunalab
        add_reference_to_stage(scene_path, self.scene_name)
        # Fetches the interactive elements
        self.collectInteractiveAssets()
        self.RM.build(self.dem, self.mask)
        # Loads the DEM and the mask
        self.switchTerrain(0)
        self.enableLensFlare(self.flare_settings.enable)
    
    def addRobotManager(self, robotManager):
        self.robotManager = robotManager

    def getLuxAssets(self, prim: "Usd.Prim") -> None:
        """
        Returns the UsdLux prims under a given prim.

        Args:
            prim (Usd.Prim): The prim to be searched.

        Returns:
            list: A list of UsdLux prims."""

        lights = []
        for prim in Usd.PrimRange(prim):
            if prim.IsA(UsdLux.SphereLight):
                lights.append(prim)
            if prim.IsA(UsdLux.CylinderLight):
                lights.append(prim)
            if prim.IsA(UsdLux.DiskLight):
                lights.append(prim)
        return lights

    def setAttributeBatch(
        self, prims: List["Usd.Prim"], attr: str, val: Union[float, int]
    ) -> None:
        """
        Sets the value of an attribute for a list of prims.

        Args:
            prims (List[Usd.Prim]): A list of prims.
            attr (str): The name of the attribute.
            val (Union[float,int]): The value to be set."""

        for prim in prims:
            prim.GetAttribute(attr).Set(val)

    def setAttribute(self, prim, attr, val):
        """
        Sets the value of an attribute for a prim.

        Args:
            prim (Usd.Prim): The prim.
            attr (str): The name of the attribute.
            val (Union[float,int]): The value to be set."""

        prim.GetAttribute(attr).Set(val)

    def loadDEM(self) -> None:
        """
        Loads the DEM and the mask from the TerrainManager."""

        self.dem = self.T.getDEM()
        self.mask = self.T.getMask()

    def collectInteractiveAssets(self) -> None:
        """
        Collects the interactive assets from the stage and assigns them to class variables.
        """

        # Projector
        self._projector_prim = self.stage.GetPrimAtPath(
            self.stage_settings.projector_path
        )
        self._projector_xform = UsdGeom.Xformable(self._projector_prim)
        self._projector_lux = self.getLuxAssets(self._projector_prim)
        self._projector_flare = self.stage.GetPrimAtPath(
            self.stage_settings.projector_shader_path
        )
        # Room Lights
        self._room_lights_prim = self.stage.GetPrimAtPath(
            self.stage_settings.room_lights_path
        )
        self._room_lights_xform = UsdGeom.Xformable(self._room_lights_prim)
        self._room_lights_lux = self.getLuxAssets(self._room_lights_prim)
        # Curtains
        self._curtain_prims = {}
        for key in self.stage_settings.curtains_path.keys():
            self._curtain_prims[key] = self.stage.GetPrimAtPath(
                self.stage_settings.curtains_path[key]
            )

    # ==============================================================================
    # Projector control
    # ==============================================================================
    def setProjectorPose(self, pose: Tuple[List[float], List[float]]) -> None:
        """
        Sets the pose of the projector.

        Args:
            pose (Tuple[List[float],List[float]]): The pose of the projector. The first element is the position, the second is the quaternion.
        """

        position = pose[0]
        quat = pose[1]
        rotation = [quat[0], quat[1], quat[2], quat[3]]
        position = [position[0], position[1], position[2]]

        setDefaultOps(self._projector_xform, position, rotation, [1, 1, 1])

    def setProjectorIntensity(self, intensity: float) -> None:
        """
        Sets the intensity of the projector.

        Args:
            intensity (float): The intensity of the projector (arbitrary unit)."""

        self.setAttributeBatch(self._projector_lux, "intensity", intensity)

    def setProjectorRadius(self, radius: float) -> None:
        """
        Sets the radius of the projector.

        Args:
            radius (float): The radius of the projector (in meters)."""

        self.setAttributeBatch(self._projector_lux, "radius", radius)

    def setProjectorColor(self, color: List[float]) -> None:
        """
        Sets the color of the projector.

        Args:
            color (List[float]): The color of the projector (RGB)."""

        color = Gf.Vec3d(color[0], color[1], color[2])
        self.setAttributeBatch(self._projector_flare, "inputs:emissive_color", color)
        self.setAttributeBatch(
            self._projector_flare, "inputs:diffuse_color_constant", color
        )
        self.setAttributeBatch(self._projector_flare, "inputs:diffuse_tint", color)
        self.setAttributeBatch(self._projector_lux, "color", color)

    def turnProjectorOnOff(self, flag: bool) -> None:
        """
        Turns the projector on or off.

        Args:
            flag (bool): True to turn the projector on, False to turn it off."""

        if flag:
            self._projector_prim.GetAttribute("visibility").Set("visible")
        else:
            self._projector_prim.GetAttribute("visibility").Set("invisible")

    # ==============================================================================
    # Room lights control
    # ==============================================================================
    def setRoomLightsIntensity(self, intensity: float) -> None:
        """
        Sets the intensity of the room lights.

        Args:
            intensity (float): The intensity of the room lights (arbitrary unit)."""

        self.setAttributeBatch(self._room_lights_lux, "intensity", intensity)

    def setRoomLightsRadius(self, radius: float) -> None:
        """
        Sets the radius of the room lights.

        Args:
            radius (float): The radius of the room lights (in meters)."""

        self.setAttributeBatch(self._room_lights_lux, "radius", radius)

    def setRoomLightsFOV(self, FOV: float) -> None:
        """
        Sets the FOV of the room lights.

        Args:
            FOV (float): The FOV of the room lights (in degrees)."""

        self.setAttributeBatch(self._room_lights_lux, "shaping:cone:angle", FOV)

    def setRoomLightsColor(self, color: List[float]) -> None:
        """
        Sets the color of the room lights.

        Args:
            color (List[float]): The color of the room lights (RGB)."""

        color = Gf.Vec3d(color[0], color[1], color[2])
        self.setAttributeBatch(self._room_lights_lux, "color", color)

    def turnRoomLightsOnOff(self, flag: bool) -> None:
        """
        Turns the room lights on or off.

        Args:
            flag (bool): True to turn the room lights on, False to turn them off."""

        if flag:
            self._room_lights_prim.GetAttribute("visibility").Set("visible")
        else:
            self._room_lights_prim.GetAttribute("visibility").Set("invisible")

    # ==============================================================================
    # Curtains control
    # ==============================================================================
    def curtainsExtend(self, flag: bool) -> None:
        """
        Extends or folds the curtains.

        Args:
            flag (bool): True to extend the curtains, False to fold them."""

        if flag:
            self._curtain_prims["extended"].GetAttribute("visibility").Set("visible")
            self._curtain_prims["folded"].GetAttribute("visibility").Set("invisible")
        else:
            self._curtain_prims["extended"].GetAttribute("visibility").Set("invisible")
            self._curtain_prims["folded"].GetAttribute("visibility").Set("visible")

    # ==============================================================================
    # Terrain control
    # ==============================================================================
    def switchTerrain(self, flag: int) -> None:
        """
        Switches the terrain to a new DEM.

        Args:
            flag (int): The id of the DEM to be loaded. If negative, a random DEM is generated.
        """

        if flag < 0:
            self.T.randomizeTerrain()
        else:
            self.T.loadTerrainId(flag)
        self.loadDEM()
        self.RM.updateImageData(self.dem, self.mask)
        self.RM.randomizeInstancers(10)

    def enableRocks(self, flag: bool) -> None:
        """
        Turns the rocks on or off.

        Args:
            flag (bool): True to turn the rocks on, False to turn them off."""

        self.RM.setVisible(flag)

    def randomizeRocks(self, num: int = 8) -> None:
        """
        Randomizes the placement of the rocks.

        Args:
            num (int): The number of rocks to be placed."""

        num = int(num)
        if num == 0:
            num += 1
        self.RM.randomizeInstancers(num)

    # ==============================================================================
    # Render control
    # ==============================================================================
    def enableRTXRealTime(self, data: int = 0) -> None:
        """
        Enables the RTX real time renderer. The ray-traced render.

        Args:
            data (int, optional): Not used. Defaults to 0."""

        action_registry = omni.kit.actions.core.get_action_registry()
        action = action_registry.get_action(
            "omni.kit.viewport.actions", "set_renderer_rtx_realtime"
        )
        action.execute()

    def enableRTXInteractive(self, data: int = 0) -> None:
        """
        Enables the RTX interactive renderer. The path-traced render.

        Args:
            data (int, optional): Not used. Defaults to 0."""

        action_registry = omni.kit.actions.core.get_action_registry()
        action = action_registry.get_action(
            "omni.kit.viewport.actions", "set_renderer_rtx_pathtracing"
        )
        action.execute()

    def enableLensFlare(self, data: bool) -> None:
        """
        Enables the lens flare effect.

        Args:
            data (bool): True to enable the lens flare, False to disable it."""

        settings = carb.settings.get_settings()
        if data:
            settings.set("/rtx/post/lensFlares/enabled", True)
            self.setFlareScale(self.flare_settings.scale)
            self.setFlareNumBlades(self.flare_settings.blades)
            self.setFlareApertureRotation(self.flare_settings.aperture_rotation)
            self.setFlareSensorAspectRatio(self.flare_settings.sensor_aspect_ratio)
            self.setFlareSensorDiagonal(self.flare_settings.sensor_diagonal)
            self.setFlareFstop(self.flare_settings.fstop)
            self.setFlareFocalLength(self.flare_settings.focal_length)
        else:
            settings.set("/rtx/post/lensFlares/enabled", False)

    def setFlareScale(self, value: float) -> None:
        """
        Sets the scale of the lens flare.

        Args:
            value (float): The scale of the lens flare."""

        settings = carb.settings.get_settings()
        settings.set("/rtx/post/lensFlares/flareScale", value)

    def setFlareNumBlades(self, value: int) -> None:
        """
        Sets the number of blades of the lens flare.
        A small number will create sharp spikes, a large number will create a smooth circle.

        Args:
            value (int): The number of blades of the lens flare."""

        settings = carb.settings.get_settings()
        settings.set("/rtx/post/lensFlares/blades", int(value))

    def setFlareApertureRotation(self, value: float) -> None:
        """
        Sets the rotation of the lens flare.

        Args:
            value (float): The rotation of the lens flare."""

        settings = carb.settings.get_settings()
        settings.set("/rtx/post/lensFlares/apertureRotation", value)

    def setFlareSensorDiagonal(self, value: float) -> None:
        """
        Sets the sensor diagonal of the lens flare.

        Args:
            value (float): The sensor diagonal of the lens flare."""

        settings = carb.settings.get_settings()
        settings.set("/rtx/post/lensFlares/sensorDiagonal", value)

    def setFlareSensorAspectRatio(self, value: float) -> None:
        """
        Sets the sensor aspect ratio of the lens flare.

        Args:
            value (float): The sensor aspect ratio of the lens flare."""

        settings = carb.settings.get_settings()
        settings.set("/rtx/post/lensFlares/sensorAspectRatio", value)

    def setFlareFstop(self, value: float) -> None:
        """
        Sets the f-stop of the lens flare.

        Args:
            value (float): The f-stop of the lens flare."""

        settings = carb.settings.get_settings()
        settings.set("/rtx/post/lensFlares/fNumber", value)

    def setFlareFocalLength(self, value: float):
        """
        Sets the focal length of the lens flare.

        Args:
            value (float): The focal length of the lens flare."""

        settings = carb.settings.get_settings()
        settings.set("/rtx/post/lensFlares/focalLength", value)
    
    def deformTerrain(self) -> None:
        """
        Deforms the terrain.
        Args:
            world_poses (np.ndarray): The world poses of the contact points.
            contact_forces (np.ndarray): The contact forces in local frame reported by rigidprimview.
        """
        world_positions = []
        world_orientations = []
        contact_forces = []
        for rrg in self.robotManager.robots_RG.values():
            position, orientation = rrg.get_pose()
            world_positions.append(position)
            world_orientations.append(orientation)
            contact_forces.append(rrg.get_net_contact_forces())
        world_positions = np.concatenate(world_positions, axis=0)
        world_orientations = np.concatenate(world_orientations, axis=0)
        contact_forces = np.concatenate(contact_forces, axis=0)
        
        self.T.deformTerrain(
            world_positions,
            world_orientations,
            contact_forces,
        )
        self.loadDEM()
        self.RM.updateImageData(self.dem, self.mask)
        
    def applyTerramechanics(self) -> None:
        for rrg in self.robotManager.robots_RG.values():
            linear_velocities, angular_velocities = rrg.get_velocities()
            sinkages = np.zeros((linear_velocities.shape[0],))
            force, torque = self.TS.compute_force_and_torque(linear_velocities, angular_velocities, sinkages)
            rrg.apply_force_torque(force, torque)
        
    
    # @staticmethod
    # def transform_to_local(vec:np.ndarray, world_poses:np.ndarray)->np.ndarray:
    #     """
    #     Returns the contact forces in world frame.

    #     Args:
    #         vec (np.ndarray): vector in world coordinate.
    #         world_poses (np.ndarray): The world poses of the contact points.

    #     Returns:
    #         np.ndarray: vector in local coordinate.
    #     """
    #     transform = world_poses.transpose(0, 2, 1)
    #     return np.matmul(transform[:, :3, :3], vec[:, :, None]).squeeze()