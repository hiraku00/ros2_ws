# ros2_ws

ROS 2 (Jazzy) の学習用ワークスペース。Apple Silicon の Mac 上で Docker コンテナ内に ROS 2 を動かし、
ノード間通信（トピック）の基本と、センサー → 判断 → 動作の制御ループを体験する。

## 構成

```
src/my_first_pkg/my_first_pkg/
├── talker.py     # my_topic に文字列を1秒ごとに送る
├── listener.py   # my_topic を受け取って表示する
├── sim_robot.py  # 仮想ロボット（体）: distance を送り、cmd に従って動く
└── brain.py      # 頭脳: distance を見て FORWARD / SLOW / TURN を cmd に送る
```

### 壁に向かって走るロボットの演習

2 つのノードが 2 本のトピックで輪になってつながる。互いの存在は知らず、トピック名だけで通信する。

```
sim_robot ──distance (Float32)──→ brain
          ←──cmd (String)───────
```

| 壁までの距離 | brain の指示 | sim_robot の動き |
|---|---|---|
| `slow_distance`（既定 8.0）以上 | `FORWARD` | 1 歩 0.5 |
| `turn_distance`（既定 3.0）以上 | `SLOW` | 1 歩 0.2 |
| `turn_distance` 未満 | `TURN` | 向きを反転 |

brain を起動しない場合、sim_robot は初期値の `FORWARD` のまま壁へ突っ込んで止まる。

## 実行方法

### 1. コンテナを起動（初回のみ）

```bash
mkdir -p ~/Practice/ros2_ws
docker run -it --name ros2 --platform linux/arm64 \
  -v ~/Practice/ros2_ws:/root/ros2_ws ros:jazzy
```

2 回目以降は `docker start ros2` の後、`docker exec -it ros2 bash` で入る。

### 2. ビルド（コンテナ内）

```bash
source /opt/ros/jazzy/setup.bash
cd /root/ros2_ws
colcon build --packages-select my_first_pkg
source install/setup.bash
```

### 3. 実行（ターミナルを 2 つ使い、それぞれ `docker exec -it ros2 bash` で入って `source` する）

```bash
# タブ1
ros2 run my_first_pkg sim_robot
# タブ2
ros2 run my_first_pkg brain
```

終了時は両方で Ctrl+C を押す。プロセスが残ると、次回の実行に干渉する。

### 実験

```bash
ros2 param set /brain turn_distance 10.0   # 実行中に頭脳の性格を変える
ros2 topic echo /cmd                       # 頭脳の指示を直接見る
ros2 topic pub /cmd std_msgs/msg/String "{data: TURN}" --once   # 人間が頭脳の代わりをする
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
