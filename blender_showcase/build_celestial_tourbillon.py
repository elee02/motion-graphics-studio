#!/usr/bin/env python3
"""
CHRONOS-IV: The Hopf-Fibration Celestial Tourbillon Orrery
==========================================================
100% Procedural Blender 4.2 LTS Scene Generator (Zero External 3D Assets)

Highlights:
- Mathematically exact meshing Involute Horological Spur Gears (structured quad topology,
  phase-locked angular drivers with zero tooth intersection, seamless 120-frame loop).
- Multi-Axis Nested Gimbaled Tourbillon (Rose Gold, Thin-Film Heat-Blued Titanium, Rhodium)
  cradled by twin arched Swan-Neck Bridges and synthetic Corundum Ruby bearings.
- Live Blender 4.2 Geometry Nodes Repeat-Zone Stereographic Hopf Fibration (S^3 -> R^3)
  generating 32 topologically linked Villarceau plasma fibers + 64 traveling micro-sparks.
- 3-Wavelength RGB Spectral Dispersion Diamond Core + Thin-Film Interference Coatings +
  Procedural Polar Rose-Engine Barleycorn Guilloche Dial.
- Studio HDRI Split-Ray Lighting + Cycles OptiX + AgX Color Management + Compositor Bloom.
"""

import argparse
import math
import os
import sys

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector


LOOP_FRAMES = 120


# ==============================================================================
# 1. SCENE RESET & CYCLES / AGX / COMPOSITOR CONFIGURATION
# ==============================================================================

def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = LOOP_FRAMES
    scene.render.fps = 24
    return scene


def configure_cycles_and_color(scene, samples=192, res_x=1920, res_y=1080):
    scene.render.engine = "CYCLES"
    scene.render.resolution_x = res_x
    scene.render.resolution_y = res_y
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False

    # Enable OptiX / CUDA hardware raytracing if available
    cycles = scene.cycles
    cycles.samples = samples
    cycles.use_adaptive_sampling = True
    cycles.adaptive_threshold = 0.01
    cycles.use_denoising = True
    if hasattr(cycles, "denoiser"):
        try:
            cycles.denoiser = "OPENIMAGEDENOISE"
        except Exception:
            pass

    cycles.max_bounces = 10
    cycles.diffuse_bounces = 3
    cycles.glossy_bounces = 6
    cycles.transmission_bounces = 8
    cycles.volume_bounces = 2
    cycles.transparent_max_bounces = 8
    cycles.sample_clamp_direct = 18.0
    cycles.sample_clamp_indirect = 8.0

    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        chosen = None
        for dev_type in ("OPTIX", "CUDA"):
            try:
                prefs.compute_device_type = dev_type
                prefs.get_devices()
                gpu_devs = [d for d in prefs.devices if d.type == dev_type]
                if gpu_devs:
                    for d in prefs.devices:
                        d.use = (d.type == dev_type)
                    chosen = dev_type
                    break
            except Exception:
                continue
        if chosen:
            cycles.device = "GPU"
            print(f"[CHRONOS-IV] Cycles GPU acceleration enabled via {chosen}")
        else:
            cycles.device = "CPU"
    except Exception as exc:
        print(f"[CHRONOS-IV] GPU setup fallback to CPU: {exc}")

    # AgX Color Management
    scene.view_settings.view_transform = "AgX"
    try:
        scene.view_settings.look = "AgX - Medium High Contrast"
    except Exception:
        pass
    scene.view_settings.exposure = 0.15
    scene.view_settings.gamma = 1.0


def configure_compositor(scene):
    scene.use_nodes = True
    nt = scene.node_tree
    nt.nodes.clear()

    rl = nt.nodes.new("CompositorNodeRLayers")
    rl.location = (-500, 0)

    # Lush physically-grounded Fog Glow bloom (controlled so core filaments stay crisp!)
    glow = nt.nodes.new("CompositorNodeGlare")
    glow.location = (-200, 120)
    glow.glare_type = "FOG_GLOW"
    glow.quality = "HIGH"
    glow.threshold = 1.95
    glow.size = 7
    glow.mix = -0.32

    # Subtle horological specular star-streaks on intense metallic highlights
    streaks = nt.nodes.new("CompositorNodeGlare")
    streaks.location = (60, 120)
    streaks.glare_type = "STREAKS"
    streaks.quality = "HIGH"
    streaks.streaks = 6
    streaks.threshold = 5.8
    streaks.fade = 0.86
    streaks.angle_offset = math.radians(15.0)
    streaks.mix = -0.45

    # Very subtle macro lens chromatic dispersion
    lens = nt.nodes.new("CompositorNodeLensdist")
    lens.location = (310, 120)
    lens.use_projector = True
    lens.inputs["Distortion"].default_value = -0.004
    lens.inputs["Dispersion"].default_value = 0.0045

    comp = nt.nodes.new("CompositorNodeComposite")
    comp.location = (580, 120)

    nt.links.new(rl.outputs["Image"], glow.inputs["Image"])
    nt.links.new(glow.outputs["Image"], streaks.inputs["Image"])
    nt.links.new(streaks.outputs["Image"], lens.inputs["Image"])
    nt.links.new(lens.outputs["Image"], comp.inputs["Image"])


# ==============================================================================
# 2. COLLECTION MANAGEMENT & DRIVER HELPERS
# ==============================================================================

def make_collection(name, parent=None):
    col = bpy.data.collections.new(name)
    if parent is None:
        bpy.context.scene.collection.children.link(col)
    else:
        parent.children.link(col)
    return col


def link_obj(obj, col):
    col.objects.link(obj)
    return obj


def add_frame_driver(target, data_path, expression, index=-1):
    if index >= 0:
        fcurve = target.driver_add(data_path, index)
    else:
        fcurve = target.driver_add(data_path)
    drv = fcurve.driver
    drv.type = "SCRIPTED"
    drv.expression = expression
    return drv


def finalize_mesh(mesh, sharp_angle_deg=34.0):
    mesh.update()
    mesh.shade_smooth()
    if sharp_angle_deg is not None:
        mesh.set_sharp_from_angle(angle=math.radians(sharp_angle_deg))
    return mesh


def add_bevel_mod(obj, width=0.0035, segments=2, angle_deg=32.0):
    bev = obj.modifiers.new("Chamfer", "BEVEL")
    bev.width = width
    bev.segments = segments
    bev.limit_method = "ANGLE"
    bev.angle_limit = math.radians(angle_deg)
    bev.harden_normals = False
    return bev


# ==============================================================================
# 3. LUXURY HOROLOGY & QUANTUM SHADER LIBRARY
# ==============================================================================

def build_materials():
    mats = {}

    # --- Helper: Brushed Anisotropic Metal ---
    def make_brushed_metal(
        name,
        base_color,
        rough_min=0.11,
        rough_max=0.20,
        aniso=0.65,
        radial=True,
        bump_strength=0.04,
        ring_scale=180.0,
        thin_film_nm=0.0,
        thin_film_ior=1.45,
    ):
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        nt = mat.node_tree
        nt.nodes.clear()

        out = nt.nodes.new("ShaderNodeOutputMaterial")
        out.location = (620, 0)

        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
        bsdf.location = (280, 0)
        bsdf.inputs["Base Color"].default_value = (*base_color, 1.0)
        bsdf.inputs["Metallic"].default_value = 1.0
        bsdf.inputs["Anisotropic"].default_value = aniso
        if thin_film_nm > 0.0:
            bsdf.inputs["Thin Film Thickness"].default_value = thin_film_nm
            bsdf.inputs["Thin Film IOR"].default_value = thin_film_ior

        tex_coord = nt.nodes.new("ShaderNodeTexCoord")
        tex_coord.location = (-780, 0)

        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        sep.location = (-560, 0)
        nt.links.new(tex_coord.outputs["Object"], sep.inputs["Vector"])

        if radial:
            # Radial distance sqrt(x^2 + y^2) for concentric lathe brushing
            len_node = nt.nodes.new("ShaderNodeVectorMath")
            len_node.operation = "LENGTH"
            len_node.location = (-560, -180)
            comb_xy = nt.nodes.new("ShaderNodeCombineXYZ")
            comb_xy.location = (-720, -180)
            nt.links.new(sep.outputs["X"], comb_xy.inputs["X"])
            nt.links.new(sep.outputs["Y"], comb_xy.inputs["Y"])
            nt.links.new(comb_xy.outputs["Vector"], len_node.inputs[0])

            noise = nt.nodes.new("ShaderNodeTexNoise")
            noise.location = (-320, -120)
            noise.noise_dimensions = "1D"
            noise.inputs["Scale"].default_value = ring_scale
            noise.inputs["Detail"].default_value = 10.0
            noise.inputs["Roughness"].default_value = 0.65
            nt.links.new(len_node.outputs["Value"], noise.inputs["W"])
            pattern_out = noise.outputs["Fac"]
        else:
            # Cotes de Geneve (Geneva Stripes) sinusoidal wave + fine linear grain
            wave = nt.nodes.new("ShaderNodeTexWave")
            wave.location = (-320, -120)
            wave.wave_type = "BANDS"
            wave.bands_direction = "X"
            wave.wave_profile = "SIN"
            wave.inputs["Scale"].default_value = 14.0
            wave.inputs["Distortion"].default_value = 0.35
            wave.inputs["Detail"].default_value = 4.0
            nt.links.new(tex_coord.outputs["Object"], wave.inputs["Vector"])
            pattern_out = wave.outputs["Fac"]

        map_r = nt.nodes.new("ShaderNodeMapRange")
        map_r.location = (-80, 40)
        map_r.inputs["To Min"].default_value = rough_min
        map_r.inputs["To Max"].default_value = rough_max
        nt.links.new(pattern_out, map_r.inputs["Value"])
        nt.links.new(map_r.outputs["Result"], bsdf.inputs["Roughness"])

        bump = nt.nodes.new("ShaderNodeBump")
        bump.location = (40, -180)
        bump.inputs["Strength"].default_value = bump_strength
        bump.inputs["Distance"].default_value = 0.002
        nt.links.new(pattern_out, bump.inputs["Height"])
        nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

        nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
        return mat

    mats["rose_gold"] = make_brushed_metal(
        "Mat_18K_RoseGold",
        (0.95, 0.56, 0.39),
        rough_min=0.09,
        rough_max=0.17,
        aniso=0.72,
        radial=True,
        bump_strength=0.025,
        ring_scale=210.0,
    )
    mats["yellow_gold"] = make_brushed_metal(
        "Mat_18K_YellowGold",
        (0.98, 0.76, 0.29),
        rough_min=0.07,
        rough_max=0.14,
        aniso=0.60,
        radial=True,
        bump_strength=0.02,
        ring_scale=240.0,
    )
    mats["brass"] = make_brushed_metal(
        "Mat_Horological_Brass",
        (0.91, 0.69, 0.28),
        rough_min=0.13,
        rough_max=0.22,
        aniso=0.68,
        radial=True,
        bump_strength=0.035,
        ring_scale=190.0,
    )
    mats["rhodium"] = make_brushed_metal(
        "Mat_Rhodium_Geneva",
        (0.83, 0.85, 0.89),
        rough_min=0.10,
        rough_max=0.20,
        aniso=0.75,
        radial=False,
        bump_strength=0.04,
    )
    mats["titanium"] = make_brushed_metal(
        "Mat_Satin_Titanium",
        (0.50, 0.53, 0.58),
        rough_min=0.17,
        rough_max=0.26,
        aniso=0.55,
        radial=True,
        bump_strength=0.03,
        ring_scale=160.0,
    )
    mats["gunmetal"] = make_brushed_metal(
        "Mat_Dark_Perlage_Plate",
        (0.11, 0.12, 0.15),
        rough_min=0.20,
        rough_max=0.32,
        aniso=0.45,
        radial=True,
        bump_strength=0.05,
        ring_scale=260.0,
    )
    mats["blued_steel"] = make_brushed_metal(
        "Mat_HeatBlued_Titanium",
        (0.07, 0.20, 0.54),
        rough_min=0.08,
        rough_max=0.15,
        aniso=0.55,
        radial=True,
        bump_strength=0.02,
        ring_scale=200.0,
        thin_film_nm=465.0,
        thin_film_ior=1.46,
    )

    # --- Polar Rose-Engine Barleycorn Guilloche Dial Shader ---
    g_mat = bpy.data.materials.new("Mat_Guilloche_Midnight")
    g_mat.use_nodes = True
    nt = g_mat.node_tree
    nt.nodes.clear()

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (880, 0)

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (540, 0)
    bsdf.inputs["Base Color"].default_value = (0.032, 0.062, 0.135, 1.0)
    bsdf.inputs["Metallic"].default_value = 0.96
    bsdf.inputs["Anisotropic"].default_value = 0.80
    bsdf.inputs["Thin Film Thickness"].default_value = 390.0
    bsdf.inputs["Thin Film IOR"].default_value = 1.38

    tc = nt.nodes.new("ShaderNodeTexCoord")
    tc.location = (-1000, 0)
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    sep.location = (-800, 0)
    nt.links.new(tc.outputs["Object"], sep.inputs["Vector"])

    # theta = atan2(y, x), r = sqrt(x^2 + y^2)
    atan2 = nt.nodes.new("ShaderNodeMath")
    atan2.operation = "ARCTAN2"
    atan2.location = (-580, 140)
    nt.links.new(sep.outputs["Y"], atan2.inputs[0])
    nt.links.new(sep.outputs["X"], atan2.inputs[1])

    comb_xy = nt.nodes.new("ShaderNodeCombineXYZ")
    comb_xy.location = (-600, -120)
    nt.links.new(sep.outputs["X"], comb_xy.inputs["X"])
    nt.links.new(sep.outputs["Y"], comb_xy.inputs["Y"])

    r_len = nt.nodes.new("ShaderNodeVectorMath")
    r_len.operation = "LENGTH"
    r_len.location = (-420, -120)
    nt.links.new(comb_xy.outputs["Vector"], r_len.inputs[0])

    # sin(36 * theta) * 1.65
    mul_th = nt.nodes.new("ShaderNodeMath")
    mul_th.operation = "MULTIPLY"
    mul_th.inputs[1].default_value = 36.0
    mul_th.location = (-380, 140)
    nt.links.new(atan2.outputs["Value"], mul_th.inputs[0])

    sin_th = nt.nodes.new("ShaderNodeMath")
    sin_th.operation = "SINE"
    sin_th.location = (-210, 140)
    nt.links.new(mul_th.outputs["Value"], sin_th.inputs[0])

    amp_th = nt.nodes.new("ShaderNodeMath")
    amp_th.operation = "MULTIPLY"
    amp_th.inputs[1].default_value = 1.65
    amp_th.location = (-40, 140)
    nt.links.new(sin_th.outputs["Value"], amp_th.inputs[0])

    # omega_r * r
    mul_r = nt.nodes.new("ShaderNodeMath")
    mul_r.operation = "MULTIPLY"
    mul_r.inputs[1].default_value = 68.0
    mul_r.location = (-210, -120)
    nt.links.new(r_len.outputs["Value"], mul_r.inputs[0])

    # wave1 = sin(68*r + 1.65*sin(36*theta)), wave2 = sin(68*r - 1.65*sin(36*theta))
    add_w = nt.nodes.new("ShaderNodeMath")
    add_w.operation = "ADD"
    add_w.location = (120, 80)
    nt.links.new(mul_r.outputs["Value"], add_w.inputs[0])
    nt.links.new(amp_th.outputs["Value"], add_w.inputs[1])

    sub_w = nt.nodes.new("ShaderNodeMath")
    sub_w.operation = "SUBTRACT"
    sub_w.location = (120, -100)
    nt.links.new(mul_r.outputs["Value"], sub_w.inputs[0])
    nt.links.new(amp_th.outputs["Value"], sub_w.inputs[1])

    s1 = nt.nodes.new("ShaderNodeMath")
    s1.operation = "SINE"
    s1.location = (270, 80)
    nt.links.new(add_w.outputs["Value"], s1.inputs[0])

    s2 = nt.nodes.new("ShaderNodeMath")
    s2.operation = "SINE"
    s2.location = (270, -100)
    nt.links.new(sub_w.outputs["Value"], s2.inputs[0])

    prod = nt.nodes.new("ShaderNodeMath")
    prod.operation = "MULTIPLY"
    prod.location = (220, -240)
    nt.links.new(s1.outputs["Value"], prod.inputs[0])
    nt.links.new(s2.outputs["Value"], prod.inputs[1])

    abs_p = nt.nodes.new("ShaderNodeMath")
    abs_p.operation = "ABSOLUTE"
    abs_p.location = (360, -240)
    nt.links.new(prod.outputs["Value"], abs_p.inputs[0])

    map_gr = nt.nodes.new("ShaderNodeMapRange")
    map_gr.location = (350, 120)
    map_gr.inputs["To Min"].default_value = 0.13
    map_gr.inputs["To Max"].default_value = 0.27
    nt.links.new(abs_p.outputs["Value"], map_gr.inputs["Value"])
    nt.links.new(map_gr.outputs["Result"], bsdf.inputs["Roughness"])
    nt.links.new(abs_p.outputs["Value"], bsdf.inputs["Anisotropic Rotation"])

    gbump = nt.nodes.new("ShaderNodeBump")
    gbump.location = (380, -80)
    gbump.inputs["Strength"].default_value = 0.16
    gbump.inputs["Distance"].default_value = 0.004
    nt.links.new(abs_p.outputs["Value"], gbump.inputs["Height"])
    nt.links.new(gbump.outputs["Normal"], bsdf.inputs["Normal"])

    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    mats["guilloche"] = g_mat

    # --- Synthetic Corundum Ruby Bearing (IOR 1.77) ---
    ruby = bpy.data.materials.new("Mat_Synthetic_Ruby")
    ruby.use_nodes = True
    nt = ruby.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.90, 0.02, 0.10, 1.0)
    bsdf.inputs["Metallic"].default_value = 0.0
    bsdf.inputs["Roughness"].default_value = 0.035
    bsdf.inputs["IOR"].default_value = 1.77
    bsdf.inputs["Transmission Weight"].default_value = 0.94
    bsdf.inputs["Coat Weight"].default_value = 0.6
    bsdf.inputs["Coat Roughness"].default_value = 0.02
    bsdf.inputs["Emission Color"].default_value = (0.85, 0.015, 0.08, 1.0)
    bsdf.inputs["Emission Strength"].default_value = 0.45
    mats["ruby"] = ruby

    # --- 3-Wavelength RGB Spectral Dispersion Diamond Core ---
    disp = bpy.data.materials.new("Mat_Spectral_Dispersion_Diamond")
    disp.use_nodes = True
    nt = disp.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (520, 0)

    g_r = nt.nodes.new("ShaderNodeBsdfGlass")
    g_r.location = (-80, 180)
    g_r.inputs["Color"].default_value = (1.0, 0.04, 0.02, 1.0)
    g_r.inputs["Roughness"].default_value = 0.008
    g_r.inputs["IOR"].default_value = 2.37

    g_g = nt.nodes.new("ShaderNodeBsdfGlass")
    g_g.location = (-80, 0)
    g_g.inputs["Color"].default_value = (0.02, 1.0, 0.05, 1.0)
    g_g.inputs["Roughness"].default_value = 0.008
    g_g.inputs["IOR"].default_value = 2.42

    g_b = nt.nodes.new("ShaderNodeBsdfGlass")
    g_b.location = (-80, -180)
    g_b.inputs["Color"].default_value = (0.03, 0.06, 1.0, 1.0)
    g_b.inputs["Roughness"].default_value = 0.008
    g_b.inputs["IOR"].default_value = 2.48

    add1 = nt.nodes.new("ShaderNodeAddShader")
    add1.location = (150, 90)
    add2 = nt.nodes.new("ShaderNodeAddShader")
    add2.location = (330, 0)

    nt.links.new(g_r.outputs["BSDF"], add1.inputs[0])
    nt.links.new(g_g.outputs["BSDF"], add1.inputs[1])
    nt.links.new(add1.outputs["Shader"], add2.inputs[0])
    nt.links.new(g_b.outputs["BSDF"], add2.inputs[1])
    nt.links.new(add2.outputs["Shader"], out.inputs["Surface"])
    mats["diamond"] = disp

    # --- Anti-Reflective Optical Sapphire Track ---
    sapph = bpy.data.materials.new("Mat_Sapphire_AR")
    sapph.use_nodes = True
    bsdf = sapph.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.88, 0.94, 1.0, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.015
    bsdf.inputs["IOR"].default_value = 1.77
    bsdf.inputs["Transmission Weight"].default_value = 0.97
    bsdf.inputs["Thin Film Thickness"].default_value = 285.0
    bsdf.inputs["Thin Film IOR"].default_value = 1.38
    mats["sapphire"] = sapph

    # --- Hopf Fibration Quantum Plasma Shader (Reads Geometry Nodes Attributes!) ---
    hopf = bpy.data.materials.new("Mat_Hopf_Quantum_Plasma")
    hopf.use_nodes = True
    nt = hopf.node_tree
    nt.nodes.clear()

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (760, 0)

    attr_fiber = nt.nodes.new("ShaderNodeAttribute")
    attr_fiber.attribute_name = "fiber_ratio"
    attr_fiber.location = (-680, 180)

    attr_arc = nt.nodes.new("ShaderNodeAttribute")
    attr_arc.attribute_name = "arc_phase"
    attr_arc.location = (-680, -40)

    attr_spark = nt.nodes.new("ShaderNodeAttribute")
    attr_spark.attribute_name = "is_spark"
    attr_spark.location = (-680, -240)

    # Harmonic color wave around the S^2 base circle: 0.5 + 0.5*sin(2*pi*fiber_ratio)
    tau_mul = nt.nodes.new("ShaderNodeMath")
    tau_mul.operation = "MULTIPLY"
    tau_mul.inputs[1].default_value = math.tau
    tau_mul.location = (-460, 180)
    nt.links.new(attr_fiber.outputs["Fac"], tau_mul.inputs[0])

    sin_f = nt.nodes.new("ShaderNodeMath")
    sin_f.operation = "SINE"
    sin_f.location = (-300, 180)
    nt.links.new(tau_mul.outputs["Value"], sin_f.inputs[0])

    map_f = nt.nodes.new("ShaderNodeMapRange")
    map_f.location = (-130, 180)
    map_f.inputs["From Min"].default_value = -1.0
    map_f.inputs["From Max"].default_value = 1.0
    map_f.inputs["To Min"].default_value = 0.0
    map_f.inputs["To Max"].default_value = 1.0
    nt.links.new(sin_f.outputs["Value"], map_f.inputs["Value"])

    # Dual-spectrum 24K Molten Amber <-> Royal Cobalt-Cyan ramp (deep saturated colors!)
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.location = (60, 200)
    elems = ramp.color_ramp.elements
    elems[0].position = 0.0
    elems[0].color = (1.0, 0.22, 0.015, 1.0)  # Rich molten 24K gold-amber
    elems[1].position = 1.0
    elems[1].color = (0.015, 0.52, 1.0, 1.0)  # Deep relativistic electric cyan
    mid1 = elems.new(0.36)
    mid1.color = (1.0, 0.58, 0.12, 1.0)       # Warm horological gold
    mid2 = elems.new(0.68)
    mid2.color = (0.18, 0.22, 0.95, 1.0)      # Deep sapphire-violet transition
    nt.links.new(map_f.outputs["Result"], ramp.inputs["Fac"])

    # Traveling pulse along each Villarceau circle: (0.5 + 0.5*sin(2*pi*2*arc_phase))^3
    arc_mul = nt.nodes.new("ShaderNodeMath")
    arc_mul.operation = "MULTIPLY"
    arc_mul.inputs[1].default_value = math.tau * 2.0
    arc_mul.location = (-460, -40)
    nt.links.new(attr_arc.outputs["Fac"], arc_mul.inputs[0])

    arc_sin = nt.nodes.new("ShaderNodeMath")
    arc_sin.operation = "SINE"
    arc_sin.location = (-300, -40)
    nt.links.new(arc_mul.outputs["Value"], arc_sin.inputs[0])

    arc_map = nt.nodes.new("ShaderNodeMapRange")
    arc_map.location = (-130, -40)
    arc_map.inputs["From Min"].default_value = -1.0
    arc_map.inputs["From Max"].default_value = 1.0
    arc_map.inputs["To Min"].default_value = 0.20
    arc_map.inputs["To Max"].default_value = 1.0
    nt.links.new(arc_sin.outputs["Value"], arc_map.inputs["Value"])

    arc_pow = nt.nodes.new("ShaderNodeMath")
    arc_pow.operation = "POWER"
    arc_pow.inputs[1].default_value = 3.0
    arc_pow.location = (60, -40)
    nt.links.new(arc_map.outputs["Result"], arc_pow.inputs[0])

    # Controlled intensity so individual Villarceau circles & central diamond stay razor-sharp!
    spark_boost = nt.nodes.new("ShaderNodeMath")
    spark_boost.operation = "MULTIPLY_ADD"
    spark_boost.inputs[1].default_value = 6.5
    spark_boost.inputs[2].default_value = 0.0
    spark_boost.location = (60, -240)
    nt.links.new(attr_spark.outputs["Fac"], spark_boost.inputs[0])

    base_str = nt.nodes.new("ShaderNodeMath")
    base_str.operation = "MULTIPLY_ADD"
    base_str.inputs[1].default_value = 3.4
    base_str.inputs[2].default_value = 1.25
    base_str.location = (240, -40)
    nt.links.new(arc_pow.outputs["Value"], base_str.inputs[0])

    tot_str = nt.nodes.new("ShaderNodeMath")
    tot_str.operation = "ADD"
    tot_str.location = (410, -100)
    nt.links.new(base_str.outputs["Value"], tot_str.inputs[0])
    nt.links.new(spark_boost.outputs["Value"], tot_str.inputs[1])

    emis = nt.nodes.new("ShaderNodeEmission")
    emis.location = (560, 0)
    nt.links.new(ramp.outputs["Color"], emis.inputs["Color"])
    nt.links.new(tot_str.outputs["Value"], emis.inputs["Strength"])
    nt.links.new(emis.outputs["Emission"], out.inputs["Surface"])
    mats["hopf_plasma"] = hopf

    # --- Dark Obsidian / Brushed Slate Watchmaker's Workbench ---
    slate = bpy.data.materials.new("Mat_Obsidian_Workbench")
    slate.use_nodes = True
    nt = slate.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (560, 0)

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (240, 0)
    bsdf.inputs["Base Color"].default_value = (0.016, 0.018, 0.024, 1.0)
    bsdf.inputs["Metallic"].default_value = 0.15
    bsdf.inputs["Coat Weight"].default_value = 0.25
    bsdf.inputs["Coat Roughness"].default_value = 0.18

    tc = nt.nodes.new("ShaderNodeTexCoord")
    tc.location = (-560, 0)
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.location = (-340, 0)
    noise.inputs["Scale"].default_value = 8.5
    noise.inputs["Detail"].default_value = 12.0
    noise.inputs["Roughness"].default_value = 0.72
    nt.links.new(tc.outputs["Object"], noise.inputs["Vector"])

    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.location = (-100, 80)
    mr.inputs["To Min"].default_value = 0.18
    mr.inputs["To Max"].default_value = 0.38
    nt.links.new(noise.outputs["Fac"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], bsdf.inputs["Roughness"])

    sbump = nt.nodes.new("ShaderNodeBump")
    sbump.location = (-60, -140)
    sbump.inputs["Strength"].default_value = 0.045
    sbump.inputs["Distance"].default_value = 0.01
    nt.links.new(noise.outputs["Fac"], sbump.inputs["Height"])
    nt.links.new(sbump.outputs["Normal"], bsdf.inputs["Normal"])

    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    mats["workbench"] = slate

    # --- Localized Atmospheric Volumetric Haze ---
    vol = bpy.data.materials.new("Mat_Tourbillon_Atmosphere")
    vol.use_nodes = True
    nt = vol.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (300, 0)
    pvol = nt.nodes.new("ShaderNodeVolumePrincipled")
    pvol.location = (0, 0)
    pvol.inputs["Color"].default_value = (0.72, 0.80, 0.95, 1.0)
    pvol.inputs["Density"].default_value = 0.022
    pvol.inputs["Anisotropy"].default_value = 0.62
    nt.links.new(pvol.outputs["Volume"], out.inputs["Volume"])
    mats["volume"] = vol

    # --- Luminous Dust Mote Bokeh Material ---
    mote_mat = bpy.data.materials.new("Mat_Golden_Bokeh_Motes")
    mote_mat.use_nodes = True
    bsdf = mote_mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (1.0, 0.80, 0.45, 1.0)
    bsdf.inputs["Emission Color"].default_value = (1.0, 0.72, 0.36, 1.0)
    bsdf.inputs["Emission Strength"].default_value = 4.5
    mats["motes"] = mote_mat

    return mats


# ==============================================================================
# 4. PARAMETRIC HOROLOGICAL GEOMETRY BUILDERS (PURE STRUCTURED BMESH)
# ==============================================================================

def create_annulus_mesh(name, r_in, r_out, z_bot, z_top, segs=96, r_top_in=None, r_top_out=None):
    """Structured quad annulus/frustum ring with clean manifold normals."""
    if r_top_in is None:
        r_top_in = r_in
    if r_top_out is None:
        r_top_out = r_out

    bm = bmesh.new()
    rings = []
    for z, ri, ro in ((z_bot, r_in, r_out), (z_top, r_top_in, r_top_out)):
        inner_v = []
        outer_v = []
        for i in range(segs):
            ang = math.tau * i / segs
            ca, sa = math.cos(ang), math.sin(ang)
            inner_v.append(bm.verts.new((ri * ca, ri * sa, z)))
            outer_v.append(bm.verts.new((ro * ca, ro * sa, z)))
        rings.append((inner_v, outer_v))

    (bi, bo), (ti, to) = rings
    for i in range(segs):
        j = (i + 1) % segs
        # Bottom face (-Z normal)
        bm.faces.new((bi[j], bo[j], bo[i], bi[i]))
        # Top face (+Z normal)
        bm.faces.new((ti[i], to[i], to[j], ti[j]))
        # Outer wall
        bm.faces.new((bo[i], bo[j], to[j], to[i]))
        # Inner wall
        bm.faces.new((bi[j], bi[i], ti[i], ti[j]))

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    return finalize_mesh(mesh)


def create_arc_plate_mesh(name, r_in, r_out, ang_start, ang_end, z_bot, z_top, segs=48):
    """Structured quad sector/crescent plate spanning [ang_start, ang_end]."""
    bm = bmesh.new()
    bot_i, bot_o, top_i, top_o = [], [], [], []
    for k in range(segs + 1):
        ang = ang_start + (ang_end - ang_start) * (k / segs)
        ca, sa = math.cos(ang), math.sin(ang)
        bot_i.append(bm.verts.new((r_in * ca, r_in * sa, z_bot)))
        bot_o.append(bm.verts.new((r_out * ca, r_out * sa, z_bot)))
        top_i.append(bm.verts.new((r_in * ca, r_in * sa, z_top)))
        top_o.append(bm.verts.new((r_out * ca, r_out * sa, z_top)))

    for k in range(segs):
        bm.faces.new((bot_i[k + 1], bot_o[k + 1], bot_o[k], bot_i[k]))
        bm.faces.new((top_i[k], top_o[k], top_o[k + 1], top_i[k + 1]))
        bm.faces.new((bot_o[k], bot_o[k + 1], top_o[k + 1], top_o[k]))
        bm.faces.new((bot_i[k + 1], bot_i[k], top_i[k], top_i[k + 1]))

    # End caps
    bm.faces.new((bot_i[0], bot_o[0], top_o[0], top_i[0]))
    bm.faces.new((bot_o[-1], bot_i[-1], top_i[-1], top_o[-1]))

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    return finalize_mesh(mesh)


def involute_tooth_sector_points(num_teeth, module, pressure_deg=20.0):
    """
    Exact involute tooth boundary points for one pitch [-pi/N, +pi/N)
    with tooth crest centered at angle 0.
    """
    rp = 0.5 * module * num_teeth
    alpha = math.radians(pressure_deg)
    rb = rp * math.cos(alpha)
    ra = rp + 0.96 * module
    rf = max(0.15 * rp, rp - 1.22 * module)

    inv_alpha = math.tan(alpha) - alpha
    half_tooth_at_pitch = (math.pi / (2.0 * num_teeth)) * 0.94  # 6% backlash clearance
    half_base_angle = half_tooth_at_pitch + inv_alpha

    r_start = max(rb, rf)
    pts = []

    # Left root valley
    pitch_half = math.pi / num_teeth
    flank_samples = 5

    # Compute left & right involute flank
    right_flank = []
    for s in range(flank_samples):
        r = r_start + (ra - r_start) * (s / (flank_samples - 1))
        phi = math.acos(min(1.0, rb / r))
        inv_phi = math.tan(phi) - phi
        ang = half_base_angle - inv_phi
        if ang > 0.0005:
            right_flank.append((r, ang))

    root_ang = min(pitch_half * 0.84, right_flank[0][1] * 1.12)

    # Assemble strictly increasing angles from -pitch_half to +root_ang
    pts.append((rf, -pitch_half))
    pts.append((rf, -root_ang))
    for r, ang in right_flank:
        pts.append((r, -ang))
    pts.append((ra, 0.0))
    for r, ang in reversed(right_flank):
        pts.append((r, ang))
    pts.append((rf, root_ang))
    return pts, rf, rp, ra


def create_horological_gear_mesh(name, num_teeth, module, thickness=0.075, spokes=5):
    """
    Builds a true spoked involute horological wheel with:
    - 100% quad manifold outer toothed rim
    - Proud central hub collar with precision arbor bore
    - Tapered chamfered radial spokes
    """
    sector_pts, rf, rp, ra = involute_tooth_sector_points(num_teeth, module)
    r_rim_in = rf - 1.45 * module
    r_bore = max(0.045, 0.14 * rp)
    r_hub_out = max(r_bore + 0.07, 0.34 * rp)

    # Ensure small pinions stay clean even when compact
    has_spokes = (r_rim_in - r_hub_out) > (1.3 * module) and spokes >= 3
    if not has_spokes:
        r_rim_in = r_bore

    bm = bmesh.new()

    # 1. Outer Toothed Rim
    outline = []
    for k in range(num_teeth):
        base_ang = math.tau * k / num_teeth
        for r, local_ang in sector_pts:
            ang = base_ang + local_ang
            outline.append((r, ang))

    total = len(outline)
    hz = 0.5 * thickness
    bi, bo, ti, to = [], [], [], []
    for r_out, ang in outline:
        ca, sa = math.cos(ang), math.sin(ang)
        bi.append(bm.verts.new((r_rim_in * ca, r_rim_in * sa, -hz)))
        bo.append(bm.verts.new((r_out * ca, r_out * sa, -hz)))
        ti.append(bm.verts.new((r_rim_in * ca, r_rim_in * sa, +hz)))
        to.append(bm.verts.new((r_out * ca, r_out * sa, +hz)))

    for i in range(total):
        j = (i + 1) % total
        bm.faces.new((bi[j], bo[j], bo[i], bi[i]))
        bm.faces.new((ti[i], to[i], to[j], ti[j]))
        bm.faces.new((bo[i], bo[j], to[j], to[i]))
        bm.faces.new((bi[j], bi[i], ti[i], ti[j]))

    # 2. Central Hub & Tapered Spokes (if spoked wheel)
    if has_spokes:
        hub_segs = max(32, spokes * 8)
        hub_hz = 0.68 * thickness
        hbi, hbo, hti, hto = [], [], [], []
        for i in range(hub_segs):
            ang = math.tau * i / hub_segs
            ca, sa = math.cos(ang), math.sin(ang)
            hbi.append(bm.verts.new((r_bore * ca, r_bore * sa, -hub_hz)))
            hbo.append(bm.verts.new((r_hub_out * ca, r_hub_out * sa, -hub_hz)))
            hti.append(bm.verts.new((r_bore * ca, r_bore * sa, +hub_hz)))
            hto.append(bm.verts.new((r_hub_out * ca, r_hub_out * sa, +hub_hz)))
        for i in range(hub_segs):
            j = (i + 1) % hub_segs
            bm.faces.new((hbi[j], hbo[j], hbo[i], hbi[i]))
            bm.faces.new((hti[i], hto[i], hto[j], hti[j]))
            bm.faces.new((hbo[i], hbo[j], hto[j], hto[i]))
            bm.faces.new((hbi[j], hbi[i], hti[i], hti[j]))

        # Tapered radial spokes overlapped slightly into hub & rim
        sp_hz = 0.36 * thickness
        w_in = max(0.032, 0.24 * r_hub_out)
        w_out = max(0.024, 0.68 * w_in)
        r0 = r_hub_out - 0.015
        r1 = r_rim_in + 0.015
        for s in range(spokes):
            ang = math.tau * s / spokes
            rot = Matrix.Rotation(ang, 3, "Z")
            local_corners = [
                Vector((r0, -w_in, -sp_hz)),
                Vector((r1, -w_out, -sp_hz)),
                Vector((r1, +w_out, -sp_hz)),
                Vector((r0, +w_in, -sp_hz)),
                Vector((r0, -w_in, +sp_hz)),
                Vector((r1, -w_out, +sp_hz)),
                Vector((r1, +w_out, +sp_hz)),
                Vector((r0, +w_in, +sp_hz)),
            ]
            sv = [bm.verts.new(rot @ c) for c in local_corners]
            bm.faces.new((sv[3], sv[2], sv[1], sv[0]))
            bm.faces.new((sv[4], sv[5], sv[6], sv[7]))
            bm.faces.new((sv[0], sv[1], sv[5], sv[4]))
            bm.faces.new((sv[1], sv[2], sv[6], sv[5]))
            bm.faces.new((sv[2], sv[3], sv[7], sv[6]))
            bm.faces.new((sv[3], sv[0], sv[4], sv[7]))

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    return finalize_mesh(mesh, sharp_angle_deg=32.0), r_bore, rp, ra


def create_slotted_screw_mesh(name="Horological_Screw", r_head=0.052, h_head=0.028):
    """Domed watchmaker's slotted screw head with recessed center slot."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=r_head)
    slot_half = 0.22 * r_head
    slot_depth = 0.38 * r_head
    to_del = [v for v in bm.verts if v.co.z < -0.05 * r_head]
    bmesh.ops.delete(bm, geom=to_del, context="VERTS")
    for v in bm.verts:
        if v.co.z >= 0:
            v.co.z *= (h_head / r_head) * 1.35
            if abs(v.co.y) < slot_half and v.co.z > slot_depth * (h_head / r_head):
                v.co.z = slot_depth * (h_head / r_head)
    # Close flat underside
    boundary_edges = [e for e in bm.edges if e.is_boundary]
    if boundary_edges:
        bmesh.ops.ContextualCreate(bm, geom=boundary_edges) if hasattr(bmesh.ops, "ContextualCreate") else bmesh.ops.edgeloop_fill(bm, edges=boundary_edges)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    return finalize_mesh(mesh, sharp_angle_deg=28.0)


def create_brilliant_diamond_mesh(name="Singularity_Diamond", radius=0.23):
    """Multi-faceted brilliant-cut crown + pavilion crystal polyhedron."""
    bm = bmesh.new()
    segs = 16
    table_r = 0.56 * radius
    crown_z = 0.42 * radius
    girdle_z = 0.04 * radius
    girdle_b = -0.04 * radius
    culet_z = -0.78 * radius

    v_top_center = bm.verts.new((0.0, 0.0, crown_z))
    v_culet = bm.verts.new((0.0, 0.0, culet_z))

    table_v, star_v, gird_t, gird_b, pav_mid = [], [], [], [], []
    for i in range(segs):
        a0 = math.tau * i / segs
        a_half = math.tau * (i + 0.5) / segs
        table_v.append(bm.verts.new((table_r * math.cos(a0), table_r * math.sin(a0), crown_z)))
        star_v.append(bm.verts.new((0.80 * radius * math.cos(a_half), 0.80 * radius * math.sin(a_half), 0.24 * radius)))
        gird_t.append(bm.verts.new((radius * math.cos(a0), radius * math.sin(a0), girdle_z)))
        gird_b.append(bm.verts.new((radius * math.cos(a0), radius * math.sin(a0), girdle_b)))
        pav_mid.append(bm.verts.new((0.52 * radius * math.cos(a_half), 0.52 * radius * math.sin(a_half), -0.38 * radius)))

    for i in range(segs):
        j = (i + 1) % segs
        # Table octagon/16-gon triangles
        bm.faces.new((v_top_center, table_v[i], table_v[j]))
        # Star & bezel crown facets
        bm.faces.new((table_v[i], star_v[i], table_v[j]))
        bm.faces.new((table_v[i], gird_t[i], star_v[i]))
        bm.faces.new((star_v[i], gird_t[j], table_v[j]))
        bm.faces.new((star_v[i], gird_t[i], gird_t[j]))
        # Girdle
        bm.faces.new((gird_t[i], gird_b[i], gird_b[j], gird_t[j]))
        # Pavilion facets
        bm.faces.new((gird_b[i], pav_mid[i], gird_b[j]))
        bm.faces.new((gird_b[i], v_culet, pav_mid[i]))
        bm.faces.new((pav_mid[i], v_culet, gird_b[j]))

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    # Flat-faceted crisp crystal reflections!
    for poly in mesh.polygons:
        poly.use_smooth = False
    mesh.update()
    return mesh


def build_pivot_jewel_assembly(col, mats, screw_mesh, loc_xy, z_base, z_top, tag):
    """Creates turned steel arbor + gold chaton + crimson synthetic ruby bearing."""
    x, y = loc_xy
    # Turned arbor axle
    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=24,
        radius1=0.036,
        radius2=0.036,
        depth=(z_top - z_base) + 0.08,
    )
    arbor_mesh = bpy.data.meshes.new(f"Arbor_{tag}")
    bm.to_mesh(arbor_mesh)
    bm.free()
    finalize_mesh(arbor_mesh)
    arbor = bpy.data.objects.new(f"Arbor_{tag}", arbor_mesh)
    arbor.location = (x, y, 0.5 * (z_base + z_top))
    arbor.data.materials.append(mats["rhodium"])
    link_obj(arbor, col)

    # Gold chaton collar at top
    chaton_m = create_annulus_mesh(
        f"Chaton_{tag}", 0.072, 0.118, z_top - 0.015, z_top + 0.024, segs=36, r_top_in=0.076, r_top_out=0.106
    )
    chaton = bpy.data.objects.new(f"Chaton_{tag}", chaton_m)
    chaton.location = (x, y, 0.0)
    chaton.data.materials.append(mats["yellow_gold"])
    link_obj(chaton, col)

    # Synthetic Corundum Ruby doughnut jewel
    ruby_m = create_annulus_mesh(
        f"Ruby_{tag}", 0.037, 0.074, z_top - 0.010, z_top + 0.028, segs=32, r_top_in=0.037, r_top_out=0.068
    )
    ruby = bpy.data.objects.new(f"Ruby_{tag}", ruby_m)
    ruby.location = (x, y, 0.0)
    ruby.data.materials.append(mats["ruby"])
    link_obj(ruby, col)


# ==============================================================================
# 5. BLENDER 4.2 GEOMETRY NODES: STEREOGRAPHIC HOPF FIBRATION (S^3 -> R^3)
# ==============================================================================

def build_hopf_fibration_geonodes(hopf_mat):
    """
    Constructs a live Blender 4.2 Geometry Nodes tree using a Repeat Zone to
    project K topologically linked Villarceau circles of the S^3 -> S^2 Hopf
    Fibration stereographically into R^3, plus traveling plasma micro-sparks!
    """
    ng = bpy.data.node_groups.new("GN_Hopf_Fibration_Core", "GeometryNodeTree")

    # Clean modifier interface sliders for interactive tweaking in Blender UI
    ng.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

    s_cnt = ng.interface.new_socket(name="Fiber Count", in_out="INPUT", socket_type="NodeSocketInt")
    s_cnt.default_value = 32
    s_cnt.min_value = 4
    s_cnt.max_value = 128

    s_eta = ng.interface.new_socket(name="Hopf Latitude", in_out="INPUT", socket_type="NodeSocketFloat")
    s_eta.default_value = 0.72
    s_eta.min_value = 0.15
    s_eta.max_value = 1.35

    s_scale = ng.interface.new_socket(name="Core Scale", in_out="INPUT", socket_type="NodeSocketFloat")
    s_scale.default_value = 0.80
    s_scale.min_value = 0.2
    s_scale.max_value = 3.0

    s_rad = ng.interface.new_socket(name="Filament Radius", in_out="INPUT", socket_type="NodeSocketFloat")
    s_rad.default_value = 0.0095
    s_rad.min_value = 0.002
    s_rad.max_value = 0.08

    s_phase = ng.interface.new_socket(name="Quantum Phase", in_out="INPUT", socket_type="NodeSocketFloat")
    s_phase.default_value = 0.0

    s_spark = ng.interface.new_socket(name="Spark Radius", in_out="INPUT", socket_type="NodeSocketFloat")
    s_spark.default_value = 0.017
    s_spark.min_value = 0.0
    s_spark.max_value = 0.1

    nodes = ng.nodes
    links = ng.links

    def N(bl_id, x, y, label=None):
        node = nodes.new(bl_id)
        node.location = (x, y)
        if label:
            node.label = label
        return node

    def M(op, x, y, v0=None, v1=None, label=None):
        node = N("ShaderNodeMath", x, y, label=label)
        node.operation = op
        if v0 is not None:
            node.inputs[0].default_value = v0
        if v1 is not None:
            node.inputs[1].default_value = v1
        return node

    g_in = N("NodeGroupInput", -1650, 120)
    g_out = N("NodeGroupOutput", 1850, 120)

    # Pre-loop math: cos(eta), sin(eta), norm_scale = Core_Scale * (1 - sin(eta))
    cos_eta = M("COSINE", -1380, 320, label="cos(eta)")
    sin_eta = M("SINE", -1380, 180, label="sin(eta)")
    links.new(g_in.outputs["Hopf Latitude"], cos_eta.inputs[0])
    links.new(g_in.outputs["Hopf Latitude"], sin_eta.inputs[0])

    one_minus_sin = M("SUBTRACT", -1180, 220, v0=1.0, label="1 - sin(eta)")
    links.new(sin_eta.outputs["Value"], one_minus_sin.inputs[1])

    norm_scale = M("MULTIPLY", -980, 220, label="Norm Scale")
    links.new(g_in.outputs["Core Scale"], norm_scale.inputs[0])
    links.new(one_minus_sin.outputs["Value"], norm_scale.inputs[1])

    # Base unit circle in XY plane -> psi = atan2(Y, X)
    base_circle = N("GeometryNodeCurvePrimitiveCircle", -1380, -140, label="S1 Fiber Template")
    base_circle.inputs["Resolution"].default_value = 96
    base_circle.inputs["Radius"].default_value = 1.0

    # Profile circle for Curve to Mesh & Icosphere for traveling sparks
    prof_circle = N("GeometryNodeCurvePrimitiveCircle", 860, -240, label="Filament Profile")
    prof_circle.inputs["Resolution"].default_value = 10
    links.new(g_in.outputs["Filament Radius"], prof_circle.inputs["Radius"])

    spark_ico = N("GeometryNodeMeshIcoSphere", 420, -480, label="Plasma Spark Mesh")
    spark_ico.inputs["Subdivisions"].default_value = 2
    links.new(g_in.outputs["Spark Radius"], spark_ico.inputs["Radius"])

    # Repeat Zone: Accumulatesprojected Villarceau curves + spark mesh instances
    rep_in = N("GeometryNodeRepeatInput", -740, 40)
    rep_out = N("GeometryNodeRepeatOutput", 1180, 40)
    rep_in.pair_with_output(rep_out)
    rep_out.repeat_items.new("INT", "Index")
    rep_out.repeat_items.new("GEOMETRY", "Sparks")

    links.new(g_in.outputs["Fiber Count"], rep_in.inputs["Iterations"])
    rep_in.inputs["Index"].default_value = 0

    # Inside Repeat Zone: ratio = Index / Fiber Count, phi_k = 2*pi*ratio + Quantum Phase
    idx_div = M("DIVIDE", -520, -140, label="k / K")
    links.new(rep_in.outputs["Index"], idx_div.inputs[0])
    links.new(g_in.outputs["Fiber Count"], idx_div.inputs[1])

    phi_base = M("MULTIPLY", -340, -140, v1=math.tau, label="2*pi*k/K")
    links.new(idx_div.outputs["Value"], phi_base.inputs[0])

    phi_k = M("ADD", -160, -140, label="phi_k")
    links.new(phi_base.outputs["Value"], phi_k.inputs[0])
    links.new(g_in.outputs["Quantum Phase"], phi_k.inputs[1])

    # Evaluate psi = atan2(pos.y, pos.x) on the 96 circle control points
    pos_in = N("GeometryNodeInputPosition", -540, 260)
    sep_xy = N("ShaderNodeSeparateXYZ", -360, 260)
    links.new(pos_in.outputs["Position"], sep_xy.inputs["Vector"])

    psi = M("ARCTAN2", -180, 260, label="psi")
    links.new(sep_xy.outputs["Y"], psi.inputs[0])
    links.new(sep_xy.outputs["X"], psi.inputs[1])

    # Twist angle along fiber: psi_plus_phi = psi + phi_k
    psi_phi = M("ADD", 0, 160, label="psi + phi_k")
    links.new(psi.outputs["Value"], psi_phi.inputs[0])
    links.new(phi_k.outputs["Value"], psi_phi.inputs[1])

    cos_psi = M("COSINE", 0, 340, label="cos(psi)")
    sin_psi = M("SINE", 0, 250, label="sin(psi)")
    links.new(psi.outputs["Value"], cos_psi.inputs[0])
    links.new(psi.outputs["Value"], sin_psi.inputs[0])

    cos_pp = M("COSINE", 170, 190, label="cos(psi+phi)")
    sin_pp = M("SINE", 170, 90, label="sin(psi+phi)")
    links.new(psi_phi.outputs["Value"], cos_pp.inputs[0])
    links.new(psi_phi.outputs["Value"], sin_pp.inputs[0])

    # 4D coordinates on S^3: x1, x2, x3, x4
    x1 = M("MULTIPLY", 350, 360, label="x1")
    links.new(cos_eta.outputs["Value"], x1.inputs[0])
    links.new(cos_psi.outputs["Value"], x1.inputs[1])

    x2 = M("MULTIPLY", 350, 260, label="x2")
    links.new(cos_eta.outputs["Value"], x2.inputs[0])
    links.new(sin_psi.outputs["Value"], x2.inputs[1])

    x3 = M("MULTIPLY", 350, 160, label="x3")
    links.new(sin_eta.outputs["Value"], x3.inputs[0])
    links.new(cos_pp.outputs["Value"], x3.inputs[1])

    x4 = M("MULTIPLY", 350, 60, label="x4")
    links.new(sin_eta.outputs["Value"], x4.inputs[0])
    links.new(sin_pp.outputs["Value"], x4.inputs[1])

    # Stereographic factor = norm_scale / (1 - x4)
    denom = M("SUBTRACT", 520, 60, v0=1.0, label="1 - x4")
    links.new(x4.outputs["Value"], denom.inputs[1])

    stereo_fac = M("DIVIDE", 680, 120, label="Stereo Scale")
    links.new(norm_scale.outputs["Value"], stereo_fac.inputs[0])
    links.new(denom.outputs["Value"], stereo_fac.inputs[1])

    comb_3d = N("ShaderNodeCombineXYZ", 540, 260)
    links.new(x1.outputs["Value"], comb_3d.inputs["X"])
    links.new(x2.outputs["Value"], comb_3d.inputs["Y"])
    links.new(x3.outputs["Value"], comb_3d.inputs["Z"])

    vec_scale = N("ShaderNodeVectorMath", 720, 280)
    vec_scale.operation = "SCALE"
    links.new(comb_3d.outputs["Vector"], vec_scale.inputs[0])
    links.new(stereo_fac.outputs["Value"], vec_scale.inputs["Scale"])

    set_pos = N("GeometryNodeSetPosition", 560, -80, label="Project Fiber to R3")
    links.new(base_circle.outputs["Curve"], set_pos.inputs["Geometry"])
    links.new(vec_scale.outputs["Vector"], set_pos.inputs["Position"])

    # Store fiber_ratio and traveling arc_phase attributes for the shader
    store_f = N("GeometryNodeStoreNamedAttribute", 740, -60, label="Store fiber_ratio")
    store_f.data_type = "FLOAT"
    store_f.domain = "POINT"
    store_f.inputs["Name"].default_value = "fiber_ratio"
    links.new(set_pos.outputs["Geometry"], store_f.inputs["Geometry"])
    links.new(idx_div.outputs["Value"], store_f.inputs["Value"])

    # arc_phase = fract(psi / (2*pi) - Quantum_Phase / pi)
    psi_norm = M("DIVIDE", 360, -140, v1=math.tau)
    links.new(psi.outputs["Value"], psi_norm.inputs[0])
    ph_shift = M("DIVIDE", 360, -240, v1=math.pi)
    links.new(g_in.outputs["Quantum Phase"], ph_shift.inputs[0])
    arc_raw = M("SUBTRACT", 520, -200)
    links.new(psi_norm.outputs["Value"], arc_raw.inputs[0])
    links.new(ph_shift.outputs["Value"], arc_raw.inputs[1])
    arc_frac = M("FRACT", 660, -200)
    links.new(arc_raw.outputs["Value"], arc_frac.inputs[0])

    store_arc = N("GeometryNodeStoreNamedAttribute", 880, -40, label="Store arc_phase")
    store_arc.data_type = "FLOAT"
    store_arc.domain = "POINT"
    store_arc.inputs["Name"].default_value = "arc_phase"
    links.new(store_f.outputs["Geometry"], store_arc.inputs["Geometry"])
    links.new(arc_frac.outputs["Value"], store_arc.inputs["Value"])

    # Sample a glowing plasma micro-spark sliding smoothly along every 2nd fiber!
    gold_step = M("MULTIPLY", 360, -360, v1=0.6180339887)
    links.new(rep_in.outputs["Index"], gold_step.inputs[0])
    spark_t_raw = M("ADD", 520, -360)
    links.new(gold_step.outputs["Value"], spark_t_raw.inputs[0])
    links.new(ph_shift.outputs["Value"], spark_t_raw.inputs[1])
    spark_fac = M("FRACT", 680, -360, label="Spark Curve Factor")
    links.new(spark_t_raw.outputs["Value"], spark_fac.inputs[0])

    samp_curve = N("GeometryNodeSampleCurve", 840, -360, label="Sample Spark Pos")
    samp_curve.mode = "FACTOR"
    links.new(store_arc.outputs["Geometry"], samp_curve.inputs["Curves"])
    links.new(spark_fac.outputs["Value"], samp_curve.inputs["Factor"])

    spark_move = N("GeometryNodeSetPosition", 980, -440, label="Place Spark")
    links.new(spark_ico.outputs["Mesh"], spark_move.inputs["Geometry"])
    links.new(samp_curve.outputs["Position"], spark_move.inputs["Position"])

    store_sp_f = N("GeometryNodeStoreNamedAttribute", 1040, -300)
    store_sp_f.data_type = "FLOAT"
    store_sp_f.domain = "POINT"
    store_sp_f.inputs["Name"].default_value = "fiber_ratio"
    links.new(spark_move.outputs["Geometry"], store_sp_f.inputs["Geometry"])
    links.new(idx_div.outputs["Value"], store_sp_f.inputs["Value"])

    join_curves = N("GeometryNodeJoinGeometry", 1020, 60)
    links.new(rep_in.outputs["Geometry"], join_curves.inputs["Geometry"])
    links.new(store_arc.outputs["Geometry"], join_curves.inputs["Geometry"])

    join_sparks = N("GeometryNodeJoinGeometry", 1040, -140)
    links.new(rep_in.outputs["Sparks"], join_sparks.inputs["Geometry"])
    links.new(store_sp_f.outputs["Geometry"], join_sparks.inputs["Geometry"])

    inc_idx = M("ADD", 980, 200, v1=1.0, label="k + 1")
    links.new(rep_in.outputs["Index"], inc_idx.inputs[0])

    links.new(join_curves.outputs["Geometry"], rep_out.inputs["Geometry"])
    links.new(inc_idx.outputs["Value"], rep_out.inputs["Index"])
    links.new(join_sparks.outputs["Geometry"], rep_out.inputs["Sparks"])

    # Post-loop: Sweep all K Villarceau fibers into smooth tubes, tag sparks, join & assign shader!
    c2m = N("GeometryNodeCurveToMesh", 1360, 120, label="Sweep Hopf Tubes")
    links.new(rep_out.outputs["Geometry"], c2m.inputs["Curve"])
    links.new(prof_circle.outputs["Curve"], c2m.inputs["Profile Curve"])

    tag_tube = N("GeometryNodeStoreNamedAttribute", 1500, 140)
    tag_tube.data_type = "FLOAT"
    tag_tube.domain = "POINT"
    tag_tube.inputs["Name"].default_value = "is_spark"
    tag_tube.inputs["Value"].default_value = 0.0
    links.new(c2m.outputs["Mesh"], tag_tube.inputs["Geometry"])

    tag_spark = N("GeometryNodeStoreNamedAttribute", 1380, -120)
    tag_spark.data_type = "FLOAT"
    tag_spark.domain = "POINT"
    tag_spark.inputs["Name"].default_value = "is_spark"
    tag_spark.inputs["Value"].default_value = 1.0
    links.new(rep_out.outputs["Sparks"], tag_spark.inputs["Geometry"])

    final_join = N("GeometryNodeJoinGeometry", 1620, 60)
    links.new(tag_tube.outputs["Geometry"], final_join.inputs["Geometry"])
    links.new(tag_spark.outputs["Geometry"], final_join.inputs["Geometry"])

    smooth = N("GeometryNodeSetShadeSmooth", 1710, 180)
    links.new(final_join.outputs["Geometry"], smooth.inputs["Geometry"])

    set_mat = N("GeometryNodeSetMaterial", 1760, 40)
    set_mat.inputs["Material"].default_value = hopf_mat
    links.new(smooth.outputs["Geometry"], set_mat.inputs["Geometry"])
    links.new(set_mat.outputs["Geometry"], g_out.inputs["Geometry"])

    return ng, s_phase.identifier


def build_atmospheric_motes_geonodes(mote_mat):
    """Geometry Nodes floating micro-dust bokeh particles orbiting gently above the dial."""
    ng = bpy.data.node_groups.new("GN_Atmospheric_Bokeh_Motes", "GeometryNodeTree")
    ng.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

    s_cnt = ng.interface.new_socket(name="Mote Count", in_out="INPUT", socket_type="NodeSocketInt")
    s_cnt.default_value = 110
    s_phase = ng.interface.new_socket(name="Orbit Phase", in_out="INPUT", socket_type="NodeSocketFloat")
    s_phase.default_value = 0.0

    nodes = ng.nodes
    links = ng.links

    g_in = nodes.new("NodeGroupInput")
    g_in.location = (-900, 0)
    g_out = nodes.new("NodeGroupOutput")
    g_out.location = (700, 0)

    pts = nodes.new("GeometryNodePoints")
    pts.location = (-680, 80)
    links.new(g_in.outputs["Mote Count"], pts.inputs["Count"])

    idx = nodes.new("GeometryNodeInputIndex")
    idx.location = (-720, -140)

    # Golden-angle phyllotaxis spiral in cylindrical coords + harmonic Z float
    ga = nodes.new("ShaderNodeMath")
    ga.operation = "MULTIPLY"
    ga.inputs[1].default_value = 2.39996323
    ga.location = (-500, -80)
    links.new(idx.outputs["Index"], ga.inputs[0])

    ang = nodes.new("ShaderNodeMath")
    ang.operation = "ADD"
    ang.location = (-320, -80)
    links.new(ga.outputs["Value"], ang.inputs[0])
    links.new(g_in.outputs["Orbit Phase"], ang.inputs[1])

    # Radius between 0.75 and 5.2 (float sockets on RandomValue are inputs[2], inputs[3], outputs[1])
    rad_hash = nodes.new("FunctionNodeRandomValue")
    rad_hash.data_type = "FLOAT"
    rad_hash.inputs[2].default_value = 0.75
    rad_hash.inputs[3].default_value = 5.2
    rad_hash.inputs["Seed"].default_value = 42
    rad_hash.location = (-500, -260)

    z_hash = nodes.new("FunctionNodeRandomValue")
    z_hash.data_type = "FLOAT"
    z_hash.inputs[2].default_value = 0.25
    z_hash.inputs[3].default_value = 2.65
    z_hash.inputs["Seed"].default_value = 108
    z_hash.location = (-500, -460)

    scale_hash = nodes.new("FunctionNodeRandomValue")
    scale_hash.data_type = "FLOAT"
    scale_hash.inputs[2].default_value = 0.004
    scale_hash.inputs[3].default_value = 0.013
    scale_hash.inputs["Seed"].default_value = 777
    scale_hash.location = (-100, -340)

    ca = nodes.new("ShaderNodeMath")
    ca.operation = "COSINE"
    ca.location = (-140, -40)
    sa = nodes.new("ShaderNodeMath")
    sa.operation = "SINE"
    sa.location = (-140, -140)
    links.new(ang.outputs["Value"], ca.inputs[0])
    links.new(ang.outputs["Value"], sa.inputs[0])

    px = nodes.new("ShaderNodeMath")
    px.operation = "MULTIPLY"
    px.location = (40, -40)
    py = nodes.new("ShaderNodeMath")
    py.operation = "MULTIPLY"
    py.location = (40, -140)
    links.new(ca.outputs["Value"], px.inputs[0])
    links.new(rad_hash.outputs[1], px.inputs[1])
    links.new(sa.outputs["Value"], py.inputs[0])
    links.new(rad_hash.outputs[1], py.inputs[1])

    comb = nodes.new("ShaderNodeCombineXYZ")
    comb.location = (210, -120)
    links.new(px.outputs["Value"], comb.inputs["X"])
    links.new(py.outputs["Value"], comb.inputs["Y"])
    links.new(z_hash.outputs[1], comb.inputs["Z"])

    pts.inputs["Radius"].default_value = 0.01
    links.new(comb.outputs["Vector"], pts.inputs["Position"])

    ico = nodes.new("GeometryNodeMeshIcoSphere")
    ico.inputs["Radius"].default_value = 1.0
    ico.inputs["Subdivisions"].default_value = 1
    ico.location = (80, 160)

    inst = nodes.new("GeometryNodeInstanceOnPoints")
    inst.location = (380, 60)
    links.new(pts.outputs["Points"], inst.inputs["Points"])
    links.new(ico.outputs["Mesh"], inst.inputs["Instance"])
    links.new(scale_hash.outputs[1], inst.inputs["Scale"])

    set_m = nodes.new("GeometryNodeSetMaterial")
    set_m.location = (550, 60)
    set_m.inputs["Material"].default_value = mote_mat
    links.new(inst.outputs["Instances"], set_m.inputs["Geometry"])
    links.new(set_m.outputs["Geometry"], g_out.inputs["Geometry"])

    return ng, s_phase.identifier


# ==============================================================================
# 6. CHRONOMETER CASE, DIAL, PHASE-LOCKED GEAR TRAINS & 3-AXIS TOURBILLON
# ==============================================================================

def build_workbench_and_blueprint(col, mats, screw_mesh):
    """Dark obsidian workbench, inlaid gold horological blueprint circles, and macro props."""
    z_bench = -1.28
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= 52.0
        v.co.y *= 52.0
        v.co.z = z_bench if v.co.z > 0 else (z_bench - 0.85)
    wb_mesh = bpy.data.meshes.new("Obsidian_Workbench_Mesh")
    bm.to_mesh(wb_mesh)
    bm.free()
    finalize_mesh(wb_mesh)
    wb = bpy.data.objects.new("Obsidian_Workbench", wb_mesh)
    wb.data.materials.append(mats["workbench"])
    link_obj(wb, col)

    # Flush inlaid Brass Technical Blueprint Drafting Rings & Vernier Ticks
    for idx, r_line in enumerate((5.15, 5.32, 6.45, 6.55, 7.80)):
        ring_m = create_annulus_mesh(
            f"Blueprint_Circle_{idx}", r_line - 0.012, r_line + 0.012, z_bench - 0.001, z_bench + 0.0035, segs=160
        )
        ro = bpy.data.objects.new(f"Blueprint_Circle_{idx}", ring_m)
        ro.data.materials.append(mats["brass"])
        link_obj(ro, col)

    # 72 Radial Blueprint Degree Ticks between R=5.32 and R=5.72
    bm_ticks = bmesh.new()
    for i in range(72):
        ang = math.tau * i / 72
        r0 = 5.32
        r1 = 5.72 if (i % 6 == 0) else (5.52 if i % 2 == 0 else 5.43)
        hw = 0.011 if (i % 6 == 0) else 0.0055
        rot = Matrix.Rotation(ang, 3, "Z")
        corners = [
            Vector((r0, -hw, z_bench)),
            Vector((r1, -hw, z_bench)),
            Vector((r1, +hw, z_bench)),
            Vector((r0, +hw, z_bench)),
            Vector((r0, -hw, z_bench + 0.004)),
            Vector((r1, -hw, z_bench + 0.004)),
            Vector((r1, +hw, z_bench + 0.004)),
            Vector((r0, +hw, z_bench + 0.004)),
        ]
        cv = [bm_ticks.verts.new(rot @ c) for c in corners]
        bm_ticks.faces.new((cv[4], cv[5], cv[6], cv[7]))
        bm_ticks.faces.new((cv[0], cv[1], cv[5], cv[4]))
        bm_ticks.faces.new((cv[1], cv[2], cv[6], cv[5]))
        bm_ticks.faces.new((cv[2], cv[3], cv[7], cv[6]))
        bm_ticks.faces.new((cv[3], cv[0], cv[4], cv[7]))
    bmesh.ops.recalc_face_normals(bm_ticks, faces=bm_ticks.faces)
    tm = bpy.data.meshes.new("Blueprint_Vernier_Ticks")
    bm_ticks.to_mesh(tm)
    bm_ticks.free()
    finalize_mesh(tm)
    tick_obj = bpy.data.objects.new("Blueprint_Vernier_Ticks", tm)
    tick_obj.data.materials.append(mats["brass"])
    link_obj(tick_obj, col)

    # Foreground & Background Bokeh Horological Props resting on the bench!
    prop_gears = [
        ("Bench_SpareGear_01", 24, 0.045, (5.65, -2.65), 0.35, "brass"),
        ("Bench_SpareGear_02", 18, 0.042, (-5.45, 2.85), 0.82, "rose_gold"),
        ("Bench_SpareGear_03", 20, 0.038, (4.35, -4.45), 0.15, "rhodium"),
    ]
    for gname, nt_cnt, mod, (px, py), rot_z, mkey in prop_gears:
        gm, _, _, _ = create_horological_gear_mesh(gname, nt_cnt, mod, thickness=0.065, spokes=4)
        go = bpy.data.objects.new(gname, gm)
        go.location = (px, py, z_bench + 0.033)
        go.rotation_euler = (0.0, 0.0, rot_z)
        go.data.materials.append(mats[mkey])
        add_bevel_mod(go, width=0.0025, segments=2)
        link_obj(go, col)

    # Loose ruby chaton jewels & blued screws on the bench
    for idx, (jx, jy) in enumerate(((5.05, -3.55), (-4.95, -3.20))):
        cm = create_annulus_mesh(f"Bench_Chaton_{idx}", 0.075, 0.13, z_bench, z_bench + 0.05, segs=32)
        co = bpy.data.objects.new(f"Bench_Chaton_{idx}", cm)
        co.location = (jx, jy, 0.0)
        co.data.materials.append(mats["yellow_gold"])
        link_obj(co, col)
        rm = create_annulus_mesh(f"Bench_Ruby_{idx}", 0.035, 0.078, z_bench + 0.005, z_bench + 0.058, segs=32)
        ru = bpy.data.objects.new(f"Bench_Ruby_{idx}", rm)
        ru.location = (jx, jy, 0.0)
        ru.data.materials.append(mats["ruby"])
        link_obj(ru, col)

    for idx, (sx, sy, srot) in enumerate(((5.95, -1.85, 0.6), (5.25, -4.05, 1.4), (-5.80, 1.90, 2.2))):
        so = bpy.data.objects.new(f"Bench_BluedScrew_{idx}", screw_mesh)
        so.location = (sx, sy, z_bench + 0.002)
        so.scale = (1.35, 1.35, 1.35)
        so.rotation_euler = (0.0, 0.0, srot)
        so.data.materials.append(mats["blued_steel"])
        link_obj(so, col)


def build_chronometer_case_and_dial(col, mats, screw_mesh):
    """Multi-stepped titanium & coin-edge rose-gold case, lugs, crown, deep terraced amphitheater, and guilloche dial."""
    # 1. Stepped Titanium Caseback (-1.28 to -0.88)
    cb_m = create_annulus_mesh("Caseback_Titanium", 1.72, 4.24, -1.28, -0.88, segs=128, r_top_in=1.72, r_top_out=4.56)
    cb = bpy.data.objects.new("Caseback_Titanium", cb_m)
    cb.data.materials.append(mats["titanium"])
    add_bevel_mod(cb, width=0.012, segments=2)
    link_obj(cb, col)

    # 2. Coin-Edge Fluted 18K Rose-Gold Mid-Case Band (-0.88 to +0.18)
    flute_segs = 288
    bm = bmesh.new()
    r_in = 4.10
    bot_i, bot_o, top_i, top_o = [], [], [], []
    for i in range(flute_segs):
        ang = math.tau * i / flute_segs
        flute_r = 4.60 + 0.036 * math.cos(144.0 * ang)
        ca, sa = math.cos(ang), math.sin(ang)
        bot_i.append(bm.verts.new((r_in * ca, r_in * sa, -0.88)))
        bot_o.append(bm.verts.new((flute_r * ca, flute_r * sa, -0.88)))
        top_i.append(bm.verts.new((r_in * ca, r_in * sa, +0.18)))
        top_o.append(bm.verts.new((flute_r * ca, flute_r * sa, +0.18)))
    for i in range(flute_segs):
        j = (i + 1) % flute_segs
        bm.faces.new((bot_i[j], bot_o[j], bot_o[i], bot_i[i]))
        bm.faces.new((top_i[i], top_o[i], top_o[j], top_i[j]))
        bm.faces.new((bot_o[i], bot_o[j], top_o[j], top_o[i]))
        bm.faces.new((bot_i[j], bot_i[i], top_i[i], top_i[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mid_m = bpy.data.meshes.new("Case_CoinEdge_Band")
    bm.to_mesh(mid_m)
    bm.free()
    finalize_mesh(mid_m, sharp_angle_deg=38.0)
    mid_obj = bpy.data.objects.new("Case_CoinEdge_Band", mid_m)
    mid_obj.data.materials.append(mats["rose_gold"])
    link_obj(mid_obj, col)

    # 3. Chamfered Upper Titanium Bezel (+0.18 to +0.44) + 12 Blued Bezel Screws
    bez_m = create_annulus_mesh(
        "Case_Upper_Bezel", 4.06, 4.62, 0.18, 0.44, segs=144, r_top_in=4.10, r_top_out=4.46
    )
    bez = bpy.data.objects.new("Case_Upper_Bezel", bez_m)
    bez.data.materials.append(mats["titanium"])
    add_bevel_mod(bez, width=0.015, segments=3)
    link_obj(bez, col)

    # Inner Gold Rehaut Lip
    reh_m = create_annulus_mesh("Case_Gold_Rehaut", 4.02, 4.10, 0.14, 0.45, segs=144, r_top_in=4.05, r_top_out=4.11)
    reh = bpy.data.objects.new("Case_Gold_Rehaut", reh_m)
    reh.data.materials.append(mats["rose_gold"])
    link_obj(reh, col)

    for k in range(12):
        ang = math.tau * (k + 0.5) / 12.0
        r_sc = 4.28
        sc = bpy.data.objects.new(f"Bezel_BluedScrew_{k:02d}", screw_mesh)
        sc.location = (r_sc * math.cos(ang), r_sc * math.sin(ang), 0.442)
        sc.scale = (1.35, 1.35, 1.35)
        sc.rotation_euler = (0.0, 0.0, ang + 0.4)
        sc.data.materials.append(mats["blued_steel"])
        link_obj(sc, col)

    # 4. 3H Knurled Chronometer Winding Crown with Sapphire Cabochon
    bm_cr = bmesh.new()
    cr_segs = 96
    c_bot, c_top = [], []
    for i in range(cr_segs):
        ang = math.tau * i / cr_segs
        rc = 0.46 + 0.030 * math.cos(32.0 * ang)
        c_bot.append(bm_cr.verts.new((4.60, rc * math.cos(ang), -0.32 + rc * math.sin(ang))))
        c_top.append(bm_cr.verts.new((5.10, 0.92 * rc * math.cos(ang), -0.32 + 0.92 * rc * math.sin(ang))))
    for i in range(cr_segs):
        j = (i + 1) % cr_segs
        bm_cr.faces.new((c_bot[i], c_bot[j], c_top[j], c_top[i]))
    bm_cr.faces.new(list(reversed(c_bot)))
    bm_cr.faces.new(c_top)
    bmesh.ops.recalc_face_normals(bm_cr, faces=bm_cr.faces)
    cr_m = bpy.data.meshes.new("Winding_Crown")
    bm_cr.to_mesh(cr_m)
    bm_cr.free()
    finalize_mesh(cr_m)
    crown = bpy.data.objects.new("Winding_Crown", cr_m)
    crown.data.materials.append(mats["rose_gold"])
    link_obj(crown, col)

    bm_cab = bmesh.new()
    bmesh.ops.create_uvsphere(bm_cab, u_segments=32, v_segments=16, radius=0.27)
    cab_m = bpy.data.meshes.new("Crown_Cabochon")
    bm_cab.to_mesh(cab_m)
    bm_cab.free()
    finalize_mesh(cab_m)
    cab = bpy.data.objects.new("Crown_Cabochon", cab_m)
    cab.location = (5.08, 0.0, -0.32)
    cab.scale = (0.45, 1.0, 1.0)
    cab.data.materials.append(mats["blued_steel"])
    link_obj(cab, col)

    # 5. Four Sculpted Architectural Lugs (curving down cleanly to Z=-1.24)
    for idx, deg in enumerate((62.0, 118.0, -62.0, -118.0)):
        ang = math.radians(deg)
        lug_m = create_arc_plate_mesh(f"Chronometer_Lug_{idx}", 4.48, 5.24, ang - 0.085, ang + 0.085, -1.24, 0.24, segs=12)
        lug = bpy.data.objects.new(f"Chronometer_Lug_{idx}", lug_m)
        lug.data.materials.append(mats["titanium"])
        add_bevel_mod(lug, width=0.020, segments=3)
        link_obj(lug, col)

    # 6. Movement Baseplate (R=1.96..4.10 at Z=-0.25) & Deep Terraced Guilloche Amphitheater Bowl (down to Z=-1.20!)
    base_m = create_annulus_mesh("Movement_Perlage_Baseplate", 1.96, 4.10, -0.92, -0.24, segs=128)
    base_o = bpy.data.objects.new("Movement_Perlage_Baseplate", base_m)
    base_o.data.materials.append(mats["gunmetal"])
    link_obj(base_o, col)

    # Deep Sunken Amphitheater Floor at Z = -1.20 (100% clearance for all 3 gimbal axes!)
    well_m = create_annulus_mesh("Amphitheater_Guilloche_Floor", 0.002, 1.76, -1.28, -1.20, segs=128)
    well_o = bpy.data.objects.new("Amphitheater_Guilloche_Floor", well_m)
    well_o.data.materials.append(mats["guilloche"])
    link_obj(well_o, col)

    # Concentric Gold Astrolabe Rosette Rings on the deep amphitheater floor
    for k, rr in enumerate((0.42, 0.86, 1.30, 1.68)):
        rm = create_annulus_mesh(f"Amphitheater_InlayRing_{k}", rr - 0.015, rr + 0.015, -1.202, -1.186, segs=96)
        ro = bpy.data.objects.new(f"Amphitheater_InlayRing_{k}", rm)
        ro.data.materials.append(mats["rose_gold"])
        link_obj(ro, col)

    # Terraced Amphitheater Steps rising from Z=-1.20 to Z=+0.20 (Colosseum-style horological well!)
    terraces = [
        ("Amphitheater_Step_01", 1.73, 1.86, -1.20, -0.86, "rose_gold"),
        ("Amphitheater_Step_02", 1.83, 1.96, -0.86, -0.54, "guilloche"),
        ("Amphitheater_Step_03", 1.91, 2.04, -0.54, -0.22, "titanium"),
        ("Amphitheater_Bevel_Wall", 1.93, 2.08, -0.22, +0.20, "rose_gold"),
    ]
    for tname, ri, ro_r, zb, zt, mkey in terraces:
        tm_s = create_annulus_mesh(tname, ri, ro_r, zb, zt, segs=128)
        to_s = bpy.data.objects.new(tname, tm_s)
        to_s.data.materials.append(mats[mkey])
        add_bevel_mod(to_s, width=0.007, segments=2)
        link_obj(to_s, col)

    # 7. Openworked Guilloche Crescent Dial Plates (North & South sectors framing the East/West Skeleton Windows!)
    for tag, a0, a1 in (("North", 46.0, 102.0), ("South", -134.0, -78.0)):
        pm = create_arc_plate_mesh(
            f"Guilloche_Dial_Sector_{tag}",
            2.06,
            3.86,
            math.radians(a0),
            math.radians(a1),
            0.12,
            0.20,
            segs=36,
        )
        po = bpy.data.objects.new(f"Guilloche_Dial_Sector_{tag}", pm)
        po.data.materials.append(mats["guilloche"])
        add_bevel_mod(po, width=0.006, segments=2)
        link_obj(po, col)

        # Gold chamfered frame border along inner & outer edges of the dial plate
        fm = create_arc_plate_mesh(
            f"Dial_GoldTrim_{tag}",
            2.05,
            2.11,
            math.radians(a0 - 0.6),
            math.radians(a1 + 0.6),
            0.13,
            0.215,
            segs=36,
        )
        fo = bpy.data.objects.new(f"Dial_GoldTrim_{tag}", fm)
        fo.data.materials.append(mats["rose_gold"])
        link_obj(fo, col)

    # 8. Astrolabe Outer Chapter Ring (R=3.80..4.05, Z=0.18..0.25) + 12 Applied Gold Hour Obelisks + 60 Minute Pearls
    chap_m = create_annulus_mesh("Astrolabe_Chapter_Ring", 3.78, 4.04, 0.16, 0.24, segs=144, r_top_in=3.80, r_top_out=4.04)
    chap_o = bpy.data.objects.new("Astrolabe_Chapter_Ring", chap_m)
    chap_o.data.materials.append(mats["guilloche"])
    add_bevel_mod(chap_o, width=0.006, segments=2)
    link_obj(chap_o, col)

    # Optical Anti-Reflective Sapphire Mystery Track Ring (R=2.07..2.22 at Z=0.21..0.245)
    sap_m = create_annulus_mesh("Peripheral_Sapphire_Track", 2.06, 2.24, 0.205, 0.242, segs=128)
    sap_o = bpy.data.objects.new("Peripheral_Sapphire_Track", sap_m)
    sap_o.data.materials.append(mats["sapphire"])
    link_obj(sap_o, col)

    # 12 Faceted Rose-Gold Applied Hour Markers & 60 Minute Studs
    bm_idx = bmesh.new()
    for m in range(60):
        ang = math.tau * m / 60.0
        rot = Matrix.Rotation(ang, 3, "Z")
        if m % 5 == 0:
            # Faceted roofed gold obelisk marker
            r0, r1 = 3.58, 3.96
            hw = 0.048 if (m % 15 == 0) else 0.036
            zb, zm, zt = 0.235, 0.275, 0.305
            pts = [
                Vector((r0, 0.0, zb)),
                Vector((r0 + 0.08, -hw, zb)),
                Vector((r1, -hw * 1.15, zb)),
                Vector((r1, +hw * 1.15, zb)),
                Vector((r0 + 0.08, +hw, zb)),
                Vector((r0 + 0.04, 0.0, zt)),
                Vector((r1 - 0.02, 0.0, zt)),
                Vector((r0 + 0.08, -hw * 0.85, zm)),
                Vector((r1, -hw * 0.95, zm)),
                Vector((r1, +hw * 0.95, zm)),
                Vector((r0 + 0.08, +hw * 0.85, zm)),
            ]
            pv = [bm_idx.verts.new(rot @ p) for p in pts]
            bm_idx.faces.new((pv[0], pv[4], pv[3], pv[2], pv[1]))
            bm_idx.faces.new((pv[0], pv[1], pv[7], pv[5]))
            bm_idx.faces.new((pv[1], pv[2], pv[8], pv[7]))
            bm_idx.faces.new((pv[2], pv[3], pv[9], pv[8]))
            bm_idx.faces.new((pv[3], pv[4], pv[10], pv[9]))
            bm_idx.faces.new((pv[4], pv[0], pv[5], pv[10]))
            bm_idx.faces.new((pv[5], pv[7], pv[8], pv[6]))
            bm_idx.faces.new((pv[6], pv[9], pv[10], pv[5]))
            bm_idx.faces.new((pv[6], pv[8], pv[9]))
        else:
            # Crisp minute prism stud
            bmesh.ops.create_icosphere(
                bm_idx,
                subdivisions=1,
                radius=0.018,
                matrix=Matrix.Translation(rot @ Vector((3.91, 0.0, 0.252))),
            )

    bmesh.ops.recalc_face_normals(bm_idx, faces=bm_idx.faces)
    idx_m = bpy.data.meshes.new("Applied_Gold_Hour_Markers")
    bm_idx.to_mesh(idx_m)
    bm_idx.free()
    finalize_mesh(idx_m, sharp_angle_deg=24.0)
    idx_o = bpy.data.objects.new("Applied_Gold_Hour_Markers", idx_m)
    idx_o.data.materials.append(mats["yellow_gold"])
    link_obj(idx_o, col)

    # 9. Peripheral Mystery Pointer Hands (Set at classic 10:10 framing the Central Tourbillon!)
    for h_name, deg, r_tip, w_base, m_key in (
        ("Peripheral_Hour_Pointer", 145.0, 3.38, 0.085, "rose_gold"),     # ~10 o'clock
        ("Peripheral_Minute_Pointer", 35.0, 3.68, 0.068, "blued_steel"),  # ~10 minutes past
    ):
        bm_h = bmesh.new()
        r_start = 2.09
        pts = [
            Vector((r_start, -w_base, 0.250)),
            Vector((r_tip, -0.008, 0.250)),
            Vector((r_tip, +0.008, 0.250)),
            Vector((r_start, +w_base, 0.250)),
            Vector((r_start + 0.04, 0.0, 0.292)),
            Vector((r_tip, 0.0, 0.274)),
        ]
        hv = [bm_h.verts.new(p) for p in pts]
        bm_h.faces.new((hv[3], hv[2], hv[1], hv[0]))
        bm_h.faces.new((hv[0], hv[1], hv[5], hv[4]))
        bm_h.faces.new((hv[1], hv[2], hv[5]))
        bm_h.faces.new((hv[2], hv[3], hv[4], hv[5]))
        bm_h.faces.new((hv[3], hv[0], hv[4]))
        bmesh.ops.recalc_face_normals(bm_h, faces=bm_h.faces)
        hm = bpy.data.meshes.new(h_name)
        bm_h.to_mesh(hm)
        bm_h.free()
        finalize_mesh(hm, sharp_angle_deg=20.0)
        ho = bpy.data.objects.new(h_name, hm)
        ho.rotation_euler = (0.0, 0.0, math.radians(deg))
        ho.data.materials.append(mats[m_key])
        link_obj(ho, col)


def build_phase_locked_gear_trains(col, mats, screw_mesh):
    """
    Constructs TWO symmetric 5-wheel Involute Horological Gear Trains (10 meshing gears + coaxial pinions!)
    along R_arc = 3.00 with module m = 0.052.
    Every wheel has teeth in [30, 18, 24, 18, 30] and spokes [5, 3, 4, 3, 5] (6 teeth/spoke everywhere!),
    advancing by EXACTLY 18 teeth per 120 frames for a 100% mathematically seamless tooth & spoke loop!
    """
    module = 0.052
    r_arc = 3.00
    teeth_seq = [30, 18, 24, 18, 30]
    spoke_seq = [5, 3, 4, 3, 5]
    mat_seq = ["brass", "rhodium", "rose_gold", "rhodium", "brass"]
    teeth_advance_per_loop = 18.0  # Divisible by 6 -> every spoke AND tooth matches identically at frame 121!

    trains = [
        ("East", math.radians(-68.0)),
        ("West", math.radians(112.0)),
    ]

    for train_tag, start_phi in trains:
        # 1. Compute exact polar angles on circle R_arc so Euclidean chord distance == m*(N_i + N_{i+1})/2
        phis = [start_phi]
        centers = []
        for i in range(len(teeth_seq)):
            if i > 0:
                d_exact = 0.5 * module * (teeth_seq[i - 1] + teeth_seq[i])
                d_phi = 2.0 * math.asin(d_exact / (2.0 * r_arc))
                phis.append(phis[-1] + d_phi)
            cx = r_arc * math.cos(phis[i])
            cy = r_arc * math.sin(phis[i])
            centers.append((cx, cy))

        # 2. Compute exact phase-locked angular trajectories theta_i(frame)
        # theta_i(f) = theta_i0 + dir_i * omega_i * u, where u = (frame - 1) / LOOP_FRAMES
        # Base gear 0:
        theta0_list = [phis[0]]
        omega_per_loop = [teeth_advance_per_loop * (math.tau / teeth_seq[0])]

        for i in range(1, len(teeth_seq)):
            x1, y1 = centers[i - 1]
            x2, y2 = centers[i]
            beta = math.atan2(y2 - y1, x2 - x1)
            n1, n2 = teeth_seq[i - 1], teeth_seq[i]
            # Exact involute tooth-to-valley meshing equation:
            # theta_2(t) = beta + pi + pi/n2 - (n1/n2)*(theta_1(t) - beta)
            th2_0 = beta + math.pi + (math.pi / n2) - (n1 / n2) * (theta0_list[i - 1] - beta)
            om2 = -(n1 / n2) * omega_per_loop[i - 1]
            theta0_list.append(th2_0)
            omega_per_loop.append(om2)

        # 3. Instantiate all 5 meshing wheels, coaxial pinions, arbors, gold chatons & synthetic rubies
        z_gear = -0.05
        for i, (cx, cy) in enumerate(centers):
            nt_cnt = teeth_seq[i]
            sp_cnt = spoke_seq[i]
            gname = f"Gear_{train_tag}_{i:02d}_{nt_cnt}T"
            gmesh, _, _, _ = create_horological_gear_mesh(
                gname, nt_cnt, module, thickness=0.072, spokes=sp_cnt
            )
            gobj = bpy.data.objects.new(gname, gmesh)
            gobj.location = (cx, cy, z_gear)
            gobj.data.materials.append(mats[mat_seq[i]])
            add_bevel_mod(gobj, width=0.0028, segments=2)
            link_obj(gobj, col)

            th0 = theta0_list[i]
            om = omega_per_loop[i]
            expr = f"{th0:.8f} + ({om:.8f}) * ((frame - 1) / {LOOP_FRAMES}.0)"
            add_frame_driver(gobj, "rotation_euler", expr, index=2)

            # Coaxial lower/upper horological pinion on alternating gears for rich multi-tier depth!
            if i in (0, 2, 4):
                pname = f"Pinion_{train_tag}_{i:02d}_12T"
                pmesh, _, _, _ = create_horological_gear_mesh(pname, 12, module * 0.72, thickness=0.085, spokes=0)
                pobj = bpy.data.objects.new(pname, pmesh)
                pobj.location = (cx, cy, z_gear - 0.085)
                pobj.data.materials.append(mats["blued_steel" if i == 2 else "rhodium"])
                add_bevel_mod(pobj, width=0.002, segments=2)
                link_obj(pobj, col)
                add_frame_driver(pobj, "rotation_euler", expr, index=2)

            # Arbor + Gold Chaton + Synthetic Ruby Jewel Bearing above the skeleton bridge!
            build_pivot_jewel_assembly(
                col, mats, screw_mesh, (cx, cy), z_base=-0.26, z_top=0.145, tag=f"{train_tag}_{i:02d}"
            )

        # 4. Sculpted Chamfered Rhodium Horological Finger Bridge spanning all 5 gear arbors!
        bridge_m = create_arc_plate_mesh(
            f"Skeleton_FingerBridge_{train_tag}",
            r_arc - 0.14,
            r_arc + 0.14,
            phis[0] - 0.06,
            phis[-1] + 0.06,
            0.095,
            0.138,
            segs=44,
        )
        bridge_o = bpy.data.objects.new(f"Skeleton_FingerBridge_{train_tag}", bridge_m)
        bridge_o.data.materials.append(mats["rhodium"])
        add_bevel_mod(bridge_o, width=0.008, segments=3)
        link_obj(bridge_o, col)

        # Gold Bridge Standoff Pillars & Blued Bridge Screws at ends of the finger bridge
        for end_idx, end_ang in enumerate((phis[0] - 0.09, phis[-1] + 0.09)):
            px = r_arc * math.cos(end_ang)
            py = r_arc * math.sin(end_ang)
            pil_m = create_annulus_mesh(
                f"Bridge_Pillar_{train_tag}_{end_idx}", 0.02, 0.11, -0.25, 0.138, segs=28
            )
            pil_o = bpy.data.objects.new(f"Bridge_Pillar_{train_tag}_{end_idx}", pil_m)
            pil_o.location = (px, py, 0.0)
            pil_o.data.materials.append(mats["rose_gold"])
            link_obj(pil_o, col)

            sc = bpy.data.objects.new(f"Bridge_Screw_{train_tag}_{end_idx}", screw_mesh)
            sc.location = (px, py, 0.140)
            sc.scale = (1.15, 1.15, 1.15)
            sc.rotation_euler = (0.0, 0.0, end_ang)
            sc.data.materials.append(mats["blued_steel"])
            link_obj(sc, col)


def create_gimbal_ring_mesh(name, radius, half_w, half_t, plane="XZ", cutouts=12):
    """
    Precision-machined horological gimbal ring with dual structural rails
    and chamfered lightening windows around its circumference.
    """
    bm = bmesh.new()
    segs = cutouts * 8
    r_in = radius - half_w
    r_out = radius + half_w

    def to_plane(u, v, w):
        if plane == "XZ":
            return Vector((u, w, v))
        elif plane == "YZ":
            return Vector((w, u, v))
        return Vector((u, v, w))

    # Build solid clean outer/inner structural ring with undulating sculpted thickness for visual elegance
    bi, bo, ti, to = [], [], [], []
    for i in range(segs):
        ang = math.tau * i / segs
        # Subtle horological scalloping between spoke nodes
        scallop = 1.0 - 0.22 * (0.5 - 0.5 * math.cos(cutouts * ang)) ** 2
        ri = radius - half_w * scallop
        ro = radius + half_w * scallop
        ht = half_t * (0.82 + 0.18 * scallop)
        ca, sa = math.cos(ang), math.sin(ang)
        bi.append(bm.verts.new(to_plane(ri * ca, ri * sa, -ht)))
        bo.append(bm.verts.new(to_plane(ro * ca, ro * sa, -ht)))
        ti.append(bm.verts.new(to_plane(ri * ca, ri * sa, +ht)))
        to.append(bm.verts.new(to_plane(ro * ca, ro * sa, +ht)))

    for i in range(segs):
        j = (i + 1) % segs
        bm.faces.new((bi[j], bo[j], bo[i], bi[i]))
        bm.faces.new((ti[i], to[i], to[j], ti[j]))
        bm.faces.new((bo[i], bo[j], to[j], to[i]))
        bm.faces.new((bi[j], bi[i], ti[i], ti[j]))

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    return finalize_mesh(mesh, sharp_angle_deg=34.0)


def build_three_axis_tourbillon_and_hopf_core(col, mats, screw_mesh):
    """
    Builds the Twin Arched Swan-Neck Bridges (anchored cleanly on the Amphitheater Rim Wall),
    the 3-Axis Nested Gimbaled Tourbillon centered at (0, 0, +0.52), mechanical pivot axles,
    the Central Spectral Dispersion Diamond, and the Blender 4.2 Geometry Nodes Hopf Core!
    """
    tourb_center = Vector((0.0, 0.0, 0.52))

    def make_axle_pin(name, parent, loc, rot_euler, length, rad=0.032, mat_key="rhodium"):
        bm_a = bmesh.new()
        bmesh.ops.create_cone(bm_a, cap_ends=True, cap_tris=False, segments=20, radius1=rad, radius2=rad, depth=length)
        am = bpy.data.meshes.new(name)
        bm_a.to_mesh(am)
        bm_a.free()
        finalize_mesh(am)
        ao = bpy.data.objects.new(name, am)
        if parent is not None:
            ao.parent = parent
        ao.location = loc
        ao.rotation_euler = rot_euler
        ao.data.materials.append(mats[mat_key])
        link_obj(ao, col)
        return ao

    # 1. Twin Arched Swan-Neck Bridges anchored cleanly on Amphitheater_Bevel_Wall (R ~ 2.01, zero gear bridge overlap!)
    for side, y_sign in (("North", +1.0), ("South", -1.0)):
        y_piv = y_sign * 1.68
        bm = bmesh.new()
        steps = 36
        x_span = 1.06  # Feet sit at ( +/-1.06, +/-1.72 ) -> R = 2.02 right on Amphitheater_Bevel_Wall!
        prof_prev = None
        for k in range(steps + 1):
            u = -1.0 + 2.0 * (k / steps)
            x = x_span * u
            arch = 0.5 * (1.0 + math.cos(math.pi * u))
            zc = 0.20 + 0.32 * arch
            yc = y_piv + y_sign * 0.04 * (1.0 - arch)
            hw = 0.092 - 0.024 * math.sin(math.pi * abs(u))
            ht = 0.034 + 0.018 * arch
            pts = [
                bm.verts.new((x, yc - hw, zc - ht)),
                bm.verts.new((x, yc + hw, zc - ht)),
                bm.verts.new((x, yc + hw, zc + ht)),
                bm.verts.new((x, yc - hw, zc + ht)),
            ]
            if k == 0:
                bm.faces.new((pts[3], pts[2], pts[1], pts[0]))
            else:
                for c in range(4):
                    d = (c + 1) % 4
                    bm.faces.new((prof_prev[c], prof_prev[d], pts[d], pts[c]))
            if k == steps:
                bm.faces.new((pts[0], pts[1], pts[2], pts[3]))
            prof_prev = pts

        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        br_m = bpy.data.meshes.new(f"Tourbillon_SwanBridge_{side}")
        bm.to_mesh(br_m)
        bm.free()
        finalize_mesh(br_m, sharp_angle_deg=30.0)
        br_o = bpy.data.objects.new(f"Tourbillon_SwanBridge_{side}", br_m)
        br_o.data.materials.append(mats["rhodium"])
        add_bevel_mod(br_o, width=0.007, segments=3)
        link_obj(br_o, col)

        for fx in (-x_span + 0.10, +x_span - 0.10):
            fy = y_piv + y_sign * 0.04
            sc = bpy.data.objects.new(f"SwanBridge_FootScrew_{side}_{fx:+.1f}", screw_mesh)
            sc.location = (fx, fy, 0.236)
            sc.scale = (1.15, 1.15, 1.15)
            sc.data.materials.append(mats["blued_steel"])
            link_obj(sc, col)

        ch_m = create_annulus_mesh(f"SwanTrunnion_Chaton_{side}", 0.072, 0.148, -0.04, 0.04, segs=36)
        ch_o = bpy.data.objects.new(f"SwanTrunnion_Chaton_{side}", ch_m)
        ch_o.location = (0.0, y_piv, tourb_center.z)
        ch_o.rotation_euler = (math.pi * 0.5, 0.0, 0.0)
        ch_o.data.materials.append(mats["yellow_gold"])
        link_obj(ch_o, col)

        rb_m = create_annulus_mesh(f"SwanTrunnion_Ruby_{side}", 0.035, 0.078, -0.045, 0.045, segs=32)
        rb_o = bpy.data.objects.new(f"SwanTrunnion_Ruby_{side}", rb_m)
        rb_o.location = (0.0, y_piv, tourb_center.z)
        rb_o.rotation_euler = (math.pi * 0.5, 0.0, 0.0)
        rb_o.data.materials.append(mats["ruby"])
        link_obj(rb_o, col)

    # 2. Gimbal 1 — Outer Rose-Gold Cage (R = 1.54, rotates 1 rev / 120f around Y-axis)
    g1_m = create_gimbal_ring_mesh("Tourbillon_Gimbal1_Outer", 1.54, 0.068, 0.046, plane="XY", cutouts=16)
    g1 = bpy.data.objects.new("Tourbillon_Gimbal1_Outer", g1_m)
    g1.location = tourb_center
    g1.data.materials.append(mats["rose_gold"])
    add_bevel_mod(g1, width=0.006, segments=2)
    link_obj(g1, col)
    add_frame_driver(
        g1, "rotation_euler", f"0.488692 + ({math.tau:.8f}) * ((frame - 1) / {LOOP_FRAMES}.0)", index=1
    )

    # Y-axis trunnion pins linking Gimbal 1 to Swan-Neck ruby bearings
    for sgn in (-1.0, +1.0):
        make_axle_pin(f"Trunnion_G1_Y_{sgn:+.0f}", g1, (0.0, sgn * 1.62, 0.0), (math.pi * 0.5, 0.0, 0.0), 0.20)

    for b in range(8):
        ang = math.tau * b / 8.0
        bw = bpy.data.objects.new(f"Gimbal1_TimingScrew_{b}", screw_mesh)
        bw.parent = g1
        bw.location = (1.61 * math.cos(ang), 1.61 * math.sin(ang), 0.0)
        bw.rotation_euler = (0.0, math.pi * 0.5, ang)
        bw.scale = (0.92, 0.92, 0.92)
        bw.data.materials.append(mats["blued_steel"])
        link_obj(bw, col)

    # 3. Gimbal 2 — Middle Heat-Blued Titanium Astrolabe Ring (R = 1.33, child of G1, rotates 1 rev / 120f around X-axis)
    g2_m = create_gimbal_ring_mesh("Tourbillon_Gimbal2_Middle", 1.33, 0.058, 0.042, plane="XZ", cutouts=12)
    g2 = bpy.data.objects.new("Tourbillon_Gimbal2_Middle", g2_m)
    g2.parent = g1
    g2.location = (0.0, 0.0, 0.0)
    g2.data.materials.append(mats["blued_steel"])
    add_bevel_mod(g2, width=0.005, segments=2)
    link_obj(g2, col)
    add_frame_driver(
        g2, "rotation_euler", f"-0.628318 + ({math.tau:.8f}) * ((frame - 1) / {LOOP_FRAMES}.0)", index=0
    )
    for sgn in (-1.0, +1.0):
        make_axle_pin(f"Trunnion_G2_X_{sgn:+.0f}", g1, (sgn * 1.43, 0.0, 0.0), (0.0, math.pi * 0.5, 0.0), 0.18)

    # 4. Gimbal 3 — Inner Yellow-Gold Chronometer Cage (R = 1.12, child of G2, rotates 2 rev / 120f around Z-axis)
    g3_m = create_gimbal_ring_mesh("Tourbillon_Gimbal3_Inner", 1.12, 0.050, 0.036, plane="XY", cutouts=12)
    g3 = bpy.data.objects.new("Tourbillon_Gimbal3_Inner", g3_m)
    g3.parent = g2
    g3.location = (0.0, 0.0, 0.0)
    g3.data.materials.append(mats["yellow_gold"])
    add_bevel_mod(g3, width=0.0045, segments=2)
    link_obj(g3, col)
    add_frame_driver(
        g3, "rotation_euler", f"0.314159 + ({2.0 * math.tau:.8f}) * ((frame - 1) / {LOOP_FRAMES}.0)", index=2
    )
    for sgn in (-1.0, +1.0):
        make_axle_pin(f"Trunnion_G3_Z_{sgn:+.0f}", g2, (0.0, 0.0, sgn * 1.22), (0.0, 0.0, 0.0), 0.18)

    # 3 Delicate Filigree Suspension Struts & Gold Girdle Collar holding the Singularity Diamond inside Gimbal 3
    collar_m = create_annulus_mesh("Singularity_Gold_Collar", 0.285, 0.325, -0.022, 0.022, segs=48)
    collar_o = bpy.data.objects.new("Singularity_Gold_Collar", collar_m)
    collar_o.parent = g3
    collar_o.data.materials.append(mats["rose_gold"])
    link_obj(collar_o, col)
    for sp_i in range(3):
        sp_ang = math.tau * sp_i / 3.0
        mid_r = 0.70
        len_sp = 0.78
        make_axle_pin(
            f"Singularity_Suspension_Spoke_{sp_i}",
            g3,
            (mid_r * math.cos(sp_ang), mid_r * math.sin(sp_ang), 0.0),
            (0.0, math.pi * 0.5, sp_ang),
            len_sp,
            rad=0.012,
            mat_key="rose_gold",
        )

    # 5. Live Blender 4.2 Geometry Nodes Stereographic Hopf Fibration Core!
    hopf_ng, phase_sock_id = build_hopf_fibration_geonodes(mats["hopf_plasma"])
    hopf_mesh = bpy.data.meshes.new("Hopf_Fibration_Carrier")
    hopf_obj = bpy.data.objects.new("Hopf_Fibration_Quantum_Core", hopf_mesh)
    hopf_obj.parent = g3
    hopf_obj.location = (0.0, 0.0, 0.0)
    link_obj(hopf_obj, col)

    hopf_mod = hopf_obj.modifiers.new("Hopf_Fibration_S3", "NODES")
    hopf_mod.node_group = hopf_ng
    add_frame_driver(
        hopf_mod,
        f'["{phase_sock_id}"]',
        f"({math.tau:.8f}) * ((frame - 1) / {LOOP_FRAMES}.0)",
    )

    # 6. Central 3-Wavelength RGB Spectral Dispersion Brilliant Diamond Core!
    dia_m = create_brilliant_diamond_mesh("Singularity_Dispersion_Diamond", radius=0.28)
    dia_o = bpy.data.objects.new("Singularity_Dispersion_Diamond", dia_m)
    dia_o.parent = g3
    dia_o.location = (0.0, 0.0, 0.0)
    dia_o.data.materials.append(mats["diamond"])
    link_obj(dia_o, col)
    add_frame_driver(
        dia_o, "rotation_euler", f"-({math.tau:.8f}) * ((frame - 1) / {LOOP_FRAMES}.0)", index=2
    )

    return tourb_center


# ==============================================================================
# 7. STUDIO HDRI LIGHTING, ATMOSPHERICS & CINEMATIC MACRO CAMERAS
# ==============================================================================

def build_lighting_and_atmosphere(scene, col, mats, tourb_center):
    # 1. Split-Ray Studio World: Moody dark obsidian gradient for Camera rays,
    #    real bundled Blender studio.exr HDRI reflections for Glossy/Transmission rays!
    world = bpy.data.worlds.new("Chronos_Studio_World")
    scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()

    out = nt.nodes.new("ShaderNodeOutputWorld")
    out.location = (560, 0)

    lp = nt.nodes.new("ShaderNodeLightPath")
    lp.location = (-120, 260)

    bg_cam = nt.nodes.new("ShaderNodeBackground")
    bg_cam.location = (120, -100)
    bg_cam.inputs["Color"].default_value = (0.004, 0.006, 0.011, 1.0)
    bg_cam.inputs["Strength"].default_value = 1.0

    bg_refl = nt.nodes.new("ShaderNodeBackground")
    bg_refl.location = (120, 100)
    bg_refl.inputs["Strength"].default_value = 0.55

    # Locate bundled Blender 4.2 studio.exr for authentic softbox metal reflections
    blender_dir = os.path.dirname(bpy.app.binary_path)
    exr_path = os.path.join(blender_dir, "4.2", "datafiles", "studiolights", "world", "studio.exr")
    if os.path.exists(exr_path):
        env_tex = nt.nodes.new("ShaderNodeTexEnvironment")
        env_tex.location = (-220, 80)
        env_tex.image = bpy.data.images.load(exr_path)
        nt.links.new(env_tex.outputs["Color"], bg_refl.inputs["Color"])
    else:
        bg_refl.inputs["Color"].default_value = (0.65, 0.72, 0.85, 1.0)

    mix_sh = nt.nodes.new("ShaderNodeMixShader")
    mix_sh.location = (340, 20)
    nt.links.new(lp.outputs["Is Camera Ray"], mix_sh.inputs["Fac"])
    nt.links.new(bg_refl.outputs["Background"], mix_sh.inputs[1])
    nt.links.new(bg_cam.outputs["Background"], mix_sh.inputs[2])
    nt.links.new(mix_sh.outputs["Shader"], out.inputs["Surface"])

    # 2. Four-Point Luxury Watch Cinematography Rig
    def add_area_light(name, loc, target_pt, energy, color, size_x, size_y):
        ldata = bpy.data.lights.new(name, type="AREA")
        ldata.energy = energy
        ldata.color = color
        ldata.shape = "RECTANGLE"
        ldata.size = size_x
        ldata.size_y = size_y
        lobj = bpy.data.objects.new(name, ldata)
        lobj.location = loc
        direction = Vector(target_pt) - Vector(loc)
        lobj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
        link_obj(lobj, col)
        return lobj

    # Warm Golden Key Softbox (raking across guilloche & involute gear teeth)
    add_area_light(
        "Light_Key_WarmSoftbox",
        loc=(6.5, -5.2, 6.2),
        target_pt=(0.4, 0.0, 0.1),
        energy=360.0,
        color=(1.0, 0.90, 0.78),
        size_x=5.2,
        size_y=3.4,
    )

    # Cool Cobalt-Silver Rim Backlight (carving razor-sharp edges on tourbillon & bridges)
    add_area_light(
        "Light_Rim_CobaltBack",
        loc=(-6.0, 6.8, 4.4),
        target_pt=(0.0, 0.0, 0.3),
        energy=420.0,
        color=(0.68, 0.84, 1.0),
        size_x=6.0,
        size_y=2.2,
    )

    # Side Specular Accent Strip (illuminating East involute gear teeth & ruby chatons!)
    add_area_light(
        "Light_Accent_EastGearStrip",
        loc=(7.2, 2.2, 2.8),
        target_pt=(2.8, -0.5, 0.0),
        energy=190.0,
        color=(1.0, 0.95, 0.88),
        size_x=1.6,
        size_y=4.5,
    )

    # Overhead Soft Diffuser Fill
    add_area_light(
        "Light_Top_DiffuserFill",
        loc=(-1.2, -1.5, 9.5),
        target_pt=(0.0, 0.0, 0.0),
        energy=140.0,
        color=(0.92, 0.95, 1.0),
        size_x=7.5,
        size_y=7.5,
    )

    # Core Point Light inside the Hopf Singularity (casting real gimbal shadows into the terraced amphitheater!)
    pt_data = bpy.data.lights.new("Light_Singularity_Core", type="POINT")
    pt_data.energy = 18.0
    pt_data.color = (1.0, 0.68, 0.34)
    pt_data.shadow_soft_size = 0.06
    pt_obj = bpy.data.objects.new("Light_Singularity_Core", pt_data)
    pt_obj.location = tourb_center
    link_obj(pt_obj, col)

    # 3. Localized Atmospheric Volume Domain around the chronometer
    bm_v = bmesh.new()
    bmesh.ops.create_cube(bm_v, size=1.0)
    for v in bm_v.verts:
        v.co.x *= 13.0
        v.co.y *= 13.0
        v.co.z = 4.5 if v.co.z > 0 else -1.27
    vol_m = bpy.data.meshes.new("Atmosphere_Domain_Mesh")
    bm_v.to_mesh(vol_m)
    bm_v.free()
    vol_o = bpy.data.objects.new("Atmosphere_Volume_Domain", vol_m)
    vol_o.data.materials.append(mats["volume"])
    vol_o.display_type = "WIRE"
    link_obj(vol_o, col)

    # 4. Floating Golden Bokeh Dust Motes (Geometry Nodes)
    mote_ng, mote_phase_id = build_atmospheric_motes_geonodes(mats["motes"])
    mote_mesh = bpy.data.meshes.new("Bokeh_Motes_Carrier")
    mote_obj = bpy.data.objects.new("Atmospheric_Bokeh_Motes", mote_mesh)
    link_obj(mote_obj, col)
    mote_mod = mote_obj.modifiers.new("Bokeh_Motes", "NODES")
    mote_mod.node_group = mote_ng
    add_frame_driver(
        mote_mod,
        f'["{mote_phase_id}"]',
        f"({math.tau:.8f}) * ((frame - 1) / {LOOP_FRAMES}.0)",
    )


def build_cameras(scene, col, tourb_center):
    """Creates 4 museum-grade still cameras + 1 seamless 120-frame looping orbital macro camera."""
    cams = {}

    def make_cam(name, loc, target_loc, lens_mm, fstop, sensor_w=36.0):
        focus_empty = bpy.data.objects.new(f"Focus_{name}", None)
        focus_empty.empty_display_size = 0.2
        focus_empty.location = target_loc
        link_obj(focus_empty, col)

        cdata = bpy.data.cameras.new(name)
        cdata.lens = lens_mm
        cdata.sensor_width = sensor_w
        cdata.clip_start = 0.05
        cdata.clip_end = 140.0
        cdata.dof.use_dof = True
        cdata.dof.focus_object = focus_empty
        cdata.dof.aperture_fstop = fstop
        cdata.dof.aperture_blades = 7

        cobj = bpy.data.objects.new(name, cdata)
        cobj.location = loc
        t_con = cobj.constraints.new(type="TRACK_TO")
        t_con.target = focus_empty
        t_con.track_axis = "TRACK_NEGATIVE_Z"
        t_con.up_axis = "UP_Y"
        link_obj(cobj, col)
        return cobj, focus_empty

    # Camera 1: Full Chronometer Hero 3/4 Portrait (Coin-Edge Case, Crown, Blueprint Bench & Tourbillon!)
    c1, _ = make_cam(
        "Cam_01_Hero_Chronometer",
        loc=(7.6, -10.4, 6.8),
        target_loc=(0.15, -0.10, 0.05),
        lens_mm=58.0,
        fstop=0.95,
    )
    cams["hero"] = c1

    # Camera 2: Tight Uncropped 3-Axis Tourbillon & Hopf Fibration Singularity Close-Up!
    c2, _ = make_cam(
        "Cam_02_Macro_Tourbillon_Hopf",
        loc=(5.1, -6.9, 4.15),
        target_loc=(0.0, 0.0, 0.44),
        lens_mm=84.0,
        fstop=0.72,
    )
    cams["tourbillon"] = c2

    # Camera 3: Extreme 120mm Macro on East Involute Gear Mesh, Ruby Chaton, Geneva Stripes & Blued Screw!
    c3, _ = make_cam(
        "Cam_03_Macro_GearRuby",
        loc=(5.15, -4.45, 2.25),
        target_loc=(2.70, -1.28, 0.02),
        lens_mm=120.0,
        fstop=0.65,
    )
    cams["macro"] = c3

    # Camera 4: Architectural Overhead Astrolabe & Inlaid Brass Blueprint Symmetry View!
    c4, _ = make_cam(
        "Cam_04_Top_Astrolabe",
        loc=(0.0, -2.1, 17.6),
        target_loc=(0.0, 0.0, 0.0),
        lens_mm=54.0,
        fstop=2.0,
    )
    cams["top"] = c4

    # Camera 5: Seamless 120-Frame Breathing Orbital Macro Glide (Framing Full Chronometer -> Tourbillon -> Back!)
    c5, _ = make_cam(
        "Cam_05_Anim_Loop",
        loc=(6.6, -9.0, 5.7),
        target_loc=(0.08, -0.04, 0.24),
        lens_mm=66.0,
        fstop=0.82,
    )
    u_expr = f"({math.tau:.8f}) * ((frame - 1) / {LOOP_FRAMES}.0)"
    base_r = 11.15
    base_az = -0.938
    add_frame_driver(
        c5,
        "location",
        f"({base_r} - 1.55*(1 - cos({u_expr}))) * cos({base_az} + 0.30*sin({u_expr}))",
        index=0,
    )
    add_frame_driver(
        c5,
        "location",
        f"({base_r} - 1.55*(1 - cos({u_expr}))) * sin({base_az} + 0.30*sin({u_expr}))",
        index=1,
    )
    add_frame_driver(
        c5,
        "location",
        f"5.75 - 0.95*(1 - cos({u_expr}))",
        index=2,
    )
    cams["anim"] = c5

    scene.camera = c1
    return cams


# ==============================================================================
# 8. MAIN ORCHESTRATOR & CLI ENTRYPOINT
# ==============================================================================

def build_full_scene(samples=192, res_x=1920, res_y=1080):
    scene = reset_scene()
    configure_cycles_and_color(scene, samples=samples, res_x=res_x, res_y=res_y)
    configure_compositor(scene)

    root_col = make_collection("CHRONOS_IV_Celestial_Tourbillon")
    col_bench = make_collection("01_Workbench_And_Blueprint", root_col)
    col_case = make_collection("02_Chronometer_Case_And_Dial", root_col)
    col_gears = make_collection("03_Involute_Gear_Trains", root_col)
    col_tourb = make_collection("04_Tourbillon_And_Hopf_Core", root_col)
    col_studio = make_collection("05_Studio_Lighting_And_Cameras", root_col)

    mats = build_materials()
    screw_mesh = create_slotted_screw_mesh()

    build_workbench_and_blueprint(col_bench, mats, screw_mesh)
    build_chronometer_case_and_dial(col_case, mats, screw_mesh)
    build_phase_locked_gear_trains(col_gears, mats, screw_mesh)
    tourb_center = build_three_axis_tourbillon_and_hopf_core(col_tourb, mats, screw_mesh)
    build_lighting_and_atmosphere(scene, col_studio, mats, tourb_center)
    cams = build_cameras(scene, col_studio, tourb_center)

    bpy.context.view_layer.update()
    return scene, cams


def parse_args():
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1 :]
    else:
        argv = []

    p = argparse.ArgumentParser(description="CHRONOS-IV Celestial Tourbillon Generator")
    p.add_argument("--save-blend", type=str, default="", help="Output .blend path")
    p.add_argument("--render-stills", type=str, default="", help="Directory to render 3 hero stills")
    p.add_argument("--render-anim", type=str, default="", help="Directory to render animation frames")
    p.add_argument("--samples", type=int, default=192)
    p.add_argument("--res", type=int, nargs=2, default=[1920, 1080])
    p.add_argument("--frame-start", type=int, default=1)
    p.add_argument("--frame-end", type=int, default=LOOP_FRAMES)
    p.add_argument("--frame-step", type=int, default=1)
    return p.parse_args(argv)


def main():
    args = parse_args()
    scene, cams = build_full_scene(samples=args.samples, res_x=args.res[0], res_y=args.res[1])

    if args.save_blend:
        os.makedirs(os.path.dirname(os.path.abspath(args.save_blend)), exist_ok=True)
        try:
            bpy.ops.file.pack_all()
        except Exception as exc:
            print(f"[CHRONOS-IV] Pack note: {exc}")
        scene.camera = cams["hero"]
        scene.frame_set(1)
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.save_blend))
        print(f"[CHRONOS-IV] Saved .blend -> {args.save_blend}")

    if args.render_stills:
        out_dir = os.path.abspath(args.render_stills)
        os.makedirs(out_dir, exist_ok=True)
        scene.render.image_settings.file_format = "PNG"
        scene.render.image_settings.color_mode = "RGBA"

        shots = [
            ("01_hero_chronometer.png", cams["hero"], 16),
            ("02_macro_tourbillon_hopf.png", cams["tourbillon"], 26),
            ("03_macro_gear_ruby.png", cams["macro"], 38),
            ("04_top_astrolabe.png", cams["top"], 54),
        ]
        for fname, cam, fnum in shots:
            scene.camera = cam
            scene.frame_set(fnum)
            scene.render.filepath = os.path.join(out_dir, fname)
            print(f"[CHRONOS-IV] Rendering {fname} (frame {fnum})...")
            bpy.ops.render.render(write_still=True)

    if args.render_anim:
        anim_dir = os.path.abspath(args.render_anim)
        os.makedirs(anim_dir, exist_ok=True)
        scene.camera = cams["anim"]
        scene.render.image_settings.file_format = "PNG"
        scene.render.image_settings.color_mode = "RGB"
        for f in range(args.frame_start, args.frame_end + 1, args.frame_step):
            scene.frame_set(f)
            scene.render.filepath = os.path.join(anim_dir, f"frame_{f:04d}.png")
            bpy.ops.render.render(write_still=True)
            print(f"[CHRONOS-IV] Rendered animation frame {f}/{args.frame_end}")


if __name__ == "__main__":
    main()
