"""
Procedural Headless Blender (`bpy`) Scene Builder.
Enforces the Zero-Binary Git ("Code-as-Scene") rule: all geometry, shader node trees,
three-point studio lighting, and camera orbits are constructed purely from Python code.
Also provides a built-in deterministic software 3D preview renderer when invoked outside
the `blender` binary so keyframe checks work in any environment.
"""

from __future__ import annotations

import argparse
import math
import sys
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
    """Unified RGBA colors (linear sRGB for Blender shaders & hex for overlays)."""
    BG_DARK = (0.015, 0.021, 0.040, 1.0)
    CYAN = (0.000, 0.780, 1.000, 1.0)
    AMBER = (1.000, 0.450, 0.000, 1.0)
    VIOLET = (0.350, 0.080, 0.950, 1.0)
    EMERALD = (0.010, 0.520, 0.250, 1.0)
    WHITE = (0.950, 0.960, 0.980, 1.0)


@dataclass
class ProceduralCurve3D:
    """Stores a 3D parametric curve for both bpy curve generation and software preview."""
    name: str
    points: List[Tuple[float, float, float]]
    color: Tuple[float, float, float, float]
    bevel_radius: float = 0.04


@dataclass
class StudioScene:
    """High-level declarative wrapper over headless Blender (`bpy`)."""
    fps: int = 60
    duration_sec: float = 5.0
    width: int = 1920
    height: int = 1080
    seed: int = 42
    title: str = "Studio 3D Scene"
    subtitle: str = "Procedural Blender Rig"
    curves: List[ProceduralCurve3D] = field(default_factory=list)
    camera_orbit: Tuple[float, float, float, float] = (8.5, 24.0, -35.0, 55.0)

    @property
    def total_frames(self) -> int:
        return max(1, int(round(self.fps * self.duration_sec)))

    def reset_scene(self) -> None:
        """Clears default cube/light/camera and configures 1080p60 /Cycles or EEVEE."""
        if not HAS_BPY:
            return
        bpy.ops.wm.read_factory_settings(use_empty=True)
        scn = bpy.context.scene
        scn.render.fps = self.fps
        scn.frame_start = 1
        scn.frame_end = self.total_frames
        scn.render.resolution_x = self.width
        scn.render.resolution_y = self.height
        scn.render.resolution_percentage = 100

        # Configure dark obsidian world background
        world = bpy.data.worlds.new("StudioWorld")
        scn.world = world
        world.use_nodes = True
        bg_node = world.node_tree.nodes.get("Background")
        if bg_node:
            bg_node.inputs[0].default_value = StudioPalette.BG_DARK
            bg_node.inputs[1].default_value = 1.0

    def setup_three_point_lighting(self, energy_scale: float = 1.0) -> None:
        """Creates Key, Fill, and Rim area lights procedurally."""
        if not HAS_BPY:
            return
        lights = [
            ("KeyLight", (5.0, -5.0, 6.0), 450.0 * energy_scale, StudioPalette.WHITE, 3.0),
            ("FillLight", (-6.0, -3.0, 3.0), 180.0 * energy_scale, StudioPalette.CYAN, 4.5),
            ("RimLight", (0.0, 6.0, 5.0), 320.0 * energy_scale, StudioPalette.VIOLET, 2.5),
        ]
        for name, loc, energy, color, size in lights:
            light_data = bpy.data.lights.new(name=name, type="AREA")
            light_data.energy = energy
            light_data.color = color[:3]
            light_data.size = size
            light_obj = bpy.data.objects.new(name=name, object_data=light_data)
            bpy.context.collection.objects.link(light_obj)
            light_obj.location = loc
            direction = mathutils.Vector((0.0, 0.0, 0.0)) - mathutils.Vector(loc)
            light_obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

    def create_orbit_camera(
        self,
        radius: float = 8.5,
        elevation_deg: float = 24.0,
        start_angle_deg: float = -35.0,
        end_angle_deg: float = 55.0,
    ) -> None:
        """Creates a camera attached to an empty rig that smoothly orbits the origin."""
        self.camera_orbit = (radius, elevation_deg, start_angle_deg, end_angle_deg)
        if not HAS_BPY:
            return
        rig = bpy.data.objects.new("CameraOrbitRig", None)
        bpy.context.collection.objects.link(rig)

        cam_data = bpy.data.cameras.new("StudioCamera")
        cam_data.lens = 38.0
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
        """Builds a procedural Emission + Principled BSDF shader node tree."""
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
        """Generates a smooth 3D beveled curve from a mathematical function f(t) -> (x,y,z)."""
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

    def render_software_preview_ppm(self, frame: int, output_png: Path) -> None:
        """
        Renders a deterministic, anti-aliased 3D perspective projection of the scene's
        parametric curves and coordinate axes directly to PNG (via FFmpeg) so keyframe
        inspection works even when headless Blender is not installed locally.
        """
        import subprocess
        import tempfile

        w, h = self.width, self.height
        # Use 1280x720 internal buffer for fast preview generation, scaled cleanly
        pw, ph = 1280, 720
        buf = bytearray(pw * ph * 3)

        # Fill dark studio obsidian gradient background (#0B0F19 -> #111827)
        for y in range(ph):
            r = int(11 + (y / ph) * 6)
            g = int(15 + (y / ph) * 10)
            b = int(25 + (y / ph) * 16)
            row_slice = bytes((r, g, b)) * pw
            buf[y * pw * 3 : (y + 1) * pw * 3] = row_slice

        radius, elev_deg, start_deg, end_deg = self.camera_orbit
        progress = (frame - 1) / max(1, self.total_frames - 1)
        azim_rad = math.radians(start_deg + (end_deg - start_deg) * progress)
        elev_rad = math.radians(elev_deg)

        cam_x = radius * math.sin(azim_rad) * math.cos(elev_rad)
        cam_y = -radius * math.cos(azim_rad) * math.cos(elev_rad)
        cam_z = radius * math.sin(elev_rad)

        # Forward, Right, Up basis vectors looking at origin (0, 0, 0)
        fx, fy, fz = -cam_x, -cam_y, -cam_z
        fl = math.sqrt(fx * fx + fy * fy + fz * fz) or 1.0
        fx, fy, fz = fx / fl, fy / fl, fz / fl

        # World up (0, 0, 1)
        rx, ry, rz = fy * 1.0 - fz * 0.0, fz * 0.0 - fx * 1.0, fx * 0.0 - fy * 0.0
        rl = math.sqrt(rx * rx + ry * ry + rz * rz) or 1.0
        rx, ry, rz = rx / rl, ry / rl, rz / rl

        ux = ry * fz - rz * fy
        uy = rz * fx - rx * fz
        uz = rx * fy - ry * fx

        fov_scale = ph * 0.92

        def project(pt: Tuple[float, float, float]) -> Optional[Tuple[int, int, float]]:
            dx, dy, dz = pt[0] - cam_x, pt[1] - cam_y, pt[2] - cam_z
            cz = dx * fx + dy * fy + dz * fz
            if cz <= 0.2:
                return None
            cx = dx * rx + dy * ry + dz * rz
            cy = dx * ux + dy * uy + dz * uz
            sx = int(pw * 0.5 + (cx / cz) * fov_scale)
            sy = int(ph * 0.5 - (cy / cz) * fov_scale)
            return sx, sy, cz

        def draw_dot(px: int, py: int, rgb: Tuple[int, int, int], rad: int) -> None:
            for dy in range(-rad, rad + 1):
                yy = py + dy
                if yy < 0 or yy >= ph:
                    continue
                for dx in range(-rad, rad + 1):
                    xx = px + dx
                    if xx < 0 or xx >= pw:
                        continue
                    if dx * dx + dy * dy <= rad * rad:
                        idx = (yy * pw + xx) * 3
                        # Additive-style glow blend
                        buf[idx] = min(255, int(buf[idx] * 0.25 + rgb[0] * 0.9))
                        buf[idx + 1] = min(255, int(buf[idx + 1] * 0.25 + rgb[1] * 0.9))
                        buf[idx + 2] = min(255, int(buf[idx + 2] * 0.25 + rgb[2] * 0.9))

        def draw_segment(
            p0: Tuple[float, float, float],
            p1: Tuple[float, float, float],
            rgb: Tuple[int, int, int],
            thickness: int = 2,
        ) -> None:
            pr0 = project(p0)
            pr1 = project(p1)
            if not pr0 or not pr1:
                return
            x0, y0, _ = pr0
            x1, y1, _ = pr1
            steps = max(abs(x1 - x0), abs(y1 - y0), 1)
            if steps > pw * 2:
                return
            for s in range(0, steps + 1, max(1, thickness // 2)):
                t = s / steps
                ix = int(x0 + (x1 - x0) * t)
                iy = int(y0 + (y1 - y0) * t)
                draw_dot(ix, iy, rgb, thickness)

        # Draw 3D reference floor grid at z = -1.5
        grid_rgb = (32, 48, 75)
        for g in range(-4, 5):
            draw_segment((-4.0, float(g), -1.5), (4.0, float(g), -1.5), grid_rgb, 1)
            draw_segment((float(g), -4.0, -1.5), (float(g), 4.0, -1.5), grid_rgb, 1)

        # Draw primary 3D axes
        draw_segment((-3.8, 0.0, 0.0), (3.8, 0.0, 0.0), (90, 120, 160), 2)
        draw_segment((0.0, -2.5, 0.0), (0.0, 2.5, 0.0), (70, 100, 140), 1)
        draw_segment((0.0, 0.0, -1.5), (0.0, 0.0, 1.8), (70, 100, 140), 1)

        # Draw all parametric 3D curves with animated reveal / phase
        for curve in self.curves:
            rgb = (
                min(255, int(curve.color[0] ** 0.45 * 255)),
                min(255, int(curve.color[1] ** 0.45 * 255)),
                min(255, int(curve.color[2] ** 0.45 * 255)),
            )
            thick = max(2, int(curve.bevel_radius * 65))
            pts = curve.points
            for i in range(len(pts) - 1):
                draw_segment(pts[i], pts[i + 1], rgb, thick)

        output_png.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(suffix=".ppm", delete=False) as tmp:
            ppm_path = Path(tmp.name)
            tmp.write(f"P6\n{pw} {ph}\n255\n".encode("ascii"))
            tmp.write(buf)

        try:
            safe_title = self.title.replace(":", "\\:")
            safe_sub = f"{self.subtitle}  |  Frame {frame}/{self.total_frames}".replace(":", "\\:")
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-loglevel",
                    "error",
                    "-i",
                    str(ppm_path),
                    "-vf",
                    (
                        f"scale={w}:{h}:flags=lanczos,"
                        f"drawbox=x=48:y=36:w=1180:h=105:color=0x0B0F19@0.78:t=fill,"
                        f"drawtext=text='{safe_title}':fontcolor=white:fontsize=38:x=68:y=52,"
                        f"drawtext=text='{safe_sub}':"
                        f"fontcolor=0x00E5FF:fontsize=24:x=68:y=102"
                    ),
                    str(output_png),
                ],
                check=True,
            )
        finally:
            ppm_path.unlink(missing_ok=True)

    @classmethod
    def run_cli(cls, builder_fn: Callable[["StudioScene"], None]) -> None:
        """Standard CLI entry point for both `blender -b -P` and standalone preview."""
        argv = sys.argv
        if "--" in argv:
            argv = argv[argv.index("--") + 1 :]
        else:
            argv = argv[1:]

        parser = argparse.ArgumentParser(description="Studio Headless Blender Scene")
        parser.add_argument("--output", required=True, help="Output PNG or MP4 path")
        parser.add_argument("--frame", type=int, default=None, help="Single preview frame number")
        parser.add_argument("--fps", type=int, default=60)
        parser.add_argument("--duration", type=float, default=5.0)
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
            scn = bpy.context.scene
            if args.frame is not None:
                scn.frame_set(args.frame)
                scn.render.image_settings.file_format = "PNG"
                scn.render.filepath = str(out_path)
                bpy.ops.render.render(write_still=True)
            else:
                scn.render.image_settings.file_format = "FFMPEG"
                scn.render.ffmpeg.format = "MPEG4"
                scn.render.ffmpeg.codec = "H264"
                scn.render.ffmpeg.constant_rate_factor = "HIGH"
                scn.render.filepath = str(out_path)
                bpy.ops.render.render(animation=True)
        else:
            # Deterministic software 3D renderer when `blender` binary is not installed
            target_frame = args.frame if args.frame is not None else max(1, scene.total_frames // 2)
            if out_path.suffix.lower() == ".png":
                scene.render_software_preview_ppm(target_frame, out_path)
            else:
                # Render keyframe sequence and encode smooth MP4 via FFmpeg
                import subprocess
                import tempfile

                with tempfile.TemporaryDirectory() as tmpdir:
                    tmp_path = Path(tmpdir)
                    preview_fps = min(scene.fps, 24)
                    num_f = max(1, int(scene.duration_sec * preview_fps))
                    for f_idx in range(1, num_f + 1):
                        mapped_f = int(1 + (f_idx - 1) * (scene.total_frames - 1) / max(1, num_f - 1))
                        scene.render_software_preview_ppm(mapped_f, tmp_path / f"f_{f_idx:04d}.png")
                    subprocess.run(
                        [
                            "ffmpeg",
                            "-y",
                            "-loglevel",
                            "error",
                            "-framerate",
                            str(preview_fps),
                            "-i",
                            str(tmp_path / "f_%04d.png"),
                            "-r",
                            str(scene.fps),
                            "-c:v",
                            "libx264",
                            "-pix_fmt",
                            "yuv420p",
                            str(out_path),
                        ],
                        check=True,
                    )
