# 台灣麻將功能規格 v1

本文件為受測程式的功能契約，使用 Python 3.10.x。這是明確裁定的**簡化台灣十六張麻將**，不主張涵蓋各地完整玩法。需求編號為穩定識別碼。

## 1. 範圍與共同契約

- **RULE-001**：四人單局。座次為整數 0、1、2、3（分別表示東南西北），行動順序為 `(player + 1) % 4`。莊家由初始化參數指定，預設 0；座次不隨莊家改變。
- **RULE-002**：使用 144 張牌：萬、筒、索各 1–9，每種四張；東南西北中發白每種四張；花牌 F1–F8 各一張。花牌不能組成面子或將眼。
- **RULE-003**：僅支援順子、刻子、將眼的一般五面子一將眼胡牌。無最低台數；沒有槓、搶槓、過水、特殊花牌胡、計台、結算、連莊及圈風。未支援的動作不構成合法動作。
- **API-001**：公開資料使用 frozen dataclass、tuple 及 Enum。核心函式不改變輸入，不使用系統時間或全域亂數；不向終端輸出。`random.Random` 僅能由呼叫端提供，使用時會推進該物件的亂數狀態。
- **API-002**：公開函式對非法輸入拋出 `MahjongError`（`ValueError` 子類），具有穩定字串 `code`。錯誤訊息可補充細節，非契約比較對象。布林值不視為整數。
- **API-003**：核心錯誤碼為 `INVALID_TILE`、`INVALID_HAND`、`INVALID_MELD`、`INVALID_WALL`、`INVALID_PLAYER`、`INVALID_STATE`、`INVALID_ACTION`、`INVALID_POLICY`、`INVALID_RECORD`。由外層傳入的錯誤資料先依該介面的型別與結構檢查；同時違反多項規則時不保證錯誤優先順序。

## 2. 牌與副露模型

- **TILE-001**：`Tile(id)` 的 id 限 0–143。0–135 的 `kind = id // 4`；136–143 的 kind 為 34–41。實體牌以 id 區別，同種牌可有不同 id。
- **TILE-002**：一般牌 kind 依序為萬 0–8、筒 9–17、索 18–26、東南西北中發白 27–33。`Tile.code` 為 `1m`–`9m`、`1p`–`9p`、`1s`–`9s`、`E S W N R G B`、`F1`–`F8`。`tile_kind(code)` 做大小寫敏感、完整字串匹配，回傳 kind；非法代碼為 `INVALID_TILE`。
- **TILE-003**：`full_deck()` 依 id 升冪回傳完整 tuple。持牌與輸出牌組以實體 id 升冪排序。相同 id 在同一份手牌分析或整個牌局中只能出現一次。
- **MELD-001**：`Meld(kind, tiles, source, claimed_tile)` 包含三張相異的一般實體牌。kind 為 `CHI` 或 `PENG`；CHI 必須同花色連續三數，PENG 必須同種三張。source 為 0–3，claimed_tile 必須是三張之一的 id；副露 tiles 必須以 id 排序。
- **MELD-002**：牌局副露 source 不能是擁有者自己；CHI 的擁有者必須為 source 的下家。副露最多五組；分析函式不推定擁有者，只驗證副露本身。

## 3. 牌牆與初始化

- **WALL-001**：`Wall(tiles)` 接受不重複、按指定順序排列的 Tile tuple（可為空或完整牌組的子集）。`draw_front()` / `draw_back()` 回傳 `(tile, new_wall)`；空牌牆為 `INVALID_WALL`，原牌牆不變。
- **INIT-001**：`create_game(*, dealer=0, tile_order=None, rng=None)` 回傳 `GameState`。tile_order 為完整 144 個 Tile、無重複的 tuple；指定後不再洗牌。未指定時須提供 `random.Random`，對完整牌組執行一次 shuffle。兩者同時提供或兩者皆未提供為 `INVALID_WALL`。
- **INIT-002**：按莊家起的行動順序，一次一張、共十六輪，發給各人 16 張一般牌，最後再給莊家一張。每個發牌位置先取前端，遇花立即公開並從後端補，補到花繼續補，直到取得一般牌，再發下一個位置。
- **INIT-003**：完成後莊家一般手牌 17 張，其他人各 16 張；副露、河牌、回應為空。phase 為 `DISCARD`、turn 為莊家，last_drawn 為莊家最後取得的一般牌 id，因此可立即自摸。
- **INIT-004**：發牌或補花無牌可取時立刻以 `WALL_EXHAUSTED` 結束，保留已取得的牌與花，允許未發齊；實際完整牌組通常不會在發牌時耗盡。

## 4. 胡牌判定

- **HAND-001**：`analyze_hand(hand, melds=()) -> HandAnalysis` 接受一般實體牌 tuple 與副露 tuple。所有牌含副露不得重複；副露至多五組。一般牌不可能超過每種四張；花牌、非法型別或錯誤長度為 `INVALID_HAND`（副露格式錯誤為 `INVALID_MELD`）。
- **HAND-002**：若有 m 組副露，暗手長度必須為 `17 - 3*m`。其他張數是非法輸入，而非合法但未成胡。分析胡別人牌時，呼叫端將待胡牌加進暗手。
- **HAND-003**：`HandAnalysis.winning` 表示是否至少有一種完整拆解；`decompositions` 是全部拆解的 tuple。合法但無法拆解時回傳 False 與空 tuple。
- **HAND-004**：`Decomposition(pair, groups)` 以 kind 表示將眼及暗手面子。pair 是 kind；每組為三個 kind 的 tuple，順子同花色連續，刻子同種，字牌不能當順子。groups 依字典序排序；所有拆解去重，依 `(pair, groups)` 排序。既有副露不重複列入 groups。
- **HAND-005**：分析結果不受手牌及副露輸入排列影響；不因實體副本互換產生額外拆解。回溯需探索刻子與順子等所有可能分支。

## 5. 狀態與合法操作

- **STATE-001**：`GameState` 包含 wall、四份 `PlayerState(hand, melds, flowers)`、四份河牌 discards、dealer、turn、phase、pending、responses、last_drawn、winner、win_source、winning_tile、end_reason。phase 為 `DRAW`、`DISCARD`、`RESPONSE`、`ENDED`。`PendingDiscard(player, tile)` 指向仍在該玩家河牌最後一張的牌，不是額外所有權區域。
- **STATE-002**：`validate_state(state)` 驗證完整 144 張實體牌恰好各存在一次於牌牆、暗手、副露、花區或河牌。暗手、花區、河牌與副露皆為 tuple；暗手與花區按 id 排序，河牌保留出牌順序，副露保留成立順序。花區只含花牌，其他持牌區不得含花牌。
- **STATE-003**：一般情況每家 `len(hand) + 3*len(melds) = 16`；DISCARD 階段 turn 玩家為 17。自摸結束同樣保留贏家 17，放槍結束所有人為 16（胡牌仍留河牌）。耗盡結束允許初始化未發齊的 0–16 張等效手牌。pending 僅 RESPONSE 存在；responses 依 player 升冪保存，不能重複。last_drawn 僅自摸可能的 DISCARD 或 SELF_DRAW 結束存在，且屬於 turn 暗手。
- **ACTION-001**：`Action(kind, player, tiles=())` 的 kind 為 `DRAW`、`DISCARD`、`CHI`、`PENG`、`HU`、`PASS`。tiles 是 id 升冪 tuple。DISCARD 含一個自己的暗手 id；CHI/PENG 含從自己暗手拿出的兩個 id（不含河牌）；其餘為空。
- **ACTION-002**：`legal_actions(state, player)` 先驗證狀態與座次，回傳合法 Action tuple，不改變輸入。無權操作、已回應或結束時回傳空 tuple。排序依 HU、PENG、CHI、DRAW、DISCARD、PASS，再以 tiles 字典序排列；同種牌不同實體選擇全部列出。
- **ACTION-003**：DRAW 階段僅 turn 可 DRAW。DISCARD 階段僅 turn 可出暗手任一張；僅 last_drawn 非空且手牌成胡時可 HU。吃碰後不可在出牌前自摸。
- **ACTION-004**：RESPONSE 階段，除出牌者外的三人各須回應一次，即使僅能 PASS。成胡可 HU、持兩張同種可 PENG、下家持相應兩張可 CHI；所有回應者皆可 PASS。沒有過水限制。
- **ACTION-005**：`apply_action(state, action) -> Transition(state, events)` 只接受列於合法操作中的 Action，否則 `INVALID_ACTION`。所有輸入維持不變，傳回新狀態。非法型別、非標準欄位、錯誤座次或 tiles 不合法同樣拒絕。

## 6. 轉移、裁決與結束

- **TURN-001**：DRAW 先取前端，花牌移花區再由後端補；每取得一張都產生事件。取得一般牌後為 DISCARD 並設定 last_drawn。無牌可取立即 ENDED / WALL_EXHAUSTED。
- **TURN-002**：DISCARD 將該實體牌移至河牌尾，建立 pending，清除 last_drawn，進入 RESPONSE。turn 暫留出牌者。
- **TURN-003**：回應只登記意向，不提前移牌。收齊三人回應才裁決。胡 > 碰 > 吃；同類依出牌者之後的行動距離取最近者。不因回應提交順序改變裁決結果。
- **TURN-004**：全 PASS 時清除 pending 與 responses，下家進入 DRAW。吃碰成功則從出牌者河牌取走該牌，與回應者兩張暗手成立副露；回應者進入 DISCARD，清除 pending、responses、last_drawn。
- **TURN-005**：自摸為 ENDED / SELF_DRAW，winner 與 win_source 皆為自己，winning_tile 為 last_drawn。放槍為 ENDED / DISCARD_WIN，winner 為得胡者，win_source 為出牌者，winning_tile 指向河牌胡牌；此牌不複製至贏家暗手。耗盡時三項贏牌資訊皆為 None。任何結束後不能再操作。
- **EVENT-001**：`Event(kind, player=None, tile=None, action=None)` 是不可變結果事件。kind 為 `DRAWN`、`FLOWER`、`DISCARDED`、`RESPONSE`、`CLAIMED`、`TURN`、`WON`、`EXHAUSTED`。取牌依實際順序輸出 DRAWN（一般牌）或 FLOWER（花牌）；出牌為 DISCARDED；每次回應為 RESPONSE；最終回應後再附 CLAIMED / TURN / WON。DRAWN、FLOWER、DISCARDED、CLAIMED、WON 記錄 tile id，相關操作附 action；TURN 記錄下一位玩家，EXHAUSTED 無玩家。初始化不回傳事件，其結果已完整存在初態。

## 7. 模擬與重播

- **SIM-001**：`simulate(initial_state, policies)` 接受四個 callable（`policy(state, player) -> Action`），回傳 `SimulationResult(initial_state, final_state, actions)`。每步選第一個具有合法操作的座次，因此回應預設按座次提交；輸入已結束時不呼叫策略且 actions 為空。非法策略輸出為 `INVALID_POLICY`。策略自身拋出的例外原樣傳遞。
- **SIM-002**：`SimplePolicy(rng)` 需注入 `random.Random`。能 HU 則 HU、能 PENG 則選第一個、能 CHI 則選第一個，否則 DRAW、隨機 DISCARD、PASS。每次隨機出牌只對合法 DISCARD 清單呼叫一次 choice。策略可看完整狀態，非網路遊戲的資訊隔離 API。
- **SIM-003**：模擬自然終止：每次一般摸牌消耗牌牆，吃碰消耗河牌與可副露暗手，回應每人每輪僅一次；不設任意步數截斷或時間依賴。
- **REPLAY-001**：`replay(initial_state, actions)` 依序呼叫 apply_action，回傳最終 GameState；非法步驟照原錯誤碼拒絕。允許空紀錄與合法前綴，不要求一定結束。
- **RECORD-001**：`record_to_json(result)` / `record_from_json(text)` 提供 UTF-8 相容 JSON 字串往返。根物件為 `version: 1`、`initial_state`、`actions`、`final_state`；狀態序列化完整公開欄位，牌以 id、Enum 以其字串值表示，tuple 以 JSON array 表示。欄位必須精確符合格式，不接受缺漏、多餘欄位、重複 JSON key、非整數牌 id 或座次。讀取時驗證初末狀態並重播操作，末態必須一致，否則 `INVALID_RECORD`。檔案不含 seed、執行時間或策略，亦不依賴本機路徑。
- **CLI-001**：`python -m tw_mahjong simulate --seed N [--dealer 0..3] [--output PATH]` 使用獨立亂數來源洗牌與建立四個策略，列印 JSON 結果摘要；指定 output 時存重播 JSON（既有檔案拒絕覆寫）。`python -m tw_mahjong replay PATH` 讀取驗證並輸出摘要。可預期使用錯誤以非零 exit code 回報至 stderr。

## 8. 實作對照

| 需求 | 實作元件 |
|---|---|
| RULE、API、TILE、MELD | `model`、公開套件介面 |
| WALL、INIT | `wall`、`engine.create_game` |
| HAND | `hand` |
| STATE、ACTION、TURN、EVENT | `engine` |
| SIM、REPLAY | `simulation` |
| RECORD、CLI | `records`、命令列入口 |

開發不新增測試程式；交付前以程式審查、Python 3.10 編譯檢查與直接執行代表性情境核對上述要求。
