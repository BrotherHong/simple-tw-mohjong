# 簡易台灣麻將模擬器

使用 **Python 3.10.x** 模擬四人台灣十六張麻將，提供電腦對局、紀錄重播與可調速的終端機觀戰。

支援摸打、吃碰、明槓／暗槓／加槓、搶槓、補花、聽牌分析及固定牌型計分。採單局簡化規則，也可作為測試撰寫工具的實驗專案；詳細功能與限制見 [SPEC.md](SPEC.md)。

## 使用教學

以下指令請在專案根目錄執行。若已有 `.venv`，可直接啟用；首次建立環境則需先安裝 Python 3.10.x。

### 1. 建立與啟用虛擬環境

**Windows PowerShell**

已有虛擬環境時：

```powershell
# Activate the existing environment.
.\.venv\Scripts\Activate.ps1
```

首次建立時：

```powershell
# Create and activate a Python 3.10 environment.
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

`py -3.10` 需要已安裝並登錄 Python 3.10，可用 `py -0p` 檢查。若未列出，請先安裝 Python 3.10，或改用該版本 `python.exe` 的完整路徑執行 `-m venv .venv`。

啟用後安裝專案並建立輸出目錄：

```powershell
# Install the project and prepare the output directory.
python -m pip install -e .
New-Item -ItemType Directory -Force output | Out-Null
```

**macOS／Linux**

已有虛擬環境時：

```bash
# Activate the existing environment.
source .venv/bin/activate
```

首次建立時：

```bash
# Create and activate a Python 3.10 environment.
python3.10 -m venv .venv
source .venv/bin/activate
```

啟用後安裝專案並建立輸出目錄：

```bash
# Install the project and prepare the output directory.
python -m pip install -e .
mkdir -p output
```

啟用後可用 `python --version` 確認版本為 3.10。若缺少啟用腳本或無法啟用，可直接使用 Windows 的 `.\.venv\Scripts\python.exe`，或 macOS／Linux 的 `.venv/bin/python` 取代後續的 `python`，不必先啟用。例如已有 `output/game.json` 時：

```powershell
# Watch a saved game without activating the environment.
.\.venv\Scripts\python.exe -m tw_mahjong watch output/game.json --speed 2
```

### 2. 產生對局

```bash
# Simulate a game and save its replay record.
python -m tw_mahjong simulate --seed 17 --dealer 2 --output output/game.json
```

預設使用基本牌效率策略；加上 `--policy simple` 可改用原本的隨機出牌策略。同一策略與參數可重現相同結果。紀錄不會覆寫既有檔案，重新產生時請換檔名。

### 3. 觀看對局

```bash
# Watch the saved game at two visible steps per second.
python -m tw_mahjong watch output/game.json --speed 2
```

播放器從發牌完成開始，顯示四家手牌、副露、花牌與河牌，結束後列出計台及分數增減。預設略過純 PASS，仍保留其觸發的吃碰槓胡結果。

| 按鍵 | 功能 |
|---|---|
| 空白 | 暫停／繼續 |
| n 或 Enter | 單步並暫停 |
| +／- | 加速／減速 |
| q | 離開 |

| 選項 | 用途 |
|---|---|
| `--speed N` | 每秒可見步驟數，範圍 0.25–64 |
| `--step` | 從暫停開始，方便逐步觀看 |
| `--detail` | 顯示全部操作，包含 PASS |
| `--ascii --no-color` | 使用英文牌代碼並關閉顏色 |
| `--plain` | 輸出純文字，保留完整河牌 |

建議使用至少 120 欄的終端機，顯示兩欄四家盤面；較窄時改為直列。互動畫面河牌顯示最近 12 張，`*` 標記剛摸入或打出的牌。Windows 已實際驗證，macOS／Linux 尚未實機驗證。

```bash
# Export the complete action log without terminal controls.
python -m tw_mahjong watch output/game.json --plain --detail > output/transcript.txt
```

`--step` 需要互動終端機，不能搭配 `--plain` 或輸出重新導向。

### 4. 查看摘要與離開環境

```bash
# Validate the record and print the final summary.
python -m tw_mahjong replay output/game.json

# Leave the virtual environment when finished.
deactivate
```

## 開發注意事項

- 固定使用 Python 3.10；執行期只有標準函式庫，使用 `pip install -e .` 方便開發。
- 功能與介面以 [SPEC.md](SPEC.md) 為準，行為變更應同步更新規格。
- 核心資料保持不可變，亂數由呼叫端注入；呈現層的速度與按鍵不可影響牌局結果。
- 保留 JSON v1／v2 相容性；重播使用已保存的操作，不重新呼叫電腦策略。
- 專案供外部工具產生測試，不附測試程式。修改後可編譯檢查，並直接模擬或重播核對。
- 主線為 `main`，依完整工作階段提交；虛擬環境、快取、建置及 `output/` 產物不納入 Git。

| 模組 | 用途 |
|---|---|
| `model`、`wall`、`hand` | 牌與狀態資料、牌牆、胡牌及聽牌分析 |
| `engine` | 合法操作、回應裁決與狀態轉移 |
| `scoring`、`records` | 計台結算、紀錄保存與驗證 |
| `simulation`、`policies` | 模擬、重播與電腦策略 |
| `playback`、`board`、`__main__` | 終端機操作、盤面與 CLI |

```bash
# Check syntax and accidental whitespace changes.
python -m compileall -q src
git diff --check
```
