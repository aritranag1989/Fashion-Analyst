from pydantic import BaseModel, Field


class SwatchColor(BaseModel):
    swatch_id: int
    hex_color: str
    role_index: int


class RenderParams(BaseModel):
    tile_size_px: int = 256
    stripe_width_px: int = 16
    repeat_count: int = Field(default=1, ge=1)
