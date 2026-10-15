# ros2_ws

ROS 2 (Jazzy) の学習用ワークスペース。Apple Silicon の Mac 上で Docker コンテナ内に ROS 2 を動かし、
ノード間通信（トピック）の基本と、**センサー → 判断 → 動作**の制御ループを体験する。

壁に向かって走る仮想ロボットを、頭脳ノード（`brain`）で制御する演習を通して、
センサーノイズ・チャタリング・移動平均・ヒステリシスまでを、実測の数字つきで学べる。

## ドキュメント

初めての人は、上から順に読む。

| 文書 | 内容 |
|---|---|
| [01. ROS 2 の基本](docs/01-ros2-basics.md) | ノード・トピック・パラメータ、なぜ Docker を使うのか、用語集 |
| [02. 壁に向かって走るロボット](docs/02-robot-exercise.md) | sim_robot と brain の仕組み、6 つの実験 |
| [03. ノイズ・チャタリング・フィルタ](docs/03-noise-and-filters.md) | 移動平均とヒステリシスの考え方、N と幅の選び方 |
| [04. つまずきやすい点と対処](docs/04-troubleshooting.md) | よくあるエラー、「コードを変えたのに変わらない」の原因 |

## 構成

```
src/my_first_pkg/my_first_pkg/
├── talker.py     # my_topic に文字列を 1 秒ごとに送る
├── listener.py   # my_topic を受け取って表示する
├── sim_robot.py  # 仮想ロボット（体）: ノイズ入りの distance を送り、cmd に従って動く
└── brain.py      # 頭脳: distance を移動平均して、FORWARD / SLOW / STOP / TURN を cmd に送る
tools/
├── simulate_filters.py          # ノイズ対策の効果を ROS 2 なしで数値化する（Mac で実行）
└── probe_brain_slow_band.py     # 本物の brain に距離を直接送り、SLOW の境界の揺れを確かめる（コンテナ内）
docs/                     # 解説ドキュメント
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
| `hysteresis` | 1.0 | `STOP` と `SLOW` の「出る線」を、「入る線」からどれだけ遠くに置くか。3.0→4.0、8.0→9.0（[詳細](docs/03-noise-and-filters.md#4-対策2-ヒステリシス)） |

移動平均の個数 `N` は、`brain.py` の `deque(maxlen=5)` で指定する。

## 実行方法

### 1. コンテナを起動（初回のみ）

```bash
mkdir -p ~/Practice/ros2_ws
docker run -it --name ros2 --platform linux/arm64 \
  -v ~/Practice/ros2_ws:/root/ros2_ws ros:jazzy
```

2 回目以降は、`docker start ros2` の後に `docker exec -it ros2 bash` で入る。
Docker Desktop が起動していないとエラーになる（[対処](docs/04-troubleshooting.md)）。

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
```

## 本物のロボットとの対応

| この演習 | 実機の ROS 2 |
|---|---|
| `distance` | `/scan`（LiDAR） |
| `cmd` | `/cmd_vel`（走行指令） |
| `brain` | 障害物回避・経路計画（Nav2 など） |
| `sim_robot` | モーターとタイヤ |

## 注意

- `build/` `install/` `log/` は colcon の生成物なので追跡しない。
- 機密情報（`.env` など）はコミットしない。
