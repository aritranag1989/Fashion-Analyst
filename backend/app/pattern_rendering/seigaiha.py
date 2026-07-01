import math

from PIL import Image

from app.pattern_rendering.base import PatternRenderer, hex_to_rgb, require_swatch_count
from app.pattern_rendering.schemas import RenderParams, SwatchColor


class SeigaihaRenderer(PatternRenderer):
    """Traditional Japanese seigaiha ("blue ocean waves") motif: rows of nested concentric arcs,
    each row's arc centers sitting on that row's bottom edge and offset horizontally by half the
    center spacing from the row above/below, so each arc appears to nest inside the arc above it.
    Ring banding (2 alternating tones by distance from the nearest center) always falls in {0, 1}
    for every pixel by construction (max distance within a row is R*sqrt(2) < 2*R), so the tile is
    fully covered with no "outside all arcs" gap to special-case."""

    pattern_type = "seigaiha"
    min_swatches = 2
    max_swatches = 2

    def render(self, swatches: list[SwatchColor], params: RenderParams) -> Image.Image:
        require_swatch_count(swatches, self.min_swatches, self.max_swatches, self.pattern_type)
        ordered = sorted(swatches, key=lambda s: s.role_index)
        outer_ring = hex_to_rgb(ordered[0].hex_color)
        inner_ring = hex_to_rgb(ordered[1].hex_color)

        size = params.tile_size_px
        band = params.stripe_width_px  # ring width AND row height
        col_spacing = band * 2

        image = Image.new("RGB", (size, size))
        pixels = image.load()
        assert pixels is not None  # can't happen: load() on a freshly created "RGB" image

        for y in range(size):
            row_index = y // band
            center_y = (row_index + 1) * band
            x_offset = band if (row_index % 2 == 1) else 0
            for x in range(size):
                shifted = x - x_offset
                k = shifted // col_spacing
                left = k * col_spacing
                right = left + col_spacing
                nearest = left if (shifted - left) <= (right - shifted) else right
                center_x = nearest + x_offset

                dist = math.hypot(x - center_x, y - center_y)
                ring = int(dist // band)  # always 0 or 1 - see class docstring
                pixels[x, y] = outer_ring if ring == 0 else inner_ring
        return image
