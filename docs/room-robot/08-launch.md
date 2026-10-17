# 08. launch ファイル ― 1 つのコマンドで起動する（フェーズ 5）

> **この章でわかること**
>
> - launch ファイルが何のためにあるか
> - launch ファイルの書きかたと、`setup.py` への登録のしかた
> - 起動するときに、`noise:=1.0` のように値を変える方法（引数）
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

まず、基本の形です（引数を足した、いまの形は 5 章）。コードは [room.launch.py](../../src/room_robot_pkg/launch/room.launch.py) にあります。

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

## 5. 引数：起動するときに、値を変える

### 何のためか

基本の形では、`noise` の 0.5 を、ファイルの中に書きこんでいます。ノイズを 1.0 にして実験するたびに、ファイルを書きかえて、あとで戻すのは、手間です。
**launch の引数**を使うと、起動するときに、コマンドで値を渡せます。

```bash
ros2 launch room_robot_pkg room.launch.py noise:=1.0
```

| | 基本の形 | 引数を使う |
|---|---|---|
| ノイズ 1.0 で試す | ファイルを書きかえる | `noise:=1.0` を付けて起動する |
| いつもの値（0.5）で動かす | そのまま | 何も付けずに起動する |
| ファイル | 実験のたびに変わる | 変わらない |

`:=` は、「この名前に、この値を入れる」という印です（`--ros-args -p noise:=0.5` の `:=` と同じです）。

### コード

```python
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('noise', default_value='0.5'),          # ① 宣言する
        DeclareLaunchArgument('hysteresis', default_value='0.5'),
        Node(package='room_robot_pkg', executable='room_sim',
             parameters=[{'noise': LaunchConfiguration('noise')}]),   # ② 使う
        Node(package='room_robot_pkg', executable='avoider',
             parameters=[{'hysteresis': LaunchConfiguration('hysteresis')}]),
    ])
```

| 部品 | 意味 |
|---|---|
| `DeclareLaunchArgument('noise', default_value='0.5')` | ① 「引数 `noise` を受け付けます。何も渡されなければ `'0.5'` にします」と宣言する。`'0.5'` を**既定値（デフォルト）**と呼ぶ |
| `LaunchConfiguration('noise')` | ② 引数 `noise` の値を、ここで使う |

既定値は、`'0.5'` のように、**文字（`'...'`）**で書きます。

### 動かして確かめる

| 起動のしかた | `noise` | `hysteresis` |
|---|---|---|
| 何も付けない | **0.5**（既定値） | 0.5 |
| `noise:=1.0` | **1.0** | 0.5（付けていないので、既定値のまま） |
| `hysteresis:=1.0` | 0.5 | **1.0** |
| `noise:=1.0 hysteresis:=1.0` | **1.0** | **1.0** |

受け付ける引数の一覧は、次のコマンドで見られます。

```bash
ros2 launch room_robot_pkg room.launch.py --show-args
```

### 値が決まる順番

あとから渡したものほど、強くなります。

```
① room_sim のコードの既定値（0.0）
        ↓ 上書き
② launch ファイルの既定値（0.5）
        ↓ 上書き
③ 起動するときの引数（noise:=1.0）
        ↓ 上書き
④ 動いている最中の ros2 param set
```

**問題**：何も付けずに起動すると、`room_sim` の `noise` はいくつか。

| | あなたの予想 | 結果 |
|---|---|---|
| 答え | **B：0.5**（launch に書いた既定値） | ✅ 0.5（コードの 0.0 は、使われない） |

### 小数点を付ける

```
noise:=1      →  InvalidParameterTypeException: Trying to set parameter 'noise' to '1' of type 'INTEGER', expecting type 'DOUBLE'
noise:=1.0    →  動く
```

`1` は**整数**、`1.0` は**小数**として読まれます。`room_sim` の `noise` は、はじめに `0.0`（小数）で作ってあるので、整数は受け付けません。**小数点を付けて、`noise:=1.0` と書きます。**

### 引数で実験する：ノイズを 2 倍にする

```bash
ros2 launch room_robot_pkg room.launch.py noise:=1.0
```

幅は 0.5 のままです。計算（100 回ずつ、60 秒）と、実機の結果です。

| | ノイズ 0.5 | ノイズ 1.0（計算） | ノイズ 1.0（実機） |
|---|---|---|---|
| 60 秒の「回り始めた」回数 | 3.0 回 | **3.5 回**（3〜4 回） | 3 回 |
| 最初に回り始めた x | 18.12 | **17.66** | 17.62 |
| 最初の回転 | 72° | 67° | 3° → 66° |

| | あなたの予想 | 結果 |
|---|---|---|
| 回数 | C：減る | **A：ほとんど変わらない**（3.0 → 3.5 回） |

ノイズを 2 倍にしても、回数はほとんど変わりませんでした。変わったのは、**どこで回り始めるか**です（壁まで 1.88 m → 2.34 m）。

| ノイズを 2 倍にすると | 起きたこと |
|---|---|
| **かたより**（最小値が近く見える量）が、約 2 倍になる | 回り始めるのが早くなった（x = 18.12 → 17.66） |
| **ぶれ**（判断に使う値のゆれ） | 最小値を 5 回平均しているので、もともと小さい。2 倍になっても、幅 0.5 の中に収まる → 回数は、ほぼ同じ |

最小値は、ノイズが大きいほど、近い側にずれます（[06 の 2 章](06-noise-and-filter.md#2-最小値はノイズで近い側にずれる)）。

## 6. ログの読みかた

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

## 7. 予想と結果

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

## 8. Ctrl+C で、きれいに止める

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

## 9. よくある書きまちがい

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
| 引数 | `DeclareLaunchArgument` で宣言し、`LaunchConfiguration` で使う。`noise:=1.0` のように、起動するときに値を変える。小数は `1.0` と書く |
| 止めかた | Ctrl+C 1 回。2 回目の合図を無視すると、きれいに止まる |

## 用語集

| 用語 | 意味 |
|---|---|
| launch ファイル | 複数のノードを、まとめて起動するための台本（Python のファイル） |
| `LaunchDescription` | 起動するものの一覧 |
| 引数（launch） | 起動するときに、`名前:=値` で渡す設定 |
| 既定値（デフォルト） | 何も渡されなかったときに使う値 |
| `data_files` | `colcon build` で `install/` にコピーするファイルの一覧（`setup.py` に書く） |
| `glob` | 「この形の名前のファイルを、全部さがす」道具 |
| `exec_depend` | 「動かすときに、これが必要」と `package.xml` に書く印 |
| `SIGINT` | Ctrl+C を押したとき、プログラムに届く合図 |
