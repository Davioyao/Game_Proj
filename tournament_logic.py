"""8人雙敗淘汰賽共用核心邏輯。
規則：數字小者勝 winner = min(a,b)。
L2 準決賽採交叉配對 [0]vs[3]、[1]vs[2]，以重現需求範例排名。
"""
from __future__ import annotations
import random


def play(a: int, b: int) -> tuple[int, int]:
    """回傳 (winner, loser)。"""
    return (a, b) if a < b else (b, a)


def run_tournament(players: list[int]) -> dict:
    """輸入 8 人扁平 list（順序即為初始配對順），回傳完整賽果。
    回傳 dict 包含 w1w, w1l, w2w, w2l, r1..r8, matches 逐場紀錄。
    """
    if len(players) != 8 or set(players) != set(range(1, 9)):
        raise ValueError("players 必須是 1~8 的排列")
    p = list(players)

    # W1
    w1w, w1l, w1_matches = [], [], []
    for i in (0, 2, 4, 6):
        w, l = play(p[i], p[i + 1])
        w1w.append(w)
        w1l.append(l)
        w1_matches.append((p[i], p[i + 1], w, l))

    # W2: [0]vs[1], [2]vs[3]
    w2w, w2l, w2_matches = [], [], []
    for a, b in ((w1w[0], w1w[1]), (w1w[2], w1w[3])):
        w, l = play(a, b)
        w2w.append(w)
        w2l.append(l)
        w2_matches.append((a, b, w, l))

    # L1 爭 #3 #4：W2L 互打
    r3, r4 = play(w2l[0], w2l[1])

    # L2 準決賽（交叉）：W1L[0]vsW1L[3], W1L[1]vsW1L[2]
    s1w, s1l = play(w1l[0], w1l[3])
    s2w, s2l = play(w1l[1], w1l[2])
    # 決賽爭 #5 #6
    r5, r6 = play(s1w, s2w)
    # 敗者賽爭 #7 #8
    r7, r8 = play(s1l, s2l)

    # WF 爭 #1 #2
    r1, r2 = play(w2w[0], w2w[1])

    return {
        "players": p,
        "w1w": w1w, "w1l": w1l, "w1_matches": w1_matches,
        "w2w": w2w, "w2l": w2l, "w2_matches": w2_matches,
        "l1_match": (w2l[0], w2l[1], r3, r4),
        "l2_semi": [(w1l[0], w1l[3], s1w, s1l), (w1l[1], w1l[2], s2w, s2l)],
        "l2_final": (s1w, s2w, r5, r6),
        "l3_final": (s1l, s2l, r7, r8),
        "wf": (w2w[0], w2w[1], r1, r2),
        "ranks": {1: r1, 2: r2, 3: r3, 4: r4, 5: r5, 6: r6, 7: r7, 8: r8},
        "ranking_list": [r1, r2, r3, r4, r5, r6, r7, r8],
    }


def shuffled_players(seed: int | None = None) -> list[int]:
    ps = list(range(1, 9))
    rnd = random.Random(seed)
    rnd.shuffle(ps)
    return ps


if __name__ == "__main__":
    ex = [1, 3, 5, 2, 4, 8, 6, 7]
    res = run_tournament(ex)
    print(res["ranking_list"])
