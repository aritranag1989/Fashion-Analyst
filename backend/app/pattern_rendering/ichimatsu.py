from PIL import Image

from app.pattern_rendering.base import PatternRenderer, hex_to_rgb, require_swatch_count
from app.pattern_rendering.schemas import RenderParams, SwatchColor


class IchimatsuRenderer(PatternRenderer):
    """Traditional Japanese ichimatsu (checkerboard) motif: a flat 2-color alternating grid.
    Deliberately does NOT blend a third tone at intersections the way gingham does - ichimatsu is
    a solid-block check, not a woven-crossing check, and that flat-block/no-blend distinction is
    what keeps it visually and technically distinct from gingham despite the shared grid math."""

    pattern_type = "ichimatsu"
    min_swatches = 2
    max_swatches = 2

    def render(self, swatches: list[SwatchColor], params: RenderParams) -> Image.Image:
        require_swatch_count(swatches, self.min_swatches, self.max_swatches, self.pattern_type)
        ordered = sorted(swatches, key=lambda s: s.role_index)
        color_a = hex_to_rgb(ordered[0].hex_color)
        color_b = hex_to_rgb(ordered[1].hex_color)

        size = params.tile_size_px
        cell = params.stripe_width_px

        image = Image.new("RGB", (size, size))
        pixels = image.load()
        assert pixels is not None  # can't happen: load() on a freshly created "RGB" image
        for y in range(size):
            row_parity = (y // cell) % 2
            for x in range(size):
                col_parity = (x // cell) % 2
                pixels[x, y] = color_a if (row_parity + col_parity) % 2 == 0 else color_b
        return image
