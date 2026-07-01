from app.pattern_rendering.pinstripe import PinstripeRenderer
from app.pattern_rendering.schemas import RenderParams, SwatchColor

_GROUND = (0, 0, 0)
_STRIPE = (255, 255, 255)


def _swatches() -> list[SwatchColor]:
    return [
        SwatchColor(swatch_id=1, hex_color="#000000", role_index=0),
        SwatchColor(swatch_id=2, hex_color="#ffffff", role_index=1),
    ]


def test_pinstripe_ground_and_stripe_columns():
    params = RenderParams()  # tile_size_px=256, stripe_width_px=16 -> period=64, pin_width=2
    tile = PinstripeRenderer().render(_swatches(), params)

    assert tile.getpixel((0, 10)) == _STRIPE  # first pin at x=0
    assert tile.getpixel((10, 10)) == _GROUND  # between pins
    assert tile.getpixel((64, 10)) == _STRIPE  # second pin starts at x=period=64
    assert tile.getpixel((63, 10)) == _GROUND  # just before the second pin


def test_pinstripe_has_no_horizontal_variation_within_a_column():
    """Pinstripe has no crossing grid at all - a stripe column stays the stripe color for the
    full tile height, unlike gingham/tartan/houndstooth's crossing patterns."""
    params = RenderParams()
    tile = PinstripeRenderer().render(_swatches(), params)

    assert tile.getpixel((0, 0)) == _STRIPE
    assert tile.getpixel((0, 255)) == _STRIPE
