"""Python Tkinter GUI：8人雙敗淘汰賽模擬器。
執行： python3 tournament_gui.py
v1.1：#4改為殿軍＋Canvas樹狀圖（保留文字看板）。
"""
import tkinter as tk
from tkinter import ttk
import random

from tournament_logic import play

# 配色（與 HTML 版一致）
C_WIN_FILL, C_WIN_LINE = "#e6f4ea", "#188038"
C_LOSE_FILL, C_LOSE_LINE = "#fce8e6", "#d93025"
C_PEND_FILL, C_PEND_LINE = "#f1f3f4", "#9aa0a6"
C_CHAMP_FILL, C_CHAMP_LINE = "#fff8e1", "#f9ab00"
C_NORM_FILL, C_NORM_LINE = "#ffffff", "#5f6368"


class TournamentGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("8人雙敗淘汰賽模擬器")
        self.root.geometry("1000x800")
        self.state = 0
        self.players: list[int] = [1, 2, 3, 4, 5, 6, 7, 8]
        self.w1w: list[int] = []
        self.w1l: list[int] = []
        self.w2w: list[int] = []
        self.w2l: list[int] = []
        self.s1w = self.s1l = self.s2w = self.s2l = 0
        self.setup_ui()
        self.refresh_tree()

    # ---------- UI（整窗可垂直捲動，避免樹狀圖被遮蔽） ----------
    def setup_ui(self):
        # 外層捲動容器
        self._vbar = ttk.Scrollbar(self.root, orient=tk.VERTICAL)
        self._vbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._outer = tk.Canvas(self.root, highlightthickness=0, yscrollcommand=self._vbar.set)
        self._outer.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._vbar.config(command=self._outer.yview)
        container = ttk.Frame(self._outer, padding=4)
        self._inner_id = self._outer.create_window((0, 0), window=container, anchor="nw")

        def _on_inner_configure(_e=None):
            self._outer.configure(scrollregion=self._outer.bbox("all"))

        def _on_outer_configure(e):
            self._outer.itemconfig(self._inner_id, width=e.width - 8)
            _on_inner_configure()

        container.bind("<Configure>", _on_inner_configure)
        self._outer.bind("<Configure>", _on_outer_configure)
        # mac 滾輪 / 觸控板支援
        def _on_wheel(e):
            try:
                self._outer.yview_scroll(-1 if e.delta > 0 else 1, "units")
            except Exception:
                pass
            return "break"
        self._outer.bind_all("<MouseWheel>", _on_wheel, add=True)

        top = ttk.Frame(container, padding=8)
        top.pack(fill=tk.X)
        self.status = ttk.Label(top, text="Step0 準備：請抽籤分組", font=("Arial", 12, "bold"))
        self.status.pack(side=tk.LEFT, padx=5)
        btns = ttk.Frame(top)
        btns.pack(side=tk.RIGHT)
        ttk.Button(btns, text="範例種子", command=self.load_example).pack(side=tk.LEFT, padx=2)
        ttk.Button(btns, text="重置", command=self.reset).pack(side=tk.LEFT, padx=2)
        self.next_btn = ttk.Button(btns, text="開始隨機分組", command=self.next_step)
        self.next_btn.pack(side=tk.LEFT, padx=2)

        main = ttk.Frame(container, padding=8)
        main.pack(fill=tk.X)
        left = ttk.LabelFrame(main, text=" ⚔️ 對戰看板（文字說明保留） ", padding=8)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self.text = tk.Text(left, wrap=tk.WORD, font=("Arial", 11), bg="#ffffff", state=tk.DISABLED, height=8)
        self.text.pack(fill=tk.BOTH, expand=True)

        right = ttk.LabelFrame(main, text=" 📊 排名紀錄 ", padding=8)
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=5)
        titles = ["#1 冠軍", "#2 亞軍", "#3 季軍", "#4 殿軍",
                  "#5 第五", "#6 第六", "#7 第七", "#8 第八"]
        self.rank_labels: dict[str, ttk.Label] = {}
        for i, t in enumerate(titles):
            ttk.Label(right, text=t, font=("Arial", 10)).grid(row=i, column=0, sticky="w", pady=2, padx=5)
            lbl = ttk.Label(right, text="-", font=("Arial", 11, "bold"), foreground="blue")
            lbl.grid(row=i, column=1, padx=18)
            self.rank_labels[f"r{i+1}"] = lbl

        hint = ttk.Label(container, text="規則：小號必勝 min(A,B)。L2準決賽交叉配對 W1L[0]vsW1L[3]、W1L[1]vsW1L[2]｜金=贏家線 紅=輸家線 灰=未定",
                         font=("Arial", 9), foreground="#555")
        hint.pack()

        tree = ttk.LabelFrame(container, text=" 🌳 樹狀分支圖（Canvas連線圖） ", padding=8)
        tree.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        win_head = ttk.Frame(tree)
        win_head.pack(fill=tk.X)
        ttk.Label(win_head, text="勝部樹 Winners", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        self.win_btn = ttk.Button(win_head, text="開始隨機分組", command=self.next_step)
        self.win_btn.pack(side=tk.RIGHT)
        # 高度加大＋留白，避免底部節點被切掉（內容最高約326）
        self.cv_win = tk.Canvas(tree, height=360, bg="#fbfcff", highlightthickness=1, highlightbackground="#ddd")
        self.cv_win.pack(fill=tk.X)
        lose_head = ttk.Frame(tree)
        lose_head.pack(fill=tk.X, pady=(6, 0))
        ttk.Label(lose_head, text="敗部樹 Losers（爭 #3季軍/#4殿軍、#5~#8）", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        self.lose_btn = ttk.Button(lose_head, text="開始隨機分組", command=self.next_step)
        self.lose_btn.pack(side=tk.RIGHT)
        # 高度加大＋留白（內容最高約262，另加L3標籤空間）
        self.cv_lose = tk.Canvas(tree, height=310, bg="#fbfcff", highlightthickness=1, highlightbackground="#ddd")
        self.cv_lose.pack(fill=tk.X)

    def _sync_buttons(self, label: str | None = None, disabled: bool = False):
        """三按鍵同步：頂部主按鍵＋勝部樹內＋敗部樹內。"""
        if label is not None:
            self.next_btn.config(text=label)
            self.win_btn.config(text=label)
            self.lose_btn.config(text=label)
        state = tk.DISABLED if disabled else tk.NORMAL
        self.next_btn.config(state=state)
        self.win_btn.config(state=state)
        self.lose_btn.config(state=state)

    # ---------- Canvas 繪圖 helpers ----------
    def _box(self, cv: tk.Canvas, x, y, w, h, text, fill, outline, bold=False):
        cv.create_rectangle(x, y, x + w, y + h, fill=fill, outline=outline, width=2)
        cv.create_text(x + w / 2, y + h / 2, text=str(text),
                       font=("Arial", 10, "bold" if bold else "normal"))

    def _edge(self, cv: tk.Canvas, x1, y1, x2, y2, color, width=2, dash=None):
        mx = (x1 + x2) / 2
        cv.create_line(x1, y1, mx, y1, mx, y2, x2, y2, fill=color, width=width,
                       dash=dash, joinstyle="round")

    def _rank(self, key: str) -> str:
        v = self.rank_labels[key].cget("text")
        return v if v != "-" else "?"

    # ---------- 樹狀圖重繪 ----------
    def refresh_tree(self):
        self._draw_win()
        self._draw_lose()

    def _draw_win(self):
        cv = self.cv_win
        cv.delete("all")
        W = cv.winfo_width()
        if W < 100:
            W = 940
        # 固定座標（viewBox 概念：640x330）
        qx, qw, qh = 20, 55, 24
        qy = [30, 60, 115, 145, 200, 230, 265, 295] if False else [25, 53, 108, 136, 191, 219, 274, 302]
        # 簡化：4 組
        qy = [25, 53, 108, 136, 191, 219, 274, 302]
        w1x, w1y = 150, [39, 122, 205, 288]
        w2x, w2y = 290, [80, 246]
        cx, cw = 440, 110
        decided_w1 = len(self.w1w) == 4
        decided_w2 = len(self.w2w) == 2
        decided_wf = self._rank("r1") != "?"
        cv.create_text(qx, 12, text="QF初賽", anchor="w", font=("Arial", 9), fill="#5f6368")
        for i in range(8):
            label = "?" if self.state == 0 else str(self.players[i])
            if self.state == 0:
                fill, line = C_PEND_FILL, C_PEND_LINE
            elif decided_w1:
                mi = i // 2
                is_win = (self.players[i] == self.w1w[mi])
                fill, line = (C_WIN_FILL, C_WIN_LINE) if is_win else (C_LOSE_FILL, C_LOSE_LINE)
            else:
                fill, line = C_NORM_FILL, C_NORM_LINE
            self._box(cv, qx, qy[i], qw, qh, label, fill, line, bold=decided_w1)
        cv.create_text(w1x, 26, text="W1勝", anchor="w", font=("Arial", 9), fill="#5f6368")
        for i in range(4):
            label = str(self.w1w[i]) if decided_w1 else "?"
            fill, line = (C_WIN_FILL, C_WIN_LINE) if decided_w1 else (C_PEND_FILL, C_PEND_LINE)
            self._box(cv, w1x, w1y[i], qw, qh, label, fill, line, bold=True)
        cv.create_text(w2x, 66, text="決賽者", anchor="w", font=("Arial", 9), fill="#5f6368")
        for i in range(2):
            label = str(self.w2w[i]) if decided_w2 else "?"
            fill, line = (C_WIN_FILL, C_WIN_LINE) if decided_w2 else (C_PEND_FILL, C_PEND_LINE)
            self._box(cv, w2x, w2y[i], qw, qh, label, fill, line, bold=True)
        self._box(cv, cx, 150, cw, 30, f"👑#1:{self._rank('r1')}",
                  C_CHAMP_FILL if decided_wf else C_PEND_FILL,
                  C_CHAMP_LINE if decided_wf else C_PEND_LINE, bold=True)
        self._box(cv, cx, 186, cw, 30, f"#2:{self._rank('r2')}",
                  C_NORM_FILL if decided_wf else C_PEND_FILL,
                  C_NORM_LINE if decided_wf else C_PEND_LINE, bold=False)
        # 連線 QF->W1
        for m in range(4):
            for k in range(2):
                i = m * 2 + k
                x1, y1, x2, y2 = qx + qw, qy[i] + qh / 2, w1x, w1y[m] + qh / 2
                if not decided_w1:
                    self._edge(cv, x1, y1, x2, y2, C_PEND_LINE)
                else:
                    is_win = (self.players[i] == self.w1w[m])
                    self._edge(cv, x1, y1, x2, y2,
                               C_CHAMP_LINE if is_win else C_LOSE_LINE,
                               3 if is_win else 2, None if is_win else (5, 3))
        # W1->W2
        for a, b, t in ((0, 1, 0), (2, 3, 1)):
            for s in (a, b):
                x1, y1, x2, y2 = w1x + qw, w1y[s] + qh / 2, w2x, w2y[t] + qh / 2
                if not decided_w2:
                    self._edge(cv, x1, y1, x2, y2, C_PEND_LINE)
                else:
                    is_win = (self.w1w[s] == self.w2w[t])
                    self._edge(cv, x1, y1, x2, y2,
                               C_CHAMP_LINE if is_win else C_LOSE_LINE,
                               3 if is_win else 2, None if is_win else (5, 3))
        # W2->冠亞
        for i in range(2):
            x1, y1 = w2x + qw, w2y[i] + qh / 2
            x2, y2 = cx, 165 if i == 0 else 201
            if not decided_w2:
                self._edge(cv, x1, y1, x2, y2, C_PEND_LINE)
            else:
                is_champ = decided_wf and (str(self.w2w[i]) == self._rank("r1"))
                if not decided_wf:
                    self._edge(cv, x1, y1, x2, y2, C_PEND_LINE)
                else:
                    self._edge(cv, x1, y1, x2, y2,
                               C_CHAMP_LINE if is_champ else C_LOSE_LINE,
                               3 if is_champ else 2, None if is_champ else (5, 3))

    def _draw_lose(self):
        cv = self.cv_lose
        cv.delete("all")
        r3, r4 = self._rank("r3"), self._rank("r4")
        r5, r6, r7, r8 = self._rank("r5"), self._rank("r6"), self._rank("r7"), self._rank("r8")
        has_w2l = len(self.w2l) == 2
        has_semi = (self.s1w != 0)
        has_w1l = len(self.w1l) == 4
        # L1
        cv.create_text(15, 12, text="L1 爭#3季軍/#4殿軍", anchor="w", font=("Arial", 9), fill="#5f6368")
        for i, y in enumerate((28, 58)):
            label = str(self.w2l[i]) if has_w2l else "?"
            if not has_w2l:
                fill, line = C_PEND_FILL, C_PEND_LINE
            else:
                is_win = (label == r3)
                fill, line = (C_WIN_FILL, C_WIN_LINE) if is_win else (C_LOSE_FILL, C_LOSE_LINE)
            self._box(cv, 15, y, 55, 24, label, fill, line, bold=has_w2l)
        self._edge(cv, 70, 40, 130, 40, C_CHAMP_LINE if r3 != "?" else C_PEND_LINE, 3 if r3 != "?" else 1.5)
        self._edge(cv, 70, 70, 130, 70, C_LOSE_LINE if r3 != "?" else C_PEND_LINE, 2 if r3 != "?" else 1.5,
                   None if r3 == "?" else (5, 3))
        self._box(cv, 130, 28, 75, 24, f"#3:{r3}", C_CHAMP_FILL if r3 != "?" else C_PEND_FILL,
                  C_CHAMP_LINE if r3 != "?" else C_PEND_LINE, bold=True)
        self._box(cv, 130, 58, 75, 24, f"#4:{r4}", C_NORM_FILL if r4 != "?" else C_PEND_FILL,
                  C_NORM_LINE if r4 != "?" else C_PEND_LINE)
        # L2
        cv.create_text(280, 12, text="L2 準決賽(交叉)→爭#5/#6", anchor="w", font=("Arial", 9), fill="#5f6368")
        order_labels = [str(self.w1l[0]) if has_w1l else "?", str(self.w1l[3]) if has_w1l else "?",
                        str(self.w1l[1]) if has_w1l else "?", str(self.w1l[2]) if has_w1l else "?"]
        semi_y = (28, 58, 118, 148)
        for i, y in enumerate(semi_y):
            if not has_semi:
                fill, line = C_PEND_FILL, C_PEND_LINE
            else:
                win_vals = {str(self.s1w), str(self.s2w)}
                fill, line = (C_WIN_FILL, C_WIN_LINE) if order_labels[i] in win_vals else (C_LOSE_FILL, C_LOSE_LINE)
                # 需排除重複數字誤判：數字唯一故可直接比
            self._box(cv, 280, y, 55, 24, order_labels[i], fill, line, bold=has_semi)
        self._box(cv, 395, 43, 55, 24, str(self.s1w) if has_semi else "?", C_WIN_FILL if has_semi else C_PEND_FILL,
                  C_WIN_LINE if has_semi else C_PEND_LINE, bold=True)
        self._box(cv, 395, 133, 55, 24, str(self.s2w) if has_semi else "?", C_WIN_FILL if has_semi else C_PEND_FILL,
                  C_WIN_LINE if has_semi else C_PEND_LINE, bold=True)
        self._edge(cv, 335, 40, 395, 51, C_CHAMP_LINE if has_semi else C_PEND_LINE, 3 if has_semi else 1.5)
        self._edge(cv, 335, 70, 395, 59, C_LOSE_LINE if has_semi else C_PEND_LINE, 2 if has_semi else 1.5,
                   None if not has_semi else (5, 3))
        self._edge(cv, 335, 130, 395, 141, C_CHAMP_LINE if has_semi else C_PEND_LINE, 3 if has_semi else 1.5)
        self._edge(cv, 335, 160, 395, 149, C_LOSE_LINE if has_semi else C_PEND_LINE, 2 if has_semi else 1.5,
                   None if not has_semi else (5, 3))
        self._edge(cv, 450, 55, 515, 70, C_CHAMP_LINE if r5 != "?" else C_PEND_LINE, 3 if r5 != "?" else 1.5)
        self._edge(cv, 450, 145, 515, 100, C_LOSE_LINE if r5 != "?" else C_PEND_LINE, 2 if r5 != "?" else 1.5,
                   None if r5 == "?" else (5, 3))
        self._box(cv, 515, 58, 70, 24, f"#5:{r5}", C_CHAMP_FILL if r5 != "?" else C_PEND_FILL,
                  C_CHAMP_LINE if r5 != "?" else C_PEND_LINE, bold=True)
        self._box(cv, 515, 88, 70, 24, f"#6:{r6}", C_NORM_FILL if r6 != "?" else C_PEND_FILL,
                  C_NORM_LINE if r6 != "?" else C_PEND_LINE)
        # L3
        cv.create_text(280, 194, text="L3 爭#7/#8", anchor="w", font=("Arial", 9), fill="#5f6368")
        for i, (v, y) in enumerate(((str(self.s1l) if has_semi else "?", 208),
                                   (str(self.s2l) if has_semi else "?", 238))):
            if not has_semi:
                fill, line = C_PEND_FILL, C_PEND_LINE
            else:
                is_win = (v == r7)
                fill, line = (C_WIN_FILL, C_WIN_LINE) if is_win else (C_LOSE_FILL, C_LOSE_LINE)
            self._box(cv, 280, y, 55, 24, v, fill, line, bold=has_semi)
        self._edge(cv, 335, 220, 395, 220, C_CHAMP_LINE if r7 != "?" else C_PEND_LINE, 3 if r7 != "?" else 1.5)
        self._edge(cv, 335, 250, 395, 250, C_LOSE_LINE if r7 != "?" else C_PEND_LINE, 2 if r7 != "?" else 1.5,
                   None if r7 == "?" else (5, 3))
        self._box(cv, 395, 208, 70, 24, f"#7:{r7}", C_CHAMP_FILL if r7 != "?" else C_PEND_FILL,
                  C_CHAMP_LINE if r7 != "?" else C_PEND_LINE, bold=True)
        self._box(cv, 395, 238, 70, 24, f"#8:{r8}", C_NORM_FILL if r8 != "?" else C_PEND_FILL,
                  C_NORM_LINE if r8 != "?" else C_PEND_LINE)

    # ---------- 邏輯 ----------
    def log(self, msg: str, clear: bool = True):
        self.text.config(state=tk.NORMAL)
        if clear:
            self.text.delete("1.0", tk.END)
        self.text.insert(tk.END, msg + "\n")
        self.text.config(state=tk.DISABLED)

    def load_example(self):
        self.reset(silent=True)
        self.players = [1, 3, 5, 2, 4, 8, 6, 7]
        self.show_groups(is_example=True)
        self.state = 1
        self.status.config(text="Step0 完成：已載入範例，準備 W1")
        self._sync_buttons("執行 勝部第一輪 W1", False)
        self.refresh_tree()

    def reset(self, silent: bool = False):
        self.state = 0
        self.players = [1, 2, 3, 4, 5, 6, 7, 8]
        self.w1w, self.w1l, self.w2w, self.w2l = [], [], [], []
        self.s1w = self.s1l = self.s2w = self.s2l = 0
        for k in self.rank_labels:
            self.rank_labels[k].config(text="-")
        self._sync_buttons("開始隨機分組", False)
        self.status.config(text="Step0 準備：請抽籤分組")
        if not silent:
            self.log("已重置。請開始隨機分組或載入範例種子。")
        self.refresh_tree()

    def show_groups(self, is_example: bool = False):
        p = self.players
        tag = "範例配對" if is_example else "隨機配對"
        self.log(f"{tag}完成：\n\n對決1: {p[0]} vs {p[1]}\n對決2: {p[2]} vs {p[3]}\n"
                 f"對決3: {p[4]} vs {p[5]}\n對決4: {p[6]} vs {p[7]}")

    def next_step(self):
        if self.state == 0:
            random.shuffle(self.players)
            self.show_groups()
            self.status.config(text="Step1 準備：分組完成，執行 W1")
            self._sync_buttons("執行 勝部第一輪 W1", False)
            self.state = 1
        elif self.state == 1:  # W1
            p = self.players
            self.w1w, self.w1l = [], []
            lines = ["勝部第一輪 W1 結果：\n"]
            for i in (0, 2, 4, 6):
                w, l = play(p[i], p[i + 1])
                self.w1w.append(w)
                self.w1l.append(l)
                lines.append(f"【勝】{w} vs【敗】{l}  （{p[i]}vs{p[i+1]}）")
            self.log("\n".join(lines))
            self.status.config(text="Step2 準備：W1結束，執行 W2")
            self._sync_buttons("執行 勝部第二輪 W2", False)
            self.state = 2
        elif self.state == 2:  # W2
            w1, l1 = play(self.w1w[0], self.w1w[1])
            w2, l2 = play(self.w1w[2], self.w1w[3])
            self.w2w, self.w2l = [w1, w2], [l1, l2]
            self.log(f"勝部第二輪 W2 結果：\n\n【晉級總決賽】{w1} vs【掉入敗部】{l1}\n"
                     f"【晉級總決賽】{w2} vs【掉入敗部】{l2}")
            self.status.config(text="Step3 準備：W2結束，先打總決賽爭#1冠軍#2亞軍")
            self._sync_buttons("執行 總決賽 (爭#1冠軍#2亞軍)", False)
            self.state = 3
        elif self.state == 3:  # WF 先出
            w, l = play(self.w2w[0], self.w2w[1])
            self.rank_labels["r1"].config(text=str(w))
            self.rank_labels["r2"].config(text=str(l))
            self.log(f"🏆 總決賽先出：\n\n👑冠軍 #1：{w}\n🥈亞軍 #2：{l}")
            self.status.config(text="Step4 準備：#1#2確定，執行敗部 L1")
            self._sync_buttons("執行 敗部第一次賽 (爭#3季軍#4殿軍)", False)
            self.state = 4
        elif self.state == 4:  # L1
            a, b = self.w2l[0], self.w2l[1]
            w, l = play(a, b)
            self.rank_labels["r3"].config(text=str(w))
            self.rank_labels["r4"].config(text=str(l))
            self.log(f"敗部第一次賽 L1：\n\n季軍殿軍賽 {a} vs {b}\n→【#3季軍】{w} vs【#4殿軍】{l}")
            self.status.config(text="Step5 準備：#3季軍#4殿軍確定，執行 L2")
            self._sync_buttons("執行 敗部第二次賽 (爭#5#6)", False)
            self.state = 5
        elif self.state == 5:  # L2
            self.s1w, self.s1l = play(self.w1l[0], self.w1l[3])
            self.s2w, self.s2l = play(self.w1l[1], self.w1l[2])
            w, l = play(self.s1w, self.s2w)
            self.rank_labels["r5"].config(text=str(w))
            self.rank_labels["r6"].config(text=str(l))
            self.log(f"敗部第二次賽 L2：\n\n準決賽1: {self.w1l[0]} vs {self.w1l[3]} → {self.s1w}勝/{self.s1l}待定\n"
                     f"準決賽2: {self.w1l[1]} vs {self.w1l[2]} → {self.s2w}勝/{self.s2l}待定\n"
                     f"決賽: {self.s1w} vs {self.s2w} →【#5】{w} vs【#6】{l}")
            self.status.config(text="Step6 準備：#5#6確定，執行 L3")
            self._sync_buttons("執行 敗部第三次賽 (爭#7#8)", False)
            self.state = 6
        elif self.state == 6:  # L3 收尾
            w, l = play(self.s1l, self.s2l)
            self.rank_labels["r7"].config(text=str(w))
            self.rank_labels["r8"].config(text=str(l))
            r1 = self.rank_labels["r1"].cget("text")
            r2 = self.rank_labels["r2"].cget("text")
            r3 = self.rank_labels["r3"].cget("text")
            r4 = self.rank_labels["r4"].cget("text")
            self.log(f"🎉 全部結束！（總決賽已先出）\n\n👑#1:{r1} 🥈#2:{r2} 🥉#3:{r3} 殿軍#4:{r4}\n"
                     f"#5:{self.rank_labels['r5'].cget('text')} #6:{self.rank_labels['r6'].cget('text')} "
                     f"#7:{w} #8:{l}")
            self.status.config(text="完賽！總決賽先出，後續排名全定")
            self._sync_buttons("比賽結束", True)
        self.refresh_tree()


if __name__ == "__main__":
    root = tk.Tk()
    TournamentGUI(root)
    root.mainloop()
