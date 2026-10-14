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
| `turn_distance` 未満（最初の 2 秒） | `STOP` | 停止 |
| `turn_distance` 未満（2 秒経過後） | `TURN` | 向きを反転 |

`STOP` を出し始めた時刻は brain が保持し、壁から離れる（`SLOW` / `FORWARD` に戻る）と破棄する。
反対側の壁でも、再び 2 秒の `STOP` から始まる。

brain を起動しない場合、sim_robot は初期値の `FORWARD` のまま壁へ突っ込んで止まる。

### センサーノイズと移動平均フィルタ

`sim_robot` は、`distance` に ±0.5 の一様ノイズを加えて送信する（画面の「壁まで」は真の値）。
判断の境界（`turn_distance`）付近で測定値が揺れると、`STOP` と `SLOW` が短い間隔で入れ替わり、
STOP の 2 秒タイマーも毎回リセットされる（チャタリング）。

`brain` は、直近 `N` 個の測定値の平均で判断する（`N = 5`）。ただし平均は過去の値を含むため、
接近中は実際より壁が遠いと誤認し、停止が遅れる。

| N | STOP が始まった壁までの距離（真値） | 傾向 |
|---|---|---|
| 1（平均なし） | 約 2.7 | チャタリングが発生する |
| 5 | 約 2.6 | チャタリングが解消し、遅れも小さい |
| 20 | 約 0.4 | 壁の直前まで進み、安全余裕がほぼない |

フィルタを強くするほどノイズは減るが、反応は遅れる。速度と許容できる安全距離から N を決める。

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
