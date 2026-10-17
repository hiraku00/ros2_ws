# CLAUDE.md

ROS 2 (Jazzy) の学習用ワークスペース。ROS 2 初心者の学習を、一緒に進める。

**まず [docs/handoff.md](docs/handoff.md) を読むこと。** 経緯、現状、次にやること、環境、進め方が、すべて書いてある。解説は `docs/basics/`（入門編）と `docs/room-robot/`（ステップ 2）に分けてある。

## 環境（要点）

- Mac（Apple Silicon）の Docker コンテナ `ros2`（`ros:jazzy`）の中で ROS 2 を動かす。このフォルダは、コンテナの `/root/ros2_ws` と共有されている。
- Claude は、Bash ツールの `docker exec ros2 bash -c '...'`（`-it` なし）で、コンテナ内のコマンドを実行する。ターミナルアプリへの入力はできない。
- コマンドの前に `source /opt/ros/jazzy/setup.bash && source /root/ros2_ws/install/setup.bash` が必要。
- Docker Desktop やコンテナが止まっていることがある（`open -a Docker`、`docker start ros2`）。
- **`pkill -f` は使わない**（コンテナのシェルを巻き込んで停止させたことがある）。PID を指定して `kill` する。テスト用のノードは、`ROS_DOMAIN_ID` を別の値にして、学習者のノードと分ける。

## 進め方（要点）

- すべて**日本語**。中学生でも分かるように、図・表・たとえ話・用語の説明を入れる。
- **学習者が自分でコードを書き、Claude がレビューする。** 答えを先に書かず、ヒント → 学習者が書く → 確認の順にする。
- コードを触る前に**予想**を書いてもらい、実測と比べる。
- 学習者が貼ったログは、結論の前に、ファイルの中身や動いているプロセスと照らして確認する（保存しただけでは、動いているノードは変わらない）。
- 説明に使う数字は、模擬実験や実測で裏づける。間違いに気づいたら、すぐ訂正する。
- お題は 1 つずつ。返信を長くしすぎない。
- 予想問題や新しい概念は、**何のためか・条件・単位**を先に説明してから出す。学習者の「なぜ？」には、先に答える。
- 文書では、高校以上の数学を本文で使わない（図と具体的な数字で説明する）。図は計算から作る（入門編は `tools/make_basics_figures.py`、ステップ 2 は `tools/make_room_robot_figures.py`）。

## Git / GitHub（要点）

- 学習者が「GitHub に上げて」と言ってから行う。流れは、ブランチ作成 → コミット → push → PR → `gh pr merge --merge --delete-branch` → `main` を最新に。
- コミットは `feat:` / `fix:` / `docs:` などの接頭辞 + 日本語。本文は **【背景】【変更内容】【検証内容】**。検証内容には、実際にやったことだけを書く。コードとドキュメントは、コミットを分ける。詳しい書式は [docs/handoff.md の 4 章](docs/handoff.md#4-git--github-の流儀)。
- コミット前に `git status` と `git diff` を確認し、生成物（`build/` `install/` `log/` `output/`）や機密情報（`.env`、API キー）を含めない。`.gitignore` を更新する。
- README と `docs/` を、変更に合わせて更新する。README は入口に絞り、詳細は `docs/` へ。文書内のリンクの実在を確認する。
- リポジトリは private。公開範囲は、勝手に変えない。
