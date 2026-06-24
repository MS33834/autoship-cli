# プラグイン公開ガイド（Plugin Publishing Guide）

本文書はプラグインを AutoShip 公式プラグインストアに提出する方法を説明します。

## 1. 公開フロー概要

1. [examples/custom-plugin](https://github.com/MS33834/autoship-cli/tree/main/examples/custom-plugin) をテンプレートとしてプラグインを開発。
2. ローカルでテストを完了し、少なくとも `ruff check`、`pytest`、AutoShip の `plugin verify` にパスすることを確認。
3. プラグインパッケージの sha256 チェックサムを生成し、オプションで PGP 署名を生成。
4. パッケージを PyPI（または GitHub Release など pip でインストール可能な場所）に公開。
5. 本リポジトリに PR を提出し、`registry/plugins.json` にプラグインエントリを追加。
6. メンテナーのレビュー通過後にマージされ、プラグインは自動的に[プラグインレジストリ Web UI](https://ms33834.github.io/autoship-cli/registry/) に表示されます。

## 2. メタデータ形式

各プラグインエントリは JSON オブジェクトである必要があり、フィールドは以下の通りです：

| フィールド | 型 | 必須 | 説明 |
|---|---|---|---|
| `name` | string | はい | プラグインの一意識別子。小文字、数字、ハイフンのみ許可。 |
| `package` | string | はい | pip インストールパッケージ名（例：`autoship-commit-sign`）。 |
| `module` | string | はい | Python インポートパス（例：`autoship_commit_sign.plugin`）。 |
| `version` | string | はい | セマンティックバージョン番号（例：`1.2.3`）。 |
| `description` | string | はい | 一文の説明。 |
| `trust_level` | string | はい | `builtin` / `verified` / `community` / `untrusted`。 |
| `entry_point` | string | はい | プラグインエントリ（例：`autoship_commit_sign.plugin:CommitSignPlugin`）。 |
| `hooks` | string[] | はい | サポートするフック（例：`["pre_commit", "post_commit"]`）。 |
| `publisher` | object | はい | `{ id, verified, url }`。`verified` は管理者が確認する必要があります。 |
| `maintainer` | string | はい | メンテナーの氏名と連絡先メールアドレス。 |
| `license` | string | はい | SPDX ライセンス識別子。 |
| `sha256` | string | 推奨 | 公開パッケージ（wheel）の sha256 チェックサム。`verified` プラグインは必須。 |
| `signature` | string | 推奨 | AutoShip 公式秘密鍵で sha256 に base64 エンコードした署名。`verified` プラグインは必須。 |
| `permissions` | object | はい | `{ filesystem, network, shell, git, env }`。プラグインが必要とする権限を宣言。 |
| `categories` | string[] | はい | カテゴリタグ（例：`["security", "git"]`）。 |
| `tags` | string[] | いいえ | 検索キーワード。 |
| `homepage` | string | 推奨 | プラグインのホームページ URL。 |
| `source_url` | string | 推奨 | ソースコードリポジトリ URL。 |
| `downloads` | integer | いいえ | ダウンロード数。レジストリが管理。 |
| `rating` | object | いいえ | `{ score, count }`。レジストリが管理。 |
| `audit_status` | string | はい | `pending` / `approved` / `rejected`。新規提出は `pending`、管理者レビュー後に更新。 |

完全な例：

```json
{
  "name": "commit-sign",
  "package": "autoship-commit-sign",
  "module": "autoship_commit_sign.plugin",
  "version": "1.0.0",
  "description": "自動で生成されたコミットに署名を追加。",
  "trust_level": "verified",
  "entry_point": "autoship_commit_sign.plugin:CommitSignPlugin",
  "hooks": ["pre_commit"],
  "publisher": {
    "id": "alice-chen",
    "verified": true,
    "url": "https://github.com/alice-chen"
  },
  "maintainer": "Alice Chen <alice@example.com>",
  "license": "MIT",
  "sha256": "a3f5c8e2b4d6f7a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5",
  "signature": "base64-encoded-pgp-signature",
  "permissions": {
    "filesystem": "read-only",
    "network": false,
    "shell": false,
    "git": true,
    "env": []
  },
  "categories": ["security", "git"],
  "tags": ["gpg", "sign", "commit"],
  "downloads": 0,
  "rating": { "score": 0.0, "count": 0 },
  "homepage": "https://github.com/example/autoship-commit-sign",
  "source_url": "https://github.com/example/autoship-commit-sign",
  "audit_status": "approved"
}
```

## 3. チェックサムと署名の要件

### 3.1 sha256 の計算

```bash
python -m build --wheel
sha256sum dist/autoship_commit_sign-1.0.0-py3-none-any.whl
```

出力された 64 桁の 16 進数文字列を `registry/plugins.json` の `sha256` フィールドに書き込みます。

### 3.2 署名の生成（verified プラグイン）

`trust_level: verified` のプラグインのみ署名が必要です。管理者は AutoShip 公式 PGP 秘密鍵で sha256 文字列に署名します：

```bash
echo -n "<sha256-hex>" | gpg --armor --detach-sign --output signature.asc
# base64 エンコードした署名の内容を registry/plugins.json に書き込み
base64 -w 0 signature.asc
```

プラグインが `verified` レベルを申請しない場合は、`trust_level: community` を維持し、`sha256`/`signature` は記入しないでください。

## 4. Verified Publisher 認証フロー

`verified` 信頼レベルは AutoShip チームがレビューしたパブリッシャーとプラグインを識別するために使用されます。申請フローは以下の通りです：

### 4.1 パブリッシャー資格

申請者は以下を満たす必要があります：

- 実名または活動的な組織アカウントでプラグインをメンテナンスしている。
- プラグインのソースコードリポジトリが公開されており、少なくとも 3 か月間継続してメンテナンスされているか、2 バージョン以上をリリースしている。
- 過去に重大なセキュリティインシデントや悪意ある行為の記録がない。

### 4.2 認証申請の提出

GitHub で issue を作成し、**Verified Publisher Application** テンプレートを選択して以下を提供：

- パブリッシャー ID（GitHub ユーザー名または組織名）とホームページ URL。
- 公開済みまたはメンテナンス予定のプラグインリスト。
- 連絡先（公開メールまたは組織メール）。

### 4.3 審査基準

メンテナーは以下の基準で審査します：

| 次元 | 要件 |
|---|---|
| 身元の真実性 | パブリッシャーの身元が検証可能で、ホームページまたは組織のプロフィールが完全であること。 |
| プラグイン品質 | コードが `ruff check` と `pytest` にパスし、ドキュメントと例が完全であること。 |
| セキュリティコンプライアンス | 権限宣言と実際の動作が一致し、過度な `network`/`shell` の申請がないこと。 |
| 継続的メンテナンス | 直近 3 か月にアクティブなコミットまたはバージョンリリースがあること。 |

### 4.4 認証結果

- 通過時：`registry/publishers.json` にパブリッシャー情報を登録し、そのプラグインに `publisher.verified = true` のマークを許可。
- 不通過時：issue で理由を返信し、資料を補完後に再申請可能。
- 認証取り消し：パブリッシャーが後にセキュリティインシデントを起こした場合、長期間メンテナンスされていない場合、または虚偽の情報を提供した場合、メンテナーは `verified` ステータスを取り消すことができます。

## 5. PR テンプレート

`registry/plugins.json` にプラグインを提出する際、PR の説明に以下の内容を記入してください：

```markdown
## Plugin Submission

- **Plugin name**:
- **PyPI package name**:
- **Source URL**:
- **Requested trust level**: community / verified
- **sha256 of wheel**:
- **Signature** (if verified):

## Checklist

- [ ] プラグインのソースコードリポジトリに `README.md`、オープンソースライセンス、使用例が含まれている。
- [ ] プラグインが少なくとも `pytest` と `ruff check` にパスしている。
- [ ] `autoship plugin verify <package>` でインストールを検証済み。
- [ ] `permissions` を記入し、権限範囲がプラグインの実際の必要を超えていない。
- [ ] wheel の sha256 チェックサムを提供済み（verified プラグインは署名も必要）。
- [ ] [プライバシーポリシー](./privacy.md) を読み、同意している。
```

## 6. 審査と公開

1. 自動チェック：CI が JSON スキーマ、sha256 形式、必須フィールドを検証。
2. セキュリティ審査：メンテナーが `permissions`、`network`、`shell` などの高感度宣言を審査。
3. 体験審査：ドキュメント、エラーメッセージ、使用例が完全であることを確認。
4. マージ後：registry-web が自動デプロイされ、ユーザーは `autoship plugin search <name>` でプラグインを見つけられます。

## 7. 更新と取り下げ

- **バージョン更新**：新規 PR を提出し、`version`、`sha256`、`signature` を更新。
- **プラグインの取り下げ**：`audit_status` を `rejected` に変更し理由を説明。重大なセキュリティ問題のあるプラグインはレジストリから削除されます。

## 8. 関連リソース

- [プラグイン開発例](https://github.com/MS33834/autoship-cli/tree/main/examples/custom-plugin)
- [プラグインレジストリスキーマ](https://github.com/MS33834/autoship-cli/blob/main/registry/schema.json)
- [プラグインレジストリ Web UI](https://ms33834.github.io/autoship-cli/registry/)
