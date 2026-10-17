# 08. launch ファイル ― 1 つのコマンドで起動する（フェーズ 5）

> **この章でわかること**
>
> - launch ファイルが何のためにあるか
> - launch ファイルの書きかたと、`setup.py` への登録のしかた
> - 1 つのタブに出るログの読みかた。Ctrl+C できれいに止める方法

## 1. 何のためか

launch（ローンチ）ファイルは、**「どのノードを、どの設定で起動するか」を書いておく台本**です。

| | 1 つずつ起動する | launch ファイル |
|---|---|---|
| タブ | 2 つ | **1 つ** |
| 打つコマンド | 4 回（タブごとに `docker exec` と `ros2 run`） | **2 回**（`docker exec` と `ros2 launch`） |
| ノイズや幅の設定 | 毎回 `--ros-args -p noise:=0.5` を打つ | **ファイルに書いておける** |
| 止めるとき | 2 つのタブで Ctrl+C | **Ctrl+C 1 回** |

本物のロボットは、ノードが 10 個、20 個とあります。launch ファイルがないと、起動するだけで大変です。

## 2. launch ファイルを書く

### 置き場所

```
src/room_robot_pkg/
├── launch/
│   └── room.launch.py      ← launch ファイル
├── room_robot_pkg/
│   ├── room_sim.py
│   └── avoider.py
├── package.xml
└── setup.py
```

### コード

コードは [room.launch.py](../../src/room_robot_pkg/launch/room.launch.py) です。

```python
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(package='room_robot_pkg', executable='room_sim', parameters=[{'noise': 0.5}]),
        Node(package='room_robot_pkg', executable='avoider', parameters=[{'hysteresis': 0.5}]),
    ])
```

| 部品 | 意味 |
|---|---|
| `generate_launch_description()` | `ros2 launch` が呼ぶ関数。**この名前は決まり** |
| `LaunchDescription([...])` | 起動するものの一覧 |
| `Node(...)` | 1 つのノード |
| `package='room_robot_pkg'` | ノードが入っているパッケージ |
| `executable='room_sim'` | ノードの名前。`ros2 run room_robot_pkg room_sim` の `room_sim` と同じ |
| `parameters=[{'noise': 0.5}]` | 設定。`--ros-args -p noise:=0.5` と同じ |

### 名前は `'...'` で囲む

ノードやパラメータの名前は、**文字**として渡します。

```python
x = 3
print(x)      # → 3        （変数 x の中身）
print('x')    # → x        （x という文字）
print(y)      # → NameError（y という変数はない）
```

`executable=room_sim` と書くと、Python は「`room_sim` という変数」を探して、見つからずに止まります。

### `parameters` は `[ ]` で囲む

| 記号 | 名前 | ここでの役わり |
|---|---|---|
| `{ }` | 辞書 | 「名前: 値」の組（`'noise': 0.5`） |
| `[ ]` | リスト | 辞書を、いくつでも並べられる入れ物 |

1 組だけでも、`[{'noise': 0.5}]` と、`[ ]` で囲みます。何組でも並べられる形に、決まっているからです（例：`[{'noise': 0.5}, {'range_max': 20.0}]`）。

## 3. `setup.py` に登録する

`ros2 launch` は、**`install/` の中**から launch ファイルを探します。`src/` の中は探しません。

```
src/room_robot_pkg/launch/room.launch.py           ← 書く所
        │  colcon build で、コピーされる（setup.py に書いたものだけ）
        ▼
install/room_robot_pkg/share/room_robot_pkg/launch/room.launch.py   ← ros2 launch が探す所
```

`colcon build` は、`setup.py` の `data_files` に書いたファイルだけを、`install/` にコピーします。

```python
from glob import glob

from setuptools import find_packages, setup
...
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.launch.py')),   ← 足した行
    ],
```

| 部品 | 意味 |
|---|---|
| `'share/' + package_name + '/launch'` | コピー先（`install/.../share/room_robot_pkg/launch`） |
| `glob('launch/*.launch.py')` | コピーするもの（`launch` フォルダーの、`.launch.py` で終わるファイル全部） |

`package.xml` には、launch を使うことを書いておきます。ほかのパソコンでパッケージを入れるとき、足りない部品が分かるようにするためです。

```xml
  <exec_depend>launch_ros</exec_depend>
  <exec_depend>ros2launch</exec_depend>
```

**`setup.py` を変えたら、ビルドが必要です。** launch ファイルの中身を変えただけなら、`--symlink-install` でビルドしてあれば、ビルドし直さなくて済みます。

```bash
colcon build --symlink-install --packages-select room_robot_pkg
```

## 4. 動かしかた

コンテナの中（`root@...:/#`）で、1 回だけ打ちます。

```bash
ros2 launch room_robot_pkg room.launch.py
```

止めるときは、Ctrl+C を 1 回押します。

## 5. ログの読みかた

1 つのタブに、次のように出ます（時刻は省略）。

```
[INFO] [launch]: All log files can be found below /root/.ros/log/...
[INFO] [launch]: Default logging verbosity is set to INFO
[INFO] [room_sim-1]: process started with pid [2171]
[INFO] [avoider-2]: process started with pid [2172]
[room_sim-1] [INFO] [...] [room_sim]: room_sim 起動。…
[room_sim-1] [INFO] [...] [room_sim]: 回り始めた: x=18.13 y=10.00 θ=3°
[room_sim-1] [INFO] [...] [room_sim]: 回るのをやめた: x=18.14 y=10.03 θ=69°
^C[WARNING] [launch]: user interrupted with ctrl-c (SIGINT)
[INFO] [avoider-2]: process has finished cleanly [pid 2172]
[INFO] [room_sim-1]: process has finished cleanly [pid 2171]
```

| 行の頭 | 意味 |
|---|---|
| `[launch]` | launch 自身の知らせ（ログの保存場所など） |
| `[room_sim-1]`、`[avoider-2]` | **どのノードの行か**。launch が付ける。ノードが増えても見分けられる |
| `process started` | ノードが起動した |
| `process has finished cleanly` | ノードが、きれいに止まった |

`avoider` は、もともとログを出さないので、起動と停止の行だけが出ます。

## 6. 予想と結果

**問題**：launch で 1 つのタブに起動すると、`room_sim` のログは、どこに、どう出るか。

| | あなたの予想 | 結果 |
|---|---|---|
| 答え | **A：`room_sim` のログだけが出る** | ✅ 行の頭に `[room_sim-1]` が付いて出る |

| 見たこと | あなたの実機 |
|---|---|
| 使ったタブ | 1 つ |
| 起動から 60 秒間の「回り始めた」 | 3 回（27.4 秒・34.0 秒・57.9 秒） |
| 最初の回転 | 3° → 69°（フェーズ 4 と同じ動き） |
| Ctrl+C のあと | 2 つのノードとも `process has finished cleanly` |

## 7. Ctrl+C で、きれいに止める

launch で起動したノードを Ctrl+C で止めると、**終わりの処理の途中で、もう一度「止まれ」の合図が届く**ことがあります。
そのままだと、終わりの処理が途中で止められて、エラーの表示（Traceback）が出ます。ROS 2 の公式サンプルのノードでも起きます。

そこで、`room_sim` と `avoider` の `main()` では、**止まると決めたら、2 回目の合図を無視**してから、後片づけをします。

```python
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    ...
    signal.signal(signal.SIGINT, signal.SIG_IGN)  # 止まると決めたら、2 回目の Ctrl+C の合図は無視する
    node.destroy_node()
    rclpy.try_shutdown()
```

| 書きかた | launch から止めたとき（試験 10 回） |
|---|---|
| 2 回目の合図を、無視しない | Traceback 9 回 |
| **2 回目の合図を、無視する** | **Traceback 0 回**（10 回とも、きれいに終了） |

`SIGINT` は、Ctrl+C を押したときにプログラムへ届く合図の名前です。`SIG_IGN` は「無視する」という意味です。

## 8. よくある書きまちがい

| 書きかた | 出るエラー | 正しくは |
|---|---|---|
| `executable=room_sim`（`'...'` がない） | `NameError: name 'room_sim' is not defined` | `executable='room_sim'` |
| `parameters={'noise': 0.5}`（`[ ]` がない） | `TypeError: 'Node' expected 'parameters' to be one of [<class 'list'>] …` | `parameters=[{'noise': 0.5}]` |
| ほかのパッケージのノードを書く（`executable='brain'`） | `executable 'brain' not found on the libexec directory …` | そのパッケージに入っているノード（`'avoider'`） |
| `setup.py` に登録していない、またはビルドしていない | `file 'room.launch.py' was not found in the share directory of package 'room_robot_pkg'` | `data_files` に 1 行足して、`colcon build` |

## まとめ

| 覚えること | 内容 |
|---|---|
| launch ファイル | 起動するノードと設定を書いておく台本。`ros2 launch パッケージ ファイル名` で起動 |
| 書きかた | `generate_launch_description()` の中で、`Node(...)` を並べる。名前は `'...'`、設定は `[{...}]` |
| 登録 | `setup.py` の `data_files` に書いて、ビルドする。`ros2 launch` は `install/` から探す |
| ログ | 行の頭の `[ノード名-番号]` で、どのノードの行か分かる |
| 止めかた | Ctrl+C 1 回。2 回目の合図を無視すると、きれいに止まる |

## 用語集

| 用語 | 意味 |
|---|---|
| launch ファイル | 複数のノードを、まとめて起動するための台本（Python のファイル） |
| `LaunchDescription` | 起動するものの一覧 |
| `data_files` | `colcon build` で `install/` にコピーするファイルの一覧（`setup.py` に書く） |
| `glob` | 「この形の名前のファイルを、全部さがす」道具 |
| `exec_depend` | 「動かすときに、これが必要」と `package.xml` に書く印 |
| `SIGINT` | Ctrl+C を押したとき、プログラムに届く合図 |
