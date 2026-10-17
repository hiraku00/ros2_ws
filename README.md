# ros2_ws

ROS 2 (Jazzy) の学習用ワークスペース。Apple Silicon の Mac 上で Docker コンテナ内に ROS 2 を動かし、
ノード間通信（トピック）の基本と、**センサー → 判断 → 動作**の制御ループを体験する。

2 つのパートからなる。

| パート | 内容 | パッケージ |
|---|---|---|
| **入門編** | 壁に向かって走る仮想ロボットを、頭脳ノード（`brain`）で制御する。センサーノイズ・チャタリング・移動平均・ヒステリシスを、実測の数字つきで学ぶ | `my_first_pkg` |
| **ステップ 2（進行中）** | 本物と同じ型（`/scan`、`/cmd_vel`）で、2D の部屋を走る掃除ロボットを作る。フェーズ 0〜4（世界、障害物をよける頭脳、ノイズ対策、ヒステリシス）まで完了 | `room_robot_pkg` |

## ドキュメント

初めての人は、入門編を上から順に読む。

### 入門編（`docs/basics/`）

| 文書 | 内容 |
|---|---|
| [01. ROS 2 の基本](docs/basics/01-ros2-basics.md) | ノード・トピック・パラメータ、なぜ Docker を使うのか、用語集 |
| [02. 壁に向かって走るロボット](docs/basics/02-robot-exercise.md) | sim_robot と brain の仕組み、6 つの実験 |
| [03. ノイズ・チャタリング・フィルタ](docs/basics/03-noise-and-filters.md) | 移動平均とヒステリシスの考え方、N と幅の選び方 |
| [04. つまずきやすい点と対処](docs/basics/04-troubleshooting.md) | よくあるエラー、「コードを変えたのに変わらない」の原因 |

### ステップ 2: 2D の部屋の掃除ロボット（`docs/room-robot/`）

| 文書 | 内容 |
|---|---|
| [01. 目的と、2 つのメッセージ](docs/room-robot/01-lidar-and-twist.md) | 何のためにやるのか、`/scan`（LaserScan）と `/cmd_vel`（Twist）、フェーズの一覧 |
| [02. room_sim の仕組み](docs/room-robot/02-room-sim.md) | 部屋・ロボットの動き・LiDAR のまねかた・図の見かた・パラメータ |
| [03. 実験の記録](docs/room-robot/03-experiments.md) | 予想 → 実測 → 差の理由（正面の距離、壁まで前進、その場で回転） |
| [04. つまずきやすい点と対処](docs/room-robot/04-troubleshooting.md) | 数字の意味、図が見えない、プロセスの後始末 |
| [05. avoider（障害物をよける頭脳）](docs/room-robot/05-avoider.md) | 前方 ±30° の最小値で、回る／進むを決める。実験の記録と、弱点（チャタリング） |
| [06. ノイズと、最小値・平均・移動平均](docs/room-robot/06-noise-and-filter.md) | 最小値のかたより、平均の危険、移動平均（N=1/5/20）の比較。実測の数字つき |
| [07. ヒステリシス](docs/room-robot/07-hysteresis.md) | 回り始める線（1.5 m）とやめる線（2.0 m）を分けて、ちょこちょこ回りを止める。幅の決めかた |

### その他

| 文書 | 内容 |
|---|---|
| [引き継ぎ書](docs/handoff.md) | 経緯、現状、次にやること、進め方。新しいセッションの開始点 |

## 構成

```
src/my_first_pkg/my_first_pkg/          # 入門編
├── talker.py     # my_topic に文字列を 1 秒ごとに送る
├── listener.py   # my_topic を受け取って表示する
├── sim_robot.py  # 仮想ロボット（体）: ノイズ入りの distance を送り、cmd に従って動く
└── brain.py      # 頭脳: distance を移動平均して、FORWARD / SLOW / STOP / TURN を cmd に送る
src/room_robot_pkg/room_robot_pkg/      # ステップ 2
├── room_sim.py   # 2D の部屋: /cmd_vel で動き、/scan（360 本）を送り、図を output/ に書き出す
└── avoider.py    # 頭脳: /scan の前方 ±30° の最小値（過去 5 回の平均）で、1.5 m 未満なら回り始め、2.0 m（hysteresis 0.5）あくまで回る（/cmd_vel）
tools/
├── simulate_filters.py          # ノイズ対策の効果を ROS 2 なしで数値化する（Mac で実行）
├── probe_brain_slow_band.py     # 本物の brain に距離を直接送り、SLOW の境界の揺れを確かめる（コンテナ内）
├── make_basics_figures.py       # docs/basics/images/ の図（SVG）を、simulate_filters.py と同じ計算から作る（Mac。約 10 秒）
├── simulate_avoider_filters.py  # avoider の最小値・平均・移動平均を、ROS 2 なしで比べる（Mac で実行。約 3 分）
└── make_room_robot_figures.py   # docs/room-robot/images/ の図（SVG）を、room_sim と同じ計算から作る（Mac。約 3〜4 分）
docs/                     # 解説ドキュメント（basics/ と room-robot/）
output/                   # room_sim が書き出す図（生成物。Git では追跡しない）
```

```
sim_robot ──distance (Float32)──→ brain
          ←──cmd (String)───────
```

## brain のパラメータ

実行中に `ros2 param set /brain <名前> <値>` で変更できる（再起動すると初期値に戻る）。

| 名前 | 初期値 | 意味 |
|---|---|---|
| `slow_distance` | 8.0 | これ未満で `SLOW`（減速）に入る |
| `turn_distance` | 3.0 | これ未満で `STOP`（2 秒）→ `TURN` に入る |
| `hysteresis` | 1.0 | `STOP` と `SLOW` の「出る線」を、「入る線」からどれだけ遠くに置くか。3.0→4.0、8.0→9.0（[詳細](docs/basics/03-noise-and-filters.md#4-対策-2ヒステリシス)） |

移動平均の個数 `N` は、`brain.py` の `deque(maxlen=5)` で指定する。

## 実行方法

### 1. コンテナを起動（初回のみ）

```bash
mkdir -p ~/Practice/ros2_ws
docker run -it --name ros2 --platform linux/arm64 \
  -v ~/Practice/ros2_ws:/root/ros2_ws ros:jazzy
```

2 回目以降は、`docker start ros2` の後に `docker exec -it ros2 bash` で入る。
Docker Desktop が起動していないとエラーになる（[対処](docs/basics/04-troubleshooting.md)）。

### 2. ビルド（コンテナ内）

```bash
source /opt/ros/jazzy/setup.bash
cd /root/ros2_ws
colcon build --symlink-install --packages-select my_first_pkg
source install/setup.bash
```

### 3. 実行（ターミナルを 2 つ。どちらも `docker exec -it ros2 bash` で入って `source` する）

```bash
# タブ1
ros2 run my_first_pkg sim_robot
# タブ2
ros2 run my_first_pkg brain
```

壁の手前で `SLOW` → `STOP`（約 2 秒）→ `TURN` となり、廊下を往復する。
終了時は両方で Ctrl+C を押す。プロセスが残ると、次回の実行に干渉する。

コードを変えたら、**変えたノードを再起動する**（保存しただけでは、動いているノードに反映されない）。

### 実験

```bash
ros2 param set /brain turn_distance 10.0   # 実行中に頭脳の性格を変える
ros2 param set /brain hysteresis 0.0       # ヒステリシスを切る（効果は maxlen=1 で見やすい）
ros2 topic echo /cmd                       # 頭脳の指示を直接見る
ros2 topic pub /cmd std_msgs/msg/String "{data: TURN}" --once   # 人間が頭脳の代わりをする
```

### ノイズ対策の効果を数値で確かめる

```bash
python3 tools/simulate_filters.py          # Mac で。ROS 2 不要
python3 tools/probe_brain_slow_band.py     # コンテナの中で。本物の brain を検証する
python3 tools/simulate_avoider_filters.py  # Mac で。ステップ 2 の avoider の、フィルタ比較
python3 tools/simulate_avoider_filters.py --hysteresis  # Mac で。ヒステリシスの幅の比較
python3 tools/make_basics_figures.py       # Mac で。入門編の文書の図を作り直す（matplotlib が必要）
python3 tools/make_room_robot_figures.py   # Mac で。ステップ 2 の文書の図を作り直す（matplotlib が必要）
```

## ステップ 2 の実行方法（room_sim）

ビルド（コンテナ内。初回と `setup.py` を変えたときだけ）:

```bash
cd /root/ros2_ws
colcon build --symlink-install --packages-select room_robot_pkg
source install/setup.bash
```

```bash
# タブ 1: シミュレータ
ros2 run room_robot_pkg room_sim
# タブ 2: 頭脳を動かす（壁ぞいに、走り続ける）
ros2 run room_robot_pkg avoider
```

`/scan` にノイズを足して試すには、`room_sim` を、`--ros-args -p noise:=0.5` つきで起動する（[06](docs/room-robot/06-noise-and-filter.md)）。

頭脳なしで、手で動かすこともできる（Ctrl+C で止める。0.5 秒指示が途絶えると、ロボットは止まる）。

```bash
ros2 topic pub -r 10 /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.5}, angular: {z: 0.0}}"
```

Mac のブラウザで、`file:///Users/hiraku/Practice/ros2_ws/output/index.html` を開くと、動きが見える（1 秒ごとに更新）。
タブ 1 の `room_sim` には、「回り始めた／回るのをやめた」の瞬間の位置が出る。詳しくは [02. room_sim の仕組み](docs/room-robot/02-room-sim.md) と [05. avoider](docs/room-robot/05-avoider.md)。

## 本物のロボットとの対応

| 入門編 | ステップ 2（本物と同じ型） | 実機の ROS 2 |
|---|---|---|
| `distance`（数字 1 つ） | `/scan`（`LaserScan`、360 個の配列） | LiDAR |
| `cmd`（文字） | `/cmd_vel`（`Twist`、速さ） | 走行指令 |
| `brain` | `avoider` | 障害物回避・経路計画（Nav2 など） |
| `sim_robot` | `room_sim` | モーターとタイヤ、LiDAR |

## 注意

- `build/` `install/` `log/` は colcon の生成物、`output/` は room_sim が書き出す図なので、追跡しない。
- 機密情報（`.env` など）はコミットしない。
