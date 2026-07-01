from app.pattern_rendering.kasuri import KasuriRenderer
from app.pattern_rendering.schemas import RenderParams, SwatchColor

_GROUND = (0, 0, 0)
_MOTIF = (255, 255, 255)


def _swatches() -> list[SwatchColor]:
    return [
        SwatchColor(swatch_id=1, hex_color="#000000", role_index=0),
        SwatchColor(swatch_id=2, hex_color="#ffffff", role_index=1),
    ]


def test_kasuri_cross_motif_center_and_ground_corner():
    params = RenderParams()  # stripe_width_px=16 -> cell=16, center=8, half_arm=2, margin=4
    tile = KasuriRenderer().render(_swatches(), params)

    assert tile.getpixel((8, 8)) == _MOTIF  # dead center of the cross
    assert tile.getpixel((0, 0)) == _GROUND  # cell corner, well outside both bars


def test_kasuri_motif_repeats_identically_with_no_swap():
    """Distinct from houndstooth: adjacent cells show the identical motif on the identical
    ground, with no foreground/background swap."""
    params = RenderParams()
    tile = KasuriRenderer().render(_swatches(), params)

    assert tile.getpixel((24, 8)) == tile.getpixel((8, 8)) == _MOTIF
    assert tile.getpixel((16, 16)) == tile.getpixel((0, 0)) == _GROUND
