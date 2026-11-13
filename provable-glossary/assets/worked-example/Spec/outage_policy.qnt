// 停止時の規則の案を検査する。
//
// 場面: 電子チケットの販売が、不正アクセスで止まる。発券用のコードと購入者の氏名が流出する。
// 上映 (公演) の開始時刻は待ってくれない。
// 登場するのは、チケット 1 枚、正規の購入者 1 人、流出した情報を持つ第三者 1 人。
//
// 規則の案は 4 つのスイッチで表す。
module outage_policy {
  const VENUE_ISSUE: bool        // 停止中でも、会場は購入者の一覧で決済済みの客を通す (第 3 条)
  const ON_LEAK: int             // 流出した券の扱い (第 4 条)。0: 有効のまま、1: すべて無効、2: 本人確認に切り替える
  const ACCEPT_NAME_ONLY: bool   // 会場は、氏名を告げるだけの客を通す (第 4 条 2 項が禁じる)
  const AUTO_REFUND: bool        // 入場できなかった決済済みの客に、申し出なしで返金する (第 5 条)

  type Tx = NoTx | Pending | PaidUnticketed | Ticketed | Refunded
  type Phase = BeforeShow | ShowTime | AfterShow
  type Entrant = Nobody | Legit | Impostor

  var siteUp: bool
  var phase: Phase
  var tx: Tx
  var leaked: bool          // 発券用のコードと氏名が流出した
  var admitted: Entrant     // 席に入った人
  var legitRefused: bool    // 正規の購入者が、開始時刻に来たのに入れなかった

  val paid = tx == PaidUnticketed or tx == Ticketed

  action init = all {
    siteUp' = true, phase' = BeforeShow, tx' = NoTx,
    leaked' = false, admitted' = Nobody, legitRefused' = false,
  }

  action startPayment = all {
    siteUp, phase == BeforeShow, tx == NoTx,
    tx' = Pending,
    siteUp' = siteUp, phase' = phase, leaked' = leaked, admitted' = admitted, legitRefused' = legitRefused,
  }

  // 決済サービスの成功は、サイトが止まっていても届く。
  action paySucceeds = all {
    tx == Pending,
    tx' = PaidUnticketed,
    siteUp' = siteUp, phase' = phase, leaked' = leaked, admitted' = admitted, legitRefused' = legitRefused,
  }

  // オンラインの発券は、サイトが動いているときだけ。
  action issue = all {
    siteUp, tx == PaidUnticketed, phase != AfterShow,
    tx' = Ticketed,
    siteUp' = siteUp, phase' = phase, leaked' = leaked, admitted' = admitted, legitRefused' = legitRefused,
  }

  action breach = all {
    not(leaked),
    leaked' = true,
    siteUp' = siteUp, phase' = phase, tx' = tx, admitted' = admitted, legitRefused' = legitRefused,
  }

  action stop = all {
    siteUp,
    siteUp' = false,
    phase' = phase, tx' = tx, leaked' = leaked, admitted' = admitted, legitRefused' = legitRefused,
  }

  action recover = all {
    not(siteUp),
    siteUp' = true,
    phase' = phase, tx' = tx, leaked' = leaked, admitted' = admitted, legitRefused' = legitRefused,
  }

  action showStarts = all {
    phase == BeforeShow,
    phase' = ShowTime,
    siteUp' = siteUp, tx' = tx, leaked' = leaked, admitted' = admitted, legitRefused' = legitRefused,
  }

  action showEnds = all {
    phase == ShowTime,
    phase' = AfterShow,
    siteUp' = siteUp, tx' = tx, leaked' = leaked, admitted' = admitted, legitRefused' = legitRefused,
  }

  // 正規の購入者を通すか。
  //   - 席がすでに埋まっていれば通せない。
  //   - 券があり、流出後に「すべて無効」としていれば通せない。
  //   - 決済済みで券がまだなければ、会場が一覧で通す規則があるときだけ通す。
  val legitPasses =
    admitted == Nobody and (
      (tx == Ticketed and not(leaked and ON_LEAK == 1)) or
      (tx == PaidUnticketed and VENUE_ISSUE)
    )

  action legitArrives = all {
    phase == ShowTime, paid, admitted != Legit, not(legitRefused),
    admitted' = if (legitPasses) Legit else admitted,
    legitRefused' = not(legitPasses),
    siteUp' = siteUp, phase' = phase, tx' = tx, leaked' = leaked,
  }

  // 流出した情報を持つ第三者を通してしまうか。
  //   - サイトが動いていれば、流出したコードを読み取り機にかざす。コードが有効のままなら通る。
  //   - サイトが止まっていれば、読み取り機は使えない。会場が氏名だけで通すなら通る。
  val impostorPasses =
    leaked and paid and admitted == Nobody and (
      (siteUp and tx == Ticketed and ON_LEAK == 0) or
      (not(siteUp) and ACCEPT_NAME_ONLY)
    )

  action impostorArrives = all {
    phase == ShowTime, admitted != Impostor,
    admitted' = if (impostorPasses) Impostor else admitted,
    siteUp' = siteUp, phase' = phase, tx' = tx, leaked' = leaked, legitRefused' = legitRefused,
  }

  // 返金は、止まっている販売の経路を使わない。サイトの状態に関係なく実行できる。
  val refundEnabled = AUTO_REFUND and phase == AfterShow and paid and admitted != Legit

  action refund = all {
    refundEnabled,
    tx' = Refunded,
    siteUp' = siteUp, phase' = phase, leaked' = leaked, admitted' = admitted, legitRefused' = legitRefused,
  }

  action step = any {
    startPayment, paySucceeds, issue, breach, stop, recover,
    showStarts, showEnds, legitArrives, impostorArrives, refund,
  }

  // 流出した情報だけで入場した人はいない。
  val noImpostor = admitted != Impostor

  // 決済を済ませて開始時刻に来た正規の購入者は、入場を断られない。
  val noLockout = not(legitRefused)

  // 終了後に、入場も返金もされず、返金の手段もない決済済みの取引は残らない。
  val noLimbo = not(phase == AfterShow and paid and admitted != Legit and not(refundEnabled))

  val Safety = noImpostor and noLockout and noLimbo
}

// 規則の案。4 つの規則をすべて採る。
module draft {
  import outage_policy(VENUE_ISSUE = true, ON_LEAK = 2, ACCEPT_NAME_ONLY = false, AUTO_REFUND = true).*

  // 公表された経過と同じ順で出来事を起こす。第三者は通らず、正規の購入者は通る。
  run reportedTimelineTest =
    init.then(startPayment).then(paySucceeds).then(issue)
      .then(breach).then(stop).then(showStarts)
      .then(impostorArrives).expect(admitted == Nobody)
      .then(legitArrives).expect(admitted == Legit and not(legitRefused))

  // 決済は済んだが券が出る前に止まった客も、会場で通る。
  run paidUnticketedTest =
    init.then(startPayment).then(stop).then(paySucceeds).then(showStarts)
      .then(legitArrives).expect(admitted == Legit)
}

// 公表された案内を単純化したもの: 購入者の一覧で通す、券は有効のまま、
// メールがなければ氏名を告げる、返金は未公表。
module as_reported {
  import outage_policy(VENUE_ISSUE = true, ON_LEAK = 0, ACCEPT_NAME_ONLY = true, AUTO_REFUND = false).*

  // 同じ経過で、氏名を知る第三者が先に来ると通り、正規の購入者が断られる。
  run reportedTimelineTest =
    init.then(startPayment).then(paySucceeds).then(issue)
      .then(breach).then(stop).then(showStarts)
      .then(impostorArrives).expect(admitted == Impostor)
      .then(legitArrives).expect(legitRefused)
}

// 規則を 1 つずつ外す。どの規則も、外すと性質が 1 つ破れる。
module without_venue_issue {
  import outage_policy(VENUE_ISSUE = false, ON_LEAK = 2, ACCEPT_NAME_ONLY = false, AUTO_REFUND = true).*
}

module without_identity_check {
  import outage_policy(VENUE_ISSUE = true, ON_LEAK = 0, ACCEPT_NAME_ONLY = false, AUTO_REFUND = true).*
}

module with_name_only {
  import outage_policy(VENUE_ISSUE = true, ON_LEAK = 2, ACCEPT_NAME_ONLY = true, AUTO_REFUND = true).*
}

module without_auto_refund {
  import outage_policy(VENUE_ISSUE = true, ON_LEAK = 2, ACCEPT_NAME_ONLY = false, AUTO_REFUND = false).*
}

// 流出した券をすべて無効にする。第三者は防げるが、正規の購入者も入れなくなる。
module invalidate_all {
  import outage_policy(VENUE_ISSUE = true, ON_LEAK = 1, ACCEPT_NAME_ONLY = false, AUTO_REFUND = true).*
}
