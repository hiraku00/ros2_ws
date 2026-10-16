# セッション引き継ぎ書

新しいセッションで、これまでの経緯を踏まえて、続きから始めるための文書です。
最初に **[0. 3分で把握する](#0-3-分で把握する)** だけ読めば、作業を再開できます。

最終更新: 2026-10-15 / 対象リポジトリ: [hiraku00/ros2_ws](https://github.com/hiraku00/ros2_ws)（private）

---

## 0. 3 分で把握する

| 項目 | 内容 |
|---|---|
| 何をしているか | ROS 2 (Jazzy) の学習。Mac（Apple Silicon）の Docker コンテナ内で動かす |
| 学習者 | ROS 2 初心者。説明は日本語で、中学生が分かるレベルを求めている |
| 済んだこと | ノード・トピック・パラメータの基本、壁に向かって走るロボットの制御（`sim_robot` + `brain`）、ノイズ、移動平均、ヒステリシス（STOP と SLOW の 2 境界）、ステップ 2 のフェーズ 0〜3（`room_sim`、`avoider`、ノイズと移動平均。最小値のかたより、平均の危険、N の比較） |
| いまの状態 | ステップ 2 の**フェーズ 0〜3 が完了**（`room_sim`、学習者が書いた `avoider`（最小値の移動平均 N=5））。`main` にマージ済みの PR は #1〜#7 と、フェーズ 3 の PR（`git log` で確認） |
| 次にやること | **ステップ 2 のフェーズ 4: ヒステリシス**（`avoider` に、回りはじめる線と、やめる線を作る。`avoiding` 状態変数、`hysteresis` パラメータ）。詳細は [5 章](#5-これからやること-ステップ-22d-部屋の掃除ロボット) |
| 進め方 | 学習者が自分でコードを書き、Claude がレビューする（[3 章](#3-学習者との進め方)） |
| 最初に確認すること | [7 章](#7-新しいセッションの最初の手順)のコマンドで、Docker とコンテナの状態を見る |

---

## 1. 環境

### 1.1 構成

```
Mac (macOS, Apple Silicon)
├─ Ghostty（シェルは fish）          ← 学習者がコマンドを打つ場所
├─ Claude Code（デスクトップアプリ）   ← Bash ツールで docker コマンドを実行できる
└─ Docker Desktop
    └─ コンテナ `ros2`（イメージ ros:jazzy, arm64, 中身は bash）
         └─ /root/ros2_ws  ←→  Mac の ~/Practice/ros2_ws（同じフォルダを共有）
```

| 項目 | 値 |
|---|---|
| Mac 側のワークスペース | `/Users/hiraku/Practice/ros2_ws`（Git リポジトリ） |
| コンテナ名 | `ros2`（`docker run -it --name ros2 --platform linux/arm64 -v ~/Practice/ros2_ws:/root/ros2_ws ros:jazzy`） |
| コンテナ内のパス | `/root/ros2_ws` |
| コンテナ内の `~/.bashrc` | `source /opt/ros/jazzy/setup.bash` と `source /root/ros2_ws/install/setup.bash` を追記済み（コンテナを消すと失われる） |
| GitHub | `hiraku00/ros2_ws`（private）。`gh` は認証済み |
| 追加パッケージ | ROS 2 のデモ（`ros-jazzy-demo-nodes-*`）、`colcon` はコンテナに導入済み |

**フォルダが共有されているので、Mac で編集したファイルは、すぐコンテナから見えます。** ビルド成果物（`build/` `install/` `log/`）もここに出ますが、`.gitignore` で追跡しません。

### 1.2 よく使うコマンド

Mac 側（Bash ツールから）:

```bash
docker ps -a --format '{{.Names}} {{.Status}}'          # コンテナの状態
docker info >/dev/null 2>&1 || open -a Docker           # Docker Desktop が止まっていたら起動
docker start ros2                                       # コンテナを起動
docker exec ros2 bash -c 'source /opt/ros/jazzy/setup.bash && source /root/ros2_ws/install/setup.bash && <コマンド>'
```

学習者の操作（Ghostty の別タブで、ノードを 2〜3 つ動かす）:

```bash
docker exec -it ros2 bash      # コンテナに入る（プロンプトが root@...:/# になる）
ros2 run my_first_pkg sim_robot
ros2 run my_first_pkg brain
```

### 1.3 Claude Code でできないこと・注意

| 項目 | 内容 |
|---|---|
| ターミナルに入力できない | Ghostty などのターミナルアプリは、画面操作では「クリックのみ」。タイプ・貼り付けは不可。**Claude は `docker exec`（`-it` なし）で、コンテナ内のコマンドを実行する**。対話の `docker exec -it` は、学習者が Ghostty で行う |
| `!` で始まる入力欄 | 対話用の端末ではない。`docker exec -it ros2 bash` を実行しても、すぐ戻される |
| `pkill -f my_first_pkg` は使わない | コマンド文字列自身にも一致して、コンテナのシェルを巻き込み、**コンテナが停止した**ことがある。PID を指定して `kill` する |
| テスト用ノードを動かすとき | 学習者のノードと混ざらないよう、`ROS_DOMAIN_ID` を別の値にする（`tools/probe_brain_slow_band.py` が例） |
| 実験後の後始末 | 自分が起動したプロセスは、必ず止める。起動時刻（`ps -eo pid,lstart,args`）で、学習者のものと見分ける |

---

## 2. これまでの経緯

### 2.1 時系列

| 段階 | 内容 | 結果 |
|---|---|---|
| 1. 環境構築 | Mac に ROS 2 は直接入らないため、Docker（`ros:jazzy`、arm64）を使う。最初は Intel 版を入れてしまい、作り直した | コンテナ `ros2` が動作 |
| 2. 基本操作 | `talker` / `listener`、`ros2 node/topic/service/param`、自作パッケージ `my_first_pkg` を作成 | 通信を確認 |
| 3. ロボット演習 | `sim_robot`（体）と `brain`（頭脳）を作り、`distance` と `cmd` の 2 トピックで輪にした | 壁の手前で減速・旋回して往復 |
| 4. お題 1: STOP | 壁の手前で 2 秒止まってから TURN。**時刻を覚える変数**で実装（学習者が自分で書いた） | PR #1 |
| 5. お題 2: ノイズ | `sim_robot` に ±0.5 のノイズを足し、チャタリングを再現。**移動平均**（N=5）で対策。N=1/5/20 を比べて、遅れとのトレードオフを確認 | PR #2 |
| 6. ヒステリシス | STOP の境界に、入る線 3.0 と出る線 4.0 を導入。パラメータ `hysteresis` を実行時に変更可能にした | PR #3（解説ドキュメントも整備） |
| 7. SLOW の境界 | 同じ考え方を、8.0（入る）/ 9.0（出る）にも適用。状態変数 `self.slowing` を追加 | PR #4 |

### 2.2 現在のコード

| ファイル | 役割 |
|---|---|
| `src/my_first_pkg/my_first_pkg/talker.py` / `listener.py` | `my_topic` の Pub/Sub の最小例 |
| `src/my_first_pkg/my_first_pkg/sim_robot.py` | 40 マスの廊下。`distance` に **±0.5 のノイズ**を足して送信。`cmd` に従って動く（`TURN` に切り替わった瞬間だけ向きを反転） |
| `src/my_first_pkg/my_first_pkg/brain.py` | `distance` の**移動平均（N=5）**で判断。`FORWARD` / `SLOW` / `STOP`（2 秒）/ `TURN`。ヒステリシス付き |
| `tools/simulate_filters.py` | ROS 2 なし（Mac で実行）。判断ロジックを再現して、ノイズ対策の効果を数千回シミュレート |
| `tools/probe_brain_slow_band.py` | コンテナ内で実行。本物の `brain` に距離を直接送り、SLOW の境界の揺れを数える |

### 2.3 `brain.py` のパラメータと判断

| パラメータ | 初期値 | 意味 |
|---|---|---|
| `turn_distance` | 3.0 | これ未満で `STOP`（最初の 2 秒）→ `TURN` |
| `slow_distance` | 8.0 | これ未満で `SLOW` |
| `hysteresis` | 1.0 | `STOP` と `SLOW` の「出る線」を、「入る線」からどれだけ遠くに置くか |

| 境界 | 入る線 | 出る線 | 状態の持ち方 |
|---|---|---|---|
| STOP | 3.0 | 4.0 | `self.stop_started`（時刻 or `None`） |
| SLOW | 8.0 | 9.0 | `self.slowing`（`True` / `False`） |

移動平均の個数 N は、`brain.py` の `deque(maxlen=5)`（パラメータ化していない）。

### 2.4 実測で分かったこと（要点）

| 項目 | 結果 |
|---|---|
| ノイズ ±0.5、対策なし | STOP の途中に SLOW が混ざる（95% の壁）。最接近が 2.50 まで近づく |
| 移動平均 N=5 | 中断 1.6%。ただし STOP の開始が 2.5 に近づく（遅れ） |
| 移動平均 N=20 | 中断 0% だが、STOP の開始が **0.58**（壁の直前）。危険 |
| ヒステリシス 1.0（平均なし） | 中断 0.0%、最接近 3.00（ノイズ全幅 1.0 以上の幅が必要） |
| ノイズ ±1.0 | 幅 1.0 では足りない（中断 63%）。**幅はノイズの全幅に合わせる** |
| SLOW の境界の揺れ | 対策なしで 18.8% の壁で発生。SLOW 側にも入れて 0.0% |
| 本物の `brain` での検証 | 帯の中の切り替え回数: `hysteresis=0.0` で 31 回、`1.0` で 0 回 |

### 2.5 学習者が身につけたこと

- ノード・トピック・パブリッシャ・サブスクライバ・パラメータの区別と、コードのどこに出るか
- 状態を持つノード（時刻や真偽値を、`__init__` で作って、メッセージのたびに更新する）
- 「保存しても、動いているノードは変わらない。再起動が必要」
- ノイズ、チャタリング、移動平均、ヒステリシスの考え方と、トレードオフ
- 予想を先に書いてから、結果と比べる学び方

---

## 3. 学習者との進め方

学習者の希望と、これまでうまくいったやり方です。**新しいセッションでも、これを守ってください。**

| 項目 | 内容 |
|---|---|
| 言語 | すべて日本語 |
| 説明のレベル | 中学生でも分かるように。図・表・たとえ話・用語の説明を入れる |
| 学習のしかた | **学習者が自分でコードを書き、Claude がレビューする**（「A: 自分で手を動かす」を選んだ）。答えを先に書かない。ヒント → 学習者が書く → 貼ってもらう → 確認、の順 |
| 予想 | コードを触る前に、結果を予想してもらう。そのあと実測し、差を一緒に確認する |
| ログの確認 | 学習者が貼ったログは、結論を出す前に**ファイルの中身と照らして確認**する（保存前のコードで動いていることが、何度もあった） |
| 数字の裏付け | 説明に使う数字は、模擬実験や実測で出す。確率が低い現象は、1 回で判断しない |
| 訂正 | 間違いや、言い過ぎに気づいたら、すぐ認めて訂正する（例:「STOP の位置は変わらない」を「始める位置は変わらないが、最接近は変わる」に訂正した） |
| 一度に出す量 | お題は 1 つずつ。長すぎる返信にしない |
| 文書の書きかた | 中学生向け。高校以上の数学（cos・sin・ラジアンの理屈・統計の式）は、本文で使わず、図と具体的な数字で説明し、必要なら「もっと知りたい人へ」に回す。各章は「この章でわかること」で始め、「まとめ」で終える。1 文は短く、表のマスには 1 文まで |
| 文書の図 | `docs/room-robot/images/` の SVG は、`tools/make_room_robot_figures.py` で `room_sim` と同じ計算から作る（手で数字を書かない）。図の数字と本文の表を一致させる。ブラウザの実画面と色をそろえる（当たったレーザーは赤） |
| 予想の選択肢 | 選択肢は、**向きだけでなく、大きさ**も書く（「C: 18.57 より先」と書いて、実際は 0.07 m の差だった）。学習者の理由が、仕組みとして正しいときは、そこを認める |
| ログの場所 | ログは**コンテナの中**にできる。Mac 側のタブ（`❯`）で `grep` すると、見つからない。どのタブで実行するか、書く |
| 観察のしかた | 図は 1 秒おきで、瞬間は見失う。「見てほしいこと」を頼むときは、**どこを見るか（ブラウザの図の左上、`room_sim` のログ）を、先に伝える**。ログが要るなら、Claude が足す |
| 新しい概念の出し方 | 問題に使う前に、**何のためか・どういう条件で起きるか・単位**を説明する（例: 「回転」を説明なしに出して、「なぜ回転が出てくるのか」と指摘された。`x=0.5` を「0.5 m ずつ」と読み違えたのも、速さと距離の説明が先になかったため）。学習者の「なぜ？」は、理解の入口なので、先に答える |
| 破壊的な操作 | コンテナの停止・削除、プロセスの強制終了は、事前に説明する |

---

## 4. Git / GitHub の流儀

| 項目 | 内容 |
|---|---|
| 流れ | `main` から作業ブランチを作成 → コミット → push → PR 作成 → **マージ（merge commit）** → ブランチ削除（リモート・ローカル）→ `main` を最新に |
| ブランチ名 | `feature/<内容>`、`fix/<内容>`、`docs/<内容>`（例: `feature/slow-boundary-hysteresis`） |
| マージ方法 | `gh pr merge <番号> --merge --delete-branch`（過去のリポジトリが merge commit 方式） |
| 公開範囲 | private。変えるときは学習者に確認する |
| 事前確認 | 学習者が「GitHub に上げて」と言ってから行う。勝手に push しない |
| 差分の確認 | コミット前に `git diff`・`git status` で、生成物や機密情報が入っていないか確認する |

### コミットメッセージの書式

過去の学習者のリポジトリ（`auto-daily-report`、`bing検索` など）に合わせた書式です。

```
<type>: <要約（日本語、1 行）>

【背景】
なぜこの変更が必要か（2〜3 行）

【変更内容】
- 変更点を箇条書き（ファイル名・理由つき）

【検証内容】
- 実際に確認したことだけを書く（推測や未実施のことは書かない）

Co-Authored-By: Claude <使用中のモデル名> <noreply@anthropic.com>
```

| type | 使う場面 |
|---|---|
| `feat` | 機能追加・動作の変更 |
| `fix` | 不具合修正 |
| `docs` | ドキュメントのみ |
| `refactor` | 動作を変えない整理 |
| `chore` | 設定・雑務 |

コードとドキュメントは、**コミットを分ける**。

### PR の書式

```
## 概要
## 変更内容
## 検証内容（表で、実測の数字を入れる）
## 備考（既知の制限、次の候補）

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

### 毎回のルール

- `.gitignore` を確認する（`build/` `install/` `log/` `__pycache__/` `.env` など。API キー・機密情報は、絶対に上げない）
- README と `docs/` を、変更に合わせて更新する（README は入口に絞り、詳細は `docs/` へのリンクにする）
- 文書内のリンクが、実在するファイルを指すか確認する
- コミットメッセージの「検証内容」には、**実際にやったことだけ**を書く

---

## 5. これからやること: ステップ 2（2D 部屋の掃除ロボット）

### 5.1 ねらい

今までは、名前も型も自作でした（`Float32` の `distance`、`String` の `cmd`）。
ステップ 2 では、**本物のロボットと同じ型**で作り直します。ここで書く `brain` に近いものは、実機や Gazebo にも載せられる形になります。

| 今まで | ステップ 2（本物と同じ） |
|---|---|
| `distance`（`Float32`、数値 1 つ） | `/scan`（`sensor_msgs/LaserScan`、360° 分の距離の配列） |
| `cmd`（`String`、`FORWARD` など） | `/cmd_vel`（`geometry_msgs/Twist`、前進速度と回転速度） |
| 1 本の廊下（1 次元） | 障害物のある 2D の部屋 |
| 文字の表示 | ブラウザで見える画像 |

**今日までの知識（ノイズ、移動平均、ヒステリシス、状態を持つノード）は、そのまま使います。**

### 5.2 決まっていること

| 項目 | 決定 |
|---|---|
| リポジトリ | **分けない**。同じ `ros2_ws` に、新しいパッケージを足す |
| パッケージ名 | `room_robot_pkg`（`src/room_robot_pkg/`）。`my_first_pkg` は、そのまま残す（壊さない） |
| ブランチ | `feature/room-robot`（フェーズごとに細かく切ってもよい） |
| ドキュメント | **フォルダを分ける**。入門編は `docs/basics/`（01〜04）、ステップ 2 は `docs/room-robot/`（01〜）。README の目次に「入門編」「ステップ 2」を並べた |
| 進め方 | [3 章](#3-学習者との進め方)のとおり（学習者が書く部分と、Claude が用意する部分を分ける） |

### 5.3 決まったこと（学習者に確認済み）

| 項目 | 選択肢 | おすすめ |
|---|---|---|
| ブラウザでの見せ方 | **A: 決定。** ロボットが SVG（または PNG）を毎秒書き出し、HTML を自動更新で開く / B: コンテナ内に Web サーバーを立て、ポート転送で見る（不採用） | **A**。フォルダが Mac と共有されているので、**書き出したファイルは Mac 側にすぐ出る**。Docker のポート設定が不要 |
| 画像の形式 | **SVG: 決定。** SVG（文字ファイル。追加ライブラリ不要）/ PNG（`matplotlib` か `Pillow` が必要。不採用） | SVG（コンテナに `apt install` しなくて済む。`apt` で入れたものは、コンテナを消すと失われる） |

### 5.4 構成（案）

```
room_sim ──/scan (LaserScan)──→ avoider ──/cmd_vel (Twist)──→ room_sim
   │                                                              ▲
   └─ 部屋の SVG を毎秒書き出す → output/room.svg → Mac のブラウザで表示
```

| ノード | 役割 | 誰が書くか（案） |
|---|---|---|
| `room_sim` | 2D の部屋（壁と障害物）。ロボットの位置・向きを持つ。`/cmd_vel` で動く。LiDAR を模擬して `/scan` に、ノイズ付きで送る。SVG も書き出す | **Claude が用意**（世界の模擬は、学習の本筋ではないため） |
| `avoider`（頭脳） | `/scan` を読み、障害物を避けて走る指示を `/cmd_vel` に出す | **学習者が書く**（今日までの学びを生かす中心部分） |

### 5.5 フェーズ（各フェーズで、予想 → 実装 → 実測 → PR）

| フェーズ | 内容 | 担当 | 学べること |
|---|---|---|---|
| 0. 準備 ✅ | `room_robot_pkg` の作成（`ros2 pkg create`）、`setup.py`・`package.xml`（`sensor_msgs`、`geometry_msgs` の依存）、`.gitignore` に `output/` | Claude（手順は説明する） | パッケージ構成、依存の宣言 |
| 1. 世界と表示 ✅ | `room_sim`。固定の部屋、壁と障害物、ロボットの位置、SVG の書き出し。最初は `/cmd_vel` を手で送って動かす（`ros2 topic pub`） | Claude が作り、学習者が動かして確認 | `Twist`、`LaserScan` のフィールド（`ranges`、`angle_min`、`angle_increment`、`range_max`） |
| 2. 避けるだけ ✅ | `avoider`。`/scan` の前方の最小距離が近ければ曲がる、遠ければ進む | **学習者** | `LaserScan` の配列の扱い、サブスクライバと `Twist` の発行 |
| 3. ノイズとフィルタ ✅ | `/scan` にノイズを足す。前方を**扇形に切り出して、最小値や平均を取る**（移動平均・中央値）。外れ値（`inf`、範囲外）の扱い | **学習者** | 配列のフィルタ、`inf` の処理、**チャタリングが 2D でも起きる**こと |
| 4. ヒステリシス（**次**） | 「避けモード」に入る線と出る線をずらす（`avoiding` 状態変数）。`hysteresis` をパラメータ化 | **学習者** | 今日の学びの再適用 |
| 5. launch ファイル | 2〜3 つのタブで起動していたものを、1 コマンドで起動する | 学習者と Claude で | `launch.py`、パラメータの渡し方 |
| 6. 発展（任意） | `rosbag2` で記録・再生、`rqt`、地図とゴール、TurtleBot3 + Gazebo | — | 実機への道筋 |

### 5.6 フェーズ 1 の仕様（案。着手時に学習者と確認する）

| 項目 | 案 |
|---|---|
| 部屋 | 20 × 20 程度の四角い部屋。中に、四角や円の障害物を 2〜3 個。壁と障害物は、線分や円の集まり |
| ロボット | 位置 (x, y)、向き θ。円で表示 |
| 動かし方 | `Twist`（`linear.x`、`angular.z`）を積分する。`dt` は、タイマー（0.1 秒） |
| LiDAR | 360 本のレーザー（1° ごと）。各レーザーで、壁・障害物への距離を計算。`range_max` を超えたら `inf` |
| ノイズ | `/scan` の `ranges` に、乱数を足す（大きさはパラメータ。初期値は 0.0 で、フェーズ 3 で上げる） |
| 表示 | SVG に、壁・障害物・ロボット・レーザーを描く。`output/room.svg` と、自動更新（`<meta http-equiv="refresh" content="1">`）つきの `output/index.html` |
| 見かた | Mac のブラウザで `file:///Users/hiraku/Practice/ros2_ws/output/index.html` を開く |
| `.gitignore` | `output/` を追加する（生成物のため） |

### 5.7 先に学習者へ聞く予想問題（例）

- **フェーズ 4 の最初（次に出す）**: 「回りはじめる線（1.5 m）と、やめる線を同じにすると、なぜ揺れるのか。やめる線を、どう置くか」。ノイズの大きさと、移動平均の遅れ（N=5 で約 0.07 m）を、幅の決めかたに使う
- フェーズ 3 の前: 「LiDAR にノイズを足すと、壁沿いを走るとき、どんな動きが出ますか？」
- フェーズ 3: 「前方の最小値と平均値は、どちらがノイズに強いですか？ 安全なのはどちらですか？」（最小値は安全寄りだが、外れ値に弱い。平均は遅れる）
- フェーズ 4: 「避けモードの入る線と出る線の幅は、どう決めますか？」（ノイズの全幅以上）

### 5.8 完了の目安

- 部屋の中を、障害物に当たらず、走り続けられる
- `/scan` にノイズを足しても、避けモードの出入りが揺れない
- 起動が 1 コマンドで済み、ブラウザで動きが見える
- `docs/room-robot/` に、図・表つきで、構成と手順が書かれている（01〜04 はフェーズ 1 まで。以降は、フェーズごとに足す）
- すべて `main` にマージされている

---

## 6. 既知の課題・改善候補

| 項目 | 内容 |
|---|---|
| `N`（移動平均の個数）が固定 | `deque(maxlen=5)` をパラメータ化すると、実行中に比べられる（`deque` は、サイズを後から変えられないので、作り直す必要がある） |
| `hysteresis` の共有 | STOP と SLOW で共有している。ノイズが違う境界では、分ける |
| `sim_robot` のノイズ幅が固定 | `±0.5` をパラメータ化すると、「ノイズを上げたら幅も上げる」実験ができる |
| 自動テストなし | `tools/` のスクリプトで、検証している。`pytest` を足してもよい（`ament_flake8` などの雛形は `test/` にある） |
| flake8 | `room_robot_pkg` は `D400`（日本語の句点）のみ。`my_first_pkg` は、`brain.py` を直したあと、`sim_robot.py` の import 順（`random` を `rclpy` より上に）が残っている |
| 実機への道筋 | Gazebo + TurtleBot3 は、Apple Silicon の Docker では描画の設定が重い。ステップ 2 を終えてから |

---

## 7. 新しいセッションの最初の手順

### 7.1 状態を確認する（Claude が実行）

```bash
cd /Users/hiraku/Practice/ros2_ws
git status -sb && git log --oneline --first-parent -5     # main が最新で、作業中の変更がないか
docker info >/dev/null 2>&1 && echo "docker ok" || echo "docker 停止中"
docker ps -a --format '{{.Names}} {{.Status}}'            # ros2 が Up か
```

| 状態 | 対処 |
|---|---|
| Docker が停止中 | `open -a Docker` で起動し、`docker info` が通るまで待つ |
| `ros2` が `Exited` | `docker start ros2` |
| 他に動いているノードがある | `ps -eo pid,lstart,args` で確認し、学習者のものか見分ける。勝手に止めない |

### 7.2 コンテナ内でパッケージが見えるか確認する

```bash
docker exec ros2 bash -c 'source /opt/ros/jazzy/setup.bash && source /root/ros2_ws/install/setup.bash && ros2 pkg executables my_first_pkg'
```

`brain`、`sim_robot`、`my_talker`、`my_listener` が出れば正常です。

### 7.3 学習者に伝えること

1. 前回までの内容を、短く要約する（[0 章](#0-3-分で把握する)）
2. フェーズ 3 の予想問題の回答を聞く（[5.7 章](#57-先に学習者へ聞く予想問題例)の、`noise=0.5` で最初に回り始める `x=` はいくつか）
3. 学習者が、前方の距離をフィルタするコードを書き、Claude がレビューする（答えを先に書かない）

### 7.4 新しいセッションの最初のメッセージ（例）

> `docs/handoff.md` を読んで、ステップ 2 の続きを始めてください。

---

## 8. 参考: 作成済みのドキュメント

| 文書 | 内容 |
|---|---|
| [README.md](../README.md) | 入口。構成、パラメータ表、実行手順 |
**入門編（`docs/basics/`）**

| 文書 | 内容 |
|---|---|
| [01-ros2-basics.md](basics/01-ros2-basics.md) | ノード・トピック・パラメータ、用語集 |
| [02-robot-exercise.md](basics/02-robot-exercise.md) | `sim_robot` と `brain` の仕組み、6 つの実験 |
| [03-noise-and-filters.md](basics/03-noise-and-filters.md) | ノイズ、チャタリング、移動平均、ヒステリシス（実測値つき） |
| [04-troubleshooting.md](basics/04-troubleshooting.md) | エラーと対処、コードの落とし穴 |

**ステップ 2（`docs/room-robot/`）**

| 文書 | 内容 |
|---|---|
| [01-lidar-and-twist.md](room-robot/01-lidar-and-twist.md) | 目的、`/scan`（LaserScan）、`/cmd_vel`（Twist）、フェーズ一覧 |
| [02-room-sim.md](room-robot/02-room-sim.md) | `room_sim` の仕組み、図の見かた、パラメータ |
| [03-experiments.md](room-robot/03-experiments.md) | フェーズ 1 の実験の記録（予想 → 実測 → 理由） |
| [04-troubleshooting.md](room-robot/04-troubleshooting.md) | ステップ 2 のつまずきと対処 |
| [05-avoider.md](room-robot/05-avoider.md) | フェーズ 2: `avoider` の仕組み、実験の記録、弱点（チャタリング） |
| [06-noise-and-filter.md](room-robot/06-noise-and-filter.md) | フェーズ 3: ノイズ、最小値のかたより、平均の危険、移動平均（N=1/5/20）の比較 |

過去のリポジトリ（コミット書式の参考）: `~/Practice/auto-daily-report`、`~/Practice/bing検索`、`~/Practice/connect-proton`
