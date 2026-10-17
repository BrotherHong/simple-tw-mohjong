# 台灣麻將受測專案

Python **3.10.x** 的簡化台灣十六張麻將規則核心，提供其他測試撰寫工具作為受測程式。完整功能契約見 [SPEC.md](SPEC.md)。專案不包含測試程式、故意缺陷或評分工具。

## 環境與安裝

先安裝 Python 3.10.x，並確認 Windows Python Launcher 能以 `py -3.10` 找到該版本。

```powershell
py -3.10 -m venv .venv
.venv\Scripts\python -m pip install -e .
```

執行期只使用 Python 標準函式庫。開發主線為 `main`，各元件與對應規格一起提交。

## 開發範圍

牌模型與牌牆、胡牌與聽牌分析、合法操作、牌局狀態機、四人模擬、JSON 重播及終端機觀戰。支援摸打、吃碰、明槓／暗槓／加槓、搶槓、補花、固定牌型計台及單局結算。

不包含真人出牌、多局連莊、完整一將、特殊花牌胡、過水、網路連線及圖形介面；計台僅採用 spec 中明列的固定子集。

## 執行模擬與重播

安裝後，不需啟用虛擬環境即可執行：

```powershell
.venv\Scripts\python -m tw_mahjong simulate --seed 17
.venv\Scripts\python -m tw_mahjong simulate --seed 17 --dealer 2 --output game.json
.venv\Scripts\python -m tw_mahjong replay game.json
.venv\Scripts\python -m tw_mahjong watch game.json --speed 2
.venv\Scripts\python -m tw_mahjong watch game.json --step
```

也可使用 `.venv\Scripts\tw-mahjong.exe`。摘要為 JSON，包含結束原因、贏家、胡牌來源玩家、胡牌實體 id、操作數及剩餘牌數；自摸時來源玩家為自己，流局時為 null。`--output` 拒絕覆寫既有檔案。模擬生成的檔案請放在已忽略的 `output/`，或自行指定其他位置，父目錄須已存在。

程式接受相同 seed 與莊家時，使用相同洗牌及策略亂數來源。紀錄包含完整初態、操作序列與末態；重播不依賴 seed。載入紀錄時會逐步重播，拒絕與操作不符的末態。

新牌局產生 JSON v2，保存圈風、摸牌背景、結算設定與重算後的付款資訊。舊 JSON v1 使用原規則重播、禁止槓且不補算計台；播放器會明示未包含計分資訊。`replay` 仍只輸出原有摘要。

結算使用抽象分數，預設底分 100、每台 20；圈風預設東風，可自行設定：

```powershell
.venv\Scripts\python -m tw_mahjong simulate --seed 17 --base 50 --tai-value 10 --round-wind S
```

### 播放控制

播放器從發牌完成的四家起手狀態開始，顯示全部手牌、副露、花、河牌、階段與近期事件；適合使用較寬且較高的終端機視窗。數牌使用 m／p／s，字牌使用 E／S／W／N／R／G／B，花牌使用 F1–F8。

| 操作 | 功能 |
|---|---|
| 空白 | 暫停／繼續 |
| n 或 Enter | 前進一個操作並暫停 |
| +／- | 速度加倍／減半 |
| q | 提前離開 |
| Ctrl+C | 中斷，exit code 130 |

`--speed` 是每秒操作數，預設 2，範圍 0.25–64；`--step` 初始暫停。播完顯示計台、付款及四家分數增減後返回終端機，保留結果畫面。補花等同一操作的多個事件會一起顯示。離開時還原游標及終端機模式。

非互動輸入／輸出會自動改用無延遲、無 ANSI 的逐步文字紀錄，也可明確指定：

```powershell
.venv\Scripts\python -m tw_mahjong watch game.json --plain > transcript.txt
```

`--step` 不能搭配 `--plain` 或輸出重新導向。播放速度不改變牌局結果，也不寫入紀錄。

## Python 介面

```python
from random import Random
from tw_mahjong import (
    SimplePolicy, create_game, simulate, replay,
    record_to_json, record_from_json, score_hand, settle_hand,
)

initial = create_game(rng=Random(17))
policies = tuple(SimplePolicy(Random(100 + player)) for player in range(4))
result = simulate(initial, policies)
print(result.final_state.end_reason.value)

text = record_to_json(result)
loaded = record_from_json(text)
final_state = replay(loaded.initial_state, loaded.actions)
print(final_state == result.final_state)
print(score_hand(final_state))
print(settle_hand(final_state, loaded.settlement_config))
```

分析手牌時必須傳入實體牌，而不是只有牌種：

```python
from tw_mahjong import Tile, analyze_hand

# 123萬、456萬、123筒、123索、東東東、中中。
hand = tuple(Tile(i) for i in (
    0, 4, 8, 12, 16, 20, 36, 40, 44, 72, 76, 80, 108, 109, 110, 124, 125,
))
analysis = analyze_hand(hand)
print(analysis.winning)  # True
print(analysis.decompositions)
```

有 m 組副露時，成胡分析的暗手必須有 `17 - 3*m` 張。長度錯誤、花牌或重複實體牌會拋出 `MahjongError`；合法但未成胡則回傳 `winning=False`。

槓即使有四張牌也只算一組面子。`find_waits(hand, melds)` 接受 `16 - 3*m` 張暗手，回傳可胡牌種的排序 tuple；不估算他家暗手或河牌的剩餘牌數。

```python
from tw_mahjong import find_waits
print(find_waits(hand[:-1]))  # (31,)：中
```

使用 `legal_actions(state, player)` 查詢，再以 `apply_action(state, action)` 取得 `Transition`（新狀態與事件）。資料為不可變物件，非法操作不會改變原狀態。`MahjongError.code` 是穩定錯誤碼，完整清單與優先序契約見 spec。

`RESPONSE` 階段須讓出牌者以外的三人各回應一次，包括只能過牌的玩家。前兩次僅登記意向，第三次才裁決。玩家座次採 `0 → 1 → 2 → 3 → 0`，莊家可以是任一座次。

加槓會進入 `ROB_KONG`，其他三人同樣各回應一次 HU 或 PASS，未裁決前原碰牌及加槓牌保留原位。搶槓成功才將牌移入 `robbed_tile`，不當作一般棄牌。暗槓不破門清；暗槓與加槓不能在吃碰後未摸牌時宣告。

`iter_replay(initial_state, actions)` 先產生 index 0 的初態，再為每個操作產生 `ReplayFrame`，包含新狀態及事件。此介面不讀取鍵盤、不等待、不輸出畫面，可供其他呈現方式使用。

`score_hand` 僅接受已結束的 v2 狀態，流局回傳零台。多種拆解及胡牌落點取最高台數，同分依 spec 排序。`settle_hand` 內部重算台數；自摸三家付款，放槍／搶槓只有來源者付款，每筆交易個別計算莊家加台，四家分數增減加總為零。

```python
from tw_mahjong import SettlementConfig
print(settle_hand(final_state, SettlementConfig(base=100, tai_value=20)))
```

自訂結算參數若要保存於紀錄，傳入 `simulate(..., settlement_config=config)`。底分須為非負整數，每台分數須為正整數。v1 狀態不接受計分；新建牌局預設 v2，需要原規則時可指定 `create_game(..., rules_version=1)`。

自訂策略為 `policy(state, player) -> Action`；`simulate` 接受四個策略的 tuple。策略可讀取完整狀態，因此適合規則實驗，未實作多人連線所需的資訊隔離。

## 元件與實作方式

| 元件 | 位置 | 說明 |
|---|---|---|
| 牌與公開資料 | [model.py](src/tw_mahjong/model.py) | 以實體 id 區分同種牌，使用不可變資料 |
| 牌牆 | [wall.py](src/tw_mahjong/wall.py) | 前端摸牌、後端補花，回傳新的牌牆 |
| 胡牌分析 | [hand.py](src/tw_mahjong/hand.py) | 枚舉將眼，對最小剩餘牌回溯拆解刻子與順子，快取子問題並去重排序 |
| 規則與流程 | [engine.py](src/tw_mahjong/engine.py) | 驗證牌張守恆、列舉合法動作、純函式狀態轉移與延後裁決 |
| 模擬與重播 | [simulation.py](src/tw_mahjong/simulation.py) | 注入策略與亂數，重播既有操作 |
| JSON 紀錄 | [records.py](src/tw_mahjong/records.py) | 嚴格格式檢查與重播核對 |
| 計台與結算 | [scoring.py](src/tw_mahjong/scoring.py) | 枚舉胡牌落點、選最高台、逐付款方結算 |
| 終端機播放器 | [playback.py](src/tw_mahjong/playback.py) | 呈現逐步快照、處理按鍵與顯示速度 |

## 開發與交付

Python 僅支援 **3.10.x**；`.python-version` 與套件 metadata 均有指定。執行期無第三方相依套件，建置時使用 setuptools。

```powershell
.venv\Scripts\python --version
.venv\Scripts\python -m compileall -q src
git status --short --branch
```

本專案不附測試程式，供外部工具根據 [SPEC.md](SPEC.md) 產生測試。開發時以規格核對、程式審查、編譯檢查及直接執行代表性牌型與牌局確認行為。

Git 提交順序為規格與環境、牌模型與牌牆、胡牌分析、初始化與狀態機、模擬與紀錄、最終文件與核對。虛擬環境、下載的直譯器、快取及建置產物不納入版本控制。

第二階段先提交規格，再提交逐步重播與播放器；槓、計台與 v2 紀錄因共用資料契約一併提交，最後補齊文件與核對。
