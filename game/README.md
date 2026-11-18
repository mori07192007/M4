# Integrated run

みんなの担当ファイルをまとめて起動するための入口です。

## 起動

```bash
python -m pip install -r ../requirements.txt
python -m game.main
```

## 担当の置き換え

- `game/player/player_stub.py` は仮プレイヤーです（描画なし）。
  友達のプレイヤー実装ができたら、このStubを差し替えるか、main.pyのimportを変更してください。
- 敵は `game/enemies/virus_enemy.py` に分離しています。
