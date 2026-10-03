"""回歸測試：固定範例 + 隨機完整性。"""
from tournament_logic import run_tournament, shuffled_players


def test_example():
    ex = [1, 3, 5, 2, 4, 8, 6, 7]
    res = run_tournament(ex)
    expected = [1, 4, 2, 6, 3, 5, 7, 8]
    assert res["ranking_list"] == expected, f"got {res['ranking_list']}, want {expected}"
    print("PASS example:", res["ranking_list"])


def test_random_100():
    for seed in range(100):
        ps = shuffled_players(seed)
        res = run_tournament(ps)
        rl = res["ranking_list"]
        assert sorted(rl) == list(range(1, 9)), f"seed {seed} ranking broken: {rl}"
        # 勝負規則：每場皆為小號勝
        for a, b, w, _l in res["w1_matches"] + res["w2_matches"]:
            assert w == min(a, b)
    print("PASS random 100 seeds")


if __name__ == "__main__":
    test_example()
    test_random_100()
