# Agents — Usage credits

Omarchy標準Agentsを基に、Claude追加利用の月間消費率表示と英語・日本語対応を追加した実験的なコミュニティ版です。

[English](README.md) · [ライセンス](LICENSE) · [出典](NOTICE.md)

## 対応環境

初版0.1.0は、手元のOmarchy `4.0.0.alpha` に含まれるAgentsを基にしています。元ファイルのハッシュは `UPSTREAM.json` に記録しています。新しいOmarchyではAgentsの構造や共通翻訳基盤が変わっており、互換性は未検証です。Omarchy公式の配布物ではありません。

Omarchy Quickshell、Python 3、標準の `omarchy-agent-usage-update` が必要です。Claudeの追加利用情報には既存のClaude Codeログインを利用します。翻訳テストにだけNode.jsが必要です。

## 導入

以下のURLに公開された後、通常の端末から実行します。

```bash
omarchy plugin add https://github.com/kazuhidet/omarchy-usage-credits.git
omarchy plugin enable kazu.usage-credits
omarchy restart shell
```

公開リポジトリの直下にmanifest.jsonとQMLが必要です。ビルドスクリプトだけの作業用ディレクトリは、そのままplugin addできません。

アーカイブ配布の場合は、新規ディレクトリ `~/.config/omarchy/plugins/kazu.usage-credits/` に内容を展開し、`omarchy-shell shell rescanPlugins` の後に上記のenable・restartを実行します。既存ディレクトリには上書きしないでください。

標準版を置き換えるクローンとして動作します。独自のAgentsクローンを使っている場合はshell.jsonをバックアップし、既存クローンを無効化してから必要なバー設定を移してください。複数版は利用記録とIPCを共有するため、同時に有効にしないでください。課金設定は変更しません。

## 表示と警告

- 通常のセッション・週次使用率と、既存のCodex・Fireworks統計を維持します。
- Claude追加利用の有効・無効、月間支出上限への消費率を表示します。
- 消費率は `used_credits / monthly_limit`、上限情報がなければ `utilization` を使います。上限ゼロは無制限とは解釈しません。
- 取得不能や不正な応答では追加利用情報を取得不能として扱います。

月間支出上限は購入残高とは別物です。金額・残りトークン数は表示しません。OAuthエンドポイントは安定した公開APIではなく、実応答の検証はまだ不十分です。

追加利用が有効かつ割合が取得できる場合、通常枠と追加利用の両方が90%以上でClaudeのバーアイコンを赤くします。それ以外は通常枠による警告を使います。個別メーターはそれぞれの割合で警告します。パネルの `r` で再取得できます。

## 言語

```bash
omarchy bar set kazu.usage-credits language ja
```

`auto`（既定、セッションのロケール）、`en`、`ja` を指定できます。C.UTF-8ではautoは英語です。未翻訳の文字列は英語に戻ります。この版の言語設定は、新しいOmarchy本体の言語設定とは独立しています。

## データと通信

Claude Codeの既存資格情報、ローカルの会話記録・統計を読み、AnthropicのOAuth利用状況エンドポイントに接続します。正規化した使用状況をローカルに保存します。資格情報を利用記録へ含める処理はありません。他プロバイダーは標準収集コマンドを利用します。任意の端末間同期は元の設定に従い、追加利用の割合を同期・合算しません。

## 更新と削除

Git経由なら `omarchy plugin update kazu.usage-credits` の後に `omarchy restart shell` を実行します。Omarchy標準版の変更は自動でこの版に取り込まれません。アーカイブ版は既存ディレクトリをバックアップしてから、全体を新しい版に入れ替えてください。

標準版へ戻すには:

```bash
omarchy plugin disable kazu.usage-credits
omarchy plugin enable omarchy.agents
omarchy restart shell
```

表示を確認後、コミュニティ版のディレクトリを削除できます。履歴・資格情報・同期ファイルは残します。以前の個人クローンに戻す場合は、そのIDを有効化してください。

開発・検証手順は英語READMEを参照してください。上流への提案: https://github.com/omacom/omarchy/discussions/16844
