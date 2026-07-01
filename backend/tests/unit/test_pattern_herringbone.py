from app.pattern_rendering.herringbone import HerringboneRenderer
from app.pattern_rendering.schemas import RenderParams, SwatchColor

_GROUND = (0, 0, 0)
_DIAGONAL = (255, 255, 255)


def _swatches() -> list[SwatchColor]:
    return [
        SwatchColor(swatch_id=1, hex_color="#000000", role_index=0),
        SwatchColor(swatch_id=2, hex_color="#ffffff", role_index=1),
    ]


def test_herringbone_band_direction_alternates():
    """The alternation is load-bearing: without it this degenerates into plain diagonal
    pinstripe. Checks one fixed x-column (x=4) at two y-rows within each of the first two bands:
    band 0's diagonal stripe passes through x=4 near the band's top and has moved away by the
    band's bottom (drifting right); band 1's stripe is absent from x=4 near its top and arrives
    there by its bottom (drifting left) - the opposite trend, which is the reversal that matters.
    (Deliberately not "scan the row for the leftmost diagonal pixel": with tiled stripes, a
    different, wrapped-around stripe instance can become the leftmost one at a different y,
    which looks like a trend reversal but isn't actually testing the same stripe.)
    """
    params = RenderParams()  # tile_size_px=256, stripe_width_px=16 -> band_height=16
    tile = HerringboneRenderer().render(_swatches(), params)

    # band 0 spans y in [0, 16): the x=0..16 (slope +1) stripe covers x=4 near the top (y=2) and
    # has shifted past it by the bottom (y=14).
    assert tile.getpixel((4, 2)) == _DIAGONAL
    assert tile.getpixel((4, 14)) == _GROUND

    # band 1 spans y in [16, 32): direction reversed (slope -1) - the stripe hasn't reached x=4
    # near the top (y=18) but has arrived there by the bottom (y=30).
    assert tile.getpixel((4, 18)) == _GROUND
    assert tile.getpixel((4, 30)) == _DIAGONAL


def test_herringbone_ground_color_is_present_between_stripes():
    params = RenderParams()
    tile = HerringboneRenderer().render(_swatches(), params)
    colors_seen = {tile.getpixel((x, 8)) for x in range(tile.width)}
    assert _GROUND in colors_seen
    assert _DIAGONAL in colors_seen
