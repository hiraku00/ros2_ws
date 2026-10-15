# 02. 壁に向かって走るロボットを、頭脳ノードで救う

「センサー → 判断 → 動作」の流れを、2 つのノードで作る演習です。
実物のロボットは不要で、文字で動きを眺めます。

## 1. 登場するもの

| ノード | たとえ | 仕事 | コード |
|---|---|---|---|
| `sim_robot` | 体 | 40 マスの廊下を走る。壁までの距離を測って知らせ、指示どおりに動く | [sim_robot.py](../src/my_first_pkg/my_first_pkg/sim_robot.py) |
| `brain` | 頭脳 | 壁までの距離を見て、「どう動くか」を決めて知らせる | [brain.py](../src/my_first_pkg/my_first_pkg/brain.py) |

| トピック | 流れる向き | 中身 |
|---|---|---|
| `distance` | sim_robot → brain | 壁までの距離（数値） |
| `cmd` | brain → sim_robot | 指示（`FORWARD` / `SLOW` / `STOP` / `TURN`） |

```
sim_robot ──── distance（壁までの距離）────→ brain
          ←─── cmd（どう動くか）──────────
```

2 本の掲示板で、**輪**になっています。1 周するたびに、ロボットは 1 歩動きます。

1. sim_robot が、今の壁までの距離を `distance` に書く
2. brain がそれを読み、指示を決めて `cmd` に書く
3. sim_robot が指示を読み、次の 1 歩を動く
4. 1 に戻る

## 2. brain の判断ルール

| 壁までの距離 | 指示 | ロボットの動き |
|---|---|---|
| 8.0 以上 | `FORWARD` | 1 歩 0.5 進む |
| 3.0 以上 8.0 未満 | `SLOW` | 1 歩 0.2 進む（ゆっくり） |
| 3.0 未満になって最初の 2 秒 | `STOP` | 止まる |
| 3.0 未満になって 2 秒たったあと | `TURN` | 向きを反対にする |

```
壁 ◀── 0 ────────── 3.0 ──────────── 8.0 ───────────────▶ 遠い
        STOP→TURN      SLOW              FORWARD
```

「3.0」と「8.0」は、パラメータ（`turn_distance`、`slow_distance`）です。実行中に変えられます。

### 境界のそばで、判断が揺れないための工夫

センサーにノイズが乗ると、境界（3.0 と 8.0）のそばで、判断が行ったり来たりします（チャタリング）。
そこで、**一度入った状態は、境界より少し先まで続ける**ようにしています（ヒステリシス、`hysteresis` = 1.0）。

| 判断 | 入る線 | 出る線 |
|---|---|---|
| `SLOW` → `STOP` | 3.0 | 4.0 |
| `FORWARD` → `SLOW` | 8.0 | 9.0 |

詳しくは [03. ノイズ・チャタリング・フィルタ](03-noise-and-filters.md) を読んでください。

## 3. 動かし方

[README](../README.md#実行方法) の手順でコンテナに入り、ターミナルを 2 つ使います。

```bash
# タブ1: ロボット（体）
ros2 run my_first_pkg sim_robot
# タブ2: 頭脳
ros2 run my_first_pkg brain
```

終わったら両方で Ctrl+C を押します。プロセスが残ると、次の実行に干渉します。

## 4. 実験

### 実験①：頭脳なし

sim_robot だけを動かします。`cmd` の初期値は `FORWARD` なので、ロボットは前進し続け、右端の壁にぶつかったまま止まります。

### 実験②：頭脳あり

brain も動かします。壁の手前で `SLOW` → `STOP`（約 2 秒）→ `TURN` となり、廊下を往復します。

```
SLOW … SLOW  STOP STOP STOP STOP STOP STOP STOP STOP STOP STOP  TURN  FORWARD …
            └──────── 約 2 秒 ────────┘
```

どちらのノードも、相手のことを知りません。`distance` と `cmd` という名前だけでつながっています。

### 実験③：頭脳の性格を、実行中に変える

```bash
ros2 param set /brain turn_distance 10.0
```

壁のかなり手前で止まるようになります（慎重な性格）。`1.0` にすると、ぎりぎりまで突っ込みます。
`slow_distance` より小さい値にしてください。

### 実験④：やりとりをのぞく

```bash
ros2 topic echo /cmd
```

### 実験⑤：人間が頭脳の代わりになる

brain を止めてから、手で指示を出します。

```bash
ros2 topic pub /cmd std_msgs/msg/String "{data: TURN}" --once
```

### 実験⑥：頭脳が故障したら

brain を Ctrl+C で止めると、ロボットは**最後に受けた指示のまま**走り続けます。
本物のロボットで、安全のための監視や緊急停止が重要な理由です。

## 5. STOP の 2 秒を数える仕組み

brain は「いつから STOP を出し始めたか」を覚えています。**覚える変数を持つノード**の例です。

```python
if self.stop_started is None:        # 初めて近づいた
    self.stop_started = now          # 今の時刻を覚える
if now - self.stop_started > 2.0:    # 2 秒たったか？
    cmd = 'TURN'
else:
    cmd = 'STOP'
```

壁から離れたら、覚えた時刻を忘れます（`self.stop_started = None`）。
忘れないと、**反対側の壁で「もう 2 秒たっている」と誤判断して、STOP を出さずにいきなり TURN** になります。

## 6. 本物のロボットとの対応

| この演習 | 実機の ROS 2 |
|---|---|
| `distance` | `/scan`（LiDAR の距離データ） |
| `cmd` | `/cmd_vel`（走行指令） |
| `brain` | 障害物回避・経路計画（Nav2 など） |
| `sim_robot` | モーターとタイヤ |

次は [03. ノイズ・チャタリング・フィルタ](03-noise-and-filters.md) へ。
