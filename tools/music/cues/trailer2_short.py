"""30 s cut of the story trailer for the vertical short: build 0:00-0:04, hit at 0:04,
160 bpm battle to 0:22 (accents at 0:10 and 0:16), riser, the title hit at 0:24, ring to 0:30."""
from cues.trailer2 import LUFS, battle, low_build, riser_and_title, setup  # noqa: F401


def build():
    s = setup("trailer2_short", "The Last Lantern (story trailer, short)")
    low_build(s, bars=2, seconds=4.0)
    battle(s, blocks=3, seconds=18.0)
    riser_and_title(s, rise_s=2.0, ring_s=5.5)
    s.ducks = [(3.88, 4.0, -14.0), (23.66, 24.0, -40.0)]  # drop-outs before the two big hits
    s.end_pad = 0.5
    return s
