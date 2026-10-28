.pragma library

// English is the source language: every key is the text the stock plugin
// shows, so a missing translation falls back to the original wording.
// %1, %2, … are filled from the arguments in order.
var tables = {
  ja: {
    "Monthly": "月間",
    "Weekly": "週間",
    "Session": "セッション",
    "Limit": "上限",
    "now": "まもなく",
    "%1d %2h": "%1日%2時間",
    "%1h %2m": "%1時間%2分",
    "%1m": "%1分",
    "%1 spent of %2 funded": "入金額 %2 のうち %1 を使用",
    " · estimated": " · 推定",
    "Subscription": "サブスクリプション",
    "Prepaid": "プリペイド",
    "Sun": "日", "Mon": "月", "Tue": "火", "Wed": "水", "Thu": "木", "Fri": "金", "Sat": "土",
    "Today": "今日",
    "%1 tokens": "%1 トークン",
    "%1 prompts · %2 sessions": "%1 プロンプト · %2 セッション",
    "In %1 · out %2 · cache read %3 · cache write %4": "入力 %1 · 出力 %2 · キャッシュ読込 %3 · キャッシュ書込 %4",
    "Merged from %1 device": "%1台の端末から合算",
    "Merged from %1 devices": "%1台の端末から合算",
    "No AI coding subscriptions found.\nAgents show up here once you've used them.": "AIコーディングのサブスクリプションが見つかりません。\n使用するとここに表示されます。",
    "USAGE CREDITS": "追加利用",
    "BALANCE": "残高",
    "Prepaid credits": "プリペイドクレジット",
    "LIMITS": "利用上限",
    "TOKENS BY DAY": "日別トークン",
    "TOKENS BY MODEL": "モデル別トークン",
    "Resets in %1": "%1後にリセット",
    "Usage credit info unavailable (press r to refresh)": "追加利用情報を取得できません（rで更新）",
    "Usage credits are off": "追加利用は無効です",
    "Usage credits on · usage rate unavailable": "追加利用ON · 消費率は取得できません",
    "%1% of monthly spending limit used": "月間支出上限の %1% を消費",
    "Purchased balance is not checked. The icon warns only when both the regular allowance and usage credits are at 90% or more.": "購入残高は未確認です。アイコンは通常枠と追加利用の両方が90%以上のときに警告します。",

    // Messages written by the collectors and the sync service.
    "Usage sync mkdir failed": "同期フォルダを作成できません",
    "Usage sync scan failed": "同期データを読み込めません",
    "Waiting for auth": "認証待ち",
    "Sign-in expired": "サインインの期限切れ",
    "Claude limits unavailable": "Claudeの利用上限を取得できません",
    "Codex unavailable": "Codexを利用できません",
    "Codex limits unavailable": "Codexの利用上限を取得できません",
    "codex not found in PATH": "PATHにcodexが見つかりません",
    "Fireworks unavailable": "Fireworksを利用できません",
    "Balance unavailable": "残高を取得できません",
    "Fireworks usage scan failed": "Fireworksの利用状況を読み込めません",
    "Run `claude auth login` to restore authoritative usage.": "正確な利用状況を取得するには `claude auth login` を実行してください。",
    "Run `codex login` to authenticate.": "`codex login` を実行して認証してください。",
    "Set FIREWORKS_API_KEY, run `firectl set-api-key`, or sign in to Fireworks in opencode.": "FIREWORKS_API_KEY を設定するか、`firectl set-api-key` を実行するか、opencodeでFireworksにサインインしてください。",
    "Couldn't reach Anthropic's usage endpoint. Retrying shortly. Local Claude Code stats are still shown.": "Anthropicの利用状況エンドポイントに接続できません。まもなく再試行します。ローカルのClaude Code統計は引き続き表示します。",
    "Anthropic's usage endpoint returned no limits. Local Claude Code stats are still shown.": "Anthropicの利用状況エンドポイントが上限を返しませんでした。ローカルのClaude Code統計は引き続き表示します。"
  }
}

// Collector text with numbers or optional parts baked in. Each pattern's
// captures become %1, %2, … of its translation.
var patterns = {
  ja: [
    [/^Anthropic's usage endpoint is rate limiting checks right now \(retry after (\d+)s\)\. Local Claude Code stats are still shown\.$/,
      "Anthropicの利用状況エンドポイントがアクセスを制限しています（%1秒後に再試行可能）。ローカルのClaude Code統計は引き続き表示します。"],
    [/^Anthropic's usage endpoint is rate limiting checks right now\. Local Claude Code stats are still shown\.$/,
      "Anthropicの利用状況エンドポイントがアクセスを制限しています。ローカルのClaude Code統計は引き続き表示します。"],
    [/^Anthropic's usage endpoint returned status (\d+)\. Local Claude Code stats are still shown\.$/,
      "Anthropicの利用状況エンドポイントがステータス %1 を返しました。ローカルのClaude Code統計は引き続き表示します。"],
    [/^Claude Code's saved sign-in expired — showing the last known limits\. Start Claude Code, or run `claude auth login`, to refresh it\.$/,
      "Claude Codeの保存済みサインインが期限切れです。最後に取得した上限を表示しています。Claude Codeを起動するか `claude auth login` を実行して更新してください。"],
    [/^Claude Code's saved sign-in expired\. Start Claude Code, or run `claude auth login`, to refresh it\.$/,
      "Claude Codeの保存済みサインインが期限切れです。Claude Codeを起動するか `claude auth login` を実行して更新してください。"],
    // Model-scoped windows arrive titled "Fable Weekly".
    [/^(.+) (Monthly|Weekly|Session)$/, "%1 %2"]
  ]
}

// The plugin setting wins; otherwise follow the session locale.
function resolve(setting, localeName) {
  var wanted = String(setting || "").toLowerCase()
  if (wanted !== "" && wanted !== "auto") return tables[wanted] ? wanted : "en"
  var name = String(localeName || "").toLowerCase()
  for (var lang in tables) if (name.indexOf(lang) === 0) return lang
  return "en"
}

function fill(text, args) {
  return String(text).replace(/%(\d+)/g, function(match, n) {
    var value = args[Number(n) - 1]
    return value === undefined ? match : String(value)
  })
}

function tr(lang, text, args) {
  var table = tables[lang]
  var hit = table && Object.prototype.hasOwnProperty.call(table, text) ? table[text] : text
  return fill(hit, args || [])
}

// Free text from outside the plugin: an exact entry, then a pattern, else as is.
function message(lang, text) {
  var source = String(text || "")
  var table = tables[lang]
  if (!table || source === "") return source
  if (Object.prototype.hasOwnProperty.call(table, source)) return table[source]
  var list = patterns[lang] || []
  for (var i = 0; i < list.length; i++) {
    var match = source.match(list[i][0])
    if (match) return fill(list[i][1], match.slice(1).map(function(part) { return message(lang, part) }))
  }
  return source
}
