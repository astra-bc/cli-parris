#!/usr/bin/env python3
"""layout demo - target switching, parry, attack with lock frames"""

import curses
import time
import random
import os
import locale
import subprocess

os.environ['LANG'] = 'en_US.UTF-8'

# macOS: switch to ASCII input on launch
try:
    subprocess.run(
        ["osascript", "-e",
         'tell application "System Events" to key code 102'],
        capture_output=True, timeout=2
    )
except:
    pass

BAR_LEN = 40
ZONE_START = 33
ZONE_END = 37
PERFECT_POS = 35

# weapon params
WEAPON = {
    "name": "殺意の出刃包丁",
    "atk": 5,
    "lock_sec": 0.5,  # lock frames (seconds)
}

ENEMIES = [
    {"name": "渋谷の犬", "aa": "(^w^)", "star": "★☆☆",
     "hp": 6, "max_hp": 6, "atk": 3, "marks": 1, "marks_max": 1,
     "speed_min": 5.0, "speed_max": 7.0, "cooldown": 1.0,
     "dirs": ["W", "S", "A", "D"]},
    {"name": "(ボス) 堕落した都知事", "aa": "{o_o}", "star": "★★★",
     "hp": 20, "max_hp": 20, "atk": 8, "marks": 3, "marks_max": 3,
     "speed_min": 3.5, "speed_max": 5.0, "cooldown": 0.5,
     "dirs": ["W", "S", "A", "D"]},
    {"name": "池袋の豚", "aa": "(-.-)", "star": "★★☆",
     "hp": 8, "max_hp": 8, "atk": 5, "marks": 1, "marks_max": 1,
     "speed_min": 7.0, "speed_max": 10.0, "cooldown": 2.0,
     "dirs": ["W", "S", "A", "D"]},
]

def rand_speed(enemy):
    return random.uniform(enemy["speed_min"], enemy["speed_max"])

def rand_dir(enemy):
    return random.choice(enemy["dirs"])

def draw_bar(pos):
    bar = list("━" * BAR_LEN)
    for i in range(ZONE_START, min(ZONE_END + 1, BAR_LEN)):
        bar[i] = "░"
    bar[PERFECT_POS] = "█"
    p = int(pos)
    if 0 <= p < BAR_LEN:
        bar[p] = "●"
    return "".join(bar)

def judge(pos):
    p = int(pos)
    if p == PERFECT_POS:
        return "PERFECT", 1
    elif ZONE_START <= p <= ZONE_END:
        return "Good", 2
    else:
        return "MISS", 3

def marks_str(current, maximum):
    return "●" * current + "○" * (maximum - current)

def hp_bar(hp, max_hp, length=10):
    filled = int(length * hp / max_hp) if max_hp > 0 else 0
    return "█" * filled + "░" * (length - filled)

def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.keypad(True)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_BLACK)

    def reset():
        nonlocal target, player_hp, zanki, stats, combo, max_combo, total_parry, lock_until, atk_msg, atk_msg_until
        nonlocal bar_speeds, bar_dirs, bar_starts, results, result_times, positions
        target = 0
        player_hp = 100
        zanki = 0
        stats = {"PERFECT": 0, "Good": 0, "MISS": 0}
        combo = 0
        max_combo = 0
        total_parry = 0
        lock_until = 0
        atk_msg = ""
        atk_msg_until = 0
        zanki_max = 10
        now = time.time()
        bar_speeds = [rand_speed(e) for e in ENEMIES]
        bar_dirs = [rand_dir(e) for e in ENEMIES]
        bar_starts = [now + i * 0.7 for i in range(len(ENEMIES))]
        results = [None] * len(ENEMIES)
        result_times = [0.0] * len(ENEMIES)
        positions = [0.0] * len(ENEMIES)
        for e in ENEMIES:
            e["hp"] = e["max_hp"]
            e["marks"] = e["marks_max"]

    zanki_max = 10
    target = 0
    player_hp = 100
    zanki = 0
    stats = {"PERFECT": 0, "Good": 0, "MISS": 0}
    combo = 0
    max_combo = 0
    total_parry = 0
    lock_until = 0
    atk_msg = ""
    atk_msg_until = 0
    now = time.time()
    bar_speeds = [rand_speed(e) for e in ENEMIES]
    bar_dirs = [rand_dir(e) for e in ENEMIES]
    bar_starts = [now + i * 0.7 for i in range(len(ENEMIES))]
    results = [None] * len(ENEMIES)
    result_times = [0.0] * len(ENEMIES)
    positions = [0.0] * len(ENEMIES)

    while True:
        stdscr.erase()
        h, w = stdscr.getmaxyx()
        now = time.time()
        is_locked = now < lock_until

        # title bar
        stdscr.addstr(0, 2, "灰 都 殺 伐 行", curses.A_BOLD)
        stdscr.addstr(0, w - 10, "Floor 1")
        stdscr.addstr(1, 0, "=" * min(w, 78))

        # enemies
        row = 3
        for i, enemy in enumerate(ENEMIES):
            is_target = (i == target)

            # name line: | AA name [HPbar] hp/max  marks  stars
            indicator = "|" if is_target else " "
            hp_b = hp_bar(enemy["hp"], enemy["max_hp"])
            m_str = marks_str(enemy["marks"], enemy["marks_max"])
            name_line = f"{indicator} {enemy['aa']} {enemy['name']}  [{hp_b}] {enemy['hp']}/{enemy['max_hp']}  {m_str}  {enemy['star']}"

            if is_target:
                stdscr.addstr(row, 0, name_line, curses.color_pair(4) | curses.A_BOLD)
            else:
                stdscr.addstr(row, 0, name_line)

            # bar line
            row += 1

            # stop bars when player or enemy is dead
            if player_hp <= 0 or enemy["hp"] <= 0:
                if enemy["hp"] <= 0:
                    stdscr.addstr(row, 2, "--- DEAD ---")
                else:
                    bar_str = draw_bar(positions[i])
                    stdscr.addstr(row, 2, bar_str)
                row += 2
                continue

            elapsed = now - bar_starts[i]
            dur = bar_speeds[i]

            if results[i] is not None:
                bar_str = draw_bar(positions[i])
                stdscr.addstr(row, 2, bar_str)

                res = results[i]
                if res == "PERFECT":
                    c = curses.color_pair(1) | curses.A_BOLD
                elif res == "Good":
                    c = curses.color_pair(2)
                else:
                    c = curses.color_pair(3)
                stdscr.addstr(row, 2 + BAR_LEN + 2, res, c)

                if now - result_times[i] > enemy["cooldown"]:
                    results[i] = None
                    bar_starts[i] = now
                    bar_speeds[i] = rand_speed(enemy)
                    bar_dirs[i] = rand_dir(enemy)
            else:
                t = min(elapsed / dur, 1.0)
                positions[i] = t * (BAR_LEN - 1)
                bar_str = draw_bar(positions[i])
                stdscr.addstr(row, 2, bar_str)
                # color the bullet
                p = int(positions[i])
                if 0 <= p < BAR_LEN:
                    if is_target:
                        stdscr.addstr(row, 2 + p, "●", curses.color_pair(3) | curses.A_BOLD)  # red
                    else:
                        stdscr.addstr(row, 2 + p, "●", curses.color_pair(1))  # yellow
                stdscr.addstr(row, 2 + BAR_LEN + 1, f"[{bar_dirs[i]}]")

                if positions[i] >= BAR_LEN - 1:
                    results[i] = "MISS"
                    stats["MISS"] += 1
                    result_times[i] = now
                    dmg = enemy["atk"]
                    player_hp = max(0, player_hp - dmg)
                    combo = 0

            row += 2

        # separator
        sep_row = row
        stdscr.addstr(sep_row, 0, "=" * min(w, 78))

        # player status
        p_hp_bar = "█" * (player_hp // 5) + "░" * (20 - player_hp // 5)
        z_bar = "█" * (zanki * 2) + "░" * (20 - zanki * 2)
        stdscr.addstr(sep_row + 1, 1, f"HP [{p_hp_bar}] {player_hp}/100   残火 [{z_bar}] {zanki}/{zanki_max}")

        # lock indicator
        if is_locked:
            remain = lock_until - now
            stdscr.addstr(sep_row + 2, 1, f">>> 攻撃硬直中... {remain:.1f}s <<<", curses.color_pair(3) | curses.A_BOLD)
        elif now < atk_msg_until:
            stdscr.addstr(sep_row + 2, 1, atk_msg, curses.color_pair(5) | curses.A_BOLD)

        # stats + controls
        stdscr.addstr(sep_row + 3, 1, f"COMBO:{combo}  MAX:{max_combo}  PARRY:{total_parry}  |  PERFECT:{stats['PERFECT']}  Good:{stats['Good']}  MISS:{stats['MISS']}")
        stdscr.addstr(sep_row + 4, 1, f"[WASD:パリィ] [SPACE:攻撃] [↑↓:切替] [Q:終了]")
        stdscr.addstr(sep_row + 5, 1, f"武器: {WEAPON['name']} (ATK:{WEAPON['atk']} 硬直:{WEAPON['lock_sec']}s)")

        # game over
        if player_hp <= 0:
            stdscr.addstr(sep_row + 7, 1, "「 大いなる死に賛歌を！ 」", curses.color_pair(3) | curses.A_BOLD)
            stdscr.addstr(sep_row + 8, 1, "[Q] で終了")

        stdscr.refresh()

        # input
        try:
            key = stdscr.getch()
        except:
            key = -1

        # flush extra bytes (IME/multibyte input)
        if key > 127 and key != curses.KEY_UP and key != curses.KEY_DOWN:
            curses.flushinp()
            key = -1

        if key in (ord('q'), ord('Q')):
            break
        elif key in (ord('r'), ord('R')):
            reset()
            continue
        elif player_hp <= 0:
            time.sleep(0.016)
            continue
        elif key == curses.KEY_UP:
            target = (target - 1) % len(ENEMIES)
        elif key == curses.KEY_DOWN:
            target = (target + 1) % len(ENEMIES)
        elif key in (ord('w'), ord('a'), ord('s'), ord('d'),
                     ord('W'), ord('A'), ord('S'), ord('D')):
            if not is_locked:
                i = target
                if results[i] is None:
                    # check direction match
                    key_dir_map = {
                        ord('w'): "W", ord('W'): "W",
                        ord('s'): "S", ord('S'): "S",
                        ord('a'): "A", ord('A'): "A",
                        ord('d'): "D", ord('D'): "D",
                    }
                    pressed_dir = key_dir_map.get(key, "")
                    expected_dir = bar_dirs[i]

                    if pressed_dir != expected_dir:
                        # wrong direction = MISS
                        results[i] = "MISS"
                        stats["MISS"] += 1
                        result_times[i] = now
                        player_hp = max(0, player_hp - ENEMIES[i]["atk"])
                        combo = 0
                    else:
                        result, _ = judge(positions[i])
                        results[i] = result
                        stats[result] += 1
                        result_times[i] = now
                        if result == "MISS":
                            player_hp = max(0, player_hp - ENEMIES[i]["atk"])
                            combo = 0
                        elif result == "PERFECT":
                            zanki = min(zanki_max, zanki + 2)
                            combo += 1
                            total_parry += 1
                            max_combo = max(max_combo, combo)
                        elif result == "Good":
                        zanki = min(zanki_max, zanki + 1)
                        combo += 1
                        total_parry += 1
                        max_combo = max(max_combo, combo)
        elif key == ord(' '):
            if not is_locked:
                # attack
                i = target
                dmg = WEAPON["atk"]
                ENEMIES[i]["hp"] = max(0, ENEMIES[i]["hp"] - dmg)
                atk_msg = f">>> {ENEMIES[i]['name']} に {dmg} ダメージ！ <<<"
                atk_msg_until = now + 1.0
                lock_until = now + WEAPON["lock_sec"]

        time.sleep(0.016)

curses.wrapper(main)
