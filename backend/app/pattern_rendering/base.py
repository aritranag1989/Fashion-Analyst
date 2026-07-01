from abc import ABC, abstractmethod

from PIL import Image

from app.pattern_rendering.schemas import RenderParams, SwatchColor


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def blend_rgb(a: tuple[int, int, int], b: tuple[int, int, int], weight: float = 0.5) -> tuple[int, int, int]:
    """weight is a's share of the blend; 0.5 = an even 50/50 blend."""
    return (
        round(a[0] * weight + b[0] * (1 - weight)),
        round(a[1] * weight + b[1] * (1 - weight)),
        round(a[2] * weight + b[2] * (1 - weight)),
    )


def require_swatch_count(swatches: list[SwatchColor], min_n: int, max_n: int, pattern_type: str) -> None:
    if not (min_n <= len(swatches) <= max_n):
        raise ValueError(
            f"{pattern_type} requires between {min_n} and {max_n} swatches, got {len(swatches)}"
        )


class PatternRenderer(ABC):
    """One deterministic renderer per classic weave pattern type. render() always receives
    already-validated ordered swatches and returns exactly one repeat-unit tile; render_tiled()
    (shared, not overridden) applies RenderParams.repeat_count on top."""

    pattern_type: str
    min_swatches: int
    max_swatches: int

    @abstractmethod
    def render(self, swatches: list[SwatchColor], params: RenderParams) -> Image.Image:
        """Returns one repeat-unit tile sized params.tile_size_px x params.tile_size_px."""

    def render_tiled(self, swatches: list[SwatchColor], params: RenderParams) -> Image.Image:
        unit = self.render(swatches, params)
        if params.repeat_count <= 1:
            return unit
        size = unit.width
        canvas = Image.new("RGB", (size * params.repeat_count, size * params.repeat_count))
        for row in range(params.repeat_count):
            for col in range(params.repeat_count):
                canvas.paste(unit, (col * size, row * size))
        return canvas
