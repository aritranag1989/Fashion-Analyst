from PIL import Image

from app.pattern_rendering.base import PatternRenderer, hex_to_rgb, require_swatch_count
from app.pattern_rendering.schemas import RenderParams, SwatchColor

# A simplified digital approximation of the classic houndstooth/dogstooth silhouette - an
# asymmetric jagged unit, not a reproduction of a specific historical weave structure. True where
# the unit's "motif" color should be drawn (before the per-block foreground/background swap
# below, which is what makes adjacent motifs interlock instead of repeating identically).
_HOUNDSTOOTH_UNIT = (
    (True, True, True, False),
    (True, True, False, False),
    (True, False, False, True),
    (False, False, True, True),
)
_UNIT_SIZE = 4


class HoundstoothRenderer(PatternRenderer):
    """Fixed jagged motif tiled with foreground/background swapped every other block (in both
    axes), which is what makes the check read as broken/interlocking rather than a plain
    rectangular grid like gingham/tartan."""

    pattern_type = "houndstooth"
    min_swatches = 2
    max_swatches = 2

    def render(self, swatches: list[SwatchColor], params: RenderParams) -> Image.Image:
        require_swatch_count(swatches, self.min_swatches, self.max_swatches, self.pattern_type)
        ordered = sorted(swatches, key=lambda s: s.role_index)
        color_a = hex_to_rgb(ordered[0].hex_color)
        color_b = hex_to_rgb(ordered[1].hex_color)

        cell = max(1, params.stripe_width_px // _UNIT_SIZE)
        block = cell * _UNIT_SIZE
        size = params.tile_size_px

        image = Image.new("RGB", (size, size))
        pixels = image.load()
        assert pixels is not None  # can't happen: load() on a freshly created "RGB" image

        for y in range(size):
            block_row, local_y = divmod(y, block)
            unit_row = min(local_y // cell, _UNIT_SIZE - 1)
            for x in range(size):
                block_col, local_x = divmod(x, block)
                unit_col = min(local_x // cell, _UNIT_SIZE - 1)
                is_motif = _HOUNDSTOOTH_UNIT[unit_row][unit_col]
                swap = (block_row + block_col) % 2 == 1
                pixels[x, y] = color_b if (is_motif != swap) else color_a
        return image
