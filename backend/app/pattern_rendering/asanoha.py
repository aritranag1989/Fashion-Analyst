from PIL import Image

from app.pattern_rendering.base import PatternRenderer, hex_to_rgb, require_swatch_count
from app.pattern_rendering.schemas import RenderParams, SwatchColor


class AsanohaRenderer(PatternRenderer):
    """Traditional Japanese asanoha (hemp leaf) motif, simplified to a repeating diamond lattice:
    each cell is a diamond (a square rotated 45 degrees, via Manhattan distance from its center)
    split into 4 triangular facets. Two opposite facets (top-left and bottom-right) are the motif
    color and the other two are ground, producing a faceted pinwheel radiating from each diamond's
    center - a simplified geometric echo of real asanoha's 6-pointed radiating star at 4-fold
    rather than 6-fold symmetry, kept crisp-edged rather than curved for determinism. Pixels
    outside every diamond (the lattice gaps) are also ground color."""

    pattern_type = "asanoha"
    min_swatches = 2
    max_swatches = 2

    def render(self, swatches: list[SwatchColor], params: RenderParams) -> Image.Image:
        require_swatch_count(swatches, self.min_swatches, self.max_swatches, self.pattern_type)
        ordered = sorted(swatches, key=lambda s: s.role_index)
        ground = hex_to_rgb(ordered[0].hex_color)
        motif = hex_to_rgb(ordered[1].hex_color)

        size = params.tile_size_px
        cell = params.stripe_width_px
        half = cell // 2

        image = Image.new("RGB", (size, size))
        pixels = image.load()
        assert pixels is not None  # can't happen: load() on a freshly created "RGB" image

        for y in range(size):
            local_y = y % cell
            top = local_y < half
            for x in range(size):
                local_x = x % cell
                manhattan = abs(local_x - half) + abs(local_y - half)
                if manhattan > half:
                    pixels[x, y] = ground
                    continue
                left = local_x < half
                pixels[x, y] = motif if (top == left) else ground
        return image
