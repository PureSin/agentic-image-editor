"""Tool: inspect the current working image."""

from tools import state
from tools.magick import run


def get_image_info() -> str:
    """Get metadata about the current working image: dimensions, format, colorspace, and file size.
    Always call this first before deciding which edits to apply.
    """
    path = state.get_working_path()
    cmd = ["identify", "-format",
           "format=%m  size=%wx%h  colorspace=%[colorspace]  filesize=%b", path]
    success, output = run(cmd)
    if success:
        return output or "Image identified successfully (no output)."
    return f"Error reading image: {output}"
