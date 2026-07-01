from app.pattern_rendering.asanoha import AsanohaRenderer
from app.pattern_rendering.schemas import RenderParams, SwatchColor

_GROUND = (0, 0, 0)
_MOTIF = (255, 255, 255)


def _swatches() -> list[SwatchColor]:
    return [
        SwatchColor(swatch_id=1, hex_color="#000000", role_index=0),
        SwatchColor(swatch_id=2, hex_color="#ffffff", role_index=1),
    ]


def test_asanoha_diamond_facets_within_the_first_cell():
    params = RenderParams()  # stripe_width_px=16 -> cell=16, half=8
    tile = AsanohaRenderer().render(_swatches(), params)

    # (6,6): manhattan=4 <= 8 (inside diamond), top-left facet -> motif
    assert tile.getpixel((6, 6)) == _MOTIF
    # (2,2): manhattan=12 > 8 (outside diamond, the lattice gap) -> ground
    assert tile.getpixel((2, 2)) == _GROUND
    # (10,10): manhattan=4 <= 8, bottom-right facet -> also motif (the pinwheel symmetry)
    assert tile.getpixel((10, 10)) == _MOTIF


def test_asanoha_lattice_tiles_identically_with_no_swap():
    """Unlike houndstooth, the diamond lattice repeats identically cell-to-cell - there is no
    foreground/background swap between adjacent cells."""
    params = RenderParams()
    tile = AsanohaRenderer().render(_swatches(), params)

    # (22,6) = (6,6) shifted one full cell (16px) to the right -> same facet, same color
    assert tile.getpixel((22, 6)) == tile.getpixel((6, 6)) == _MOTIF
