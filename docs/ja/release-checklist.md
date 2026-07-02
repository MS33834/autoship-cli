# リリース前チェックリスト（Release Checklist）

本チェックリストは AutoShip-CLI メンテナーが正式版またはプレリリース版を完成させるためのガイドです。リリース前に少なくとも 2 名のメンテナーがクロスレビューし、すべての項目にチェックを入れる必要があります。

---

## 1. バージョンと変更ログ

- [ ] バージョン番号が [SemVer](https://semver.org/lang/ja/) に従っていることを確認。
  - 正式版：`MAJOR.MINOR.PATCH`（例：`1.0.0`）。
  - プレリリース版：`-alpha.N`、`-beta.N`、`-rc.N` を付加（例：`1.1.0-rc.1`）。
- [ ] ルートディレクトリの [`CHANGELOG.md`](https://github.com/MS33834/autoship-cli/blob/main/CHANGELOG.md) は GitHub Release 作成後に Release ワークフローが自動生成します（`scripts/release_changelog.py` → `update-changelog` job）。リリース後 `main` に戻り、自動書き込みされたバージョンセクションを確認。
  - バージョンセクション形式：`Added` / `Changed` / `Deprecated` / `Removed` / `Fixed` / `Security` サブセクション、リリース日（UTC+8）を明記。
- [ ] ドキュメントの [`changelog.md`](./changelog.md)（zh/en/ja の3言語）を同期更新。
- [ ] `pyproject.toml` の `project.version` が対象バージョンと一致することを確認。
- [ ] `autoship-sdk/pyproject.toml` のバージョン番号と依存制約が同期更新されていることを確認。

## 2. コード品質ゲート

ローカルで実行してパス：

```bash
uv run ruff check src tests dogfood benchmarks
uv run ruff format --check src tests dogfood benchmarks
uv run pyright
uv run pytest -q
uv run pytest autoship-sdk/tests -q
uv run bandit -r src -ll
uv run pip-audit --desc
```

- [ ] ruff lint パス
- [ ] ruff format チェックパス
- [ ] pyright 型チェックパス
- [ ] autoship ユニットテストパス（カバレッジ ≥ 85%）
- [ ] autoship-sdk テストパス
- [ ] bandit セキュリティスキャンで中高危険度問題なし
- [ ] pip-audit 依存関係脆弱性スキャンで未修正問題なし

## 3. 統合とパフォーマンステスト

```bash
uv run python dogfood/dogfood.py
uv run python benchmarks/benchmark.py
```

- [ ] dogfood スモークテストパス
- [ ] benchmark 回帰テストパス、パフォーマンス退化なし

## 4. ドキュメントとウェブサイト

- [ ] コマンドリファレンスドキュメントが実際の CLI の動作と一致。
- [ ] `docs/index.md` と `README.md` のインストール/クイックスタート手順が再現可能。
- [ ] `docs/privacy.md` と `docs/telemetry.md` のデータ収集範囲が正確。
- [ ] MkDocs サイトをローカルプレビュー：`uv run mkdocs serve`、ナビゲーションとリンクが正常か確認。
- [ ] 公式サイト `website/` のビルドパス：`cd website && npm install && npm run build`。

## 5. 署名鍵と資格情報

- [ ] `verified` プラグイン署名用の PGP 秘密鍵が有効で期限切れでない。
- [ ] PyPI/TestPyPI 公開トークンまたは Trusted Publishing 設定が有効。
- [ ] GitHub Actions 環境の `pypi` / `testpypi` の承認ルールが設定済み。

## 6. リリース実行

### 6.1 Git Tag の作成

```bash
git switch main
git pull origin main
git tag -a v<X.Y.Z> -m "Release v<X.Y.Z>"
git push origin v<X.Y.Z>
```

- [ ] tag 名がバージョン番号と一致（例：`v1.0.0`）。
- [ ] tag が `main` ブランチの最新コミットを指している。

### 6.2 Release ワークフローのトリガー

tag の push が自動的に [`.github/workflows/release.yml`](https://github.com/MS33834/autoship-cli/blob/main/.github/workflows/release.yml) をトリガー：

- [ ] `pypi` / `testpypi` の自動ルーティングが正しい（プレリリース tag は TestPyPI に送信）。
- [ ] `autoship` と `autoship-sdk` の wheel アップロード成功。
- [ ] マルチプラットフォームバイナリと SHA256 チェックサムの生成成功。
- [ ] GitHub Release Notes が自動生成され、バイナリアーティファクトを含む。

## 7. リリース後の検証

- [ ] PyPI/TestPyPI ページに新バージョンが表示される。
- [ ] `pip install autoship==<X.Y.Z>` で正常にインストール可能。
- [ ] GitHub Release のバイナリをダウンロードし、`autoship --help` と `autoship doctor` が正常に実行できる。
- [ ] 公式ドキュメントサイト `https://ms33834.github.io/autoship-cli/docs` が更新されている。
- [ ] 公式サイト `https://ms33834.github.io/autoship-cli/` が更新されている（website 変更がある場合）。

## 8. セキュリティアドバイザリとコミュニケーション

本リリースにセキュリティ修正が含まれる場合：

- [ ] `SECURITY.md` でサポートバージョンと修正説明を更新。
- [ ] GitHub Security Advisory でセキュリティアドバイザリを公開。
- [ ] コミュニティチャンネル（Discussions、Twitter/X、Zhihu など）で情報を同期公開。

---

## 過去のリリース記録

| バージョン | リリース日 | リリース担当者 | 備考 |
|------|----------|--------|------|
| 1.0.0 | 2026-06-19 | AutoShip Team | 初の安定版 |
| 1.0.0-rc.1 | 2026-06-19 | AutoShip Team | 初の RC |
| 0.2.0-beta.1 | 2026-06-18 | AutoShip Team | Beta プレビュー |
| 0.1.0 | 2026-06-18 | AutoShip Team | 初期バージョン |
