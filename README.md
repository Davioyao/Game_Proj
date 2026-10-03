# 8人雙敗淘汰賽模擬器

8 名選手（代號 `1~8`）雙敗淘汰賽互動介面：**小號必勝 `min(A,B)`**，
總決賽先決定 `#1 冠軍 / #2 亞軍`，再依序決定敗部 `#3~#8` 名次。
提供 **HTML（瀏覽器）** 與 **Python Tkinter（桌面）** 兩種 GUI，邏輯完全一致。

![game.html 完賽截圖（範例種子）](game_screenshot.png)

> 截圖：載入範例種子 `[1,3] [5,2] [4,8] [6,7]` 並跑完全程，
> 排名為 `1, 4, 2, 6, 3, 5, 7, 8`（`#1冠軍 #2亞軍 #3季軍 #4殿軍`）。

## 規則

- 參賽 8 人，代號 `1~8`，開局隨機兩兩分組。
- 任何對戰：**代號數字小者獲勝**。
- 勝部：W1（4場）→ W2（2場）→ WF 總決賽（先出 `#1/#2`）。
- 敗部：L1 爭 `#3季軍/#4殿軍`（W2 掉落 2 人互打）
  → L2 爭 `#5/#6`（W1 敗者交叉準決賽 `W1L[0]vsW1L[3]、W1L[1]vsW1L[2]` 再決賽）
  → L3 爭 `#7/#8`（準決賽敗者互打）。
- 三顆執行按鍵同步：頂部主按鍵＋勝部樹內按鍵＋敗部樹內按鍵，同文案、同狀態、同動作。

## 檔案結構

```
Game_Proj/
├── README.md            # 本文件
├── game.html            # HTML 版（單檔，免安裝）
├── game_screenshot.png  # game.html 完賽截圖
├── tournament_gui.py    # Python Tkinter 版
├── tournament_logic.py  # 共用核心邏輯
├── test_logic.py        # 回歸測試
└── PLAN.md              # 企劃書（規則＋狀態機＋分支圖）
```

## 執行方式

### 1. HTML 版（瀏覽器，免安裝）

直接用瀏覽器開啟：

```bash
open game.html        # macOS
# 或
python3 -m http.server 8000
# 瀏覽器開啟 http://localhost:8000/game.html
```

操作：`開始隨機分組` / `載入範例種子` → 依序點擊執行按鍵
（頂部、勝部樹、敗部樹三處按鍵同步）→ 跑完 W1 → W2 → 總決賽 → L1 → L2 → L3。

### 2. Python 版（桌面 GUI，僅需內建 tkinter）

```bash
python3 tournament_gui.py
```

操作同 HTML 版。視窗含捲軸，勝部／敗部 Canvas 樹狀圖不會被遮蔽。
需要 Python 3.8+（macOS / Windows 內建 tkinter 即可，不需 pip）。

### 3. 回歸測試

```bash
python3 test_logic.py
```

預期輸出：

```
PASS example: [1, 4, 2, 6, 3, 5, 7, 8]
PASS random 100 seeds
```

## 賽程順序（v1.2：總決賽提前）

```
Step0 分組 → Step1 W1 → Step2 W2 → Step3 WF(#1/#2先出)
  → Step4 L1(#3/#4) → Step5 L2(#5/#6) → Step6 L3(#7/#8完賽)
```

## 詳細設計

見 [PLAN.md](PLAN.md)。
