from PIL import Image

from app.pattern_rendering.base import PatternRenderer, hex_to_rgb, require_swatch_count
from app.pattern_rendering.schemas import RenderParams, SwatchColor


class KasuriRenderer(PatternRenderer):
    """Simplified approximation of a kasuri/ikat cloth: a small, bold cross ("+") motif repeated
    identically on a grid over a solid ground, evoking the small discrete cross/arrow motifs
    common on real kasuri-dyed cloth. Deliberately crisp-edged rather than reproducing kasuri's
    characteristic soft dye-bleed edges (per the simplified-geometric fidelity level). Unlike
    houndstooth, there is no foreground/background swap between grid cells - every cell repeats
    the identical motif on the identical ground, keeping this an isolated repeated accent motif
    rather than an interlocking check."""

    pattern_type = "kasuri"
    min_swatches = 2
    max_swatches = 2

    def render(self, swatches: list[SwatchColor], params: RenderParams) -> Image.Image:
        require_swatch_count(swatches, self.min_swatches, self.max_swatches, self.pattern_type)
        ordered = sorted(swatches, key=lambda s: s.role_index)
        ground = hex_to_rgb(ordered[0].hex_color)
        motif = hex_to_rgb(ordered[1].hex_color)

        size = params.tile_size_px
        cell = params.stripe_width_px
        center = cell // 2
        half_arm = max(1, cell // 8)
        margin = cell // 4
        arm_lo, arm_hi = margin, cell - margin

        image = Image.new("RGB", (size, size))
        pixels = image.load()
        assert pixels is not None  # can't happen: load() on a freshly created "RGB" image

        for y in range(size):
            local_y = y % cell
            for x in range(size):
                local_x = x % cell
                vertical = (
                    center - half_arm <= local_x <= center + half_arm - 1
                    and arm_lo <= local_y < arm_hi
                )
                horizontal = (
                    center - half_arm <= local_y <= center + half_arm - 1
                    and arm_lo <= local_x < arm_hi
                )
                pixels[x, y] = motif if (vertical or horizontal) else ground
        return image
