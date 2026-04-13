#!/usr/bin/env python3
"""cli-parris UI モックアップ - ターミナルで画面イメージを確認するためのスクリプト"""

import os
import sys
import time

# ターミナル幅を取得
try:
    COLS = os.get_terminal_size().columns
except Exception:
    COLS = 80

def clear():
    os.system("clear" if os.name != "nt" else "cls")

def center(text, width=None):
    w = width or COLS
    return text.center(w)

def bar(current, maximum, length=20, filled="█", empty="░"):
    ratio = current / maximum
    filled_len = int(length * ratio)
    return filled * filled_len + empty * (length - filled_len)

# ─────────────────────────────────────────
# 画面1: 戦闘画面（通常）
# ─────────────────────────────────────────
def screen_battle_normal():
    clear()
    print()
    print(center("═══════════════════ Floor 3 ═══════════════════"))
    print()
    # 敵表示
    enemies = [
        ("ゴブリン斥候",  6, 10),
        ("★亡者の騎士★", 25, 25),
        ("腐敗犬",        8, 12),
    ]
    enemy_lines = []
    for name, hp, maxhp in enemies:
        hpbar = bar(hp, maxhp, 10)
        enemy_lines.append(f"  {name:　<8} [{hpbar}] {hp}/{maxhp}")

    for line in enemy_lines:
        print(line)
    print()

    # プレイヤーステータス
    print(f"  HP:   [{bar(72, 100, 20)}] 72/100")
    print(f"  残火: [{bar(4, 10, 20)}]  4/10")
    print()
    print(f"  ITEM: [1]緋の雫  [2]灰霧の壺  [3]---  [4]---")
    print()

    # ターゲット表示
    print(center("[L-Shift ◀]  >> ★亡者の騎士★ <<  [▶ R-Shift]"))
    print()

    # 方向キーガイド
    print(center("     W(上)"))
    print(center("A(左)    D(右)"))
    print(center("     S(下)"))
    print()

    # 攻撃インジケーター
    print(center("─── 敵の攻撃 ───"))
    print(center("▶▶▶  【↑ 上段】 ◆◆◆◆◆    タイミング！"))
    print()
    print(center("[SPACE: 攻撃]"))
    print()
    print("─" * COLS)


# ─────────────────────────────────────────
# 画面2: パリィ成功演出
# ─────────────────────────────────────────
def screen_parry_perfect():
    clear()
    print()
    print(center("═══════════════════ Floor 3 ═══════════════════"))
    print()
    enemies = [
        ("ゴブリン斥候",  6, 10),
        ("★亡者の騎士★", 25, 25),
        ("腐敗犬",        8, 12),
    ]
    for name, hp, maxhp in enemies:
        hpbar = bar(hp, maxhp, 10)
        print(f"  {name:　<8} [{hpbar}] {hp}/{maxhp}")
    print()

    print(f"  HP:   [{bar(72, 100, 20)}] 72/100")
    print(f"  残火: [{bar(6, 10, 20)}]  6/10  ▲+2!")
    print()
    print(f"  ITEM: [1]緋の雫  [2]灰霧の壺  [3]---  [4]---")
    print()
    print(center("[L-Shift ◀]  >> ★亡者の騎士★ <<  [▶ R-Shift]"))
    print()
    print()
    print(center("★★★ P E R F E C T ★★★"))
    print(center("弾き返した！  残火が燃え上がる！"))
    print()
    print()
    print("─" * COLS)


# ─────────────────────────────────────────
# 画面3: パリィ失敗（被ダメージ）
# ─────────────────────────────────────────
def screen_parry_miss():
    clear()
    print()
    print(center("═══════════════════ Floor 3 ═══════════════════"))
    print()
    enemies = [
        ("ゴブリン斥候",  6, 10),
        ("★亡者の騎士★", 25, 25),
        ("腐敗犬",        8, 12),
    ]
    for name, hp, maxhp in enemies:
        hpbar = bar(hp, maxhp, 10)
        print(f"  {name:　<8} [{hpbar}] {hp}/{maxhp}")
    print()

    print(f"  HP:   [{bar(57, 100, 20)}] 57/100  ▼-15!")
    print(f"  残火: [{bar(4, 10, 20)}]  4/10")
    print()
    print(f"  ITEM: [1]緋の雫  [2]灰霧の壺  [3]---  [4]---")
    print()
    print(center("[L-Shift ◀]  >> ★亡者の騎士★ <<  [▶ R-Shift]"))
    print()
    print()
    print(center("✗✗✗  M I S S  ✗✗✗"))
    print(center("亡者の騎士の斬撃を受けた！"))
    print()
    print()
    print("─" * COLS)


# ─────────────────────────────────────────
# 画面4: 残火スキル発動
# ─────────────────────────────────────────
def screen_ember_attack():
    clear()
    print()
    print(center("═══════════════════ Floor 3 ═══════════════════"))
    print()
    enemies = [
        ("ゴブリン斥候",  2, 10),
        ("★亡者の騎士★", 18, 25),
        ("腐敗犬",        3, 12),
    ]
    for name, hp, maxhp in enemies:
        hpbar = bar(hp, maxhp, 10)
        print(f"  {name:　<8} [{hpbar}] {hp}/{maxhp}")
    print()

    print(f"  HP:   [{bar(57, 100, 20)}] 57/100")
    print(f"  残火: [{bar(0, 10, 20)}]  0/10")
    print()
    print(f"  ITEM: [1]緋の雫  [2]灰霧の壺  [3]---  [4]---")
    print()
    print()
    print(center("🔥🔥🔥  弾きの残火  解放  🔥🔥🔥"))
    print(center("灰燼の一撃！  全敵に 12 ダメージ！"))
    print()
    print()
    print("─" * COLS)


# ─────────────────────────────────────────
# 画面5: ゲームオーバー
# ─────────────────────────────────────────
def screen_game_over():
    clear()
    print()
    print()
    print()
    print()
    print(center("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"))
    print()
    print(center("Y O U   D I E D"))
    print()
    print(center("「 大いなる死に賛歌を！ 」"))
    print()
    print(center("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"))
    print()
    print()
    print(center("Floor 3  まで到達"))
    print(center("パリィ成功率: 68%"))
    print(center("Perfect率:   42%"))
    print(center("撃破数:      7"))
    print()
    print(center("獲得刻印: 「灰に沈んだ瞳」"))
    print(center("  パリィ猶予+微量 / 被ダメ-1 / 残火蓄積+5%"))
    print()
    print(center("[Enter] タイトルに戻る"))
    print()


# ─────────────────────────────────────────
# 画面6: フロアクリア → ビルド選択
# ─────────────────────────────────────────
def screen_build_select():
    clear()
    print()
    print(center("═══════════════ Floor 3 Clear! ═══════════════"))
    print()
    print(center("報酬: 凝血のトークン +15"))
    print(center("ドロップ: 朽ちた投刃 (アイテム)"))
    print()
    print(center("──── ビルドを選択せよ ────"))
    print()
    print("  [1] 残火の加護")
    print("      残火の蓄積速度 +20%")
    print()
    print("  [2] 鋼の本能")
    print("      パリィ判定の猶予時間を拡大")
    print()
    print("  [3] 血の渇望")
    print("      攻撃力 +5、被ダメージ +3")
    print()
    print()
    print(center("[1] [2] [3] で選択"))
    print()
    print("─" * COLS)


# ─────────────────────────────────────────
# 画面7: ショップ
# ─────────────────────────────────────────
def screen_shop():
    clear()
    print()
    print(center("═══════════════ 忘却の商人 ═══════════════"))
    print()
    print(center("「…何か、要るか？」"))
    print()
    print(f"  所持トークン: 45")
    print()
    print("  ┌─────────────────────────────────────────┐")
    print("  │ [1] 緋の雫          …… 10トークン       │")
    print("  │     HPを30回復                           │")
    print("  │                                         │")
    print("  │ [2] 受け流しの残滓   …… 20トークン       │")
    print("  │     一定時間パリィ猶予拡大               │")
    print("  │                                         │")
    print("  │ [3] 血錆の菜刀(武器) …… 30トークン       │")
    print("  │     攻撃力+10                            │")
    print("  │                                         │")
    print("  │ [4] 無縁墓の鎖鎧(防具)…… 25トークン      │")
    print("  │     被ダメ-6                             │")
    print("  └─────────────────────────────────────────┘")
    print()
    print(f"  ITEM: [1]緋の雫  [2]---  [3]---  [4]---")
    print(f"  装備: 亡者の包丁(攻+5) / 擦り切れた革鎧(防-3)")
    print()
    print(center("[1]-[4] 購入  [Enter] 次のフロアへ"))
    print()
    print("─" * COLS)


# ─────────────────────────────────────────
# メイン: 全画面を順番に表示
# ─────────────────────────────────────────
SCREENS = [
    ("戦闘画面（通常）", screen_battle_normal),
    ("パリィ成功 - PERFECT", screen_parry_perfect),
    ("パリィ失敗 - MISS", screen_parry_miss),
    ("残火スキル発動", screen_ember_attack),
    ("ゲームオーバー", screen_game_over),
    ("ビルド選択", screen_build_select),
    ("ショップ", screen_shop),
]

def main():
    print()
    print("=== cli-parris UI モックアップ ===")
    print(f"全{len(SCREENS)}画面を順番に表示します。")
    print("[Enter] で次の画面に進みます。")
    print()
    input("準備ができたら [Enter] を押してください...")

    for i, (title, render) in enumerate(SCREENS):
        render()
        print()
        if i < len(SCREENS) - 1:
            input(f"  ({i+1}/{len(SCREENS)}) {title}  — [Enter] で次へ...")
        else:
            print(f"  ({i+1}/{len(SCREENS)}) {title}")
            print()
            input("  全画面の表示が完了しました。[Enter] で終了...")

if __name__ == "__main__":
    main()
