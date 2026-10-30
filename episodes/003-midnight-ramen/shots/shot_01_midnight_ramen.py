#!/usr/bin/env python3
"""
Episode 003 — "MIDNIGHT RAMEN" (shot 01, the only shot).

A rain-soaked alley ramen stall at 2 a.m. One continuous 10-second camera move:
wide alley -> counter -> broth. Three characters: the cook, a hooded customer,
and a cat on a crate. Everything below is generated from code: no textures, no
meshes, no HDRIs on disk. Deterministic for a given --seed.

Run as the studio pipeline expects (mp4 out):
    blender -b --factory-startup -P shot_01_midnight_ramen.py -- \
        --output out.mp4 --fps 24 --duration 10 --seed 42

Also useful while art-directing:
    --frame 120            single still (png path in --output)
    --samples 32 --res 640 360
    --frame-start 1 --frame-end 240 --frame-step 12   contact-sheet stills
"""

from __future__ import annotations

import argparse
import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Euler, Vector

# ----------------------------------------------------------------------------
# Palette (linear sRGB) — warm tungsten against a cold wet alley
# ----------------------------------------------------------------------------
LAMP = (1.00, 0.52, 0.20)
LAMP_SOFT = (1.00, 0.72, 0.45)
NIGHT = (0.30, 0.46, 0.85)
NEON_VIOLET = (0.42, 0.10, 0.98)
NEON_CYAN = (0.05, 0.80, 1.00)
WOOD_DARK = (0.085, 0.048, 0.026)
WOOD_WARM = (0.30, 0.16, 0.07)
CONCRETE = (0.20, 0.195, 0.185)
STEEL = (0.52, 0.535, 0.56)
CERAMIC = (0.88, 0.855, 0.80)

# ----------------------------------------------------------------------------
# Layout (metres, Z up, camera on -Y looking toward +Y)
# ----------------------------------------------------------------------------
ALLEY_HALF_W = 3.25
ALLEY_BACK_Y = 3.05
STALL_W = 3.7
COUNTER_TOP = 1.06


# =============================================================================
# 1. ARGUMENT PARSING / RENDER SETUP
# =============================================================================


def parse_args() -> argparse.Namespace:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    p = argparse.ArgumentParser(description="Midnight Ramen — episode 003 shot 01")
    p.add_argument("--output", default="")
    p.add_argument("--fps", type=int, default=24)
    p.add_argument("--duration", type=float, default=10.0)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--frame", type=int, default=None)
    p.add_argument("--frame-start", type=int, default=1)
    p.add_argument("--frame-end", type=int, default=0)
    p.add_argument("--frame-step", type=int, default=0)
    p.add_argument("--png", action="store_true", help="Render a PNG sequence to the --output prefix")
    p.add_argument("--samples", type=int, default=64)
    p.add_argument("--res", type=int, nargs=2, default=[1280, 720])
    return p.parse_args(argv)


def setup_render(scene: bpy.types.Scene, args: argparse.Namespace) -> None:
    r = scene.render
    r.engine = "CYCLES"
    r.resolution_x, r.resolution_y = args.res
    r.resolution_percentage = 100
    r.fps = args.fps
    r.image_settings.file_format = "PNG"
    r.image_settings.color_mode = "RGB"

    c = scene.cycles
    c.device = "CPU"
    if os.environ.get("RAMEN_GPU", "1") == "1":
        prefs = bpy.context.preferences.addons["cycles"].preferences
        try:
            prefs.compute_device_type = "OPTIX"
            prefs.get_devices()
            for dev in prefs.devices:
                dev.use = dev.type == "OPTIX"
            c.device = "GPU"
            print("[MIDNIGHT-RAMEN] Cycles device: OPTIX GPU")
        except Exception as exc:  # pragma: no cover - hardware fallback
            print(f"[MIDNIGHT-RAMEN] GPU unavailable ({exc}); using CPU")
    c.samples = args.samples
    c.use_adaptive_sampling = True
    c.adaptive_threshold = 0.015
    c.use_denoising = True
    c.denoiser = "OPENIMAGEDENOISE"
    c.max_bounces = 6
    c.diffuse_bounces = 2
    c.glossy_bounces = 3
    c.transmission_bounces = 4
    c.transparent_max_bounces = 6
    c.caustics_reflective = False
    c.caustics_refractive = False
    c.seed = 7

    vs = scene.view_settings
    vs.view_transform = "AgX"
    vs.look = "AgX - Medium High Contrast"
    vs.exposure = 0.45


def setup_compositor(scene: bpy.types.Scene) -> None:
    scene.use_nodes = True
    tree = scene.node_tree
    tree.nodes.clear()
    rl = tree.nodes.new("CompositorNodeRLayers")
    glare = tree.nodes.new("CompositorNodeGlare")
    glare.glare_type = "FOG_GLOW"
    glare.quality = "HIGH"
    glare.threshold = 1.0
    glare.size = 9
    glare.mix = 0.0
    comp = tree.nodes.new("CompositorNodeComposite")
    tree.links.new(rl.outputs["Image"], glare.inputs["Image"])
    tree.links.new(glare.outputs["Image"], comp.inputs["Image"])


# =============================================================================
# 2. MATERIALS
# =============================================================================


def _inp(node, name, value):
    if name in node.inputs:
        node.inputs[name].default_value = value


def mat_solid(
    name,
    color,
    rough=0.5,
    metallic=0.0,
    emission=None,
    emission_strength=0.0,
    transmission=0.0,
    ior=1.45,
    alpha=1.0,
):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    _inp(b, "Base Color", (*color, 1.0))
    _inp(b, "Roughness", rough)
    _inp(b, "Metallic", metallic)
    _inp(b, "IOR", ior)
    _inp(b, "Transmission Weight", transmission)
    _inp(b, "Alpha", alpha)
    if emission is not None:
        _inp(b, "Emission Color", (*emission, 1.0))
        _inp(b, "Emission Strength", emission_strength)
    return m


def mat_noisy(name, color_a, color_b, rough=0.7, scale=4.0, bump=0.12):
    """Two-tone grunge used for concrete, wood and fur (no image textures)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    _inp(b, "Roughness", rough)
    tex = nt.nodes.new("ShaderNodeTexNoise")
    tex.inputs["Scale"].default_value = scale
    tex.inputs["Detail"].default_value = 6.0
    tex.inputs["Roughness"].default_value = 0.6
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[0].color = (*color_a, 1.0)
    ramp.color_ramp.elements[1].position = 0.65
    ramp.color_ramp.elements[1].color = (*color_b, 1.0)
    nt.links.new(tex.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    bmp = nt.nodes.new("ShaderNodeBump")
    bmp.inputs["Strength"].default_value = bump
    nt.links.new(tex.outputs["Fac"], bmp.inputs["Height"])
    nt.links.new(bmp.outputs["Normal"], b.inputs["Normal"])
    return m


def mat_wood(name, planks=6, dark=WOOD_DARK, light=WOOD_WARM):
    """Stained timber: soft grain, no banding (plank seams are geometry)."""
    return mat_noisy(name, dark, light, rough=0.66, scale=5.0, bump=0.10)


# =============================================================================
# 3. GEOMETRY HELPERS
# =============================================================================


def link(obj, coll):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    coll.objects.link(obj)
    return obj


def bevel(obj, width=0.01, segments=2):
    mod = obj.modifiers.new("Bevel", "BEVEL")
    mod.width = width
    mod.segments = segments
    mod.limit_method = "ANGLE"


def shade_smooth(obj):
    for poly in obj.data.polygons:
        poly.use_smooth = True


def box(name, size, loc, mat, bevel_w=0.008, rot=(0, 0, 0), coll=None, smooth=False):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(mat)
    if bevel_w:
        bevel(o, bevel_w)
    if smooth:
        shade_smooth(o)
    return link(o, coll) if coll else o


def cyl(name, radius, depth, loc, mat, rot=(0, 0, 0), verts=32, coll=None, smooth=True):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=verts, radius=radius, depth=depth, location=loc, rotation=rot
    )
    o = bpy.context.object
    o.name = name
    o.data.materials.append(mat)
    if smooth:
        shade_smooth(o)
    return link(o, coll) if coll else o


def sphere(name, radius, loc, mat, scale=(1, 1, 1), segments=32, rings=16, coll=None):
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=segments, ring_count=rings, radius=radius, location=loc
    )
    o = bpy.context.object
    o.name = name
    o.scale = scale
    o.data.materials.append(mat)
    shade_smooth(o)
    return link(o, coll) if coll else o


def cone(name, r1, r2, depth, loc, mat, rot=(0, 0, 0), verts=16, coll=None):
    bpy.ops.mesh.primitive_cone_add(
        vertices=verts, radius1=r1, radius2=r2, depth=depth, location=loc, rotation=rot
    )
    o = bpy.context.object
    o.name = name
    o.data.materials.append(mat)
    shade_smooth(o)
    return link(o, coll) if coll else o


def tube(name, points, radius, mat, coll=None, resolution=12):
    """Smooth bevelled curve through 3D points (cables, tail, chopsticks)."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.resolution_u = resolution
    cu.bevel_depth = radius
    cu.bevel_resolution = 4
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(len(points) - 1)
    for bp, co in zip(sp.bezier_points, points):
        bp.co = co
        bp.handle_left_type = "AUTO"
        bp.handle_right_type = "AUTO"
    o = bpy.data.objects.new(name, cu)
    o.data.materials.append(mat)
    (coll or bpy.context.scene.collection).objects.link(o)
    return o


def text(name, body, size, loc, mat, rot=(math.radians(90), 0, 0), extrude=0.004, coll=None):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.size = size
    cu.extrude = extrude
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    cu.space_character = 1.05
    o = bpy.data.objects.new(name, cu)
    o.location = loc
    o.rotation_euler = Euler(rot)
    o.data.materials.append(mat)
    (coll or bpy.context.scene.collection).objects.link(o)
    return o


def parent(child, parent_obj):
    """Parent while preserving the world transform (empty parents only)."""
    bpy.context.view_layer.update()
    child.parent = parent_obj
    child.matrix_parent_inverse = parent_obj.matrix_world.inverted()
    return child


def empty(name, loc, coll=None):
    o = bpy.data.objects.new(name, None)
    o.location = loc
    o.empty_display_size = 0.1
    (coll or bpy.context.scene.collection).objects.link(o)
    return o


def new_collection(name, parent=None):
    c = bpy.data.collections.new(name)
    (parent or bpy.context.scene.collection).children.link(c)
    return c


# =============================================================================
# 4. THE ALLEY (walls, ground, street furniture)
# =============================================================================


def build_alley(mats, coll, rng):
    box("Ground", (16, 22, 0.1), (0, -3, -0.05), mats["asphalt"], bevel_w=0)

    # Two walls with a doorway gap on the right, back wall closing the alley.
    box("Wall_L", (0.45, 13.0, 7.0), (-ALLEY_HALF_W - 0.22, -3.0, 3.5), mats["concrete"], 0.02)
    box("Wall_R", (0.45, 9.4, 7.0), (ALLEY_HALF_W + 0.22, -4.8, 3.5), mats["concrete"], 0.02)
    box("Wall_R_back", (0.45, 3.4, 7.0), (ALLEY_HALF_W + 0.22, 1.6, 3.5), mats["concrete"], 0.02)
    box("BackWall", (7.2, 0.5, 7.0), (0, ALLEY_BACK_Y + 0.25, 3.5), mats["concrete"], 0.02)
    box("BackWall_Upper", (7.2, 0.5, 7.0), (0, 3.5, 3.5), mats["concrete"], 0.02)

    # Kerb + drain channel down the middle of the alley.
    box("Kerb_L", (0.16, 12.0, 0.14), (-2.95, -3.2, 0.07), mats["concrete_dark"], 0.01)
    box("Kerb_R", (0.16, 12.0, 0.14), (2.95, -3.2, 0.07), mats["concrete_dark"], 0.01)
    box("Drain", (0.34, 9.0, 0.02), (0, -3.0, 0.011), mats["steel_dark"], 0.005)
    for i in range(16):
        box(f"DrainBar_{i}", (0.30, 0.02, 0.03), (0, -7.2 + i * 0.55, 0.03), mats["steel"], 0.003)

    # Wet patches: polished puddles that mirror the stall.
    puddle = mats["puddle"]
    for name, loc, sx, sy in (
        ("Puddle_0", (0.15, -2.05, 0.006), 0.80, 0.42),
        ("Puddle_A", (-0.7, -3.5, 0.006), 1.25, 0.62),
        ("Puddle_B", (1.45, -2.1, 0.006), 0.55, 0.30),
        ("Puddle_C", (-2.0, -5.2, 0.006), 0.75, 0.40),
    ):
        bpy.ops.mesh.primitive_circle_add(
            vertices=48, radius=1.0, fill_type="NGON", location=loc
        )
        o = bpy.context.object
        o.name = name
        o.scale = (sx, sy, 1)
        o.data.materials.append(puddle)
        link(o, coll)

    # Left wall dressing: pipes, AC unit, posters, ladder, hanging bulb.
    cyl("Pipe_L_1", 0.055, 8.0, (-3.0, -2.5, 1.1), mats["steel"], (math.radians(90), 0, 0))
    cyl("Pipe_L_2", 0.035, 6.5, (-3.02, -1.0, 2.7), mats["pipe_rust"], (math.radians(90), 0, 0))
    cyl("Pipe_L_v", 0.04, 3.4, (-3.03, -5.4, 1.7), mats["steel"])
    ac = box("AC_Unit", (0.55, 0.8, 0.42), (-2.95, 0.6, 2.5), mats["concrete_dark"], 0.015)
    for i in range(7):
        box(f"AC_Slat_{i}", (0.44, 0.02, 0.03), (-2.86, 0.25 + i * 0.09, 2.5), mats["steel_dark"], 0)
    box("AC_Bracket", (0.12, 0.2, 0.5), (-2.9, 0.6, 2.2), mats["steel_dark"], 0)

    for i, (y, z, w, h, m) in enumerate(
        (
            (-1.9, 2.15, 0.62, 0.85, "poster_a"),
            (-1.15, 2.0, 0.5, 0.7, "poster_b"),
            (0.95, 1.65, 0.45, 0.6, "poster_c"),
        )
    ):
        box(f"Poster_{i}", (0.012, w, h), (-3.01, y, z), mats[m], 0)
        box(f"PosterFrame_{i}", (0.02, w + 0.04, h + 0.04), (-3.015, y, z), mats["steel_dark"], 0.004)

    # Ladder leaning on the left wall adds silhouette depth.
    for i in range(7):
        box(f"LadderStep_{i}", (0.04, 0.34, 0.03), (-2.72, -4.15, 0.35 + i * 0.32), mats["wood_dark"], 0)
    for dx in (-0.15, 0.15):
        box(f"LadderRail_{dx}", (0.035, 0.035, 2.35), (-2.72 + dx, -4.15, 1.2), mats["wood_dark"], 0)

    # Hanging bulb over the alley, on a sagging cable.
    tube(
        "Cable_L",
        [(-3.05, -6.6, 3.35), (-2.55, -5.4, 3.0), (-2.35, -4.2, 3.12), (-2.9, -3.0, 3.4)],
        0.008,
        mats["steel_dark"],
    )
    cyl("BulbCord_L", 0.006, 0.35, (-2.42, -4.3, 2.95), mats["steel_dark"])
    bulb = sphere("Bulb_L", 0.055, (-2.42, -4.3, 2.76), mats["bulb"], (1, 1, 1.15))

    # Vending machine: cool cyan practical and a big silhouette in the foreground.
    vm_x, vm_y = -2.62, -6.25
    box("Vending_Body", (0.5, 0.95, 1.95), (vm_x, vm_y, 0.975), mats["steel_dark"], 0.02)
    box("Vending_Panel", (0.02, 0.78, 1.05), (vm_x + 0.26, vm_y, 1.32), mats["vending_glass"], 0)
    for row in range(4):
        for col in range(3):
            box(
                f"VendCan_{row}_{col}",
                (0.02, 0.13, 0.17),
                (vm_x + 0.275, vm_y - 0.26 + col * 0.26, 1.72 - row * 0.24),
                mats["vend_can"],
                0,
            )
    box("Vending_Top", (0.55, 1.0, 0.06), (vm_x, vm_y, 1.99), mats["neon_cyan"], 0.005)

    # Right wall dressing: pipes, crates, bin, cables, a distant violet doorway.
    cyl("Pipe_R_1", 0.05, 9.0, (3.02, -2.6, 1.35), mats["pipe_rust"], (math.radians(90), 0, 0))
    cyl("Pipe_R_2", 0.03, 7.0, (3.02, -3.0, 2.45), mats["steel"], (math.radians(90), 0, 0))
    for i in range(4):
        cyl(f"PipeJoint_{i}", 0.075, 0.1, (3.02, -6.0 + i * 2.0, 1.35), mats["steel_dark"])

    box("Crate_1", (0.62, 0.55, 0.5), (2.25, -1.55, 0.25), mats["crate"], 0.012)
    box("Crate_2", (0.5, 0.45, 0.4), (2.4, -1.5, 0.72), mats["crate"], 0.012, rot=(0, 0, 0.18))
    box("Bin", (0.42, 0.42, 0.72), (2.55, -3.4, 0.36), mats["steel_dark"], 0.02)
    cyl("BinLid", 0.24, 0.06, (2.55, -3.4, 0.75), mats["steel"], verts=24)

    tube(
        "Cable_R",
        [(3.05, -7.8, 4.4), (2.7, -6.0, 3.9), (2.75, -4.2, 4.05), (3.05, -2.2, 4.35)],
        0.009,
        mats["steel_dark"],
    )
    for i, (x, y, z, r) in enumerate(((2.9, -2.4, 3.3, 0.05), (2.85, -1.1, 3.55, 0.04))):
        cyl(f"WallVent_{i}", r, 0.3, (x, y, z), mats["steel_dark"], (0, math.radians(90), 0))

    # Doorway at the far end of the right gap: the alley keeps going.
    box("DoorFrame", (1.15, 0.12, 2.15), (2.72, ALLEY_BACK_Y - 0.05, 1.07), mats["wood_dark"], 0.01)
    box("DoorGlow", (0.98, 0.02, 1.95), (2.72, ALLEY_BACK_Y - 0.14, 1.0), mats["door_glow"], 0)
    box("DoorStep", (1.25, 0.5, 0.12), (2.72, ALLEY_BACK_Y - 0.35, 0.06), mats["concrete_dark"], 0.01)

    # Small scattered debris.
    for i in range(9):
        x = rng.uniform(-2.7, 2.7)
        y = rng.uniform(-7.5, 0.4)
        size = rng.uniform(0.04, 0.11)
        box(
            f"Debris_{i}",
            (size, size * rng.uniform(0.5, 1.4), size * 0.25),
            (x, y, size * 0.12),
            mats["debris"],
            0.004,
            rot=(0, 0, rng.uniform(0, 3.1)),
        )

    return {"bulb": bulb}


# =============================================================================
# 5. THE STALL
# =============================================================================


def build_stall(mats, coll, rng):
    OBJ = {}

    # Posts and frame.
    for sx in (-1, 1):
        for sy, y in (("f", -0.62), ("b", 1.88)):
            cyl(f"Post_{sx}_{sy}", 0.065, 2.62, (sx * 1.85, y, 1.31), mats["wood_dark"], verts=16)

    # Roof: sloped slab with a tarp overhang and fascia.
    box("Roof", (4.15, 2.95, 0.09), (0, 0.58, 2.44), mats["roof"], rot=(math.radians(6.0), 0, 0), bevel_w=0.01)
    box("Roof_Fascia", (4.2, 0.08, 0.22), (0, -0.86, 2.33), mats["wood_dark"], 0.006)
    for i in range(5):
        box(
            f"Roof_Rafter_{i}",
            (4.0, 0.06, 0.07),
            (0, -0.6 + i * 0.62, 2.34 + i * 0.065),
            mats["wood_dark"],
            0,
        )
    box("Roof_Trim_R", (0.08, 2.9, 0.1), (2.02, 0.55, 2.42), mats["wood_dark"], 0.01, rot=(math.radians(6), 0, 0))
    box("Roof_Trim_L", (0.08, 2.9, 0.1), (-2.02, 0.55, 2.42), mats["wood_dark"], 0.01, rot=(math.radians(6), 0, 0))

    # Counter: slab, front apron, and the worn top edge.
    box("Counter", (3.55, 0.68, 0.09), (0, -0.10, COUNTER_TOP), mats["counter_top"], 0.012)
    box("Counter_Apron", (3.55, 0.06, 0.5), (0, -0.44, 0.80), mats["wood_warm"], 0.008)
    for i in range(4):
        box(f"Counter_Batten_{i}", (3.56, 0.03, 0.05), (0, -0.475, 0.62 + i * 0.13), mats["wood_dark"], 0.004)
    box("Counter_Shelf", (3.5, 0.5, 0.06), (0, -0.12, 0.72), mats["wood_dark"], 0.006)
    box("Counter_Kick", (3.5, 0.08, 0.14), (0, -0.42, 0.06), mats["wood_dark"], 0.005)

    # Back wall, shelves, menu strips.
    box("Stall_Back", (STALL_W, 0.09, 2.55), (0, 1.93, 1.275), mats["wood_dark"], 0.008)
    for i, z in enumerate((1.62, 2.06)):
        box(f"Shelf_{i}", (3.4, 0.24, 0.05), (0, 1.80, z), mats["wood_warm"], 0.006)
    for i in range(9):
        x = -1.45 + i * 0.36
        h = rng.uniform(0.16, 0.3)
        r = rng.uniform(0.028, 0.045)
        cyl(f"Bottle_{i}", r, h, (x, 1.79, 1.645 + h / 2), mats[rng.choice(("bottle_amber", "bottle_green", "bottle_clear"))], verts=16)
        cyl(f"BottleCap_{i}", r * 0.55, 0.03, (x, 1.79, 1.645 + h + 0.015), mats["steel"], verts=12)

    box("MenuBoard", (0.62, 0.02, 0.46), (1.42, 1.878, 2.14), mats["wood_dark"], 0.006)
    for i in range(3):
        box(f"MenuLine_{i}", (0.44, 0.006, 0.035), (1.42, 1.888, 2.28 - i * 0.10), mats["menu_strip"], 0)

    # Noren curtains: three hanging cloth panels with a wave.
    cloth = mats["noren"]
    for i, cx in enumerate((-1.16, 0.0, 1.16)):
        bpy.ops.mesh.primitive_grid_add(
            x_subdivisions=14, y_subdivisions=8, size=1.0, location=(cx, -0.86, 2.02)
        )
        o = bpy.context.object
        o.name = f"Noren_{i}"
        o.scale = (0.58, 0.62, 1.0)
        o.rotation_euler = (math.radians(90), 0, 0)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        for v in o.data.vertices:
            v.co.z += math.sin(v.co.x * 9.0 + i) * 0.012
            v.co.y += math.sin(v.co.x * 7.0 + i * 2) * 0.008
        o.data.materials.append(cloth)
        bevel(o, 0.004)
        link(o, coll)

    # Crest on the centre panel.
    bpy.ops.mesh.primitive_circle_add(
        vertices=32, radius=0.105, fill_type="NGON", location=(0, -0.875, 2.06)
    )
    crest = bpy.context.object
    crest.name = "Noren_Crest"
    crest.rotation_euler = (math.radians(90), 0, 0)
    crest.data.materials.append(mats["crest"])
    link(crest, coll)
    text("Noren_Text", "RAMEN", 0.062, (0.0, -0.885, 1.86), mats["crest"], extrude=0.001, coll=coll)

    # Lanterns.
    lanterns = []
    for sx, x in (("L", -1.62), ("R", 1.62)):
        pivot = empty(f"LanternPivot_{sx}", (x, -0.98, 2.30), coll)
        cyl(f"LanternCord_{sx}", 0.006, 0.22, (x, -0.98, 2.19), mats["steel_dark"], coll=coll)
        body = cyl(f"Lantern_{sx}", 0.135, 0.36, (0, 0, -0.18), mats["lantern_paper"], verts=24)
        parent(body, pivot)
        for i, z in enumerate((-0.30, -0.18, -0.06)):
            ring = cyl(f"LanternRib_{sx}_{i}", 0.142, 0.012, (0, 0, z), mats["lantern_rib"], verts=24)
            parent(ring, pivot)
        for cap_z, cap_r in ((-0.37, 0.09), (0.01, 0.09)):
            cap = cyl(f"LanternCap_{sx}_{cap_z}", cap_r, 0.035, (0, 0, cap_z), mats["wood_dark"], verts=20)
            parent(cap, pivot)
        lanterns.append(pivot)

    # Sign board above the roof.
    box("SignBoard", (2.86, 0.10, 0.52), (0, -0.94, 2.63), mats["sign_board"], 0.012)
    text("Sign_Midnight", "MIDNIGHT", 0.098, (0, -0.995, 2.755), mats["sign_letter"], extrude=0.005, coll=coll)
    text("Sign_Ramen", "RAMEN", 0.205, (0, -0.995, 2.575), mats["sign_letter"], extrude=0.007, coll=coll)
    OBJ["sign_letters"] = mats["sign_letter"]

    # Under-roof practicals.
    for i, x in enumerate((-1.15, 1.15)):
        cyl(f"BulbCord_{i}", 0.005, 0.34, (x, 0.25, 2.30), mats["steel_dark"])
        sp = sphere(f"Bulb_Stall_{i}", 0.05, (x, 0.25, 2.12), mats["bulb"])
        OBJ[f"bulb_{i}"] = sp

    # Hanging pots and pans on the back wall.
    for i, (x, r) in enumerate(((-1.55, 0.10), (-1.35, 0.085), (1.5, 0.09))):
        cyl(f"Pan_{i}", r, 0.05, (x, 1.86, 2.22), mats["steel"], (math.radians(90), 0, 0), verts=24)
        cyl(f"PanHandle_{i}", 0.012, 0.16, (x, 1.80, 2.3), mats["steel_dark"], (math.radians(90), 0, 0), verts=8)

    # Cantilever work light over the counter.
    tube(
        "WorkLight_Arm",
        [(1.9, 1.2, 2.45), (1.55, 1.2, 2.2), (1.1, 0.9, 2.1)],
        0.012,
        mats["steel_dark"],
    )
    cone("WorkLight_Shade", 0.14, 0.05, 0.1, (1.05, 0.88, 2.05), mats["steel_dark"], verts=24)
    sphere("WorkLight_Bulb", 0.045, (1.05, 0.88, 2.0), mats["bulb"])

    # Stools.
    for i, x in enumerate((-0.95, 0.35, 1.55)):
        cyl(f"StoolSeat_{i}", 0.17, 0.05, (x, -1.02, 0.585), mats["wood_warm"], verts=24)
        for k in range(4):
            ang = math.radians(45 + k * 90)
            lx = x + math.cos(ang) * 0.11
            ly = -1.02 + math.sin(ang) * 0.11
            cyl(f"StoolLeg_{i}_{k}", 0.018, 0.57, (lx, ly, 0.285), mats["steel_dark"], verts=8)
        cyl(f"StoolRing_{i}", 0.13, 0.015, (x, -1.02, 0.24), mats["steel_dark"], verts=24)

    # Counter inventory.
    pot = cyl("BrothPot", 0.24, 0.30, (-0.62, 0.55, 1.25), mats["pot"], verts=32)
    cyl("Broth", 0.225, 0.02, (-0.62, 0.55, 1.39), mats["broth"], verts=32)
    cyl("PotRim", 0.245, 0.025, (-0.62, 0.55, 1.40), mats["steel"], verts=32)
    for i, ang in enumerate((0.4, 2.6, 4.8)):
        tube(f"PotHandle_{i}", [(-0.62 + math.cos(ang) * 0.22, 0.55 + math.sin(ang) * 0.22, 1.30),
                               (-0.62 + math.cos(ang) * 0.28, 0.55 + math.sin(ang) * 0.28, 1.33)], 0.015, mats["steel"])

    # Stacked bowls.
    for i in range(5):
        cyl(f"BowlStack_{i}", 0.13, 0.055, (1.28, 0.55, 1.13 + i * 0.052), mats["ceramic"], verts=28)
    # Condiments.
    for i, (x, y, h, m) in enumerate(((-0.05, -0.22, 0.17, "bottle_amber"), (0.12, -0.24, 0.20, "bottle_clear"))):
        cyl(f"Condiment_{i}", 0.032, h, (x, y, 1.11 + h / 2), mats[m], verts=16)
        cyl(f"CondimentCap_{i}", 0.02, 0.04, (x, y, 1.11 + h + 0.02), mats["steel"], verts=12)
    box("ChopRest", (0.14, 0.05, 0.03), (-0.55, -0.22, 1.115), mats["ceramic"], 0.008)

    # Ramen bowl waiting for the customer.
    bowl = cyl("RamenBowl", 0.135, 0.085, (-0.95, -0.16, 1.105), mats["ceramic"], verts=32)
    cyl("RamenBroth", 0.125, 0.01, (-0.95, -0.16, 1.14), mats["broth"], verts=32)
    cyl("NoodleMound", 0.10, 0.03, (-0.95, -0.16, 1.15), mats["noodle"], verts=24)
    egg_w = sphere("EggWhite", 0.045, (-1.00, -0.12, 1.16), mats["egg_white"], (1, 1, 0.5))
    sphere("EggYolk", 0.024, (-1.00, -0.12, 1.175), mats["egg_yolk"], (1, 1, 0.6))
    box("Nori", (0.09, 0.01, 0.11), (-0.88, -0.13, 1.19), mats["nori"], 0.003, rot=(0, math.radians(12), 0))
    for i in range(6):
        sphere(
            f"Scallion_{i}",
            0.011,
            (-0.98 + rng.uniform(-0.06, 0.06), -0.16 + rng.uniform(-0.05, 0.05), 1.165),
            mats["scallion"],
        )
    for i in range(2):
        cyl(
            f"Chopstick_{i}",
            0.005,
            0.26,
            (-0.89, -0.08 + i * 0.02, 1.13),
            mats["wood_warm"],
            (math.radians(80), 0, math.radians(18)),
            verts=8,
        )

    OBJ["pot"] = pot
    OBJ["bowl"] = bowl
    OBJ["lanterns"] = lanterns
    OBJ["noren"] = [bpy.data.objects[f"Noren_{i}"] for i in range(3)]
    return OBJ



# =============================================================================
# 6. MATERIAL LIBRARY
# =============================================================================


def mat_steam():
    m = bpy.data.materials.new("Steam")
    m.use_nodes = True
    nt = m.node_tree
    out = nt.nodes["Material Output"]
    bsdf = nt.nodes["Principled BSDF"]
    nt.nodes.remove(bsdf)
    mix = nt.nodes.new("ShaderNodeMixShader")
    transp = nt.nodes.new("ShaderNodeBsdfTransparent")
    emit = nt.nodes.new("ShaderNodeEmission")
    emit.inputs["Color"].default_value = (1.0, 0.78, 0.58, 1)
    emit.inputs["Strength"].default_value = 0.42
    coord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 3.4
    noise.inputs["Detail"].default_value = 8.0
    noise.inputs["Roughness"].default_value = 0.6
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.56
    ramp.color_ramp.elements[0].color = (0, 0, 0, 1)
    ramp.color_ramp.elements[1].position = 0.78
    ramp.color_ramp.elements[1].color = (1, 1, 1, 1)
    nt.links.new(coord.outputs["Generated"], mapping.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(coord.outputs["Generated"], sep.inputs["Vector"])
    inv = nt.nodes.new("ShaderNodeMath")
    inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    nt.links.new(sep.outputs["Y"], inv.inputs[1])
    powr = nt.nodes.new("ShaderNodeMath")
    powr.operation = "POWER"
    powr.inputs[1].default_value = 1.8
    nt.links.new(inv.outputs[0], powr.inputs[0])
    fade = nt.nodes.new("ShaderNodeMath")
    fade.operation = "MULTIPLY"
    nt.links.new(powr.outputs[0], fade.inputs[0])
    nt.links.new(ramp.outputs["Color"], fade.inputs[1])
    nt.links.new(fade.outputs[0], mix.inputs[0])
    nt.links.new(transp.outputs[0], mix.inputs[1])
    nt.links.new(emit.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs[0])
    drive = mapping.inputs["Location"].driver_add("default_value", 1).driver
    drive.expression = "-1.45*(((frame-1)%72)/72.0)"
    return m


def build_materials():
    m = {}
    m["asphalt"] = mat_noisy("Asphalt_Wet", (0.035, 0.036, 0.042), (0.085, 0.088, 0.10), rough=0.26, scale=11.0, bump=0.22)
    m["concrete"] = mat_noisy("Concrete_Wall", (0.15, 0.145, 0.14), (0.30, 0.29, 0.27), rough=0.88, scale=2.0, bump=0.22)
    m["concrete_dark"] = mat_noisy("Concrete_Dark", (0.07, 0.07, 0.07), (0.15, 0.145, 0.14), rough=0.86, scale=3.4, bump=0.2)
    m["puddle"] = mat_solid("Puddle", (0.004, 0.006, 0.010), rough=0.03, ior=1.33)
    m["steel"] = mat_solid("Steel", STEEL, rough=0.30, metallic=1.0)
    m["steel_dark"] = mat_solid("Steel_Dark", (0.07, 0.072, 0.078), rough=0.44, metallic=1.0)
    m["pipe_rust"] = mat_noisy("Pipe_Rust", (0.07, 0.04, 0.028), (0.28, 0.13, 0.06), rough=0.78, scale=7.0)
    m["wood_dark"] = mat_wood("Wood_Dark", planks=7, dark=(0.025, 0.014, 0.010), light=WOOD_DARK)
    m["wood_warm"] = mat_wood("Wood_Warm", planks=5, dark=(0.07, 0.035, 0.016), light=WOOD_WARM)
    m["counter_top"] = mat_wood("Counter_Top", planks=3, dark=(0.05, 0.026, 0.012), light=(0.26, 0.14, 0.065))
    m["roof"] = mat_noisy("Roof_Tarp", (0.025, 0.03, 0.035), (0.065, 0.068, 0.072), rough=0.62, scale=9.0, bump=0.35)
    m["crate"] = mat_wood("Crate_Wood", planks=4, dark=(0.05, 0.028, 0.014), light=(0.22, 0.115, 0.05))
    m["debris"] = mat_solid("Debris", (0.11, 0.11, 0.108), rough=0.8)
    m["poster_a"] = mat_solid("Poster_A", (0.55, 0.10, 0.07), rough=0.85)
    m["poster_b"] = mat_solid("Poster_B", (0.10, 0.28, 0.42), rough=0.85)
    m["poster_c"] = mat_solid("Poster_C", (0.34, 0.26, 0.07), rough=0.9)
    m["vending_glass"] = mat_solid("Vending_Glass", (0.10, 0.35, 0.45), rough=0.18, emission=(0.15, 0.75, 1.0), emission_strength=1.6)
    m["vend_can"] = mat_solid("Vend_Can", (0.62, 0.14, 0.10), rough=0.35, metallic=0.5)
    m["neon_cyan"] = mat_solid("Neon_Cyan", NEON_CYAN, emission=NEON_CYAN, emission_strength=5.0)
    m["bulb"] = mat_solid("Bulb_Warm", (1.0, 0.82, 0.62), emission=(1.0, 0.74, 0.44), emission_strength=14.0)
    m["bottle_amber"] = mat_solid("Bottle_Amber", (0.30, 0.13, 0.03), rough=0.06, transmission=0.85, ior=1.45)
    m["bottle_green"] = mat_solid("Bottle_Green", (0.05, 0.22, 0.09), rough=0.06, transmission=0.85, ior=1.45)
    m["bottle_clear"] = mat_solid("Bottle_Clear", (0.55, 0.60, 0.62), rough=0.05, transmission=0.92, ior=1.45)
    m["menu_strip"] = mat_solid("Menu_Strip", (0.86, 0.82, 0.68), rough=0.75, emission=(1.0, 0.92, 0.72), emission_strength=0.18)
    m["noren"] = mat_noisy("Noren_Indigo", (0.010, 0.026, 0.060), (0.030, 0.060, 0.115), rough=0.9, scale=16.0, bump=0.08)
    m["crest"] = mat_solid("Noren_Crest", (0.86, 0.83, 0.72), rough=0.8)
    m["lantern_paper"] = mat_solid("Lantern_Paper", (0.85, 0.50, 0.28), rough=0.55, emission=LAMP, emission_strength=3.2)
    m["lantern_rib"] = mat_solid("Lantern_Rib", (0.05, 0.028, 0.016), rough=0.7)
    m["sign_board"] = mat_noisy("Sign_Board", (0.018, 0.018, 0.020), (0.045, 0.045, 0.048), rough=0.5, scale=5.0)
    m["sign_letter"] = mat_solid("Sign_Letter", (1.0, 0.62, 0.32), rough=0.35, emission=(1.0, 0.58, 0.26), emission_strength=2.2)
    m["pot"] = mat_solid("Pot_Steel", (0.10, 0.10, 0.11), rough=0.32, metallic=1.0)
    m["broth"] = mat_solid("Broth", (0.26, 0.11, 0.035), rough=0.10, emission=(0.55, 0.22, 0.05), emission_strength=0.30)
    m["ceramic"] = mat_solid("Ceramic", CERAMIC, rough=0.20)
    m["noodle"] = mat_solid("Noodle", (0.82, 0.66, 0.34), rough=0.42)
    m["egg_white"] = mat_solid("Egg_White", (0.90, 0.86, 0.76), rough=0.35)
    m["egg_yolk"] = mat_solid("Egg_Yolk", (0.95, 0.52, 0.06), rough=0.30)
    m["nori"] = mat_solid("Nori", (0.02, 0.055, 0.03), rough=0.55)
    m["scallion"] = mat_solid("Scallion", (0.12, 0.55, 0.16), rough=0.45)
    m["door_glow"] = mat_solid("Door_Glow", (0.25, 0.08, 0.5), emission=NEON_VIOLET, emission_strength=1.2)
    # cast
    m["skin"] = mat_solid("Skin", (0.34, 0.185, 0.115), rough=0.58)
    m["skin_dark"] = mat_solid("Skin_Shadow", (0.42, 0.24, 0.16), rough=0.55)
    m["apron"] = mat_noisy("Apron", (0.030, 0.045, 0.070), (0.065, 0.085, 0.115), rough=0.92, scale=8.0, bump=0.05)
    m["shirt"] = mat_noisy("Shirt", (0.035, 0.055, 0.05), (0.075, 0.10, 0.09), rough=0.92, scale=12.0, bump=0.05)
    m["bandana"] = mat_noisy("Bandana", (0.16, 0.022, 0.020), (0.26, 0.045, 0.035), rough=0.88, scale=14.0, bump=0.04)
    m["hair_white"] = mat_solid("Hair_White", (0.72, 0.70, 0.66), rough=0.6)
    m["jacket"] = mat_noisy("Jacket_Teal", (0.035, 0.10, 0.12), (0.07, 0.17, 0.19), rough=0.85, scale=10.0, bump=0.05)
    m["denim"] = mat_noisy("Denim", (0.035, 0.05, 0.10), (0.07, 0.09, 0.16), rough=0.9, scale=18.0, bump=0.05)
    m["scarf"] = mat_noisy("Scarf_Amber", (0.40, 0.13, 0.03), (0.62, 0.24, 0.06), rough=0.9, scale=16.0, bump=0.05)
    m["shoe"] = mat_solid("Shoe", (0.05, 0.05, 0.055), rough=0.45)
    m["cat_fur"] = mat_noisy("Cat_Fur", (0.28, 0.11, 0.035), (0.55, 0.26, 0.09), rough=0.82, scale=22.0, bump=0.12)
    m["cat_eye"] = mat_solid("Cat_Eye", (0.35, 0.75, 0.25), rough=0.15, emission=(0.35, 0.85, 0.25), emission_strength=0.8)
    m["cat_nose"] = mat_solid("Cat_Nose", (0.55, 0.22, 0.22), rough=0.5)
    m["towel"] = mat_solid("Towel", (0.62, 0.60, 0.52), rough=0.95)
    m["rain"] = mat_solid("Rain", (0.55, 0.62, 0.75), rough=0.04, ior=1.33, emission=(0.35, 0.42, 0.55), emission_strength=0.07)
    m["steam"] = mat_steam()
    return m


# =============================================================================
# 7. CHARACTERS
# =============================================================================


def limb(name, a, b, radius, mat, coll, verts=14):
    a, b = Vector(a), Vector(b)
    d = b - a
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=d.length, location=(a + b) / 2)
    o = bpy.context.object
    o.name = name
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = d.to_track_quat("Z", "Y")
    o.data.materials.append(mat)
    shade_smooth(o)
    return link(o, coll)


def build_chef(mats, coll):
    O = {}
    root = empty("Chef_Root", (0.35, 0.95, 0.0), coll)
    O["root"] = root

    torso = sphere("Chef_Torso", 0.235, (0.35, 0.95, 1.19), mats["shirt"], (1.0, 0.78, 1.14), coll=coll)
    parent(torso, root)
    O["torso"] = torso
    parent(sphere("Chef_Belly", 0.195, (0.35, 0.90, 1.04), mats["shirt"], (1.06, 0.84, 0.80), coll=coll), root)
    parent(cyl("Chef_Neck", 0.062, 0.14, (0.35, 0.930, 1.525), mats["skin"], verts=20, coll=coll), root)

    apron = box("Chef_Apron", (0.30, 0.014, 0.40), (0.35, 0.752, 1.13), mats["apron"], 0.01, coll=coll)
    parent(apron, root)
    parent(box("Chef_ApronPocket", (0.14, 0.012, 0.10), (0.35, 0.742, 1.10), mats["apron"], 0.006, coll=coll), root)
    parent(box("Chef_ApronTie", (0.33, 0.016, 0.035), (0.35, 0.745, 1.31), mats["towel"], 0.006, coll=coll), root)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.088, minor_radius=0.030, location=(0.35, 0.930, 1.500))
    neck_towel = bpy.context.object
    neck_towel.name = "Chef_NeckTowel"
    neck_towel.scale = (1.0, 1.0, 0.65)
    neck_towel.data.materials.append(mats["towel"])
    shade_smooth(neck_towel)
    link(neck_towel, coll)
    parent(neck_towel, root)

    HEAD = Vector((0.35, 0.928, 1.690))
    R = 0.175
    head = sphere("Chef_Head", R, HEAD, mats["skin"], (1.0, 0.96, 1.05), coll=coll)
    parent(head, torso)
    O["head"] = head

    def face(name, obj, offset):
        obj.location = HEAD + Vector(offset)
        parent(obj, head)
        return obj

    face("Chef_Nose", sphere("Chef_Nose", 0.050, (0, 0, 0), mats["skin_dark"], (1.0, 1.0, 0.85), coll=coll), (0, -R * 0.92, -0.012))
    for side, sx in (("L", 1), ("R", -1)):
        face(
            f"Chef_Eye_{side}",
            cyl(f"Chef_Eye_{side}", 0.0085, 0.044, (0, 0, 0), mats["shoe"], (0, math.radians(90), 0), verts=10, coll=coll),
            (sx * R * 0.33, -R * 0.90, R * 0.10),
        )
        face(
            f"Chef_Brow_{side}",
            box(f"Chef_Brow_{side}", (0.062, 0.015, 0.014), (0, 0, 0), mats["hair_white"], 0, rot=(0, 0, math.radians(sx * 10)), coll=coll),
            (sx * R * 0.33, -R * 0.88, R * 0.33),
        )
        face(
            f"Chef_Mustache_{side}",
            sphere(f"Chef_Mustache_{side}", 0.052, (0, 0, 0), mats["hair_white"], (1.0, 0.42, 0.30), coll=coll),
            (sx * 0.045, -R * 0.93, -R * 0.31),
        ).rotation_euler = (0, 0, math.radians(sx * 20))
        face(
            f"Chef_Ear_{side}",
            sphere(f"Chef_Ear_{side}", 0.038, (0, 0, 0), mats["skin"], (0.50, 1.0, 1.0), coll=coll),
            (sx * R * 0.98, 0.012, 0.0),
        )
        face(
            f"Chef_Hair_{side}",
            sphere(f"Chef_Hair_{side}", 0.058, (0, 0, 0), mats["hair_white"], (0.95, 0.55, 0.55), coll=coll),
            (sx * R * 0.86, R * 0.30, R * 0.42),
        )

    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=20, radius=0.181, location=HEAD)
    cap = bpy.context.object
    cap.name = "Chef_Bandana"
    cap.scale = (1.0, 0.96, 1.08)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bm = bmesh.new()
    bm.from_mesh(cap.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < 0.052], context="VERTS")
    bm.to_mesh(cap.data)
    bm.free()
    cap.data.materials.append(mats["bandana"])
    shade_smooth(cap)
    link(cap, coll)
    parent(cap, head)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.168, minor_radius=0.009, location=(0.35, 0.928, HEAD.z + 0.056))
    rim_band = bpy.context.object
    rim_band.name = "Chef_BandanaRim"
    rim_band.data.materials.append(mats["bandana"])
    shade_smooth(rim_band)
    link(rim_band, coll)
    parent(rim_band, head)
    knot = sphere("Chef_BandanaKnot", 0.040, (0.35, HEAD.y + R * 0.90, HEAD.z + 0.075), mats["bandana"], (1.3, 0.7, 1.1), coll=coll)
    parent(knot, head)

    sh_r = empty("Chef_Shoulder_R", (0.115, 0.95, 1.415), coll)
    sh_l = empty("Chef_Shoulder_L", (0.585, 0.95, 1.415), coll)
    el_r = empty("Chef_Elbow_R", (0.0, 0.77, 1.30), coll)
    el_l = empty("Chef_Elbow_L", (0.68, 0.72, 1.27), coll)
    for e, p_ in ((sh_r, root), (sh_l, root), (el_r, sh_r), (el_l, sh_l)):
        parent(e, p_)
    O["shoulder_r"] = sh_r
    O["shoulder_l"] = sh_l
    O["elbow_r"] = el_r
    O["elbow_l"] = el_l

    # right arm reaches the broth pot (two bones: shoulder -> elbow -> hand)
    parent(limb("Chef_UpperArm_R", (0.115, 0.95, 1.415), (0.0, 0.77, 1.30), 0.062, mats["shirt"], coll), sh_r)
    parent(limb("Chef_Forearm_R", (0.0, 0.77, 1.30), (-0.30, 0.61, 1.225), 0.050, mats["skin"], coll), el_r)
    parent(sphere("Chef_Elbow_R_Ball", 0.055, (0.0, 0.77, 1.30), mats["shirt"], coll=coll), sh_r)
    parent(sphere("Chef_Hand_R", 0.056, (-0.30, 0.61, 1.225), mats["skin"], (1.0, 1.1, 0.9), coll=coll), el_r)
    # ladle in the right hand, dipping into the pot
    parent(limb("Ladle_Handle", (-0.30, 0.610, 1.225), (-0.415, 0.565, 1.475), 0.011, mats["steel"], coll, verts=10), el_r)
    parent(limb("Ladle_Neck", (-0.415, 0.565, 1.475), (-0.455, 0.552, 1.430), 0.011, mats["steel"], coll, verts=10), el_r)
    parent(sphere("Ladle_Bowl", 0.052, (-0.470, 0.550, 1.415), mats["steel"], (1, 1, 0.55), coll=coll), el_r)

    # left arm rests on the counter
    parent(limb("Chef_UpperArm_L", (0.585, 0.95, 1.415), (0.68, 0.72, 1.27), 0.062, mats["shirt"], coll), sh_l)
    parent(limb("Chef_Forearm_L", (0.68, 0.72, 1.27), (0.58, 0.30, 1.13), 0.050, mats["skin"], coll), el_l)
    parent(sphere("Chef_Elbow_L_Ball", 0.055, (0.68, 0.72, 1.27), mats["shirt"], coll=coll), sh_l)
    parent(sphere("Chef_Hand_L", 0.056, (0.58, 0.30, 1.125), mats["skin"], (1.1, 1.0, 0.85), coll=coll), el_l)
    return O


def build_customer(mats, coll):
    O = {}
    root = empty("Customer_Root", (-0.95, -0.98, 0.0), coll)
    O["root"] = root

    hips = sphere("Customer_Hips", 0.19, (-0.95, -0.96, 0.68), mats["denim"], (1.0, 0.95, 0.75), coll=coll)
    parent(hips, root)
    torso = sphere("Customer_Torso", 0.21, (-0.95, -0.90, 0.92), mats["jacket"], (0.95, 0.78, 1.0), coll=coll)
    torso.rotation_euler = (math.radians(-14), 0, 0)
    parent(torso, root)
    O["torso"] = torso

    hood = sphere("Customer_Hood", 0.185, (-0.95, -0.845, 1.215), mats["jacket"], (1.0, 0.96, 1.05), coll=coll)
    parent(hood, torso)
    O["hood"] = hood
    bpy.ops.mesh.primitive_torus_add(major_radius=0.135, minor_radius=0.022, location=(-0.95, -0.735, 1.215), rotation=(math.radians(90), 0, 0))
    rim = bpy.context.object
    rim.name = "Customer_HoodRim"
    rim.data.materials.append(mats["jacket"])
    link(rim, coll)
    parent(rim, hood)
    bpy.ops.mesh.primitive_circle_add(vertices=32, radius=0.132, fill_type="NGON", location=(-0.95, -0.742, 1.215), rotation=(math.radians(90), 0, 0))
    inner = bpy.context.object
    inner.name = "Customer_HoodInner"
    inner.data.materials.append(mats["shoe"])
    link(inner, coll)
    parent(inner, hood)

    for i in range(5):
        t = (i - 2) * 0.055
        parent(
            tube(
                f"Customer_Hair_{i}",
                [(-0.95 + t, -0.86, 1.09), (-0.95 + t * 1.4, -0.90, 0.98), (-0.95 + t * 1.7, -0.95, 0.90)],
                0.012,
                mats["denim"],
                coll,
            ),
            torso,
        )

    bpy.ops.mesh.primitive_torus_add(major_radius=0.115, minor_radius=0.038, location=(-0.95, -0.89, 1.02))
    scarf = bpy.context.object
    scarf.name = "Customer_Scarf"
    scarf.scale = (1.0, 1.0, 0.8)
    scarf.data.materials.append(mats["scarf"])
    shade_smooth(scarf)
    link(scarf, coll)
    parent(scarf, torso)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.125, minor_radius=0.034, location=(-0.95, -1.01, 1.075))
    scarf_back = bpy.context.object
    scarf_back.name = "Customer_ScarfBack"
    scarf_back.scale = (1.0, 1.0, 0.75)
    scarf_back.data.materials.append(mats["scarf"])
    shade_smooth(scarf_back)
    link(scarf_back, coll)
    parent(scarf_back, torso)
    parent(
        tube("Customer_ScarfTail", [(-1.05, -0.86, 1.02), (-1.10, -1.02, 0.92), (-1.06, -1.14, 0.86)], 0.035, mats["scarf"], coll),
        torso,
    )

    pack = box("Customer_Pack", (0.26, 0.15, 0.30), (-0.95, -1.13, 0.98), mats["denim"], 0.04, rot=(math.radians(-8), 0, 0), coll=coll)
    parent(pack, torso)
    for sx in (-1, 1):
        strap = box(f"Customer_Strap_{sx}", (0.035, 0.10, 0.30), (-0.95 + sx * 0.13, -0.97, 1.10), mats["denim"], 0.01, rot=(math.radians(20), 0, 0), coll=coll)
        parent(strap, torso)

    sh_r = empty("Customer_Shoulder_R", (-0.765, -0.86, 1.04), coll)
    sh_l = empty("Customer_Shoulder_L", (-1.135, -0.86, 1.04), coll)
    el_r = empty("Customer_Elbow_R", (-0.70, -0.60, 1.01), coll)
    for e, p_ in ((sh_r, root), (sh_l, root), (el_r, sh_r)):
        parent(e, p_)
    O["shoulder_r"] = sh_r
    O["elbow_r"] = el_r

    parent(limb("Customer_UpperArm_R", (-0.765, -0.86, 1.04), (-0.70, -0.60, 1.01), 0.055, mats["jacket"], coll), sh_r)
    parent(limb("Customer_Forearm_R", (-0.70, -0.60, 1.01), (-0.80, -0.38, 1.13), 0.045, mats["jacket"], coll), el_r)
    parent(sphere("Customer_Elbow_R_Ball", 0.048, (-0.70, -0.60, 1.01), mats["jacket"], coll=coll), sh_r)
    parent(sphere("Customer_Hand_R", 0.048, (-0.80, -0.38, 1.14), mats["skin"], coll=coll), el_r)

    parent(limb("Customer_UpperArm_L", (-1.135, -0.86, 1.04), (-1.19, -0.61, 1.00), 0.055, mats["jacket"], coll), sh_l)
    parent(limb("Customer_Forearm_L", (-1.19, -0.61, 1.00), (-1.08, -0.39, 1.12), 0.045, mats["jacket"], coll), sh_l)
    parent(sphere("Customer_Elbow_L_Ball", 0.048, (-1.19, -0.61, 1.00), mats["jacket"], coll=coll), sh_l)
    parent(sphere("Customer_Hand_L", 0.048, (-1.08, -0.39, 1.13), mats["skin"], coll=coll), sh_l)

    for i, off in enumerate((-0.008, 0.008)):
        cs = cyl(
            f"Customer_Chopstick_{i}",
            0.0045,
            0.24,
            (-0.845, -0.30, 1.145),
            mats["wood_warm"],
            (math.radians(64), 0, math.radians(6)),
            verts=8,
            coll=coll,
        )
        cs.location.x += off
        parent(cs, el_r)

    for sx in (-1, 1):
        parent(limb(f"Customer_Thigh_{sx}", (-0.95 + sx * 0.10, -0.93, 0.63), (-0.95 + sx * 0.11, -0.70, 0.56), 0.075, mats["denim"], coll), root)
        parent(limb(f"Customer_Shin_{sx}", (-0.95 + sx * 0.11, -0.70, 0.56), (-0.95 + sx * 0.10, -0.74, 0.09), 0.062, mats["denim"], coll), root)
        shoe = box(f"Customer_Shoe_{sx}", (0.10, 0.20, 0.08), (-0.95 + sx * 0.10, -0.78, 0.045), mats["shoe"], 0.02, coll=coll)
        parent(shoe, root)
    return O


def build_cat(mats, coll):
    O = {}
    root = empty("Cat_Root", (1.02, 0.04, 1.105), coll)
    O["root"] = root
    body = sphere("Cat_Body", 0.125, (1.02, 0.04, 1.235), mats["cat_fur"], (1.0, 1.30, 1.05), coll=coll)
    parent(body, root)
    chest = sphere("Cat_Chest", 0.095, (1.02, 0.14, 1.21), mats["cat_fur"], (1.0, 0.9, 1.1), coll=coll)
    parent(chest, root)
    head = sphere("Cat_Head", 0.09, (1.02, 0.17, 1.345), mats["cat_fur"], (1.0, 1.0, 0.95), coll=coll)
    parent(head, root)
    for sx in (-1, 1):
        ear = cone(f"Cat_Ear_{sx}", 0.043, 0.0, 0.08, (1.02 + sx * 0.052, 0.14, 1.405), mats["cat_fur"], verts=12, coll=coll)
        ear.rotation_euler = (math.radians(-8), 0, math.radians(sx * 12))
        parent(ear, head)
        eye = sphere(f"Cat_Eye_{sx}", 0.015, (1.02 + sx * 0.038, 0.232, 1.352), mats["cat_eye"], (0.6, 1.0, 1.3), segments=16, rings=8, coll=coll)
        parent(eye, head)
        paw = sphere(f"Cat_Paw_{sx}", 0.034, (1.02 + sx * 0.055, 0.12, 1.13), mats["cat_fur"], (1.0, 1.3, 0.8), coll=coll)
        parent(paw, root)
    muzzle = sphere("Cat_Muzzle", 0.043, (1.02, 0.242, 1.322), mats["cat_fur"], (1.0, 0.85, 0.75), coll=coll)
    parent(muzzle, head)
    nose = sphere("Cat_Nose", 0.011, (1.02, 0.268, 1.328), mats["cat_nose"], (1.2, 1.0, 0.8), segments=12, rings=8, coll=coll)
    parent(nose, head)

    tail_pivot = empty("Cat_TailPivot", (1.02, -0.04, 1.16), coll)
    parent(tail_pivot, root)
    O["tail"] = tail_pivot
    parent(
        tube(
            "Cat_Tail",
            [(1.02, -0.04, 1.16), (1.29, -0.12, 1.25), (1.33, -0.13, 1.35), (1.36, -0.09, 1.43), (1.36, -0.03, 1.46)],
            0.026,
            mats["cat_fur"],
            coll,
        ),
        tail_pivot,
    )

    # folded cushion under the cat
    cushion = box("Cat_Cushion", (0.34, 0.34, 0.03), (1.02, 0.04, 1.115), mats["scarf"], 0.01, coll=coll)
    return O


# =============================================================================
# 8. ATMOSPHERE: RAIN + STEAM
# =============================================================================


def build_rain(mats, coll, rng, count=230):
    rain_mat = mats["rain"]
    drops = []
    for i in range(count):
        x = rng.uniform(-3.15, 3.15)
        y = rng.uniform(-8.2, 2.9)
        if abs(x) < 2.15 and y > -0.95:  # keep it out of the stall
            continue
        length = rng.uniform(0.12, 0.32)
        d = box(
            f"Rain_{i}",
            (0.0022, 0.0022, length),
            (x, y, 2.0),
            rain_mat,
            0,
            rot=(math.radians(rng.uniform(-3, 3)), math.radians(4.0), 0),
            coll=coll,
        )
        d.visible_shadow = False
        period = rng.uniform(15.0, 28.0)
        f0 = -rng.uniform(1.0, 40.0)
        set_key(d, "location", f0, 4.7 + length, index=2, interp="LINEAR")
        set_key(d, "location", f0 + period, -0.3, index=2, interp="LINEAR")
        add_cycles(d, "location", 2)
        drops.append(d)
    return drops


def build_steam(mats, coll):
    steam = mats["steam"]
    planes = []
    for name, loc, size in (
        ("Steam_Pot_A", (-0.62, 0.52, 1.52), 0.34),
        ("Steam_Pot_B", (-0.64, 0.53, 1.74), 0.46),
        ("Steam_Bowl", (-0.95, -0.14, 1.30), 0.20),
    ):
        bpy.ops.mesh.primitive_plane_add(size=size, location=loc, rotation=(math.radians(90), 0, 0))
        o = bpy.context.object
        o.name = name
        o.data.materials.append(steam)
        link(o, coll)
        o.visible_shadow = False
        planes.append(o)
    return planes


# =============================================================================
# 9. LIGHTING & CAMERA
# =============================================================================


def aim(obj, target):
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def build_lighting(scene, coll, rng, mats):
    world = bpy.data.worlds.new("MidnightSky")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.010, 0.016, 0.038, 1)
    bg.inputs[1].default_value = 0.55

    bpy.ops.object.light_add(type="AREA", location=(0, 0.25, 2.30))
    key = bpy.context.object
    key.name = "Key_Stall_Warm"
    key.data.shape = "RECTANGLE"
    key.data.size, key.data.size_y = 1.5, 0.45
    key.data.energy = 46
    key.data.color = LAMP_SOFT
    link(key, coll)

    for sx, x in (("L", -1.62), ("R", 1.62)):
        bpy.ops.object.light_add(type="POINT", location=(x, -0.70, 2.02))
        pl = bpy.context.object
        pl.name = f"LanternLight_{sx}"
        pl.data.energy = 9
        pl.data.color = LAMP
        pl.data.shadow_soft_size = 0.14
        link(pl, coll)

    bpy.ops.object.light_add(type="AREA", location=(-2.45, -3.6, 3.3))
    fill = bpy.context.object
    fill.name = "Fill_Cool_Alley"
    fill.data.shape = "RECTANGLE"
    fill.data.size, fill.data.size_y = 2.6, 1.6
    fill.data.energy = 34
    fill.data.color = NIGHT
    aim(fill, (0, 0.4, 1.3))
    link(fill, coll)

    bpy.ops.object.light_add(type="AREA", location=(2.5, -1.4, 2.35))
    rim = bpy.context.object
    rim.name = "Rim_Cool_Chef"
    rim.data.shape = "RECTANGLE"
    rim.data.size, rim.data.size_y = 0.7, 1.4
    rim.data.energy = 35
    rim.data.color = NIGHT
    aim(rim, (0.25, 0.85, 1.45))
    link(rim, coll)

    bpy.ops.object.light_add(type="POINT", location=(-2.35, -6.2, 1.35))
    vend = bpy.context.object
    vend.name = "Vending_Glow"
    vend.data.energy = 14
    vend.data.color = NEON_CYAN
    vend.data.shadow_soft_size = 0.4
    link(vend, coll)

    bpy.ops.object.light_add(type="POINT", location=(2.7, 2.75, 1.3))
    door = bpy.context.object
    door.name = "Door_Glow"
    door.data.energy = 12
    door.data.color = NEON_VIOLET
    door.data.shadow_soft_size = 0.5
    link(door, coll)

    bpy.ops.object.light_add(type="POINT", location=(0.0, 0.65, 2.12))
    inner = bpy.context.object
    inner.name = "Stall_Inner_Warm"
    inner.data.energy = 15
    inner.data.color = LAMP_SOFT
    inner.data.shadow_soft_size = 0.3
    link(inner, coll)

    box("Sconce_Bracket", (0.16, 0.05, 0.05), (-3.12, -2.35, 2.35), mats["steel_dark"], 0.004, coll=coll)
    cone("Sconce_Shade", 0.11, 0.05, 0.10, (-3.02, -2.35, 2.31), mats["steel_dark"], verts=20, coll=coll)
    sphere("Sconce_Bulb", 0.045, (-3.02, -2.35, 2.26), mats["bulb"], coll=coll)
    bpy.ops.object.light_add(type="POINT", location=(-3.0, -2.35, 2.24))
    sc = bpy.context.object
    sc.name = "Sconce_Light"
    sc.data.energy = 18
    sc.data.color = LAMP
    sc.data.shadow_soft_size = 0.18
    link(sc, coll)

    bpy.ops.object.light_add(type="POINT", location=(-2.42, -4.3, 2.7))
    alley = bpy.context.object
    alley.name = "Alley_Bulb"
    alley.data.energy = 16
    alley.data.color = LAMP
    alley.data.shadow_soft_size = 0.2
    link(alley, coll)

    bpy.ops.object.light_add(type="AREA", location=(-0.4, -3.4, 2.05))
    soft = bpy.context.object
    soft.name = "Counter_Front_Soft"
    soft.data.shape = "RECTANGLE"
    soft.data.size, soft.data.size_y = 1.6, 0.9
    soft.data.energy = 18
    soft.data.color = (1.0, 0.78, 0.58)
    aim(soft, (0.2, 0.75, 1.35))
    link(soft, coll)

    bpy.ops.object.light_add(type="AREA", location=(0.4, -9.5, 3.6))
    moon = bpy.context.object
    moon.name = "Sky_Fill"
    moon.data.shape = "RECTANGLE"
    moon.data.size, moon.data.size_y = 5.0, 2.0
    moon.data.energy = 15
    moon.data.color = NIGHT
    aim(moon, (0, 0.5, 1.5))
    link(moon, coll)
    return key


def build_camera(scene, coll):
    target = empty("Cam_Target", (-0.15, 0.55, 1.52), coll)
    rig = empty("Cam_Rig", (0.85, -7.40, 1.72), coll)
    focus = empty("Cam_Focus", (0.35, 0.90, 1.60), coll)

    cam_data = bpy.data.cameras.new("Cam_Shot01")
    cam_data.lens = 50
    cam_data.sensor_width = 36
    cam_data.clip_start = 0.1
    cam_data.clip_end = 80
    cam_data.dof.use_dof = True
    cam_data.dof.focus_object = focus
    cam_data.dof.aperture_fstop = 2.8
    cam_data.dof.aperture_blades = 7

    cam = bpy.data.objects.new("Cam_Shot01", cam_data)
    coll.objects.link(cam)
    cam.parent = rig
    con = cam.constraints.new("TRACK_TO")
    con.target = target
    con.track_axis = "TRACK_NEGATIVE_Z"
    con.up_axis = "UP_Y"
    scene.camera = cam
    return rig, target, cam


# =============================================================================
# 10. ANIMATION HELPERS
# =============================================================================


def set_key(obj, path, frame, value, index=-1, interp="BEZIER"):
    if index >= 0:
        getattr(obj, path)[index] = value
    else:
        setattr(obj, path, value)
    obj.keyframe_insert(data_path=path, frame=frame, index=index)
    ad = obj.animation_data
    if not ad or not ad.action:
        return
    for fc in ad.action.fcurves:
        if fc.data_path != path:
            continue
        if index >= 0 and fc.array_index != index:
            continue
        kp = fc.keyframe_points[-1]
        kp.interpolation = interp
        if interp == "BEZIER":
            kp.handle_left_type = kp.handle_right_type = "AUTO_CLAMPED"


def add_cycles(obj, path, index, before="REPEAT", after="REPEAT"):
    for fc in obj.animation_data.action.fcurves:
        if fc.data_path == path and fc.array_index == index:
            mod = fc.modifiers.new("CYCLES")
            mod.mode_before = before
            mod.mode_after = after
            return mod
    return None


def add_noise(obj, path, index, strength, scale):
    for fc in obj.animation_data.action.fcurves:
        if fc.data_path == path and fc.array_index == index:
            mod = fc.modifiers.new("NOISE")
            mod.strength = strength
            mod.scale = scale
            mod.phase = 3.0
            mod.blend_type = "ADD"


def animate(cast, mats, rig, target, scene, total_frames):
    # --- camera: wide establishing -> counter -> close on the broth -----------
    for f, loc in ((1, (0.85, -6.95, 1.72)), (100, (1.00, -5.35, 1.60)), (total_frames, (0.72, -3.78, 1.42))):
        set_key(rig, "location", f, loc)
    for f, loc in ((1, (-0.10, 0.45, 1.55)), (100, (-0.10, 0.40, 1.40)), (total_frames, (-0.12, 0.35, 1.40))):
        set_key(target, "location", f, loc)
    for axis in range(3):
        add_noise(rig, "location", axis, 0.006 if axis != 2 else 0.004, 70.0)

    chef = cast["chef"]
    cust = cast["customer"]
    cat = cast["cat"]

    # --- cook: gentle weight shift, head nod, continuous stirring -------------
    for f, dz in ((1, 0.0), (60, 0.006), (120, 0.0), (180, 0.007), (240, 0.0)):
        set_key(chef["root"], "location", f, (0.35, 0.95, dz), index=-1, interp="BEZIER")
    for f, rz in ((1, -0.02), (120, 0.018), (240, -0.02)):
        set_key(chef["torso"], "rotation_euler", f, (0.02, 0, rz))
    for f, rx in ((1, 0.0), (138, 0.03), (166, -0.10), (196, 0.04), (240, 0.0)):
        set_key(chef["head"], "rotation_euler", f, (rx, 0, 0.0))
    # stirring loop (80 frames)
    for f, rz in ((1, -0.13), (41, 0.13), (81, -0.13)):
        set_key(chef["shoulder_r"], "rotation_euler", f, (0.10, 0, rz))
    add_cycles(chef["shoulder_r"], "rotation_euler", 2)
    set_key(chef["shoulder_l"], "rotation_euler", 1, (0, 0, 0.0))

    # --- customer: chopsticks lift to the mouth around 6 s --------------------
    for f, rx in ((1, 0.0), (118, 0.0), (146, 0.62), (176, 0.55), (208, 0.0), (240, 0.0)):
        set_key(cust["elbow_r"], "rotation_euler", f, (rx, 0, 0))
    for f, rx in ((1, 0.0), (132, 0.0), (156, -0.10), (190, 0.02), (240, 0.0)):
        set_key(cust["hood"], "rotation_euler", f, (rx, 0, 0))
    for f, rz in ((1, 0.01), (120, -0.012), (240, 0.01)):
        set_key(cust["torso"], "rotation_euler", f, (math.radians(-14), 0, rz))

    # --- cat: tail sway, head turn toward the cook ----------------------------
    for f, rz in ((1, 0.0), (36, 0.30), (78, -0.12), (120, 0.26), (170, -0.05), (210, 0.22), (240, 0.0)):
        set_key(cat["tail"], "rotation_euler", f, (0.0, 0.0, rz))
    for f, rz in ((1, 1.35), (110, 1.35), (150, 1.75), (240, 1.5)):
        set_key(cat["root"], "rotation_euler", f, (0.0, 0.0, rz))

    # --- lantern sway (96-frame loop, opposite phases) ------------------------
    for name, phase in (("LanternPivot_L", 0.0), ("LanternPivot_R", 1.6)):
        piv = bpy.data.objects[name]
        for k in range(3):
            f = 1 + k * 48
            set_key(piv, "rotation_euler", f, (math.sin(phase + k * 1.1) * 0.05, 0, math.cos(phase + k * 0.9) * 0.045))
        add_cycles(piv, "rotation_euler", 0)
        add_cycles(piv, "rotation_euler", 2)

    # --- sign flicker ---------------------------------------------------------
    letters = mats["sign_letter"]
    bsdf = letters.node_tree.nodes["Principled BSDF"]
    strength = bsdf.inputs["Emission Strength"]
    for f, v in ((1, 6.0), (58, 6.0), (61, 2.4), (64, 6.0), (129, 6.0), (133, 1.2), (137, 6.0), (240, 6.0)):
        strength.default_value = v
        strength.keyframe_insert("default_value", frame=f)
    for fc in letters.node_tree.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = "BEZIER"

    # --- rain: keep the streaks moving even while the camera drifts ----------
    scene.frame_set(1)


# =============================================================================
# 11. SCENE ASSEMBLY / CLI
# =============================================================================


def build_scene(args):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    setup_render(scene, args)
    setup_compositor(scene)
    scene.frame_start = 1
    scene.frame_end = max(1, int(round(args.fps * args.duration)))

    rng = random.Random(args.seed)
    root = new_collection("MIDNIGHT_RAMEN")
    c_alley = new_collection("01_Alley", root)
    c_stall = new_collection("02_Stall", root)
    c_cast = new_collection("03_Cast", root)
    c_atmo = new_collection("04_Atmosphere", root)
    c_light = new_collection("05_Lights_Camera", root)

    mats = build_materials()
    build_alley(mats, c_alley, rng)
    stall = build_stall(mats, c_stall, rng)
    chef = build_chef(mats, c_cast)
    customer = build_customer(mats, c_cast)
    cat = build_cat(mats, c_cast)
    build_rain(mats, c_atmo, rng)
    build_steam(mats, c_atmo)
    build_lighting(scene, c_light, rng, mats)
    rig, target, cam = build_camera(scene, c_light)

    animate(
        {"chef": chef, "customer": customer, "cat": cat},
        mats,
        rig,
        target,
        scene,
        scene.frame_end,
    )

    bpy.context.view_layer.update()
    return scene, cam


def report(scene):
    deps = bpy.context.evaluated_depsgraph_get()
    verts = 0
    for o in bpy.data.objects:
        if o.type == "MESH":
            me = o.evaluated_get(deps).to_mesh()
            verts += len(me.vertices)
            o.evaluated_get(deps).to_mesh_clear()
    print(
        f"[MIDNIGHT-RAMEN] objects={len(bpy.data.objects)} meshes="
        f"{sum(1 for o in bpy.data.objects if o.type == 'MESH')} verts={verts} "
        f"materials={len(bpy.data.materials)} frames={scene.frame_start}-{scene.frame_end} "
        f"res={scene.render.resolution_x}x{scene.render.resolution_y} samples={scene.cycles.samples}"
    )


def main():
    args = parse_args()
    scene, cam = build_scene(args)
    report(scene)

    out = args.output or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "renders", "shot_01.mp4")

    if args.frame is not None:
        scene.frame_set(args.frame)
        scene.render.image_settings.file_format = "PNG"
        scene.render.filepath = out
        bpy.ops.render.render(write_still=True)
        print(f"[MIDNIGHT-RAMEN] still -> {out}")
        return

    if args.png:
        end = args.frame_end or scene.frame_end
        scene.render.image_settings.file_format = "PNG"
        scene.render.image_settings.color_mode = "RGB"
        scene.frame_start = args.frame_start
        scene.frame_end = end
        scene.render.filepath = out
        bpy.ops.render.render(animation=True)
        print(f"[MIDNIGHT-RAMEN] png sequence -> {out}####.png")
        return

    if args.frame_step:
        scene.render.image_settings.file_format = "PNG"
        end = args.frame_end or scene.frame_end
        os.makedirs(out, exist_ok=True)
        for f in range(args.frame_start, end + 1, args.frame_step):
            scene.frame_set(f)
            scene.render.filepath = os.path.join(out, f"frame_{f:04d}.png")
            bpy.ops.render.render(write_still=True)
            print(f"[MIDNIGHT-RAMEN] frame {f}")
        return

    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.constant_rate_factor = "HIGH"
    scene.render.ffmpeg.ffmpeg_preset = "GOOD"
    scene.render.ffmpeg.audio_codec = "NONE"
    scene.render.use_file_extension = not out.lower().endswith(".mp4")
    scene.render.filepath = out
    bpy.ops.render.render(animation=True)
    print(f"[MIDNIGHT-RAMEN] video -> {out}")


if __name__ == "__main__":
    main()

