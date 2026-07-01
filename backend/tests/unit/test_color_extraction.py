from PIL import Image

from app.pattern_rendering.color_extraction import extract_dominant_color


def test_solid_color_image_returns_exact_hex(tmp_path):
    image = Image.new("RGB", (200, 200), (26, 43, 60))
    path = tmp_path / "solid.png"
    image.save(path)

    hex_color, r, g, b = extract_dominant_color(path)

    assert hex_color == "#1a2b3c"
    assert (r, g, b) == (26, 43, 60)


def test_two_tone_image_returns_majority_color_not_average(tmp_path):
    """Proves quantize-then-max-count picks the true dominant color rather than being thrown
    off by a minority high-contrast patch within the sampled center crop."""
    image = Image.new("RGB", (200, 200), (26, 43, 60))
    for x in range(60, 80):
        for y in range(60, 80):
            image.putpixel((x, y), (220, 20, 20))
    path = tmp_path / "two_tone.png"
    image.save(path)

    hex_color, r, g, b = extract_dominant_color(path)

    assert (r, g, b) == (26, 43, 60)
    assert hex_color == "#1a2b3c"


def test_content_outside_center_crop_is_ignored(tmp_path):
    """The crop excludes the outer edges (background/shadow near a swatch photo's border) -
    painting the very corner a different color should not change the extracted result."""
    image = Image.new("RGB", (200, 200), (26, 43, 60))
    for x in range(10):
        for y in range(10):
            image.putpixel((x, y), (0, 200, 0))
    path = tmp_path / "corner_painted.png"
    image.save(path)

    hex_color, _, _, _ = extract_dominant_color(path)

    assert hex_color == "#1a2b3c"
