#!/usr/bin/env python3
"""parry bar demo - constant & delay"""

import curses
import time

BAR_LEN = 40
ZONE_START = 33
ZONE_END = 37
PERFECT_POS = 35

def speed_constant(t):
    return t

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

def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)

    patterns = [
        ("slow",   speed_constant, 3.0),
        ("normal", speed_constant, 2.0),
        ("fast",   speed_constant, 1.2),
    ]
    cur = 1
    stats = {"PERFECT": 0, "Good": 0, "MISS": 0}

    while True:
        name, fn, dur = patterns[cur]
        start = time.time()
        result = None
        pos = 0

        while True:
            stdscr.erase()
            elapsed = time.time() - start

            stdscr.addstr(1, 2, "PARRY DEMO", curses.A_BOLD)
            stdscr.addstr(1, 20, f"[{name}]", curses.A_BOLD)
            stdscr.addstr(2, 2, "[WASD]:parry  [N]:switch  [Q]:quit")

            stdscr.addstr(4, 18, "[up]")

            if result is None:
                t = min(elapsed / dur, 1.0)
                pos = fn(t) * (BAR_LEN - 1)
                bar = draw_bar(pos)
                stdscr.addstr(6, 5, bar)

                if ZONE_START <= int(pos) <= ZONE_END:
                    stdscr.addstr(7, 5 + ZONE_START, "NOW!", curses.color_pair(2) | curses.A_BOLD)

                if pos >= BAR_LEN - 1:
                    result = "MISS"
                    stats["MISS"] += 1
            else:
                bar = draw_bar(pos)
                stdscr.addstr(6, 5, bar)

                if result == "PERFECT":
                    c = curses.color_pair(1) | curses.A_BOLD
                elif result == "Good":
                    c = curses.color_pair(2)
                else:
                    c = curses.color_pair(3)
                stdscr.addstr(8, 18, result, c)
                stdscr.addstr(10, 10, "[SPACE]:retry  [N]:switch  [Q]:quit")

            stdscr.addstr(12, 2, f"PERFECT:{stats['PERFECT']}  Good:{stats['Good']}  MISS:{stats['MISS']}")

            stdscr.refresh()

            try:
                key = stdscr.getch()
            except:
                key = -1

            if key in (ord('q'), ord('Q')):
                return
            elif key in (ord('n'), ord('N')):
                cur = (cur + 1) % len(patterns)
                break
            elif key in (ord('w'), ord('a'), ord('s'), ord('d'),
                         ord('W'), ord('A'), ord('S'), ord('D')):
                if result is None:
                    result, color = judge(pos)
                    stats[result] += 1
            elif key == ord(' ') and result is not None:
                break

            time.sleep(0.016)

curses.wrapper(main)
