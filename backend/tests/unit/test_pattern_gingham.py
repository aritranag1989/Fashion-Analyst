from app.pattern_rendering.gingham import GinghamRenderer
from app.pattern_rendering.schemas import RenderParams, SwatchColor

_COLOR_A = (0, 0, 0)
_COLOR_B = (255, 255, 255)
_BLENDED = (128, 128, 128)  # round(0*0.5 + 255*0.5) = round(127.5) = 128 (Python round-half-to-even)


def _swatches() -> list[SwatchColor]:
    return [
        SwatchColor(swatch_id=1, hex_color="#000000", role_index=0),
        SwatchColor(swatch_id=2, hex_color="#ffffff", role_index=1),
    ]


def test_gingham_pure_a_and_pure_b_cells():
    params = RenderParams()  # stripe_width_px=16
    tile = GinghamRenderer().render(_swatches(), params)

    assert tile.getpixel((0, 0)) == _COLOR_A  # row A, col A
    assert tile.getpixel((16, 16)) == _COLOR_B  # row B, col B


def test_gingham_crossing_cells_are_the_blended_third_tone():
    """The blended third tone at A/B crossings is what makes this read as gingham rather than a
    plain 2-color checkerboard - the one detail that must not be skipped."""
    params = RenderParams()
    tile = GinghamRenderer().render(_swatches(), params)

    assert tile.getpixel((16, 0)) == _BLENDED  # row A, col B
    assert tile.getpixel((0, 16)) == _BLENDED  # row B, col A
