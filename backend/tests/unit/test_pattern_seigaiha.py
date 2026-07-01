from app.pattern_rendering.schemas import RenderParams, SwatchColor
from app.pattern_rendering.seigaiha import SeigaihaRenderer

_OUTER = (0, 0, 0)
_INNER = (255, 255, 255)


def _swatches() -> list[SwatchColor]:
    return [
        SwatchColor(swatch_id=1, hex_color="#000000", role_index=0),
        SwatchColor(swatch_id=2, hex_color="#ffffff", role_index=1),
    ]


def test_seigaiha_ring_bands_in_the_first_row():
    params = RenderParams()  # stripe_width_px=16 -> band=16, col_spacing=32
    tile = SeigaihaRenderer().render(_swatches(), params)

    # row_index=0, center=(0,16): dist=8.0 -> ring 0
    assert tile.getpixel((0, 8)) == _OUTER
    # row_index=0, nearest center=(0,16): dist=sqrt(16**2+8**2)=~17.89 -> ring 1
    assert tile.getpixel((16, 8)) == _INNER


def test_seigaiha_second_row_centers_are_offset_by_half_spacing():
    """The half-spacing horizontal offset on alternating rows is what makes the arcs nest into the
    row above instead of forming a plain rectangular grid of circles."""
    params = RenderParams()
    tile = SeigaihaRenderer().render(_swatches(), params)

    # row_index=1, center=(16,32): dist=8.0 -> ring 0
    assert tile.getpixel((16, 24)) == _OUTER
    # row_index=1, nearest center=(-16,32) via the row's x_offset=16: dist=~17.89 -> ring 1
    assert tile.getpixel((0, 24)) == _INNER
