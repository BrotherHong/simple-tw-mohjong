# 台灣麻將功能規格 v2

本文件為受測程式的功能契約，使用 Python 3.10.x。這是明確裁定的**簡化台灣十六張麻將**，不主張涵蓋各地完整玩法。需求編號為穩定識別碼。

> 第 1–8 節保留 v1 契約供舊紀錄相容。新牌局使用第 9–13 節的 v2 擴充；有衝突時 v2 條文優先。v1 紀錄仍嚴格採舊規則且不計分。

## 1. 範圍與共同契約

- **RULE-001**：四人單局。座次為整數 0、1、2、3（分別表示東南西北），行動順序為 `(player + 1) % 4`。莊家由初始化參數指定，預設 0；座次不隨莊家改變。
- **RULE-002**：使用 144 張牌：萬、筒、索各 1–9，每種四張；東南西北中發白每種四張；花牌 F1–F8 各一張。花牌不能組成面子或將眼。
- **RULE-003**：僅支援順子、刻子、將眼的一般五面子一將眼胡牌。無最低台數；沒有槓、搶槓、過水、特殊花牌胡、計台、結算、連莊及圈風。未支援的動作不構成合法動作。
- **API-001**：公開資料使用 frozen dataclass、tuple 及 Enum。核心函式不改變輸入，不使用系統時間或全域亂數；不向終端輸出。`random.Random` 僅能由呼叫端提供，使用時會推進該物件的亂數狀態。
- **API-002**：公開函式對非法輸入拋出 `MahjongError`（`ValueError` 子類），具有穩定字串 `code`。錯誤訊息可補充細節，非契約比較對象。布林值不視為整數。
- **API-003**：核心錯誤碼為 `INVALID_TILE`、`INVALID_HAND`、`INVALID_MELD`、`INVALID_WALL`、`INVALID_PLAYER`、`INVALID_STATE`、`INVALID_ACTION`、`INVALID_POLICY`、`INVALID_RECORD`。由外層傳入的錯誤資料先依該介面的型別與結構檢查；同時違反多項規則時不保證錯誤優先順序。
- **API-004**：專案 metadata 要求 `>=3.10,<3.11`，`.python-version` 為 `3.10`。執行期不依賴第三方套件。核心 API 皆從 `tw_mahjong` 匯出。

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
- **REPLAY-002**：actions 須為 Action tuple，其他容器為 `INVALID_ACTION`。policies 須為四個 callable 的 tuple；容器、數量或成員不符為 `INVALID_POLICY`。`SimplePolicy` 的 rng 型別不符同樣為 `INVALID_POLICY`。
- **RECORD-001**：`record_to_json(result)` / `record_from_json(text)` 提供 UTF-8 相容 JSON 字串往返。根物件為 `version: 1`、`initial_state`、`actions`、`final_state`；狀態序列化完整公開欄位，牌以 id、Enum 以其字串值表示，tuple 以 JSON array 表示。欄位必須精確符合格式，不接受缺漏、多餘欄位、重複 JSON key、非整數牌 id 或座次。讀取時驗證初末狀態並重播操作，末態必須一致，否則 `INVALID_RECORD`。檔案不含 seed、執行時間或策略，亦不依賴本機路徑。
- **CLI-001**：`python -m tw_mahjong simulate --seed N [--dealer 0..3] [--output PATH]` 使用獨立亂數來源洗牌與建立四個策略，列印 JSON 結果摘要；指定 output 時存重播 JSON（既有檔案拒絕覆寫）。`python -m tw_mahjong replay PATH` 讀取驗證並輸出摘要。可預期使用錯誤以非零 exit code 回報至 stderr。

### JSON v1 欄位格式

JSON object 僅接受下列欄位；所有欄位皆必填，選用資訊以 null 表示。物件 key 順序及空白不影響意義，array 順序有意義。寫出使用雙空白縮排與 key 排序，函式回傳字串不加尾端換行。

| 物件 | 欄位與型別 |
|---|---|
| 根物件 | `version`: integer 1；`initial_state`、`final_state`: State；`actions`: Action array |
| State | `wall`: TileId array；`players`: 四個 Player；`discards`: 四個 TileId array；`dealer`、`turn`: Seat；`phase`: Phase 字串；`pending`: Pending 或 null；`responses`: Action array；`last_drawn`、`winning_tile`: TileId 或 null；`winner`、`win_source`: Seat 或 null；`end_reason`: EndReason 字串或 null |
| Player | `hand`: TileId array；`melds`: Meld array；`flowers`: TileId array |
| Meld | `kind`: `CHI` 或 `PENG`；`tiles`: 三個 TileId；`source`: Seat；`claimed_tile`: TileId |
| Pending | `player`: Seat；`tile`: TileId |
| Action | `kind`: ActionKind 字串；`player`: Seat；`tiles`: TileId array |

TileId 為 0–143 的 integer；Seat 為 0–3 的 integer，不接受 boolean 或浮點數。Phase、EndReason、ActionKind 字串使用本文定義的大寫名稱。格式合法仍須通過狀態驗證及重播核對；空操作與合法未結束前綴均可序列化。

CLI 使用 `Random(seed)` 洗牌，座次 p 的策略使用 `Random(seed * 4 + p + 1)`。摘要欄位固定為 `phase`、`end_reason`、`winner`、`win_source`、`winning_tile`、`actions`（操作數）、`remaining_tiles`。成功 exit code 0；資料或檔案錯誤為 1（檔案錯誤碼 `IO_ERROR`），參數格式錯誤由 argparse 回報 exit code 2。

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

## 9. 第二階段資料與槓規則

- **V2-001**：GameState 新增 `rules_version`（整數 1 或 2，預設 2）、`round_wind`（kind 27–30，預設 27）、`draw_source`（DrawSource 或 None）、`pending_kong`（PendingKong 或 None）、`robbed_tile`（Tile 或 None）、`last_discard_last`（bool，預設 False）。`create_game` 新增同名 rules_version、round_wind 參數；v1 僅允許預設東風。v2 的座次 0–3 為穩定玩家 id，門風為 `(player-dealer)%4 + 27`，不再固定 id 0 為東風。
- **V2-002**：DrawSource 為 INITIAL、NORMAL、FLOWER、KONG。只在 last_drawn 存在時保留；初始化補花後為 FLOWER，未補花為 INITIAL；一般摸牌遇花為 FLOWER，槓後補牌即使遇花仍為 KONG。v1 不保存來源。`last_discard_last` 僅在 RESPONSE 或 DISCARD_WIN 結束時可為 True，表示該棄牌緊接著摸到最後一張一般牌（吃碰後出牌不算）。
- **KONG-001**：MeldKind 增加 KONG_EXPOSED、KONG_CONCEALED、KONG_ADDED，皆含同種四張實體牌，結構仍算一組面子。暗槓 source、claimed_tile 必須 None；其餘維持外來來源，added 保留原碰牌 source、claimed_tile。
- **KONG-002**：ActionKind 增加同名三種操作，tiles 分別為自己持有的三張、四張、一張 id。明槓可回應棄牌；暗槓與加槓限 DISCARD 且 last_drawn 非空。補牌可再槓。排序優先序為 HU、KONG_EXPOSED/PENG（同級時依 kind 字串）、CHI、KONG_CONCEALED、KONG_ADDED、DRAW、DISCARD、PASS，再以 tiles 排序；裁決同級仍以距離為準。
- **KONG-003**：加槓建立 `PendingKong(player, tile, meld_index)`，進入 ROB_KONG，原碰與暗手皆不先變動，發出 KONG_DECLARED。其他三人各 HU/PASS 一次。可搶胡僅加槓，三人回應收齊才裁決；多胡取最近者。ROB_KONG 等效手牌數為發起者 17、其他人 16；last_drawn 與 draw_source 保留。
- **KONG-004**：搶槓成功為 EndReason.ROB_KONG，原碰不變，被搶牌從來源暗手移至 robbed_tile 專屬持有區；winning_tile 指向它，不加入贏家暗手或河牌；四人等效手牌皆 16，清除 pending_kong、last_drawn、draw_source。robbed_tile 僅該結束原因存在。
- **KONG-005**：明槓、暗槓或加槓成立後發出 KONG_COMPLETED，從後端補牌，花牌公開後繼續從後端補，取得一般牌後回 DISCARD。空牆則 WALL_EXHAUSTED，保留已成立的槓。槓成立／補花／補牌事件依實際順序回傳。無額外死牆、四槓流局或槓牌付款。
- **KONG-006**：validate_state 同時驗證新增背景與所有權；搶槓牌加入 144 張守恆計算。v1 不允許新副露、新操作、新 phase 或背景。非法新操作沿用 INVALID_ACTION，非法背景為 INVALID_STATE。
- **WAIT-001**：`find_waits(hand, melds=()) -> tuple[int, ...]` 接受 `16-3*m` 張暗手，其他輸入驗證與 analyze_hand 相同。枚舉自己暗手與副露尚未持滿四張的一般牌種，回傳可成胡 kind 升冪 tuple，不受輸入排列影響，不考慮他家持牌或河牌，不推估剩餘張數。
- **SIM-004**：v2 SimplePolicy 依 HU、KONG_EXPOSED、KONG_CONCEALED、KONG_ADDED、PENG、CHI、DRAW 優先取第一項，其餘隨機出牌或 PASS。v1 策略順序維持原樣。

## 10. 逐步重播與終端機

- **PLAY-001**：`iter_replay(initial_state, actions)` 回傳 iterator，先驗證輸入狀態及 actions tuple，再依序 yield `ReplayFrame(index, state, action, events)`。index 0 為原初態，action=None、events=()；其後每個合法操作一個 frame。非法步驟於走到該步時拋原錯誤，不先修改輸入。replay 完整消耗此 iterator 回傳末態。
- **PLAY-002**：`watch PATH [--speed 2] [--step] [--plain]` 先完整驗證紀錄，再從發牌完成的初態播放。speed 為每秒操作數，必須有限且 0.25–64；非法值為 CLI 參數錯誤。每幀顯示四家手牌、副露、花、河牌、階段、目前玩家、剩餘牌數、操作及最近事件。使用明確牌代碼（1m、E 等）避免終端機字寬差異。
- **PLAY-003**：互動時空白暫停／繼續，n/Enter 單步並暫停，+/- 將速度加倍／減半（夾在範圍內），q 正常提早離開。--step 初始暫停；最後一幀顯示結果並返回，不另外等待按鍵。Ctrl+C exit 130。離開與例外均須還原輸入模式及游標顯示。
- **PLAY-004**：stdin 或 stdout 非 TTY，或 --plain 時，逐幀列印無 ANSI、無延遲、無鍵盤等待的文字；--step 必須互動且不搭配 --plain，否則參數錯誤。呈現層可使用時間與 I/O，規則／模擬／重播函式不可等待。

## 11. 固定計台

- **SCORE-001**：`score_hand(state) -> ScoreResult(tai, items, decomposition, winning_group)` 僅接受 v2 ENDED 狀態；v1 或未結束為 INVALID_SCORE。流局回傳 0、空 items、None、None。ScoreItem 為 `(code, tai)`，按 code 排序；winning_group 為暗手拆解中胡牌所落的三張 kind tuple，落在將眼時為 None。
- **SCORE-002**：對所有胡牌拆解及可能胡牌落點計台，取最高 tai，同分依 `(pair, groups, winning_group)` 字典序（None 在所有 group 前）選擇。放槍／搶槓完成的刻子不算暗刻，暗槓算暗刻。門清表示所有既有面子皆暗槓或無既有面子。不同實體副本不產生額外計台候選。

| code | 條件與台數 |
|---|---|
| CONCEALED / SELF_DRAW / CONCEALED_SELF_DRAW | 門清 1／自摸 1／兩者同時 3，第三者取代前兩者 |
| DRAGON_R / DRAGON_G / DRAGON_B | 對應三元刻或槓各 1；有大小三元時全部不另計 |
| SEAT_WIND / ROUND_WIND | 對應風牌刻或槓各 1，可累計（包括大小四喜） |
| SEAT_FLOWER | 相對莊家門風對應的 F1–F4、F5–F8，每張 1，合併成一個 item |
| FLOWER_SET | 取得 F1–F4 或 F5–F8 全組，每組 1，可與門花累計，合併成一個 item |
| ALL_TRIPLETS | 五面子均刻或槓，4；字一色不另計 |
| MIXED_SUIT / PURE_SUIT / ALL_HONORS | 一種數牌加字 4／純一種數牌 8／全字 16，三者互斥 |
| SMALL_DRAGONS / BIG_DRAGONS | 兩組三元刻槓加另一三元將眼 4／三組三元刻槓 8 |
| SMALL_WINDS / BIG_WINDS | 三組風刻槓加另一風將眼 8／四組風刻槓 16 |
| THREE_CONCEALED / FOUR_CONCEALED / FIVE_CONCEALED | 三／四／五暗刻槓為 2／5／8，僅取最高一項 |
| SUPPLEMENT_WIN / ROB_KONG | 來源 FLOWER 或 KONG 的自摸 1／搶槓胡 1 |
| LAST_DRAW / LAST_DISCARD | 牌牆已空時自摸 1／last_discard_last 為 True 的放槍胡 1；搶槓不計此兩項 |
| SINGLE_WAIT | 胡牌前 find_waits 僅一個牌種，1；自摸移除 winning_tile 後計算，其他情形以贏家原暗手計算 |

- **SCORE-003**：不計平胡、全／半求人、早巡胡聽、宣告聽牌與特殊花牌胡。無台數上限、無最低台門檻，表外項目不計。

## 12. 單局結算

- **PAY-001**：`SettlementConfig(base=100, tai_value=20)` 是 frozen dataclass，base 為非負整數，tai_value 為正整數，拒絕 bool；非法為 INVALID_SETTLEMENT。`settle_hand(state, config=SettlementConfig()) -> Settlement(score, payments, deltas)` 內部重算 score，不接受外部未驗證台數。
- **PAY-002**：Payment 為 `(payer, payee, tai, amount)`，按 payer 排序。每筆 tai 為牌型 tai 加莊家一台（winner 或 payer 為 dealer 時）；amount=`base+tai_value*tai`。自摸三家分付，放槍／搶槓只有來源者付，流局無 payments。deltas 為四個整數 tuple，加總 0。無連莊、包牌、槓牌額外付款。

## 13. JSON v2 與相容

- **RECORD-002**：rules_version=1 的結果仍以原 JSON v1 精確欄位寫出、讀回強制使用舊規則，無計分資訊。新建牌局預設 v2；版本不可在一份紀錄途中改變。舊紀錄不得補猜背景或計分。
- **RECORD-003**：JSON v2 根欄位精確為 version（整數 2）、initial_state、actions、final_state、settlement_config、settlement。前後狀態皆 rules_version=2；State 除原 v1 欄位外新增第 V2-001 條六欄。DrawSource 以大寫字串表示，pending_kong 為 `{player,tile,meld_index}`（tile 為 id），robbed_tile 為 id 或 null。Meld 暗槓 source/claimed_tile 為 null。
- **RECORD-004**：settlement_config 為 `{base,tai_value}`。若末態未結束，settlement 必須 null；已結束時為 `{score,payments,deltas}`。score 為 `{tai,items,decomposition,winning_group}`；items 為 `{code,tai}` array；decomposition 為 `{pair,groups}` 或 null；winning_group 為三個 kind array 或 null。payments 為 `{payer,payee,tai,amount}` array，deltas 為四個 integer。讀入須重播與重算，嚴格比較包含型別的標準 JSON 資料，拒絕 boolean 冒充 integer 或任何不一致結果。
- **RECORD-005**：SimulationResult 新增 settlement_config（預設 SettlementConfig），不儲存冗餘計分物件；record_to_json 寫出時重算。simulate 新增 keyword-only settlement_config 參數。record_from_json 保留該設定。額外錯誤皆統一 INVALID_RECORD。v1 結果的設定須為預設值且不寫出。
- **CLI-002**：simulate 新增 --base、--tai-value、--round-wind（E/S/W/N），預設 100、20、E，建立 v2 牌局。原 simulate/replay 摘要欄位保持不變；watch 最終畫面額外顯示計台及付款明細，v1 顯示「計分資訊未包含」。

開發不新增測試程式；在 Python 3.10 直接執行牌型、槓與搶槓、補花耗盡、計台互斥、分數守恆與新舊重播情境核對。
