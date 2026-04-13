#!/usr/bin/env python3
"""Nononono2 - 灰都殺伐代行: 2-lane parry action game"""

import curses
import time
import random
import os
import subprocess
import copy

from cli_parris import sound

os.environ['LANG'] = 'en_US.UTF-8'

# macOS: switch to ASCII input
try:
    subprocess.run(
        ["osascript", "-e",
         'tell application "System Events" to key code 102'],
        capture_output=True, timeout=2)
except Exception:
    pass

# ─── Constants ───
BAR_LEN = 60
PERFECT_POS = 45
ATK_POS = 30  # attack point position (middle)

# Lane definitions: J=parry main, F=parry sub, SPACE=attack
LANES = [
    {"key": "J", "label": "J", "ord": [ord('j'), ord('J')]},
    {"key": "F", "label": "F", "ord": [ord('f'), ord('F')]},
    {"key": "SPACE", "label": "SPACE", "ord": [ord(' ')]},
]

WEAPON = {
    "name": "殺意の出刃包丁",
    "atk": 3,
    "lock_sec": 0.3,
    "atk_cooldown": 0.8,
}

BOSS = {
    "name": "堕落した都知事",
    "aa": "{o_o}",
    "hp": 40,
    "max_hp": 40,
    "atk": 5,
    "marks": 3,
    "marks_max": 3,
    # parry zones: (before_PERFECT, after_PERFECT) - before=long, after=short
    "parry_zone_j": (5, 2),   # J: standard
    "parry_zone_f": (8, 3),   # F: wider (easier)
}

# Wave patterns: (lane_index, delay, speed)
# lane 0 = J (melody), lane 1 = F (rhythm/bass drum)
# BPM ~90: ♩=0.667s  ♪=0.333s
# F keeps steady beat, J plays melody over it
S = 3.0   # J bullet speed
SF = 3.0  # F bullet speed (same as J so they align at parry line)

# F rhythm: 8-beat (eighth notes at 90bpm = 0.333s interval)
def _f_beat(start, count, interval=0.333):
    """Generate steady F 8-beat rhythm."""
    return [(1, start + i * interval, SF) for i in range(count)]

# BPM90: ♩=0.667s ♪=0.333s
Q = 0.667   # quarter note
E = 0.333   # eighth note

WAVE_PATTERNS = [
    # ── 8-beat F only (intro) ──
    [*_f_beat(0, 8)],

    # ── F 8-beat + J quarter notes ──
    [*_f_beat(0, 8), (0, 0.0, S), (0, Q, S), (0, Q*2, S), (0, Q*3, S)],

    # ── F 8-beat + J ♪♪♩ ♪♪♩ ──
    [*_f_beat(0, 8),
     (0, 0.0, S), (0, E, S), (0, Q, S),
     (0, Q*2, S), (0, Q*2+E, S), (0, Q*3, S)],

    # ── F 8-beat + J syncopated ──
    [*_f_beat(0, 8),
     (0, 0.0, S), (0, Q, S), (0, Q+E, S), (0, Q*2, S), (0, Q*3, S)],

    # ── F 8-beat + J march pickup ♩♩ ♪♪♪♪ ──
    [*_f_beat(0, 8),
     (0, 0.0, S), (0, Q, S),
     (0, Q*2, S), (0, Q*2+E, S), (0, Q*3, S), (0, Q*3+E, S)],

    # ── F 8-beat + J trepak ♪♪♪♪♪♪♪♪ ──
    [*_f_beat(0, 8),
     (0, 0.0, S), (0, E, S), (0, E*2, S), (0, E*3, S),
     (0, E*4, S), (0, E*5, S), (0, E*6, S), (0, E*7, S)],

    # ── F 8-beat + J dotted ♩.♪ ♩.♪ ──
    [*_f_beat(0, 8),
     (0, 0.0, S), (0, Q+E, S), (0, Q*2, S), (0, Q*3+E, S)],

    # ── F 8-beat + J 3-note phrase ──
    [*_f_beat(0, 8),
     (0, 0.0, S), (0, Q, S), (0, Q*2, S)],

    # ── F 8-beat + J rest then burst ──
    [*_f_beat(0, 8),
     (0, Q*2, S), (0, Q*2+E, S), (0, Q*3, S), (0, Q*3+E, S)],

    # ── F 8-beat + J off-beat melody ──
    [*_f_beat(0, 8),
     (0, E/2, S), (0, E*1.5, S), (0, E*2.5, S), (0, E*3.5, S),
     (0, E*4.5, S), (0, E*5.5, S), (0, E*6.5, S), (0, E*7.5, S)],
]

# Harder: slightly faster (BPM105ish)
SH = 2.2   # hard J speed
SFH = 3.0  # hard F speed

def _f_beat_h(start, count, interval=0.333):
    return [(1, start + i * interval, SFH) for i in range(count)]

WAVE_PATTERNS_HARD = [
    # ── F 16-beat + J rapid melody ──
    [*_f_beat_h(0, 16, E/2),
     (0, 0.0, SH), (0, E, SH), (0, E*2, SH), (0, E*3, SH),
     (0, E*4, SH), (0, E*5, SH), (0, E*6, SH), (0, E*7, SH)],

    # ── F 8-beat + J unison ──
    [*_f_beat_h(0, 8),
     (0, 0.0, SH), (0, E, SH), (0, E*2, SH), (0, E*3, SH),
     (0, E*4, SH), (0, E*5, SH), (0, E*6, SH), (0, E*7, SH)],

    # ── F 8-beat + J 16th rush ──
    [*_f_beat_h(0, 8),
     (0, 0.0, SH), (0, E/2, SH), (0, E, SH), (0, E*1.5, SH),
     (0, E*2, SH), (0, E*2.5, SH), (0, E*3, SH), (0, E*3.5, SH),
     (0, E*4, SH), (0, E*4.5, SH), (0, E*5, SH), (0, E*5.5, SH)],

    # ── F 8-beat + J off-beat syncopation ──
    [*_f_beat_h(0, 8),
     (0, E/2, SH), (0, E*1.5, SH), (0, E*2.5, SH), (0, E*3.5, SH),
     (0, E*4.5, SH), (0, E*5.5, SH)],

    # ── F double-pump + J finale ──
    [*_f_beat_h(0, 16, E/2),
     (0, 0.0, SH), (0, E, SH), (0, E*2, SH),
     (0, E*4, SH), (0, E*5, SH), (0, E*6, SH),
     (0, Q*4, SH), (0, Q*4+E, SH)],
]

ITEMS = [
    {"name": "緋の雫", "desc": "HP+30", "effect": "heal", "value": 30},
    {"name": "灰霧の壺", "desc": "敵減速3s", "effect": "slow", "value": 3.0},
    {"name": "朽ちた投刃", "desc": "DMG 8", "effect": "damage", "value": 8},
    {"name": "受け流しの残滓", "desc": "判定拡大5s", "effect": "parry_up", "value": 5.0},
]


class Bullet:
    """A single ● traveling along a lane."""
    __slots__ = ['lane', 'start_time', 'speed', 'active', 'result', 'result_time', 'pos', 'btype']

    def __init__(self, lane, start_time, speed, btype="parry"):
        self.lane = lane
        self.start_time = start_time
        self.speed = speed
        self.active = True
        self.result = None
        self.btype = btype  # "parry" or "attack"
        self.result_time = 0.0
        self.pos = 0.0


def _hsv_to_rgb_curses(h, s, v):
    """Convert HSV (h:0-360, s:0-1, v:0-1) to curses RGB (0-1000)."""
    import colorsys
    r, g, b = colorsys.hsv_to_rgb(h / 360.0, s, v)
    return int(r * 1000), int(g * 1000), int(b * 1000)


def draw_lane_bar(pos, pz_before, pz_after, bullet_active):
    """Draw a single lane's bar. pz_before/pz_after = Good zone width before/after PERFECT."""
    bar = list("━" * BAR_LEN)
    zone_start = max(0, PERFECT_POS - pz_before)
    zone_end = min(BAR_LEN - 1, PERFECT_POS + pz_after)
    for i in range(zone_start, zone_end + 1):
        bar[i] = "░"
    bar[PERFECT_POS] = "█"
    if bullet_active:
        p = int(pos)
        if 0 <= p < BAR_LEN:
            bar[p] = "●"
    return "".join(bar)


def judge(pos, pz_before, pz_after):
    """Judge parry timing. pz_before = Good zone before PERFECT, pz_after = after."""
    p = int(pos)
    zone_start = PERFECT_POS - pz_before
    zone_end = PERFECT_POS + pz_after
    if p == PERFECT_POS:
        return "PERFECT"
    elif zone_start <= p <= zone_end:
        return "Good"
    else:
        return "MISS"


def marks_str(current, maximum):
    return "●" * current + "○" * (maximum - current)


def hp_bar_str(hp, max_hp, length=20):
    filled = int(length * hp / max_hp) if max_hp > 0 else 0
    return "█" * filled + "░" * (length - filled)


def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.keypad(True)
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_YELLOW, -1)   # PERFECT
    curses.init_pair(2, curses.COLOR_GREEN, -1)    # Good
    curses.init_pair(3, curses.COLOR_RED, -1)      # MISS / damage
    curses.init_pair(4, curses.COLOR_CYAN, -1)     # subtitle
    curses.init_pair(5, curses.COLOR_MAGENTA, -1)  # attack msg
    curses.init_pair(6, curses.COLOR_WHITE, curses.COLOR_RED)  # flash
    curses.init_pair(7, curses.COLOR_BLACK, curses.COLOR_YELLOW)  # perfect flash
    curses.init_pair(8, curses.COLOR_BLUE, -1)    # attack bullet (blue)
    curses.init_pair(9, curses.COLOR_CYAN, -1)    # attack point marker

    # Rainbow: use custom color if terminal supports it
    can_rgb = curses.can_change_color() and curses.COLORS >= 256
    RAINBOW_BG_COLOR = 100   # custom color slot for background
    RAINBOW_FG_COLOR = 101   # custom color slot for foreground text
    RAINBOW_PAIR = 10
    if can_rgb:
        curses.init_color(RAINBOW_BG_COLOR, 0, 0, 0)
        curses.init_color(RAINBOW_FG_COLOR, 1000, 1000, 1000)
        curses.init_pair(RAINBOW_PAIR, RAINBOW_FG_COLOR, RAINBOW_BG_COLOR)

    # Pre-generate sounds
    sound._ensure_sounds()

    def run_game():
        boss = copy.deepcopy(BOSS)
        player_hp = 100
        player_max_hp = 100
        zanki = 0
        zanki_max = 10
        combo = 0
        max_combo = 0
        total_parry = 0
        stats = {"PERFECT": 0, "Good": 0, "MISS": 0}

        lock_until = 0.0
        atk_cooldown_until = 0.0
        atk_msg = ""
        atk_msg_until = 0.0

        # Zanki burst (Space hold when zanki is MAX)
        zanki_burst_active = False
        zanki_burst_last_tick = 0.0
        ZANKI_DRAIN_RATE = 4.0    # zanki drained per second
        ZANKI_DPS = 8             # damage per second during burst

        # Items
        inventory = [copy.deepcopy(ITEMS[0]), None, None, None]
        item_cursor = 0
        slow_until = 0.0
        parry_up_until = 0.0

        # Visual effects
        flash_until = 0.0
        flash_color = 0
        hitstop_until = 0.0

        # Bullets
        bullets = []
        wave_cooldown = 1.5
        last_wave_time = time.time()
        result_display = {}  # lane -> (result, time)
        melody_note = 0  # J lane melody counter (cycles through notes)

        game_start = time.time()

        while True:
            now = time.time()

            # Hitstop: freeze game logic but keep rendering
            if now < hitstop_until:
                stdscr.refresh()
                try:
                    key = stdscr.getch()
                except Exception:
                    key = -1
                time.sleep(0.016)
                continue

            stdscr.erase()
            h, w = stdscr.getmaxyx()
            is_locked = now < lock_until
            is_slow = now < slow_until
            parry_bonus = 2 if now < parry_up_until else 0

            # ── Zanki burst tick (Space held) ──
            if zanki_burst_active:
                dt = now - zanki_burst_last_tick
                zanki_burst_last_tick = now
                # drain zanki
                zanki = max(0, zanki - ZANKI_DRAIN_RATE * dt)
                # deal continuous damage
                tick_dmg = ZANKI_DPS * dt
                if boss["marks"] > 0:
                    boss["hp"] = max(1, boss["hp"] - tick_dmg)
                else:
                    boss["hp"] = max(0, boss["hp"] - tick_dmg)
                # flash while burning
                flash_until = now + 0.03
                flash_color = 7
                # end burst when zanki empty
                if zanki <= 0:
                    zanki = 0
                    zanki_burst_active = False
                    atk_msg = ">>> 残火消失... <<<"
                    atk_msg_until = now + 1.0

            # ── Spawn waves ──
            boss_alive = boss["hp"] > 0
            if boss_alive and now - last_wave_time > wave_cooldown:
                # pick pattern based on boss HP
                if boss["hp"] < boss["max_hp"] * 0.4:
                    pool = WAVE_PATTERNS + WAVE_PATTERNS_HARD
                elif boss["hp"] < boss["max_hp"] * 0.7:
                    pool = WAVE_PATTERNS
                else:
                    pool = WAVE_PATTERNS[:8]  # easier patterns

                pattern = random.choice(pool)
                # next wave starts after this pattern ends + small gap
                pattern_len = max(d for _, d, _ in pattern)
                speed_mult = 1.5 if is_slow else 1.0
                wave_cooldown = pattern_len + random.uniform(0.8, 1.5)
                for lane_idx, delay, spd in pattern:
                    b = Bullet(lane_idx, now + delay, spd * speed_mult)
                    bullets.append(b)
                last_wave_time = now

            # ── Update bullets ──
            active_per_lane = {i: [] for i in range(len(LANES))}
            for b in bullets:
                if not b.active:
                    continue
                if now < b.start_time:
                    continue  # not yet launched
                elapsed = now - b.start_time
                t = min(elapsed / b.speed, 1.0)
                b.pos = t * (BAR_LEN - 1)

                active_per_lane[b.lane].append(b)

                # parry bullet passes parry zone → becomes "missed" (gray, keeps flowing)
                lane_pz = boss["parry_zone_j"] if b.lane == 0 else boss["parry_zone_f"]
                lane_pz_after = lane_pz[1] + parry_bonus
                if b.btype == "parry" and b.pos > PERFECT_POS + lane_pz_after + 1 and b.result != "MISS":
                    b.btype = "missed"
                    b.result = "MISS"
                    result_display[b.lane] = ("MISS", now)
                    stats["MISS"] += 1
                    player_hp = max(0, player_hp - boss["atk"])
                    zanki = max(0, zanki - 2)
                    combo = 0
                    sound.play("miss")

                # bullet reaches end → deactivate
                if b.pos >= BAR_LEN - 1:
                    b.active = False
                    b.result_time = now
                    if b.result is None:
                        b.result = ""

            # Clean up old bullets
            bullets = [b for b in bullets if b.active or (now - b.result_time < 0.5)]

            # ── Header ──
            try:
                stdscr.addstr(0, 2, "灰 都 殺 伐 代 行", curses.A_BOLD)
            except curses.error:
                pass

            # ── Boss display ──
            row = 2
            boss_hp_b = hp_bar_str(boss["hp"], boss["max_hp"], 20)
            m_str = marks_str(boss["marks"], boss["marks_max"])
            boss_line = f"  {boss['aa']} {boss['name']}  [{boss_hp_b}] {int(boss['hp'])}/{boss['max_hp']}  {m_str}"
            if boss["hp"] <= 0:
                try:
                    stdscr.addstr(row, 0, boss_line, curses.A_DIM)
                except curses.error:
                    pass
            else:
                try:
                    stdscr.addstr(row, 0, boss_line, curses.A_BOLD)
                except curses.error:
                    pass

            # status effects
            row = 3
            effects = []
            if is_slow:
                effects.append(f"[減速 {slow_until - now:.1f}s]")
            if parry_bonus > 0:
                effects.append(f"[判定拡大 {parry_up_until - now:.1f}s]")
            if effects:
                try:
                    stdscr.addstr(row, 2, " ".join(effects), curses.color_pair(4))
                except curses.error:
                    pass

            # ── Lanes ──
            row = 5
            pz_j = boss["parry_zone_j"]  # (before, after)
            pz_f = boss["parry_zone_f"]

            for lane_idx, lane in enumerate(LANES):
                if lane_idx == 2:
                    # SPACE lane: zanki burst bar
                    try:
                        stdscr.addstr(row, 1, f"[{lane['label']}]", curses.A_BOLD)
                    except curses.error:
                        pass

                    if zanki_burst_active:
                        # draining zanki bar
                        ratio = zanki / zanki_max
                        filled = int(BAR_LEN * ratio)
                        gauge = "█" * filled + "░" * (BAR_LEN - filled)
                        try:
                            stdscr.addstr(row, 14, gauge, curses.color_pair(1) | curses.A_BOLD)
                            stdscr.addstr(row, 14 + BAR_LEN + 2, "BURNING!", curses.color_pair(1) | curses.A_BOLD)
                        except curses.error:
                            pass
                    elif zanki >= zanki_max:
                        # zanki MAX → yellow bar, ready to burst
                        try:
                            stdscr.addstr(row, 14, "█" * BAR_LEN, curses.color_pair(1) | curses.A_BOLD)
                            stdscr.addstr(row, 14 + BAR_LEN + 2, "HOLD SPACE!", curses.color_pair(1) | curses.A_BOLD)
                        except curses.error:
                            pass
                    elif now < atk_cooldown_until:
                        # attack cooldown
                        atk_cd = WEAPON["atk_cooldown"]
                        atk_remain = atk_cooldown_until - now
                        atk_ratio = 1.0 - (atk_remain / atk_cd)
                        atk_filled = int(BAR_LEN * atk_ratio)
                        atk_gauge = "█" * atk_filled + "░" * (BAR_LEN - atk_filled)
                        try:
                            stdscr.addstr(row, 14, atk_gauge, curses.color_pair(3))
                        except curses.error:
                            pass
                    else:
                        try:
                            stdscr.addstr(row, 14, "█" * BAR_LEN, curses.color_pair(2) | curses.A_BOLD)
                            stdscr.addstr(row, 14 + BAR_LEN + 2, "READY!", curses.color_pair(2) | curses.A_BOLD)
                        except curses.error:
                            pass
                    row += 2
                    continue

                # Parry lanes (J/F)
                try:
                    stdscr.addstr(row, 1, f"[{lane['label']}]", curses.A_BOLD)
                except curses.error:
                    pass

                lane_bullets = active_per_lane.get(lane_idx, [])
                pz = pz_j if lane_idx == 0 else pz_f
                pz_b = pz[0] + parry_bonus  # before (longer)
                pz_a = pz[1] + parry_bonus  # after (shorter)
                if lane_bullets:
                    bar = list("━" * BAR_LEN)
                    zone_start = max(0, PERFECT_POS - pz_b)
                    zone_end = min(BAR_LEN - 1, PERFECT_POS + pz_a)
                    for i in range(zone_start, zone_end + 1):
                        bar[i] = "░"
                    bar[PERFECT_POS] = "█"

                    for b in lane_bullets:
                        p = int(b.pos)
                        if 0 <= p < BAR_LEN:
                            bar[p] = "●"

                    bar_str = "".join(bar)
                    try:
                        stdscr.addstr(row, 14, bar_str)
                    except curses.error:
                        pass

                    # color the bullets
                    for b in lane_bullets:
                        p = int(b.pos)
                        if 0 <= p < BAR_LEN:
                            if b.btype == "missed":
                                # gray bullet flowing past
                                try:
                                    stdscr.addstr(row, 14 + p, "●", curses.A_DIM)
                                except curses.error:
                                    pass
                            else:
                                try:
                                    stdscr.addstr(row, 14 + p, "●", curses.color_pair(3) | curses.A_BOLD)
                                except curses.error:
                                    pass
                else:
                    bar_str = draw_lane_bar(0, pz_b, pz_a, False)
                    try:
                        stdscr.addstr(row, 14, bar_str)
                    except curses.error:
                        pass

                # result display
                if lane_idx in result_display:
                    res, res_time = result_display[lane_idx]
                    if now - res_time < 0.4:
                        if res == "PERFECT":
                            c = curses.color_pair(1) | curses.A_BOLD
                        elif res == "Good":
                            c = curses.color_pair(2) | curses.A_BOLD
                        else:
                            c = curses.color_pair(3) | curses.A_BOLD
                        try:
                            stdscr.addstr(row, 14 + BAR_LEN + 2, res, c)
                        except curses.error:
                            pass
                    else:
                        del result_display[lane_idx]

                row += 2

            # ── Separator ──
            sep_row = row
            try:
                stdscr.addstr(sep_row, 0, "=" * min(w, 78))
            except curses.error:
                pass

            # ── Player status ──
            p_hp_bar = hp_bar_str(player_hp, player_max_hp, 20)
            z_bar_filled = int(20 * zanki / zanki_max)
            z_bar = "█" * z_bar_filled + "░" * (20 - z_bar_filled)
            try:
                stdscr.addstr(sep_row + 1, 1, f"HP [{p_hp_bar}] {player_hp}/{player_max_hp}")
            except curses.error:
                pass
            zanki_color = curses.color_pair(1) | curses.A_BOLD if zanki >= zanki_max else 0
            try:
                stdscr.addstr(sep_row + 2, 1, f"残火 [{z_bar}] {zanki}/{zanki_max}", zanki_color)
            except curses.error:
                pass

            # Attack msg / lock
            if is_locked:
                remain = lock_until - now
                try:
                    stdscr.addstr(sep_row + 3, 1, f">>> 硬直中 {remain:.1f}s <<<", curses.color_pair(3))
                except curses.error:
                    pass
            elif now < atk_msg_until:
                try:
                    stdscr.addstr(sep_row + 3, 1, atk_msg, curses.color_pair(5) | curses.A_BOLD)
                except curses.error:
                    pass

            # ATK cooldown
            atk_cd = WEAPON["atk_cooldown"]
            if now < atk_cooldown_until:
                atk_remain = atk_cooldown_until - now
                atk_ratio = 1.0 - (atk_remain / atk_cd)
                atk_filled = int(10 * atk_ratio)
                atk_gauge = "█" * atk_filled + "░" * (10 - atk_filled)
                try:
                    stdscr.addstr(sep_row + 4, 1, f"ATK [{atk_gauge}] {atk_remain:.1f}s", curses.color_pair(3))
                except curses.error:
                    pass
            else:
                try:
                    stdscr.addstr(sep_row + 4, 1, "ATK [██████████] READY!", curses.color_pair(2) | curses.A_BOLD)
                except curses.error:
                    pass

            # Stats
            try:
                stdscr.addstr(sep_row + 5, 1, f"COMBO:{combo}  MAX:{max_combo}  |  P:{stats['PERFECT']}  G:{stats['Good']}  M:{stats['MISS']}")
            except curses.error:
                pass

            # Items
            item_row = sep_row + 6
            item_str = "ITEM: "
            for idx in range(4):
                sel = ">" if idx == item_cursor else " "
                if inventory[idx]:
                    item_str += f"{sel}[{idx+1}]{inventory[idx]['name']} "
                else:
                    item_str += f"{sel}[{idx+1}]--- "
            try:
                stdscr.addstr(item_row, 1, item_str)
            except curses.error:
                pass

            # Controls
            try:
                stdscr.addstr(item_row + 1, 1, "[J/F:パリィ] [SPACE:攻撃] [A/D:アイテム選択] [S:使用] [;:残火の業火]")
            except curses.error:
                pass
            try:
                stdscr.addstr(item_row + 2, 1, f"武器: {WEAPON['name']} (ATK:{WEAPON['atk']} CD:{atk_cd}s)")
            except curses.error:
                pass

            # ── Flash / Combo color effect ──
            if now < flash_until:
                blink_on = int((now - (flash_until - 0.6)) / 0.08) % 2 == 0
                try:
                    if blink_on:
                        stdscr.bkgd(' ', curses.color_pair(flash_color))
                    else:
                        stdscr.bkgd(' ')
                except curses.error:
                    pass
            elif combo >= 1 and can_rgb:
                # Background starts white, one RGB channel drops per combo
                # fff → ffd → ffb → ff9 → ... cycling through R, G, B channels
                # Each combo subtracts ~66 (curses 0-1000 scale) from one channel
                step = 66
                c = combo - 1
                r = 1000
                g = 1000
                b = 1000
                # Phase 0: drop B (white → yellow)
                # Phase 1: drop R (yellow → green)
                # Phase 2: drop G (green → blue-ish) ... etc
                phase = c // 15  # 15 combos per phase
                pos = c % 15
                drop = min(pos * step, 1000)
                channel = phase % 6
                if channel == 0:    # fff → ff0 (white → yellow)
                    b = max(0, 1000 - drop)
                elif channel == 1:  # ff0 → 0f0 (yellow → green)
                    r = max(0, 1000 - drop)
                elif channel == 2:  # 0f0 → 0ff (green → cyan)
                    b = min(1000, drop)
                    r = 0
                elif channel == 3:  # 0ff → 00f (cyan → blue)
                    g = max(0, 1000 - drop)
                    r = 0
                elif channel == 4:  # 00f → f0f (blue → magenta)
                    r = min(1000, drop)
                    g = 0
                elif channel == 5:  # f0f → f00 (magenta → red)
                    b = max(0, 1000 - drop)
                    g = 0
                # Keep background dim (30% brightness)
                br = int(r * 0.3)
                bg = int(g * 0.3)
                bb = int(b * 0.3)
                # Foreground: bright for readability
                fr = min(1000, 1000 - br + 500)
                fg = min(1000, 1000 - bg + 500)
                fb = min(1000, 1000 - bb + 500)
                try:
                    curses.init_color(RAINBOW_BG_COLOR, br, bg, bb)
                    curses.init_color(RAINBOW_FG_COLOR, fr, fg, fb)
                    stdscr.bkgd(' ', curses.color_pair(RAINBOW_PAIR))
                except curses.error:
                    pass
            else:
                try:
                    if can_rgb:
                        curses.init_color(RAINBOW_BG_COLOR, 0, 0, 0)
                    stdscr.bkgd(' ')
                except curses.error:
                    pass

            # ── Game over / Victory ──
            if player_hp <= 0:
                sound.play("death")
                try:
                    stdscr.addstr(item_row + 4, 1, "「 大いなる死に賛歌を！ 」", curses.color_pair(3) | curses.A_BOLD)
                    stdscr.addstr(item_row + 6, 1, "[Q] 終了  [R] リスタート")
                except curses.error:
                    pass
                stdscr.refresh()
                _wait_for_restart_or_quit(stdscr)
                return True  # restart

            if boss["hp"] <= 0:
                try:
                    stdscr.addstr(item_row + 4, 1, "「 灰は燃え尽き、都は静寂に還る 」", curses.color_pair(1) | curses.A_BOLD)
                    stdscr.addstr(item_row + 5, 1, f"  残りHP:{player_hp}  最大コンボ:{max_combo}  総パリィ:{total_parry}", curses.A_BOLD)
                    stdscr.addstr(item_row + 6, 1, f"  PERFECT:{stats['PERFECT']}  Good:{stats['Good']}  MISS:{stats['MISS']}")
                    stdscr.addstr(item_row + 8, 1, "[Q] 終了  [R] リスタート")
                except curses.error:
                    pass
                stdscr.refresh()
                _wait_for_restart_or_quit(stdscr)
                return True

            stdscr.refresh()

            # ── Input ──
            try:
                key = stdscr.getch()
            except Exception:
                key = -1

            if key > 127 and key != curses.KEY_UP and key != curses.KEY_DOWN and key != curses.KEY_LEFT and key != curses.KEY_RIGHT:
                curses.flushinp()
                key = -1

            # Stop zanki burst when Space is released (any non-space input or no input)
            if zanki_burst_active and key != ord(' '):
                zanki_burst_active = False
                if zanki > 0:
                    atk_msg = ">>> 残火中断 <<<"
                    atk_msg_until = now + 0.8

            if key in (ord('q'), ord('Q')):
                return False  # quit

            # Parry input (J/F only, not SPACE)
            parry_pressed = None
            for lane_idx, lane in enumerate(LANES):
                if lane_idx < 2 and key in lane["ord"]:
                    parry_pressed = lane_idx
                    break

            if parry_pressed is not None and not is_locked:
                # find the frontmost bullet in this lane
                lane_bullets = [b for b in bullets if b.active and b.lane == parry_pressed
                                and b.btype == "parry" and now >= b.start_time]
                if lane_bullets:
                    # pick the one closest to the parry zone (most advanced)
                    lane_bullets.sort(key=lambda b: b.pos, reverse=True)
                    target_b = lane_bullets[0]
                    p_pz = boss["parry_zone_j"] if parry_pressed == 0 else boss["parry_zone_f"]
                    result = judge(target_b.pos, p_pz[0] + parry_bonus, p_pz[1] + parry_bonus)
                    target_b.active = False
                    target_b.result = result
                    target_b.result_time = now
                    result_display[parry_pressed] = (result, now)
                    stats[result] += 1

                    # lane-specific sounds: J=metallic, F=bass
                    lane_key = LANES[parry_pressed]["key"]
                    if result == "PERFECT":
                        zanki = min(zanki_max, zanki + 4)
                        combo += 1
                        total_parry += 1
                        max_combo = max(max_combo, combo)
                        if lane_key == "J":
                            sound.play(f"perfect_j_{melody_note % 8}")
                            melody_note += 1
                        else:
                            sound.play("perfect_f")
                        flash_until = now + 0.06
                        flash_color = 7
                        hitstop_until = now + 0.08
                    elif result == "Good":
                        zanki = min(zanki_max, zanki + 1)
                        combo += 1
                        total_parry += 1
                        max_combo = max(max_combo, combo)
                        if lane_key == "J":
                            sound.play(f"parry_j_{melody_note % 8}")
                            melody_note += 1
                        else:
                            sound.play("parry_f")
                        flash_until = now + 0.03
                        flash_color = 2
                    else:
                        player_hp = max(0, player_hp - boss["atk"])
                        zanki = max(0, zanki - 2)
                        melody_note = 0  # reset melody on miss
                        combo = 0
                        sound.play("miss")

            # Attack (Space)
            elif key == ord(' '):
                if boss["hp"] > 0:
                    if zanki >= zanki_max and not zanki_burst_active:
                        # Start zanki burst
                        zanki_burst_active = True
                        zanki_burst_last_tick = now
                        sound.play("zanki")
                        atk_msg = ">>> 残火解放！ <<<"
                        atk_msg_until = now + 1.0
                        flash_until = now + 0.1
                        flash_color = 7
                    elif not zanki_burst_active and not is_locked and now >= atk_cooldown_until:
                        # Normal attack
                        dmg = WEAPON["atk"]
                        atk_msg = f">>> {boss['name']} に {dmg} ダメージ！ <<<"
                        sound.play("attack")
                        if boss["marks"] > 0:
                            boss["hp"] = max(1, boss["hp"] - dmg)
                        else:
                            boss["hp"] = max(0, boss["hp"] - dmg)
                        atk_msg_until = now + 0.8
                        lock_until = now + WEAPON["lock_sec"]
                        atk_cooldown_until = now + WEAPON["atk_cooldown"]

            # 残火の業火 (Enter)
            elif key == ord(';'):
                if zanki >= zanki_max and boss["marks"] > 0 and boss["hp"] <= 1:
                    boss["marks"] -= 1
                    zanki = 0
                    sound.play("zanki")
                    if boss["marks"] == 0:
                        boss["hp"] = 0
                        atk_msg = f">>> 撲殺！ {boss['name']} を葬った！ <<<"
                        sound.play("kill")
                    else:
                        boss["hp"] = boss["max_hp"]
                        atk_msg = f">>> 残火の業火！ ● を削った！ 残り{'●' * boss['marks']} <<<"
                        sound.play("kill")
                    atk_msg_until = now + 2.0
                    flash_until = now + 0.6
                    flash_color = 7
                    hitstop_until = now + 0.3

            # Item select (A/D)
            elif key in (ord('a'), ord('A')):
                item_cursor = (item_cursor - 1) % 4
            elif key in (ord('d'), ord('D')):
                item_cursor = (item_cursor + 1) % 4

            # Item use (S)
            elif key in (ord('s'), ord('S')):
                item = inventory[item_cursor]
                if item:
                    if item["effect"] == "heal":
                        player_hp = min(player_max_hp, player_hp + item["value"])
                        atk_msg = f">>> {item['name']} を使った！ HP +{item['value']} <<<"
                    elif item["effect"] == "slow":
                        slow_until = now + item["value"]
                        atk_msg = f">>> {item['name']} を使った！ 敵の攻撃が鈍る <<<"
                    elif item["effect"] == "damage":
                        if boss["marks"] > 0:
                            boss["hp"] = max(1, boss["hp"] - item["value"])
                        else:
                            boss["hp"] = max(0, boss["hp"] - item["value"])
                        atk_msg = f">>> {item['name']}！ {item['value']} ダメージ！ <<<"
                        sound.play("attack")
                    elif item["effect"] == "parry_up":
                        parry_up_until = now + item["value"]
                        atk_msg = f">>> {item['name']}！ パリィ判定拡大！ <<<"
                    atk_msg_until = now + 1.5
                    inventory[item_cursor] = None

            time.sleep(0.016)

    def _wait_for_restart_or_quit(scr):
        """Block until R or Q is pressed."""
        scr.nodelay(False)
        while True:
            try:
                key = scr.getch()
            except Exception:
                continue
            if key in (ord('r'), ord('R')):
                scr.nodelay(True)
                return
            if key in (ord('q'), ord('Q')):
                raise SystemExit(0)

    # ── Title screen ──
    while True:
        stdscr.erase()
        h, w = stdscr.getmaxyx()
        r = 2
        title_art = [
            r"  ░██╗░░██╗░█████╗░██╗░░██╗░█████╗░",
            r"  ░████╗██║██╔══██╗████╗██║██╔══██╗",
            r"  ░██╔██╗██║██║░░██║██╔██╗██║██║░░██║",
            r"  ░██║╚████║██║░░██║██║╚████║██║░░██║",
            r"  ░██║░╚███║╚█████╔╝██║░╚███║╚█████╔╝",
            r"  ░╚═╝░░╚══╝░╚════╝░╚═╝░░╚══╝░╚════╝░",
        ]
        for line in title_art:
            try:
                stdscr.addstr(r, 2, line, curses.color_pair(3) | curses.A_BOLD)
            except curses.error:
                pass
            r += 1

        r += 1
        try:
            stdscr.addstr(r, 4, "灰 都 殺 伐 代 行", curses.color_pair(1) | curses.A_BOLD)
        except curses.error:
            pass
        r += 1
        try:
            stdscr.addstr(r, 4, "── 灰燼の街に、刃だけが正義を語る ──", curses.color_pair(4))
        except curses.error:
            pass
        r += 2

        howto = [
            "【 操 作 】",
            "  F / J     ─  パリィ (2レーンに対応)",
            "  SPACE     ─  攻撃",
            "  ;         ─  残火の業火 (残火MAX + 敵HP1)",
            "  A / D     ─  アイテム選択",
            "  S         ─  アイテム使用",
            "",
            "  [J] を押してゲーム開始",
        ]
        for line in howto:
            try:
                stdscr.addstr(r, 4, line)
            except curses.error:
                pass
            r += 1

        stdscr.refresh()

        try:
            key = stdscr.getch()
        except Exception:
            key = -1

        if key in (ord('j'), ord('J')):
            sound.play("start")
            break
        elif key in (ord('q'), ord('Q')):
            sound.cleanup()
            return

        time.sleep(0.016)

    # ── Game loop ──
    while True:
        should_restart = run_game()
        if not should_restart:
            break

    sound.cleanup()


def entry_point():
    """Entry point for console_scripts."""
    try:
        curses.wrapper(main)
    finally:
        sound.cleanup()


if __name__ == "__main__":
    entry_point()
