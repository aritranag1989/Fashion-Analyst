from PIL import Image

from app.pattern_rendering.base import PatternRenderer, blend_rgb, hex_to_rgb, require_swatch_count
from app.pattern_rendering.schemas import RenderParams, SwatchColor


class GinghamRenderer(PatternRenderer):
    """Classic 2-color gingham: alternating stripe bands in both axes produce 3 visible tones -
    pure A, pure B, and their 50/50 blend where an A-band crosses a B-band. The blended third
    tone is what makes this read as gingham rather than a plain 2-color checkerboard."""

    pattern_type = "gingham"
    min_swatches = 2
    max_swatches = 2

    def render(self, swatches: list[SwatchColor], params: RenderParams) -> Image.Image:
        require_swatch_count(swatches, self.min_swatches, self.max_swatches, self.pattern_type)
        ordered = sorted(swatches, key=lambda s: s.role_index)
        color_a = hex_to_rgb(ordered[0].hex_color)
        color_b = hex_to_rgb(ordered[1].hex_color)
        blended = blend_rgb(color_a, color_b)

        size = params.tile_size_px
        cell = params.stripe_width_px

        image = Image.new("RGB", (size, size))
        pixels = image.load()
        assert pixels is not None  # can't happen: load() on a freshly created "RGB" image
        for y in range(size):
            row_is_a = (y // cell) % 2 == 0
            for x in range(size):
                col_is_a = (x // cell) % 2 == 0
                if row_is_a and col_is_a:
                    pixels[x, y] = color_a
                elif not row_is_a and not col_is_a:
                    pixels[x, y] = color_b
                else:
                    pixels[x, y] = blended
        return image
