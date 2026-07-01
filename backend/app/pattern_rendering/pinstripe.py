from PIL import Image, ImageDraw

from app.pattern_rendering.base import PatternRenderer, hex_to_rgb, require_swatch_count
from app.pattern_rendering.schemas import RenderParams, SwatchColor


class PinstripeRenderer(PatternRenderer):
    """Solid ground with thin, widely-spaced vertical stripes - the simplest of the five,
    distinguished from gingham/tartan by having no crossing grid at all."""

    pattern_type = "pinstripe"
    min_swatches = 2
    max_swatches = 2

    def render(self, swatches: list[SwatchColor], params: RenderParams) -> Image.Image:
        require_swatch_count(swatches, self.min_swatches, self.max_swatches, self.pattern_type)
        ordered = sorted(swatches, key=lambda s: s.role_index)
        ground = hex_to_rgb(ordered[0].hex_color)
        stripe = hex_to_rgb(ordered[1].hex_color)

        size = params.tile_size_px
        period = params.stripe_width_px * 4  # pinstripes are characteristically sparse
        pin_width = max(1, params.stripe_width_px // 8)

        image = Image.new("RGB", (size, size), ground)
        draw = ImageDraw.Draw(image)
        x = 0
        while x < size:
            draw.rectangle([x, 0, x + pin_width - 1, size - 1], fill=stripe)
            x += period
        return image
