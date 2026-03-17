from tools.info import get_image_info
from tools.transform import crop, rotate
from tools.filters import (
    adjust_brightness,
    adjust_contrast,
    adjust_saturation,
    sharpen,
    blur,
    grayscale,
    sepia,
    vignette,
)

ALL_TOOLS = [
    get_image_info,
    crop,
    rotate,
    adjust_brightness,
    adjust_contrast,
    adjust_saturation,
    sharpen,
    blur,
    grayscale,
    sepia,
    vignette,
]
