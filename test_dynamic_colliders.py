import omni
import math
from omni.isaac.kit import SimulationApp


if __name__ == "__main__":
    simulation_app = SimulationApp({"headless": False})

    from omni.isaac.core import World
    from WorldBuilders import pxr_utils as pu
    import math
    from pxr import UsdLux, UsdGeom
    from src.terrain_management.colliders_manager import CollidersManager
    from src.configurations.procedural_terrain_confs import (
        CollidersManagerConf,
    )

    CMC = CollidersManagerConf(
        root_path="/Main",
        sim_length=50.0,
        sim_width=50.0,
        resolution=0.1,
        build_radius=1.5,
        remove_radius=2.5,
        max_cache_size=6,
    )

    CM = CollidersManager(cfg=CMC)

    world = World(stage_units_in_meters=1.0)
    stage = omni.usd.get_context().get_stage()    

    UsdLux.DistantLight.Define(stage, "/sun")
    UsdGeom.Sphere.Define(stage, "/sphere")
    sphere = stage.GetPrimAtPath("/sphere")
    pu.addDefaultOps(sphere)
    i = 0
    r = 60
    w = 0.001
    while True:
        world.step(render=True)
        pu.setDefaultOps(sphere, (math.cos(i*w)*r, math.sin(i*w)*r, 1.), (0.,0.,0.,1.), (1.,1.,1.))
        i += 1
        CM.update_blocks((math.cos(i*w)*r, math.sin(i*w)*r, 1.))
