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

## 4. ログの見方

```
|..............>..........................| 壁まで= 9.5  指示=FORWARD
```

| 部分 | 意味 |
|---|---|
| `>` / `<` | ロボットの位置と向き（右向き／左向き） |
| 壁まで | 向いている方向の壁までの**真の**距離（ノイズなし） |
| 指示 | brain から届いた最新の指示 |

「壁まで」にはノイズが入っていないので、brain の判断（ノイズ込みの値）とは、少しずれて見えることがあります。

## 5. 実験のしかた

| ポイント | 理由 |
|---|---|
| 先に予想を書いてから動かす | 結果との差が、いちばん勉強になる |
| 1 回のログで結論を出さない | ノイズはランダムなので、2〜3 周見る |
| 一度に 1 つだけ変える | 何が効いたのか分からなくなる |
| 変えた値は、実験後に元へ戻す | 次回の起動時に、意図しない設定で動く |
