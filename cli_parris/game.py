#!/usr/bin/env python3
"""灰都殺伐代行 (cli-parris) - Terminal Roguelike Parry Action Game"""

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
except Exception:
    pass

BAR_LEN = 40
ZONE_START = 33
ZONE_END = 37
PERFECT_POS = 35

# weapon params
WEAPON = {
    "name": "殺意の出刃包丁",
    "atk": 1,
    "lock_sec": 0.5,   # parry lock after attack (seconds)
    "atk_cooldown": 2.0,  # re-attack cooldown (seconds)
}

ENEMIES_TEMPLATE = [
    {"name": "渋谷の不動産屋の鼬", "aa": "(^w^)", "star": "★☆☆",
     "hp": 6, "max_hp": 6, "atk": 3, "marks": 1, "marks_max": 1,
     "speed_min": 2.1, "speed_max": 2.9, "cooldown": 1.5,
     "parry_zone": 6,
     "dirs": ["W", "S", "A", "D"]},
    {"name": "(ボス) 堕落した都知事", "aa": "{o_o}", "star": "★★★",
     "hp": 20, "max_hp": 20, "atk": 8, "marks": 3, "marks_max": 3,
     "speed_min": 3.5, "speed_max": 5.0, "cooldown": 0.5,
     "parry_zone": 1,
     "dirs": ["W", "S", "A", "D"]},
    {"name": "池袋の町中華の豚", "aa": "(-.-)", "star": "★★☆",
     "hp": 8, "max_hp": 8, "atk": 5, "marks": 1, "marks_max": 1,
     "speed_min": 7.0, "speed_max": 10.0, "cooldown": 2.0,
     "parry_zone": 4,
     "dirs": ["W", "S", "A", "D"]},
]


def rand_speed(enemy):
    return random.uniform(enemy["speed_min"], enemy["speed_max"])


def rand_dir(enemy):
    return random.choice(enemy["dirs"])


def draw_bar(pos, parry_zone=2):
    bar = list("━" * BAR_LEN)
    zone_start = PERFECT_POS - parry_zone
    zone_end = PERFECT_POS + parry_zone
    for i in range(zone_start, min(zone_end + 1, BAR_LEN)):
        bar[i] = "░"
    bar[PERFECT_POS] = "█"
    p = int(pos)
    if 0 <= p < BAR_LEN:
        bar[p] = "●"
    return "".join(bar)


def judge(pos, parry_zone=2):
    p = int(pos)
    zone_start = PERFECT_POS - parry_zone
    zone_end = PERFECT_POS + parry_zone
    if p == PERFECT_POS:
        return "PERFECT", 1
    elif zone_start <= p <= zone_end:
        return "Good", 2
    else:
        return "MISS", 3


def marks_str(current, maximum):
    return "●" * current + "○" * (maximum - current)


def hp_bar(hp, max_hp, length=10):
    filled = int(length * hp / max_hp) if max_hp > 0 else 0
    return "█" * filled + "░" * (length - filled)


def make_enemies():
    import copy
    return copy.deepcopy(ENEMIES_TEMPLATE)


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

    ENEMIES = make_enemies()

    def reset():
        nonlocal target, player_hp, zanki, stats, combo, max_combo, total_parry, lock_until, atk_msg, atk_msg_until, atk_cooldown_until
        nonlocal bar_speeds, bar_dirs, bar_starts, results, result_times, positions, ENEMIES
        ENEMIES = make_enemies()
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
        atk_cooldown_until = 0
        now = time.time()
        bar_speeds = [rand_speed(e) for e in ENEMIES]
        bar_dirs = [rand_dir(e) for e in ENEMIES]
        bar_starts = [now for _ in range(len(ENEMIES))]
        results = [None] * len(ENEMIES)
        result_times = [0.0] * len(ENEMIES)
        positions = [0.0] * len(ENEMIES)

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
    atk_cooldown_until = 0
    perfect_counter = False
    perfect_counter_until = 0
    now = time.time()
    bar_speeds = [rand_speed(e) for e in ENEMIES]
    bar_dirs = [rand_dir(e) for e in ENEMIES]
    bar_starts = [now for _ in range(len(ENEMIES))]
    results = [None] * len(ENEMIES)
    result_times = [0.0] * len(ENEMIES)
    positions = [0.0] * len(ENEMIES)

    # title screen
    title_art = [
        r"                                                                       ",
        r"  ░██╗░░██╗░█████╗░██╗░░██╗░█████╗░██╗░░██╗░█████╗░██╗░░██╗░█████╗░  ",
        r"  ░████╗██║██╔══██╗████╗██║██╔══██╗████╗██║██╔══██╗████╗██║██╔══██╗  ",
        r"  ░██╔██╗██║██║░░██║██╔██╗██║██║░░██║██╔██╗██║██║░░██║██╔██╗██║██║░░██║  ",
        r"  ░██║╚████║██║░░██║██║╚████║██║░░██║██║╚████║██║░░██║██║╚████║██║░░██║  ",
        r"  ░██║░╚███║╚█████╔╝██║░╚███║╚█████╔╝██║░╚███║╚█████╔╝██║░╚███║╚█████╔╝  ",
        r"  ░╚═╝░░╚══╝░╚════╝░╚═╝░░╚══╝░╚════╝░╚═╝░░╚══╝░╚════╝░╚═╝░░╚══╝░╚════╝░  ",
        r"                                                                       ",
    ]
    title_jp = "灰 都 殺 伐 代 行"
    subtitle = "── 灰燼の街に、刃だけが正義を語る ──"

    howto = [
        "【 操 作 説 明 】",
        "",
        "  W A S D  ─  パリィ (表示された方向キーを押せ)",
        "  SPACE    ─  攻撃 (敵にダメージを与える)",
        "  ↑ ↓     ─  ターゲット切替",
        "  ENTER    ─  残火の血霧 (残火ゲージMAXで●を削る)",
        "",
        "【 パリィの心得 】",
        "",
        "  敵の攻撃バーが迫る ── タイミングを見極めろ",
        "  PERFECT で残火ゲージ大幅回復、Good で少量回復",
        "  方向を間違えれば即被弾、遅れても被弾",
        "",
        "  ●印はパリィでは削れない",
        "  敵のHPを1まで削り、残火の血霧で●を剥がせ",
        "  全ての●を剥がした時、敵は真に死ぬ",
    ]

    input_ok = False
    while not input_ok:
        stdscr.erase()
        h, w = stdscr.getmaxyx()

        # ASCII art title
        r = 1
        for line in title_art:
            try:
                stdscr.addstr(r, 2, line, curses.color_pair(3) | curses.A_BOLD)
            except curses.error:
                pass
            r += 1

        # Japanese title
        r += 1
        try:
            stdscr.addstr(r, 6, title_jp, curses.color_pair(1) | curses.A_BOLD)
        except curses.error:
            pass
        r += 1
        try:
            stdscr.addstr(r, 6, subtitle, curses.color_pair(4))
        except curses.error:
            pass
        r += 2

        # how to play
        for line in howto:
            try:
                if line.startswith("【"):
                    stdscr.addstr(r, 4, line, curses.A_BOLD)
                else:
                    stdscr.addstr(r, 4, line)
            except curses.error:
                pass
            r += 1

        # prompt
        r += 2
        try:
            stdscr.addstr(r, 4, "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", curses.A_DIM)
        except curses.error:
            pass
        r += 1
        try:
            stdscr.addstr(r, 4, "半角英数に切り替えて [W] を押せ", curses.color_pair(2) | curses.A_BOLD)
        except curses.error:
            pass
        r += 1
        try:
            stdscr.addstr(r, 4, "[Q] 終了", curses.A_DIM)
        except curses.error:
            pass

        stdscr.refresh()

        try:
            key = stdscr.getch()
        except Exception:
            key = -1

        if key == ord('w') or key == ord('W'):
            input_ok = True
            now = time.time()
            bar_starts = [now for _ in range(len(ENEMIES))]
            positions = [0.0] * len(ENEMIES)
        elif key in (ord('q'), ord('Q')):
            return
        elif key != -1 and key > 127:
            curses.flushinp()
            try:
                stdscr.addstr(r + 1, 4, "!! 全角入力です。半角英数に切り替えてください !!", curses.color_pair(3) | curses.A_BOLD)
            except curses.error:
                pass
            stdscr.refresh()
            time.sleep(1.0)

    while True:
        stdscr.erase()
        h, w = stdscr.getmaxyx()
        now = time.time()
        is_locked = now < lock_until

        # title bar
        stdscr.addstr(0, 2, "灰 都 殺 伐 代 行", curses.A_BOLD)
        stdscr.addstr(0, w - 10, "Floor 1")
        stdscr.addstr(1, 0, "=" * min(w, 78))

        # enemies
        row = 3
        for i, enemy in enumerate(ENEMIES):
            is_target = (i == target)

            indicator = "|" if is_target else " "
            hp_b = hp_bar(enemy["hp"], enemy["max_hp"])
            m_str = marks_str(enemy["marks"], enemy["marks_max"])
            name_line = f"{indicator} {enemy['aa']} {enemy['name']}  [{hp_b}] {enemy['hp']}/{enemy['max_hp']}  {m_str}  {enemy['star']}"

            if enemy["hp"] <= 0:
                stdscr.addstr(row, 0, name_line, curses.A_DIM)
            elif is_target:
                stdscr.addstr(row, 0, name_line, curses.A_BOLD)
            else:
                stdscr.addstr(row, 0, name_line)

            row += 2

            if player_hp <= 0 or enemy["hp"] <= 0:
                if enemy["hp"] <= 0:
                    stdscr.addstr(row, 2, "--- DEAD ---", curses.A_DIM)
                else:
                    bar_str = draw_bar(positions[i], enemy["parry_zone"])
                    stdscr.addstr(row, 2, bar_str)
                row += 2
                continue

            elapsed = now - bar_starts[i]
            dur = bar_speeds[i]
            if enemy["hp"] == 1:
                dur *= 2

            if results[i] is not None:
                bar_str = draw_bar(0, enemy["parry_zone"])
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
                bar_str = draw_bar(positions[i], enemy["parry_zone"])
                stdscr.addstr(row, 2, bar_str)
                p = int(positions[i])
                if 0 <= p < BAR_LEN:
                    if is_target:
                        stdscr.addstr(row, 2 + p, "●", curses.color_pair(3) | curses.A_BOLD)
                    else:
                        stdscr.addstr(row, 2 + p, "●", curses.color_pair(1))
                stdscr.addstr(row, 2 + BAR_LEN + 1, f"[{bar_dirs[i]}]")

                if positions[i] >= BAR_LEN - 1:
                    results[i] = "MISS"
                    stats["MISS"] += 1
                    result_times[i] = now
                    dmg = enemy["atk"]
                    player_hp = max(0, player_hp - dmg)
                    zanki = max(0, zanki - 2)
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

        # attack cooldown gauge
        atk_cd = WEAPON["atk_cooldown"]
        if now < atk_cooldown_until:
            atk_remain = atk_cooldown_until - now
            atk_ratio = 1.0 - (atk_remain / atk_cd)
            atk_filled = int(10 * atk_ratio)
            atk_gauge = "█" * atk_filled + "░" * (10 - atk_filled)
            stdscr.addstr(sep_row + 3, 1, f"ATK [{atk_gauge}] {atk_remain:.1f}s", curses.color_pair(3))
        else:
            stdscr.addstr(sep_row + 3, 1, "ATK [██████████] READY!", curses.color_pair(2) | curses.A_BOLD)

        # stats + controls
        stdscr.addstr(sep_row + 4, 1, f"COMBO:{combo}  MAX:{max_combo}  PARRY:{total_parry}  |  PERFECT:{stats['PERFECT']}  Good:{stats['Good']}  MISS:{stats['MISS']}")
        stdscr.addstr(sep_row + 5, 1, "[WASD:パリィ] [SPACE:攻撃] [↑↓:切替]")
        stdscr.addstr(sep_row + 6, 1, f"武器: {WEAPON['name']} (ATK:{WEAPON['atk']} 硬直:{WEAPON['lock_sec']}s CD:{atk_cd}s)")

        # game over / victory
        all_dead = all(e["hp"] <= 0 for e in ENEMIES)
        if player_hp <= 0:
            death_art = [
                "                    uuuuuuu                       ",
                "                uu$$$$$$$$$$$uu                   ",
                "             uu$$$$$$$$$$$$$$$$$uu                ",
                "            u$$$$$$$$$$$$$$$$$$$$$u               ",
                "           u$$$$$$$$$$$$$$$$$$$$$$$u              ",
                "          u$$$$$$$$$$$$$$$$$$$$$$$$$u             ",
                "          u$$$$$$$$$$$$$$$$$$$$$$$$$u             ",
                '          u$$$$$$"   "$$$"   "$$$$$$u             ',
                '          "$$$$"      u$u      $$$$"             ',
                "           $$$u       u$u       u$$$              ",
                "           $$$u      u$$$u      u$$$              ",
                '            "$$$$uu$$$   $$$uu$$$$"               ',
                '             "$$$$$$$"   "$$$$$$$"                ',
                "               u$$$$$$$u$$$$$$$u                  ",
                '                u$"$"$"$"$"$"$u                   ',
                '     uuu        $$u$ $ $ $ $u$$       uuu        ',
                "    u$$$$        $$$$$u$u$u$$$       u$$$$        ",
                '     $$$$$uu      "$$$$$$$$$"     uu$$$$$$        ',
                '   u$$$$$$$$$$$uu    """""    uuuu$$$$$$$$$$      ',
                '   $$$$"""$$$$$$$$$$uuu   uu$$$$$$$$$"""$$$"     ',
                '    """      ""$$$$$$$$$$$uu ""$"""              ',
                '              uuuu ""$$$$$$$$$$uuu                ',
                '     u$$$uuu$$$$$$$$$uu ""$$$$$$$$$$$uuu$$$      ',
                '     $$$$$$$$$$""""           ""$$$$$$$$$$$"      ',
                '      "$$$$$"                    ""$$$$""        ',
                '        $$$"                        $$$$"         ',
            ]
            dr = sep_row + 7
            for di, dline in enumerate(death_art):
                try:
                    stdscr.addstr(dr + di, 1, dline, curses.color_pair(3))
                except curses.error:
                    pass
            dr += len(death_art) + 1
            try:
                stdscr.addstr(dr, 1, "「 大いなる死に賛歌を！ 」", curses.color_pair(3) | curses.A_BOLD)
            except curses.error:
                pass
            try:
                stdscr.addstr(dr + 2, 1, "[Q] 終了  [R] リスタート")
            except curses.error:
                pass
        elif all_dead:
            victory_art = [
                r"        ╔══════════════════════════════════════════╗",
                r"        ║                                          ║",
                r"        ║     ██╗   ██╗██╗ ██████╗████████╗        ║",
                r"        ║     ██║   ██║██║██╔════╝╚══██╔══╝        ║",
                r"        ║     ██║   ██║██║██║        ██║            ║",
                r"        ║     ╚██╗ ██╔╝██║██║        ██║            ║",
                r"        ║      ╚████╔╝ ██║╚██████╗   ██║            ║",
                r"        ║       ╚═══╝  ╚═╝ ╚═════╝   ╚═╝            ║",
                r"        ║                                          ║",
                r"        ║    「 灰は燃え尽き、都は静寂に還る 」    ║",
                r"        ║                                          ║",
                r"        ╚══════════════════════════════════════════╝",
            ]
            for vi, vline in enumerate(victory_art):
                attr = curses.color_pair(1) | curses.A_BOLD
                try:
                    stdscr.addstr(sep_row + 7 + vi, 1, vline, attr)
                except curses.error:
                    pass
            stat_row = sep_row + 7 + len(victory_art) + 1
            stdscr.addstr(stat_row, 1, f"  残りHP: {player_hp}/100  最大コンボ: {max_combo}  総パリィ: {total_parry}", curses.A_BOLD)
            stdscr.addstr(stat_row + 1, 1, f"  PERFECT: {stats['PERFECT']}  Good: {stats['Good']}  MISS: {stats['MISS']}", curses.A_BOLD)
            stdscr.addstr(stat_row + 3, 1, "[Q] 終了  [R] リスタート")

        stdscr.refresh()

        # input
        try:
            key = stdscr.getch()
        except Exception:
            key = -1

        # flush extra bytes (IME/multibyte input)
        if key > 127 and key != curses.KEY_UP and key != curses.KEY_DOWN:
            curses.flushinp()
            key = -1

        if key in (ord('q'), ord('Q')):
            break
        elif player_hp <= 0 or all_dead:
            if key in (ord('r'), ord('R')):
                reset()
                continue
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
                    key_dir_map = {
                        ord('w'): "W", ord('W'): "W",
                        ord('s'): "S", ord('S'): "S",
                        ord('a'): "A", ord('A'): "A",
                        ord('d'): "D", ord('D'): "D",
                    }
                    pressed_dir = key_dir_map.get(key, "")
                    expected_dir = bar_dirs[i]

                    if pressed_dir != expected_dir:
                        results[i] = "MISS"
                        stats["MISS"] += 1
                        result_times[i] = now
                        player_hp = max(0, player_hp - ENEMIES[i]["atk"])
                        zanki = max(0, zanki - 2)
                        combo = 0
                    else:
                        result, _ = judge(positions[i], ENEMIES[i]["parry_zone"])
                        results[i] = result
                        stats[result] += 1
                        result_times[i] = now
                        if result == "MISS":
                            player_hp = max(0, player_hp - ENEMIES[i]["atk"])
                            zanki = max(0, zanki - 2)
                            combo = 0
                        elif result == "PERFECT":
                            zanki = min(zanki_max, zanki + 4)
                            combo += 1
                            total_parry += 1
                            max_combo = max(max_combo, combo)
                        elif result == "Good":
                            zanki = min(zanki_max, zanki + 1)
                            combo += 1
                            total_parry += 1
                            max_combo = max(max_combo, combo)
        elif key == ord(' '):
            if not is_locked and now >= atk_cooldown_until:
                i = target
                e = ENEMIES[i]
                if e["marks"] > 0:
                    dmg = WEAPON["atk"]
                    e["hp"] = max(1, e["hp"] - dmg)
                    atk_msg = f">>> {e['name']} に {dmg} ダメージ！ <<<"
                else:
                    dmg = WEAPON["atk"]
                    e["hp"] = max(0, e["hp"] - dmg)
                    atk_msg = f">>> {e['name']} に {dmg} ダメージ！ <<<"
                atk_msg_until = now + 1.0
                lock_until = now + WEAPON["lock_sec"]
                atk_cooldown_until = now + WEAPON["atk_cooldown"]
        elif key in (10, curses.KEY_ENTER):
            if zanki >= zanki_max:
                i = target
                e = ENEMIES[i]
                if e["marks"] > 0 and e["hp"] <= 1:
                    e["marks"] -= 1
                    zanki = 0
                    if e["marks"] == 0:
                        e["hp"] = 0
                        atk_msg = f">>> 撲殺！ {e['name']} を葬った！ <<<"
                    else:
                        e["hp"] = e["max_hp"]
                        atk_msg = f">>> 残火の血霧！ ● を削った！ 残り{'●' * e['marks']} <<<"
                    atk_msg_until = now + 2.0

        time.sleep(0.016)


def entry_point():
    """Entry point for the console_scripts."""
    curses.wrapper(main)


if __name__ == "__main__":
    entry_point()
