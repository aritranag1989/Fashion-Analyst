from app.pattern_rendering.schemas import RenderParams, SwatchColor
from app.pattern_rendering.tartan import TartanRenderer

_RED = (255, 0, 0)
_GREEN = (0, 255, 0)
_BLUE = (0, 0, 255)


def _swatches() -> list[SwatchColor]:
    return [
        SwatchColor(swatch_id=1, hex_color="#ff0000", role_index=0),
        SwatchColor(swatch_id=2, hex_color="#00ff00", role_index=1),
        SwatchColor(swatch_id=3, hex_color="#0000ff", role_index=2),
    ]


def test_tartan_same_color_crossings_stay_pure():
    params = RenderParams()  # stripe_width_px=16
    tile = TartanRenderer().render(_swatches(), params)

    assert tile.getpixel((0, 0)) == _RED
    assert tile.getpixel((16, 16)) == _GREEN
    assert tile.getpixel((32, 32)) == _BLUE


def test_tartan_different_color_crossings_blend_asymmetrically_toward_the_column():
    """Tartan's interwoven look comes from an asymmetric blend (the vertical/'warp' stripe reads
    as dominant at a crossing) - distinct from gingham's flat 50/50 blend. Swapping which axis is
    which must change the result, proving the blend really is direction-dependent."""
    params = RenderParams()
    tile = TartanRenderer().render(_swatches(), params)

    # row=red (y=0), col=green (x=16): column (green) should dominate
    assert tile.getpixel((16, 0)) == (102, 153, 0)
    # row=green (y=16), col=red (x=0): column (red) should dominate - a different result even
    # though it's the same two colors, because the row/column roles are swapped
    assert tile.getpixel((0, 16)) == (153, 102, 0)
