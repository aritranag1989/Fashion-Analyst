from PIL import Image

from app.pattern_rendering.base import PatternRenderer, blend_rgb, hex_to_rgb, require_swatch_count
from app.pattern_rendering.schemas import RenderParams, SwatchColor

# Horizontal ("weft") stripes are blended into the vertical ("warp") stripes at less than 50%, so
# the warp color reads as dominant at a crossing - this is what gives tartan its interwoven look,
# as opposed to gingham's flat 50/50 blend.
_WARP_DOMINANCE = 0.6


class TartanRenderer(PatternRenderer):
    """N-colored (2-6) ordered "sett" repeated as stripes in both directions. Same-color
    crossings stay pure; different-color crossings blend to emulate interweaving. The most
    visually complex of the five renderers since it echoes the full ordered color sequence,
    not just 2 colors like gingham/houndstooth/herringbone/pinstripe."""

    pattern_type = "tartan"
    min_swatches = 2
    max_swatches = 6

    def render(self, swatches: list[SwatchColor], params: RenderParams) -> Image.Image:
        require_swatch_count(swatches, self.min_swatches, self.max_swatches, self.pattern_type)
        ordered = sorted(swatches, key=lambda s: s.role_index)
        colors = [hex_to_rgb(s.hex_color) for s in ordered]
        num_colors = len(colors)

        size = params.tile_size_px
        stripe = params.stripe_width_px

        def sequence_color(coord: int) -> tuple[int, int, int]:
            return colors[(coord // stripe) % num_colors]

        image = Image.new("RGB", (size, size))
        pixels = image.load()
        assert pixels is not None  # can't happen: load() on a freshly created "RGB" image
        for y in range(size):
            row_color = sequence_color(y)
            for x in range(size):
                col_color = sequence_color(x)
                if row_color == col_color:
                    pixels[x, y] = row_color
                else:
                    pixels[x, y] = blend_rgb(col_color, row_color, weight=_WARP_DOMINANCE)
        return image
