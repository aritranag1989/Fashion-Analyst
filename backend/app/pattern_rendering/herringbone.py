from PIL import Image, ImageDraw

from app.pattern_rendering.base import PatternRenderer, hex_to_rgb, require_swatch_count
from app.pattern_rendering.schemas import RenderParams, SwatchColor


class HerringboneRenderer(PatternRenderer):
    """Horizontal bands of parallel diagonal segments, alternating direction ("/" vs "\\") every
    band so adjacent bands meet in a continuous chevron seam. The alternation is load-bearing -
    without it this degenerates into plain diagonal pinstripe."""

    pattern_type = "herringbone"
    min_swatches = 2
    max_swatches = 2

    def render(self, swatches: list[SwatchColor], params: RenderParams) -> Image.Image:
        require_swatch_count(swatches, self.min_swatches, self.max_swatches, self.pattern_type)
        ordered = sorted(swatches, key=lambda s: s.role_index)
        ground = hex_to_rgb(ordered[0].hex_color)
        diagonal = hex_to_rgb(ordered[1].hex_color)

        size = params.tile_size_px
        band_height = params.stripe_width_px
        line_width = max(2, band_height // 3)

        image = Image.new("RGB", (size, size), ground)
        draw = ImageDraw.Draw(image)

        num_bands = size // band_height
        for band_index in range(num_bands):
            y_top = band_index * band_height
            y_bottom = y_top + band_height
            direction_down = band_index % 2 == 0  # alternates every band -> the chevron seam

            start = -band_height
            while start < size + band_height:
                if direction_down:
                    x0, x1 = start, start + band_height
                else:
                    x0, x1 = start + band_height, start
                draw.polygon(
                    [
                        (x0, y_top),
                        (x0 + line_width, y_top),
                        (x1 + line_width, y_bottom),
                        (x1, y_bottom),
                    ],
                    fill=diagonal,
                )
                start += band_height
        return image
