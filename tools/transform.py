"""Tools: crop and rotate."""

from tools import state
from tools.magick import run


def crop(geometry: str) -> str:
    """Crop the image.

    Args:
        geometry: Crop specification. Formats:
            - "WxH+X+Y"  — exact pixel crop, e.g. "300x200+50+25"
            - "WxH"      — crop from top-left, e.g. "400x400"
            - "1:1"      — crop to aspect ratio from center (also accepts "16:9", "4:3", etc.)

    Returns a message indicating success or describing any error.
    """
    path = state.get_working_path()
    args_map = {"geometry": geometry}

    if ":" in geometry and "+" not in geometry and not geometry[0].isdigit() is False:
        # Aspect ratio shorthand — compute centered crop
        try:
            w_ratio, h_ratio = map(int, geometry.split(":"))
            # Get current dimensions first
            ok, info = run(["identify", "-format", "%wx%h", path])
            if not ok:
                return f"Could not read image dimensions: {info}"
            img_w, img_h = map(int, info.strip().split("x"))
            scale = min(img_w / w_ratio, img_h / h_ratio)
            crop_w = int(w_ratio * scale)
            crop_h = int(h_ratio * scale)
            offset_x = (img_w - crop_w) // 2
            offset_y = (img_h - crop_h) // 2
            geometry = f"{crop_w}x{crop_h}+{offset_x}+{offset_y}"
        except (ValueError, ZeroDivisionError) as e:
            return f"Invalid aspect ratio '{geometry}': {e}"

    cmd = [path, "-crop", geometry, "+repage", path]
    success, msg = run(cmd)
    state.record_step("crop", args_map, success, ["magick"] + cmd, msg if not success else "")
    return "Cropped successfully." if success else f"Crop failed: {msg}"


def rotate(degrees: float) -> str:
    """Rotate the image clockwise by the given number of degrees.

    Args:
        degrees: Rotation angle in degrees. Positive = clockwise. Common values: 90, 180, 270, -90.
            Non-right-angle rotations expand the canvas and fill with the background color.

    Returns a message indicating success or describing any error.
    """
    path = state.get_working_path()
    cmd = [path, "-rotate", str(degrees), path]
    success, msg = run(cmd)
    state.record_step("rotate", {"degrees": degrees}, success, ["magick"] + cmd, msg if not success else "")
    return f"Rotated {degrees}° successfully." if success else f"Rotate failed: {msg}"
