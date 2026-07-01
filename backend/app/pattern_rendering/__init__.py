from functools import lru_cache

from app.pattern_rendering.asanoha import AsanohaRenderer
from app.pattern_rendering.base import PatternRenderer
from app.pattern_rendering.gingham import GinghamRenderer
from app.pattern_rendering.herringbone import HerringboneRenderer
from app.pattern_rendering.houndstooth import HoundstoothRenderer
from app.pattern_rendering.ichimatsu import IchimatsuRenderer
from app.pattern_rendering.kasuri import KasuriRenderer
from app.pattern_rendering.pinstripe import PinstripeRenderer
from app.pattern_rendering.seigaiha import SeigaihaRenderer
from app.pattern_rendering.tartan import TartanRenderer

_RENDERERS: dict[str, type[PatternRenderer]] = {
    "gingham": GinghamRenderer,
    "tartan": TartanRenderer,
    "houndstooth": HoundstoothRenderer,
    "herringbone": HerringboneRenderer,
    "pinstripe": PinstripeRenderer,
    "kasuri": KasuriRenderer,
    "asanoha": AsanohaRenderer,
    "seigaiha": SeigaihaRenderer,
    "ichimatsu": IchimatsuRenderer,
}

PATTERN_TYPES = list(_RENDERERS.keys())


@lru_cache
def get_renderer(pattern_type: str) -> PatternRenderer:
    return _RENDERERS[pattern_type]()
