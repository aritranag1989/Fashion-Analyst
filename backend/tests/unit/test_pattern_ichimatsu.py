from app.pattern_rendering.ichimatsu import IchimatsuRenderer
from app.pattern_rendering.schemas import RenderParams, SwatchColor

_COLOR_A = (0, 0, 0)
_COLOR_B = (255, 255, 255)


def _swatches() -> list[SwatchColor]:
    return [
        SwatchColor(swatch_id=1, hex_color="#000000", role_index=0),
        SwatchColor(swatch_id=2, hex_color="#ffffff", role_index=1),
    ]


def test_ichimatsu_alternating_cells():
    params = RenderParams()  # stripe_width_px=16 -> cell=16
    tile = IchimatsuRenderer().render(_swatches(), params)

    assert tile.getpixel((0, 0)) == _COLOR_A
    assert tile.getpixel((16, 0)) == _COLOR_B
    assert tile.getpixel((0, 16)) == _COLOR_B
    assert tile.getpixel((16, 16)) == _COLOR_A


def test_ichimatsu_has_no_blended_third_tone_unlike_gingham():
    """The whole point of ichimatsu vs. gingham: every pixel must be pure A or pure B, never a
    blend, even at the exact cell-boundary crossing points gingham would blend."""
    params = RenderParams()
    tile = IchimatsuRenderer().render(_swatches(), params)

    colors_seen = {tile.getpixel((x, y)) for x in range(0, 32, 4) for y in range(0, 32, 4)}
    assert colors_seen == {_COLOR_A, _COLOR_B}
