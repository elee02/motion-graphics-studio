"""
Procedural Headless Blender (`bpy`) Scene Builder.
Enforces the Zero-Binary Git ("Code-as-Scene") rule: all 3D meshes, parametric curves,
shader node trees, three-point studio lighting, and camera orbits are constructed
purely from Python code and raytraced via Headless Blender 4.2 LTS Cycles.
"""

from __future__ import annotations

import argparse
import math
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Optional, Tuple

try:
    import bpy  # type: ignore
    import mathutils  # type: ignore
    HAS_BPY = True
except ImportError:
    HAS_BPY = False


class StudioPalette:
    """Unified RGBA colors (linear sRGB for Blender shaders)."""
    BG_DARK = (0.012, 0.016, 0.032, 1.0)
    CYAN = (0.000, 0.780, 1.000, 1.0)
    AMBER = (1.000, 0.450, 0.000, 1.0)
    GOLD = (1.000, 0.680, 0.080, 1.0)
    CRIMSON = (0.950, 0.060, 0.120, 1.0)
    VIOLET = (0.420, 0.100, 0.980, 1.0)
    EMERALD = (0.020, 0.750, 0.320, 1.0)
    SILVER = (0.780, 0.840, 0.920, 1.0)
    WHITE = (0.960, 0.970, 0.990, 1.0)


@dataclass
class ProceduralCurve3D:
    name: str
    points: List[Tuple[float, float, float]]
    color: Tuple[float, float, float, float]
    bevel_radius: float = 0.04


@dataclass
class StudioScene:
    """High-level declarative wrapper over headless Blender 4.2 (`bpy`)."""
    fps: int = 24
    duration_sec: float = 4.0
    width: int = 1920
    height: int = 1080
    seed: int = 42
    samples: int = 16
    title: str = "Studio 3D Scene"
    subtitle: str = "Procedural Blender Rig"
    include_floor_grid: bool = True
    curves: List[ProceduralCurve3D] = field(default_factory=list)
    camera_orbit: Tuple[float, float, float, float] = (10.5, 25.0, 20.0, 55.0)
    camera_target: Tuple[float, float, float] = (0.0, 0.0, 0.0)

    @property
    def total_frames(self) -> int:
        return max(1, int(round(self.fps * self.duration_sec)))

    def reset_scene(self) -> None:
        if not HAS_BPY:
            return
        bpy.ops.wm.read_factory_settings(use_empty=True)
        scn = bpy.context.scene
        scn.render.engine = "CYCLES"
        scn.cycles.device = "CPU"
        scn.cycles.samples = self.samples
        scn.cycles.use_denoising = False
        scn.render.fps = self.fps
        scn.frame_start = 1
        scn.frame_end = self.total_frames
        scn.render.resolution_x = self.width
        scn.render.resolution_y = self.height
        scn.render.resolution_percentage = 100

        world = bpy.data.worlds.new("StudioWorld")
        scn.world = world
        world.use_nodes = True
        bg_node = world.node_tree.nodes.get("Background")
        if bg_node:
            bg_node.inputs[0].default_value = StudioPalette.BG_DARK
            bg_node.inputs[1].default_value = 1.0

    def setup_three_point_lighting(
        self,
        energy_scale: float = 1.0,
        key_color: Tuple[float, float, float, float] = StudioPalette.WHITE,
        fill_color: Tuple[float, float, float, float] = StudioPalette.CYAN,
        rim_color: Tuple[float, float, float, float] = StudioPalette.VIOLET,
    ) -> None:
        if not HAS_BPY:
            return
        lights = [
            ("KeyLight", (6.0, -6.0, 7.0), 550.0 * energy_scale, key_color, 3.5),
            ("FillLight", (-6.5, -4.0, 4.0), 240.0 * energy_scale, fill_color, 5.0),
            ("RimLight", (0.0, 7.0, 6.0), 420.0 * energy_scale, rim_color, 3.0),
        ]
        for name, loc, energy, color, size in lights:
            light_data = bpy.data.lights.new(name=name, type="AREA")
            light_data.energy = energy
            light_data.color = color[:3]
            light_data.size = size
            light_obj = bpy.data.objects.new(name=name, object_data=light_data)
            bpy.context.collection.objects.link(light_obj)
            light_obj.location = loc
            direction = mathutils.Vector(self.camera_target) - mathutils.Vector(loc)
            light_obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

    def create_orbit_camera(
        self,
        radius: float = 10.5,
        elevation_deg: float = 25.0,
        start_angle_deg: float = 20.0,
        end_angle_deg: float = 55.0,
        target: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        lens_mm: float = 38.0,
    ) -> None:
        self.camera_orbit = (radius, elevation_deg, start_angle_deg, end_angle_deg)
        self.camera_target = target
        if not HAS_BPY:
            return
        rig = bpy.data.objects.new("CameraOrbitRig", None)
        rig.location = target
        bpy.context.collection.objects.link(rig)

        cam_data = bpy.data.cameras.new("StudioCamera")
        cam_data.lens = lens_mm
        cam_obj = bpy.data.objects.new("StudioCamera", cam_data)
        bpy.context.collection.objects.link(cam_obj)
        bpy.context.scene.camera = cam_obj

        elev_rad = math.radians(elevation_deg)
        cam_obj.location = (
            0.0,
            -radius * math.cos(elev_rad),
            radius * math.sin(elev_rad),
        )
        direction = mathutils.Vector((0.0, 0.0, 0.0)) - cam_obj.location
        cam_obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
        cam_obj.parent = rig

        rig.rotation_euler = (0.0, 0.0, math.radians(start_angle_deg))
        rig.keyframe_insert(data_path="rotation_euler", frame=1)
        rig.rotation_euler = (0.0, 0.0, math.radians(end_angle_deg))
        rig.keyframe_insert(data_path="rotation_euler", frame=self.total_frames)

    def create_emission_material(
        self,
        name: str,
        color: Tuple[float, float, float, float],
        strength: float = 3.5,
    ):
        if not HAS_BPY:
            return None
        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        out = nodes.new(type="ShaderNodeOutputMaterial")
        emission = nodes.new(type="ShaderNodeEmission")
        emission.inputs["Color"].default_value = color
        emission.inputs["Strength"].default_value = strength
        links.new(emission.outputs["Emission"], out.inputs["Surface"])
        return mat

    def create_metallic_material(
        self,
        name: str,
        color: Tuple[float, float, float, float],
        metallic: float = 0.9,
        roughness: float = 0.2,
        emission_color: Optional[Tuple[float, float, float, float]] = None,
        emission_strength: float = 0.0,
    ):
        if not HAS_BPY:
            return None
        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        bsdf = nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = color
            bsdf.inputs["Metallic"].default_value = metallic
            bsdf.inputs["Roughness"].default_value = roughness
            if emission_color and "Emission Color" in bsdf.inputs:
                bsdf.inputs["Emission Color"].default_value = emission_color
                bsdf.inputs["Emission Strength"].default_value = emission_strength
        return mat

    def add_sphere(
        self,
        name: str,
        location: Tuple[float, float, float],
        radius: float = 0.5,
        color: Tuple[float, float, float, float] = StudioPalette.GOLD,
        emission_strength: float = 0.0,
        metallic: float = 0.85,
        roughness: float = 0.18,
    ) -> None:
        if not HAS_BPY:
            return
        bpy.ops.mesh.primitive_uv_sphere_add(
            segments=32, ring_count=16, radius=radius, location=location
        )
        obj = bpy.context.active_object
        obj.name = name
        if emission_strength > 0.0:
            mat = self.create_emission_material(f"{name}_Mat", color, strength=emission_strength)
        else:
            mat = self.create_metallic_material(
                f"{name}_Mat", color, metallic=metallic, roughness=roughness
            )
        if mat:
            obj.data.materials.append(mat)

    def add_cylinder(
        self,
        name: str,
        location: Tuple[float, float, float],
        radius: float = 0.15,
        depth: float = 2.0,
        rotation_euler: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        color: Tuple[float, float, float, float] = StudioPalette.WHITE,
        emission_strength: float = 0.0,
        metallic: float = 0.3,
        roughness: float = 0.4,
    ) -> None:
        if not HAS_BPY:
            return
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=24,
            radius=radius,
            depth=depth,
            location=location,
            rotation=rotation_euler,
        )
        obj = bpy.context.active_object
        obj.name = name
        if emission_strength > 0.0:
            mat = self.create_emission_material(f"{name}_Mat", color, strength=emission_strength)
        else:
            mat = self.create_metallic_material(
                f"{name}_Mat", color, metallic=metallic, roughness=roughness
            )
        if mat:
            obj.data.materials.append(mat)

    def add_torus(
        self,
        name: str,
        location: Tuple[float, float, float],
        major_radius: float = 1.2,
        minor_radius: float = 0.06,
        rotation_euler: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        color: Tuple[float, float, float, float] = StudioPalette.GOLD,
        emission_strength: float = 2.5,
        animate_spin_axis: Optional[int] = None,
        spin_revolutions: float = 0.5,
    ) -> None:
        if not HAS_BPY:
            return
        bpy.ops.mesh.primitive_torus_add(
            major_segments=64,
            minor_segments=16,
            major_radius=major_radius,
            minor_radius=minor_radius,
            location=location,
            rotation=rotation_euler,
        )
        obj = bpy.context.active_object
        obj.name = name
        if emission_strength > 0.0:
            mat = self.create_emission_material(f"{name}_Mat", color, strength=emission_strength)
        else:
            mat = self.create_metallic_material(f"{name}_Mat", color, metallic=0.95, roughness=0.15)
        if mat:
            obj.data.materials.append(mat)

        if animate_spin_axis is not None:
            obj.keyframe_insert(data_path="rotation_euler", frame=1)
            rot = list(rotation_euler)
            rot[animate_spin_axis] += 2.0 * math.pi * spin_revolutions
            obj.rotation_euler = tuple(rot)
            obj.keyframe_insert(data_path="rotation_euler", frame=self.total_frames)

    def add_parametric_curve(
        self,
        name: str,
        func: Callable[[float], Tuple[float, float, float]],
        t_min: float,
        t_max: float,
        steps: int = 320,
        color: Tuple[float, float, float, float] = StudioPalette.CYAN,
        bevel_radius: float = 0.045,
        emission_strength: float = 3.5,
    ) -> None:
        pts: List[Tuple[float, float, float]] = []
        for i in range(steps + 1):
            t = t_min + (t_max - t_min) * (i / max(1, steps))
            pts.append(func(t))

        self.curves.append(
            ProceduralCurve3D(name=name, points=pts, color=color, bevel_radius=bevel_radius)
        )

        if not HAS_BPY:
            return

        curve_data = bpy.data.curves.new(name=name, type="CURVE")
        curve_data.dimensions = "3D"
        curve_data.bevel_depth = bevel_radius
        curve_data.bevel_resolution = 6

        spline = curve_data.splines.new(type="POLY")
        spline.points.add(len(pts) - 1)
        for idx, (x, y, z) in enumerate(pts):
            spline.points[idx].co = (x, y, z, 1.0)

        obj = bpy.data.objects.new(name, curve_data)
        bpy.context.collection.objects.link(obj)
        mat = self.create_emission_material(f"{name}_Mat", color, strength=emission_strength)
        if mat:
            obj.data.materials.append(mat)

    def add_polyline_curve(
        self,
        name: str,
        points: List[Tuple[float, float, float]],
        color: Tuple[float, float, float, float] = StudioPalette.AMBER,
        bevel_radius: float = 0.06,
        emission_strength: float = 5.0,
    ) -> None:
        self.curves.append(
            ProceduralCurve3D(name=name, points=points, color=color, bevel_radius=bevel_radius)
        )
        if not HAS_BPY:
            return
        curve_data = bpy.data.curves.new(name=name, type="CURVE")
        curve_data.dimensions = "3D"
        curve_data.bevel_depth = bevel_radius
        curve_data.bevel_resolution = 5

        spline = curve_data.splines.new(type="POLY")
        spline.points.add(len(points) - 1)
        for idx, (x, y, z) in enumerate(points):
            spline.points[idx].co = (x, y, z, 1.0)

        obj = bpy.data.objects.new(name, curve_data)
        bpy.context.collection.objects.link(obj)
        mat = self.create_emission_material(f"{name}_Mat", color, strength=emission_strength)
        if mat:
            obj.data.materials.append(mat)

    def import_glb_asset(
        self,
        name: str,
        filename: str,
        location: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        target_height: float = 2.4,
        rotation_euler: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        override_color: Optional[Tuple[float, float, float, float]] = None,
        emission_strength: float = 0.0,
        animate_turntable_rev: float = 0.0,
    ) -> None:
        """
        Imports an external 3D `.glb` character or prop from `.blender_cache/models/`,
        normalizes its bounding-box height to `target_height`, centers its base at `location`,
        and optionally applies a stylized emission/metallic shader or turntable animation.
        """
        if not HAS_BPY:
            return
        repo_root = Path(__file__).resolve().parents[2]
        glb_path = repo_root / ".blender_cache" / "models" / filename
        if not glb_path.exists():
            raise FileNotFoundError(f"Cached 3D model not found: {glb_path}")

        before_objs = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=str(glb_path))
        imported_objs = [o for o in bpy.data.objects if o not in before_objs]
        if not imported_objs:
            return

        # Remove any imported background/backdrop planes (e.g. in DragonAttenuation.glb)
        mesh_objs = []
        for obj in imported_objs:
            if obj.type == "MESH":
                if "cloth" in obj.name.lower() or "backdrop" in obj.name.lower() or "plane" in obj.name.lower():
                    bpy.data.objects.remove(obj, do_unlink=True)
                    continue
                mesh_objs.append(obj)

        if not mesh_objs:
            return

        bpy.context.view_layer.update()

        # Compute world-space bounding box across all imported meshes
        min_x = min_y = min_z = float("inf")
        max_x = max_y = max_z = float("-inf")
        for mobj in mesh_objs:
            for corner in mobj.bound_box:
                wc = mobj.matrix_world @ mathutils.Vector(corner)
                min_x, max_x = min(min_x, wc.x), max(max_x, wc.x)
                min_y, max_y = min(min_y, wc.y), max(max_y, wc.y)
                min_z, max_z = min(min_z, wc.z), max(max_z, wc.z)

        extent = max(max_x - min_x, max_y - min_y, max_z - min_z, 1e-4)
        scale_factor = target_height / extent
        center_x = 0.5 * (min_x + max_x)
        center_y = 0.5 * (min_y + max_y)
        base_z = min_z

        rig = bpy.data.objects.new(f"{name}_Rig", None)
        bpy.context.collection.objects.link(rig)

        # Parent top-level imported objects to our normalization rig
        imported_set = set( bpy.data.objects ) - before_objs
        for obj in imported_set:
            if obj.parent is None and obj != rig:
                orig_mat = obj.matrix_world.copy()
                obj.parent = rig
                obj.matrix_world = orig_mat

        # Offset and scale via an intermediate pivot so base sits cleanly at `location`
        rig.scale = (scale_factor, scale_factor, scale_factor)
        rig.rotation_euler = rotation_euler
        rot_mat = mathutils.Euler(rotation_euler).to_matrix()
        local_offset = rot_mat @ mathutils.Vector(
            (-center_x * scale_factor, -center_y * scale_factor, -base_z * scale_factor)
        )
        rig.location = (
            location[0] + local_offset.x,
            location[1] + local_offset.y,
            location[2] + local_offset.z,
        )

        if override_color is not None:
            mat = self.create_metallic_material(
                f"{name}_OverrideMat",
                override_color,
                metallic=0.72,
                roughness=0.24,
                emission_color=override_color,
                emission_strength=max(0.15, emission_strength * 0.22),
            )
            if mat:
                for mobj in mesh_objs:
                    mobj.data.materials.clear()
                    mobj.data.materials.append(mat)

        if abs(animate_turntable_rev) > 1e-4:
            rig.keyframe_insert(data_path="rotation_euler", frame=1)
            end_rot = list(rotation_euler)
            end_rot[2] += 2.0 * math.pi * animate_turntable_rev
            rig.rotation_euler = tuple(end_rot)
            rig.keyframe_insert(data_path="rotation_euler", frame=self.total_frames)

    @classmethod
    def run_cli(cls, builder_fn: Callable[["StudioScene"], None]) -> None:
        argv = sys.argv
        if "--" in argv:
            argv = argv[argv.index("--") + 1 :]
        else:
            argv = argv[1:]

        parser = argparse.ArgumentParser(description="Studio Headless Blender Scene")
        parser.add_argument("--output", required=True, help="Output PNG or MP4 path")
        parser.add_argument("--frame", type=int, default=None, help="Single preview frame number")
        parser.add_argument("--fps", type=int, default=24)
        parser.add_argument("--duration", type=float, default=4.0)
        parser.add_argument("--width", type=int, default=1920)
        parser.add_argument("--height", type=int, default=1080)
        parser.add_argument("--seed", type=int, default=42)
        args = parser.parse_args(argv)

        scene = cls(
            fps=args.fps,
            duration_sec=args.duration,
            width=args.width,
            height=args.height,
            seed=args.seed,
        )
        scene.reset_scene()
        builder_fn(scene)

        out_path = Path(args.output).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)

        if HAS_BPY:
            if scene.include_floor_grid:
                grid_mat = scene.create_emission_material(
                    "GridMat", (0.06, 0.11, 0.22, 1.0), strength=1.1
                )
                for g in range(-5, 6):
                    for seg_name, p0, p1 in [
                        (f"GridX_{g}", (-5.0, float(g), -1.5), (5.0, float(g), -1.5)),
                        (f"GridY_{g}", (float(g), -5.0, -1.5), (float(g), 5.0, -1.5)),
                    ]:
                        cdata = bpy.data.curves.new(name=seg_name, type="CURVE")
                        cdata.dimensions = "3D"
                        cdata.bevel_depth = 0.01
                        sp = cdata.splines.new(type="POLY")
                        sp.points.add(1)
                        sp.points[0].co = (*p0, 1.0)
                        sp.points[1].co = (*p1, 1.0)
                        cobj = bpy.data.objects.new(seg_name, cdata)
                        bpy.context.collection.objects.link(cobj)
                        if grid_mat:
                            cobj.data.materials.append(grid_mat)

            scn = bpy.context.scene
            safe_title = scene.title.replace(":", "\\:").replace("'", "")
            safe_sub = scene.subtitle.replace(":", "\\:").replace("'", "")

            if out_path.suffix.lower() == ".png":
                target_frame = args.frame if args.frame is not None else max(1, scene.total_frames // 2)
                scn.frame_set(target_frame)
                scn.render.image_settings.file_format = "PNG"
                raw_png = out_path.with_name(out_path.stem + "_raw.png")
                scn.render.filepath = str(raw_png)
                bpy.ops.render.render(write_still=True)

                subprocess.run(
                    [
                        "ffmpeg",
                        "-y",
                        "-loglevel",
                        "error",
                        "-i",
                        str(raw_png),
                        "-vf",
                        (
                            f"drawbox=x=48:y=36:w=1320:h=105:color=0x0B0F19@0.76:t=fill,"
                            f"drawtext=text='{safe_title}':fontcolor=white:fontsize=36:x=68:y=52,"
                            f"drawtext=text='{safe_sub}':fontcolor=0xFFB000:fontsize=23:x=68:y=102"
                        ),
                        str(out_path),
                    ],
                    check=True,
                )
                raw_png.unlink(missing_ok=True)
            else:
                # Render animation at efficient 1280x720 Cycles (12 samples) & upscale to 1080p MP4
                scn.render.resolution_x = 1280
                scn.render.resolution_y = 720
                scn.cycles.samples = 10
                render_fps = 12
                num_frames = max(2, int(round(scene.duration_sec * render_fps)))

                with tempfile.TemporaryDirectory() as tmpdir:
                    tmp_path = Path(tmpdir)
                    scn.render.image_settings.file_format = "PNG"
                    for idx in range(1, num_frames + 1):
                        mapped_f = int(
                            1 + (idx - 1) * (scene.total_frames - 1) / max(1, num_frames - 1)
                        )
                        scn.frame_set(mapped_f)
                        scn.render.filepath = str(tmp_path / f"f_{idx:04d}.png")
                        bpy.ops.render.render(write_still=True)

                    subprocess.run(
                        [
                            "ffmpeg",
                            "-y",
                            "-loglevel",
                            "error",
                            "-framerate",
                            str(render_fps),
                            "-i",
                            str(tmp_path / "f_%04d.png"),
                            "-vf",
                            (
                                f"scale={scene.width}:{scene.height}:flags=lanczos,"
                                f"minterpolate=fps={scene.fps}:mi_mode=blend,"
                                f"drawbox=x=48:y=36:w=1320:h=105:color=0x0B0F19@0.76:t=fill,"
                                f"drawtext=text='{safe_title}':fontcolor=white:fontsize=36:x=68:y=52,"
                                f"drawtext=text='{safe_sub}':fontcolor=0xFFB000:fontsize=23:x=68:y=102,"
                                f"fade=t=in:st=0:d=0.4,fade=t=out:st={max(0.2, scene.duration_sec - 0.4):.2f}:d=0.4"
                            ),
                            "-c:v",
                            "libx264",
                            "-pix_fmt",
                            "yuv420p",
                            str(out_path),
                        ],
                        check=True,
                    )
