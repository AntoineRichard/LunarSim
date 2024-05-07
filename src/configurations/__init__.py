__author__ = "Antoine Richard"
__copyright__ = (
    "Copyright 2023, Space Robotics Lab, SnT, University of Luxembourg, SpaceR"
)
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = "Antoine Richard"
__email__ = "antoine.richard@uni.lu"
__status__ = "development"

"""
Configurations
This packages contains all the configurations for the different modules of the simulation.

Why do we need configurations you may ask?
Well, I'm glad you asked.

Configuarions are used to enforce that the correct type of parameters are being passed onto the different modules of the simulation.
Python is not a strongly typed language, so this can go wrong real fast.
This does not mean that it's foul proof, but it should help debugging config files.
When possible, the parameter values are also checked to make sure they are within the correct range."""

from typing import Any

from src.configurations.procedural_terrain_confs import (
    TerrainManagerConf,
    MoonYardConf,
    CraterGeneratorConf,
    CraterDistributionConf,
    BaseTerrainGeneratorConf,
    DeformationEngineConf,
)
from src.configurations.auto_labeling_confs import AutoLabelingConf, CameraConf
from src.configurations.rendering_confs import FlaresConf, RendererConf
from src.configurations.environments import LunalabConf, LunaryardConf
from src.configurations.stellar_engine_confs import StellarEngineConf


class ConfigFactory:
    def __init__(self):
        self.configs = {}

    def registerConfig(self, config_name: str, config: Any) -> None:
        self.configs[config_name] = config

    def __call__(self, config_name: str, **kwargs) -> Any:
        return self.configs[config_name](**kwargs)

    def getConfigs(self) -> list:
        return self.configs.keys()


configFactory = ConfigFactory()
# Terrain Configs
configFactory.registerConfig("terrain_manager", TerrainManagerConf)
configFactory.registerConfig("moon_yard", MoonYardConf)
configFactory.registerConfig("crater_generator", CraterGeneratorConf)
configFactory.registerConfig("crater_distribution", CraterDistributionConf)
configFactory.registerConfig("base_terrain_generator", BaseTerrainGeneratorConf)
configFactory.registerConfig("deformation_engine", DeformationEngineConf)
# Rendering Configs
configFactory.registerConfig("lens_flares", FlaresConf)
configFactory.registerConfig("renderer", RendererConf)
# Environment Configs
configFactory.registerConfig("lunalab_settings", LunalabConf)
configFactory.registerConfig("lunaryard_settings", LunaryardConf)
# Auto Labeling Configs
configFactory.registerConfig("camera_settings", CameraConf)
configFactory.registerConfig("generation_settings", AutoLabelingConf)
# Stellar Engine Configs
configFactory.registerConfig("stellar_engine_settings", StellarEngineConf)
