"""Tools: image filters — brightness, contrast, saturation, sharpen, blur, grayscale, sepia, vignette."""

from tools import state
from tools.magick import run


def adjust_brightness(amount: int) -> str:
    """Brighten or darken the image.

    Args:
        amount: Brightness adjustment from -100 (very dark) to +100 (very bright). 0 = no change.

    Returns a message indicating success or describing any error.
    """
    path = state.get_working_path()
    cmd = [path, "-brightness-contrast", f"{amount}x0", path]
    success, msg = run(cmd)
    state.record_step("adjust_brightness", {"amount": amount}, success, ["magick"] + cmd, msg if not success else "")
    return f"Brightness adjusted by {amount}." if success else f"Brightness adjustment failed: {msg}"


def adjust_contrast(amount: int) -> str:
    """Increase or decrease image contrast.

    Args:
        amount: Contrast adjustment from -100 (flat) to +100 (high contrast). 0 = no change.

    Returns a message indicating success or describing any error.
    """
    path = state.get_working_path()
    cmd = [path, "-brightness-contrast", f"0x{amount}", path]
    success, msg = run(cmd)
    state.record_step("adjust_contrast", {"amount": amount}, success, ["magick"] + cmd, msg if not success else "")
    return f"Contrast adjusted by {amount}." if success else f"Contrast adjustment failed: {msg}"


def adjust_saturation(amount: int) -> str:
    """Boost or reduce color saturation.

    Args:
        amount: Saturation as a percentage. 100 = no change, 0 = grayscale, 200 = double saturation.

    Returns a message indicating success or describing any error.
    """
    path = state.get_working_path()
    # -modulate brightness,saturation,hue — keep brightness/hue at 100
    cmd = [path, "-modulate", f"100,{amount},100", path]
    success, msg = run(cmd)
    state.record_step("adjust_saturation", {"amount": amount}, success, ["magick"] + cmd, msg if not success else "")
    return f"Saturation set to {amount}%." if success else f"Saturation adjustment failed: {msg}"


def sharpen(sigma: float = 1.0) -> str:
    """Sharpen the image using an unsharp mask.

    Args:
        sigma: Sharpening strength. 0.5 = subtle, 1.0 = moderate, 2.0+ = strong.

    Returns a message indicating success or describing any error.
    """
    path = state.get_working_path()
    radius = sigma * 2
    cmd = [path, "-unsharp", f"{radius}x{sigma}+1.5+0.05", path]
    success, msg = run(cmd)
    state.record_step("sharpen", {"sigma": sigma}, success, ["magick"] + cmd, msg if not success else "")
    return f"Sharpened with sigma={sigma}." if success else f"Sharpen failed: {msg}"


def blur(sigma: float = 2.0) -> str:
    """Apply a Gaussian blur to soften the image.

    Args:
        sigma: Blur radius. 1.0 = light blur, 3.0 = moderate, 8.0+ = heavy blur.

    Returns a message indicating success or describing any error.
    """
    path = state.get_working_path()
    radius = sigma * 2
    cmd = [path, "-blur", f"{radius}x{sigma}", path]
    success, msg = run(cmd)
    state.record_step("blur", {"sigma": sigma}, success, ["magick"] + cmd, msg if not success else "")
    return f"Blurred with sigma={sigma}." if success else f"Blur failed: {msg}"


def grayscale() -> str:
    """Convert the image to grayscale (black and white).

    Returns a message indicating success or describing any error.
    """
    path = state.get_working_path()
    cmd = [path, "-colorspace", "Gray", path]
    success, msg = run(cmd)
    state.record_step("grayscale", {}, success, ["magick"] + cmd, msg if not success else "")
    return "Converted to grayscale." if success else f"Grayscale conversion failed: {msg}"


def sepia() -> str:
    """Apply a warm sepia tone effect to the image.

    Returns a message indicating success or describing any error.
    """
    path = state.get_working_path()
    cmd = [path, "-sepia-tone", "80%", path]
    success, msg = run(cmd)
    state.record_step("sepia", {}, success, ["magick"] + cmd, msg if not success else "")
    return "Sepia tone applied." if success else f"Sepia failed: {msg}"


def vignette(strength: int = 50) -> str:
    """Apply a vignette effect, darkening the edges of the image.

    Args:
        strength: How dark the edges become, 1–100. 30 = subtle, 60 = strong.

    Returns a message indicating success or describing any error.
    """
    path = state.get_working_path()
    # Get dimensions to compute a proportional vignette radius
    ok, info = run(["identify", "-format", "%wx%h", path])
    if not ok:
        return f"Could not read image dimensions: {info}"
    img_w, img_h = map(int, info.strip().split("x"))
    radius = int(min(img_w, img_h) * (strength / 100.0))
    sigma = radius // 2 or 1
    cmd = [path, "-background", "black", "-vignette", f"0x{sigma}+{radius}+{radius}", path]
    success, msg = run(cmd)
    state.record_step("vignette", {"strength": strength}, success, ["magick"] + cmd, msg if not success else "")
    return f"Vignette applied at strength {strength}." if success else f"Vignette failed: {msg}"
