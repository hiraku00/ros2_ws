# 04. つまずきやすい点と対処

この演習で実際に起きた問題と、その対処をまとめます。

## 1. 環境のエラー

| 症状 | 原因 | 対処 |
|---|---|---|
| `failed to connect to the docker API ... docker.sock` | Docker Desktop が起動していない | Docker Desktop を起動し、メニューバーにクジラが出るまで待つ。そのあと `docker start ros2` |
| `container ... is not running` | コンテナが止まっている | `docker start ros2` |
| `ros2: command not found` | `source` していない、または Mac 側で実行している | プロンプトが `root@...:/#` か確認。コンテナ内で `source /opt/ros/jazzy/setup.bash` |
| `cd: /root/ros2_ws does not exist` | Mac 側で実行している | `docker exec -it ros2 bash` でコンテナに入ってから実行 |
| `Unsupported use of '='`（fish） | Mac 側（fish）で bash 用の `source` を実行した | コンテナ（bash）の中で実行する |
| `Node not found`（`ros2 param set`） | 対象のノードが起動していない | `ros2 node list` で、`/brain` があるか確認 |

### コンテナに入るたびの `source` を省く

コンテナの中で、1 回だけ実行します。

```bash
echo 'source /opt/ros/jazzy/setup.bash' >> ~/.bashrc
echo 'source /root/ros2_ws/install/setup.bash' >> ~/.bashrc
```

これは**コンテナ内の bash** の設定です。Mac の fish とは別物です。コンテナを削除する（`docker rm`）と消えます。

## 2. 「コードを変えたのに、動きが変わらない」

いちばん多いつまずきです。

| 原因 | 説明 |
|---|---|
| **ノードを再起動していない** | 動いているプログラムは、起動した時点のコードのまま動き続ける。保存しても、動いているノードには反映されない |
| `--symlink-install` の意味 | 「ビルドし直さなくていい」という意味。「再起動しなくていい」ではない |

確認方法：

```bash
ps -eo lstart,args | grep "[l]ib/my_first_pkg"
```

プロセスの起動時刻が、ファイルの保存時刻より前なら、古いコードで動いています。
**Ctrl+C で止めて、`ros2 run ...` をやり直します。** `sim_robot` と `brain` は、別々のプロセスなので、変えた方を再起動します。

### Python のコードを変えたあとのビルド

```bash
cd /root/ros2_ws
colcon build --symlink-install --packages-select my_first_pkg
source install/setup.bash
```

`--symlink-install` を付けて 1 回ビルドすれば、以降は Python を保存するだけで済みます（再起動は必要）。
`setup.py` の `entry_points` を変えたときは、ビルドし直します。

## 3. 「ロボットが勝手に動く」「頭脳がいないのに SLOW が出る」

前の実験のプロセスが、裏で残っています。

```bash
ps -eo pid,args | grep "[l]ib/my_first_pkg"
```

残っているものは、Ctrl+C で止めます。

> **注意：`pkill -f my_first_pkg` は使わないでください。** コマンドの文字列にも `my_first_pkg` が含まれるため、
> 自分自身やコンテナのシェルまで巻き込んで、コンテナが停止することがあります。

## 4. コードを書くときの落とし穴

実際に書き間違えた例です。

| 書き方 | 起きること | 正しくは |
|---|---|---|
| `x = (cond) ? a : b` | `SyntaxError`（`? :` は Python にない。C や JavaScript の書き方） | `x = a if cond else b` |
| `on_distance` の先頭で `self.slowing = False` | メッセージのたびに `False` に戻り、状態を覚えられない | 覚えたい変数は `__init__` で 1 回だけ作る |
| `if self.slowing is not None` | `True` / `False` は `None` ではないので、常に真になる | `if self.slowing` |
| `self.stop_started = now` を、`None` のままにしてしまう | `None` と数値の引き算で `TypeError`、brain が落ちる | 初めて近づいたときに `now` を入れる |
| 判断に使う値が、`msg.data` と `dist` で混ざる | 一部の判断だけ、ノイズに弱いまま | 判断に使う値は、1 つの変数に統一する |

`is not None` は、**`None` かどうかで状態を表す変数**（`self.stop_started`）にだけ使います。

### 書いたコードの構文だけを素早く確かめる

```bash
python3 -c "import ast; ast.parse(open('src/my_first_pkg/my_first_pkg/brain.py').read()); print('ok')"
```

文法の間違いは、これで分かります。ただし、「動きが正しいか」までは分かりません（上の `is not None` の例は、文法は正しい）。

## 5. 実験の結果が、おかしいとき

| 症状 | 原因 | 対処 |
|---|---|---|
| 同じ設定なのに、結果が 2 倍に混ざる | 同じトピックに、複数の `brain` が書いている | `ps -eo pid,lstart,args \| grep "[l]ib/my_first_pkg"` で、残っているプロセスを探し、PID を指定して `kill` する |
| テスト用スクリプトの結果が、手動の結果と合わない | テストと手動のノードが、同じ通信グループにいる | テストは `ROS_DOMAIN_ID` を別の値にして、分ける（`tools/probe_brain_slow_band.py` は、そうしている） |
| 確率の低い現象（約 18%）が、1 回の壁で出ない | 出なかっただけで、直ったとは限らない | 数百回まとめて試す（`tools/` のスクリプト）、または、対策の有無を並べて比べる |

## 6. ログの見方

```
|..............>..........................| 壁まで= 9.5  指示=FORWARD
```

| 部分 | 意味 |
|---|---|
| `>` / `<` | ロボットの位置と向き（右向き／左向き） |
| 壁まで | 向いている方向の壁までの**真の**距離（ノイズなし） |
| 指示 | brain から届いた最新の指示 |

「壁まで」にはノイズが入っていないので、brain の判断（ノイズ込みの値）とは、少しずれて見えることがあります。

## 7. 実験のしかた

| ポイント | 理由 |
|---|---|
| 先に予想を書いてから動かす | 結果との差が、いちばん勉強になる |
| 1 回のログで結論を出さない | ノイズはランダムなので、2〜3 周見る |
| 一度に 1 つだけ変える | 何が効いたのか分からなくなる |
| 変えた値は、実験後に元へ戻す | 次回の起動時に、意図しない設定で動く |
