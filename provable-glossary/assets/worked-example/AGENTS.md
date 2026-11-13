This codebase is yours: what it's for and how it's built are your call, and you'll keep building on it.

用語集の正本は `Glossary/*.lean`。検査は `just check`、文書の再生成は `just generate`。
概要は README.md、結果と限界は docs/findings.md。
実験は `experiments/<名前>/` に置き、手順 (`protocol.md`) を先にコミットしてから実行する。
生成物は `docs/generated/` にあり、手では編集しない。`Glossary/*.lean` を直して `just generate` を実行する。
スキルの正本は `skills/provable-glossary/`。共通のファイルを変えたら `just skill-sync` を実行する。
