from pathlib import Path

from PIL import Image


def extract_dominant_color(
    image_path: str | Path, sample_fraction: float = 0.5
) -> tuple[str, int, int, int]:
    """Extracts the dominant color from a swatch photo.

    Center-crops to `sample_fraction` of the photo (avoids background/shadow/table edges around
    the fabric), downsamples for speed, then reduces to a small adaptive palette via Pillow's
    median-cut quantizer and takes the most-covered palette entry. Quantizing first is the
    load-bearing step - calling getcolors() on the raw photo returns thousands of near-duplicate
    colors, so the max-count entry would be noise rather than the true dominant color.

    Known v1 limitation, intentionally not solved here (documented rather than half-implemented,
    same as the Image Understanding agent's own Phase 2 notes): a strong specular highlight in the
    crop could dominate the quantized palette on shiny fabrics.
    """
    image = Image.open(image_path).convert("RGB")
    width, height = image.size

    left = width * (1 - sample_fraction) / 2
    top = height * (1 - sample_fraction) / 2
    right = width * (1 + sample_fraction) / 2
    bottom = height * (1 + sample_fraction) / 2
    cropped = image.crop((round(left), round(top), round(right), round(bottom)))
    cropped = cropped.resize((100, 100))

    quantized = cropped.quantize(colors=5, method=Image.Quantize.MEDIANCUT)
    color_counts = quantized.getcolors()
    assert color_counts is not None  # can't happen: quantize(colors=5) caps well under maxcolors
    _, dominant_index = max(color_counts, key=lambda item: item[0])
    # Pillow's getcolors() stub covers both P-mode (int palette index) and RGB-mode (tuple) images
    # in one union return type; quantize() always returns P-mode, so this is always an int here.
    assert isinstance(dominant_index, int)

    palette = quantized.getpalette()
    assert palette is not None  # can't happen: getpalette() on a just-quantized "P" mode image
    offset = dominant_index * 3
    r, g, b = palette[offset], palette[offset + 1], palette[offset + 2]
    hex_color = f"#{r:02x}{g:02x}{b:02x}"
    return hex_color, r, g, b
