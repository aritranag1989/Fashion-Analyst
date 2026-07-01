from app.pattern_rendering.houndstooth import HoundstoothRenderer
from app.pattern_rendering.schemas import RenderParams, SwatchColor

_COLOR_A = (0, 0, 0)
_COLOR_B = (255, 255, 255)


def _swatches() -> list[SwatchColor]:
    return [
        SwatchColor(swatch_id=1, hex_color="#000000", role_index=0),
        SwatchColor(swatch_id=2, hex_color="#ffffff", role_index=1),
    ]


def test_houndstooth_motif_shape_within_the_first_block():
    params = RenderParams()  # stripe_width_px=16 -> cell=4, block=16
    tile = HoundstoothRenderer().render(_swatches(), params)

    assert tile.getpixel((0, 0)) == _COLOR_B  # unit(0,0) = True -> motif color
    assert tile.getpixel((12, 0)) == _COLOR_A  # unit(0,3) = False -> background color


def test_houndstooth_adjacent_blocks_interlock_via_color_swap():
    """The foreground/background swap every other block (in both axes) is what makes adjacent
    motifs interlock instead of just repeating identically like a plain grid."""
    params = RenderParams()
    tile = HoundstoothRenderer().render(_swatches(), params)

    # same relative motif position (0,0), but the next block over (x=16) - swapped
    assert tile.getpixel((16, 0)) == _COLOR_A
    # the diagonal block (row+1, col+1) swaps back to match the original block
    assert tile.getpixel((16, 16)) == _COLOR_B
