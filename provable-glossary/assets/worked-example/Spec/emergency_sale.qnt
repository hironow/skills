// 実験 4 (Take 1): チケット販売と、通常メンテナンス・緊急メンテナンスの競合
//
// 範囲: 上映回 1 つ、座席 1 つ、顧客 2 人。時間 (上映開始時刻) は扱わない。
// 決済は外部サービスなので、サイトが遮断されていても成功の通知は届く。
//
// 設計の変種を 2 つのスイッチで表す。
//   GUARD_ISSUE  発券のとき、その顧客が座席を確保中であることを確かめる
//   FREEZE_HOLD  新概念「決済済み・発券保留取引」: 決済が始まった仮確保は期限切れにしない。
//                解決の手段として返金を持つ。
module emergency_sale {
  const GUARD_ISSUE: bool
  const FREEZE_HOLD: bool

  type Site = Open | Draining | CutoffOrdered | Blocked
  type Pay = NoPay | Pending | Succeeded | Refunded
  type Holder = Nobody | HeldBy(str)

  pure val Customers = Set("c1", "c2")

  var site: Site
  var emergency: bool            // いまの停止は脆弱性によるものか
  var holder: Holder             // 座席を仮確保している顧客
  var pay: str -> Pay
  var ticket: str -> bool        // 有効な入場権
  var ticketWhileBlocked: bool   // 遮断完了後に発券が起きた (履歴)
  var paidWhileBlocked: bool     // 遮断完了後に決済成功が起きた (履歴)

  val ticketCount = Customers.filter(c => ticket.get(c)).size()
  // 販売経路が動いている: 遮断完了までは処理中の取引が進む
  val channelsRunning = site != Blocked
  val unresolvedPayment =
    Customers.exists(c => pay.get(c) == Pending or (pay.get(c) == Succeeded and not(ticket.get(c))))

  action init = all {
    site' = Open,
    emergency' = false,
    holder' = Nobody,
    pay' = Customers.mapBy(c => NoPay),
    ticket' = Customers.mapBy(c => false),
    ticketWhileBlocked' = false,
    paidWhileBlocked' = false,
  }

  action keepSite = all { site' = site, emergency' = emergency }
  action keepHistory = all {
    ticketWhileBlocked' = ticketWhileBlocked,
    paidWhileBlocked' = paidWhileBlocked,
  }

  // --- 販売 ---

  action reserve(c: str): bool = all {
    site == Open or site == CutoffOrdered,   // Draining は新しい仮確保を受けない
    holder == Nobody,
    ticketCount == 0,
    pay.get(c) == NoPay,
    holder' = HeldBy(c),
    pay' = pay, ticket' = ticket, keepSite, keepHistory,
  }

  action startPayment(c: str): bool = all {
    channelsRunning,
    holder == HeldBy(c),
    pay.get(c) == NoPay,
    pay' = pay.set(c, Pending),
    holder' = holder, ticket' = ticket, keepSite, keepHistory,
  }

  // 外部の決済サービスで成功する。サイトの状態に関係なく起きる。
  action paymentSucceeds(c: str): bool = all {
    pay.get(c) == Pending,
    pay' = pay.set(c, Succeeded),
    paidWhileBlocked' = (paidWhileBlocked or site == Blocked),
    ticketWhileBlocked' = ticketWhileBlocked,
    holder' = holder, ticket' = ticket, keepSite,
  }

  action paymentFails(c: str): bool = all {
    pay.get(c) == Pending,
    pay' = pay.set(c, NoPay),
    holder' = holder, ticket' = ticket, keepSite, keepHistory,
  }

  action issueTicket(c: str): bool = all {
    channelsRunning,
    pay.get(c) == Succeeded,
    not(ticket.get(c)),
    GUARD_ISSUE implies holder == HeldBy(c),
    ticket' = ticket.set(c, true),
    ticketWhileBlocked' = (ticketWhileBlocked or site == Blocked),
    paidWhileBlocked' = paidWhileBlocked,
    holder' = holder, pay' = pay, keepSite,
  }

  action holdExpires(c: str): bool = all {
    holder == HeldBy(c),
    not(ticket.get(c)),
    FREEZE_HOLD implies pay.get(c) == NoPay,
    holder' = Nobody,
    pay' = pay, ticket' = ticket, keepSite, keepHistory,
  }

  // 決済済み・発券保留取引を返金で解決する。座席を解放する。
  action refund(c: str): bool = all {
    FREEZE_HOLD,
    pay.get(c) == Succeeded,
    not(ticket.get(c)),
    pay' = pay.set(c, Refunded),
    holder' = if (holder == HeldBy(c)) Nobody else holder,
    ticket' = ticket, keepSite, keepHistory,
  }

  // --- 運用 ---

  // 通常メンテナンス: まず新しい仮確保を止め、処理中の取引が片付いてから遮断する。
  action startPlannedMaintenance = all {
    site == Open,
    site' = Draining, emergency' = false,
    holder' = holder, pay' = pay, ticket' = ticket, keepHistory,
  }

  action completeDrain = all {
    site == Draining,
    not(unresolvedPayment),
    holder == Nobody or ticketCount == 1,
    site' = Blocked, emergency' = false,
    holder' = holder, pay' = pay, ticket' = ticket, keepHistory,
  }

  // 緊急メンテナンス: 脆弱性を検知して停止を指令する。処理中の取引を待たない。
  action vulnerabilityDetected = all {
    site == Open or site == Draining,
    site' = CutoffOrdered, emergency' = true,
    holder' = holder, pay' = pay, ticket' = ticket, keepHistory,
  }

  action applyCutoff = all {
    site == CutoffOrdered,
    site' = Blocked, emergency' = emergency,
    holder' = holder, pay' = pay, ticket' = ticket, keepHistory,
  }

  action recover = all {
    site == Blocked,
    site' = Open, emergency' = false,
    holder' = holder, pay' = pay, ticket' = ticket, keepHistory,
  }

  action step = any {
    nondet c = Customers.oneOf()
    any {
      reserve(c), startPayment(c), paymentSucceeds(c), paymentFails(c),
      issueTicket(c), holdExpires(c), refund(c),
    },
    startPlannedMaintenance, completeDrain, vulnerabilityDetected, applyCutoff, recover,
  }

  // --- 性質 ---

  // 1. 座席の排他性: 同じ上映回・同じ座席の有効な入場権は高々 1 つ。
  val seatExclusive = ticketCount <= 1

  // 2. 決済後の取引保全: 支払い済みで未発券の取引は、座席を保ったまま追跡されている。
  //    (発券済み・返金済みは解決済み。)
  val paidIsTracked = Customers.forall(c =>
    (pay.get(c) == Succeeded and not(ticket.get(c))) implies holder == HeldBy(c))

  // 3a. 遮断完了後に発券は起きない。
  val noTicketWhileBlocked = not(ticketWhileBlocked)

  // 3b. 遮断完了後に決済成功は起きない。「販売成立 = 決済成功」と定義した場合の遮断性。
  val noPaymentWhileBlocked = not(paidWhileBlocked)

  // 4. 通常メンテナンスの遮断中に、未解決の決済は残っていない。
  val plannedBlockIsQuiet = (site == Blocked and not(emergency)) implies not(unresolvedPayment)

  // 必須の性質。3b は定義が未決定なので入れない。
  val Safety = seatExclusive and paidIsTracked and noTicketWhileBlocked and plannedBlockIsQuiet

  // 議論の筋書き: 仮確保 → 決済開始 → 緊急停止 → 外部で決済成功 → 仮確保が期限切れ → 復旧
  //               → 別の顧客が同じ座席を買う。
  run raceUntilSecondSale =
    init
      .then(reserve("c1"))
      .then(startPayment("c1"))
      .then(vulnerabilityDetected)
      .then(applyCutoff)
      .then(paymentSucceeds("c1"))
      .then(holdExpires("c1"))
      .then(recover)
      .then(reserve("c2"))
      .then(startPayment("c2"))
      .then(paymentSucceeds("c2"))
      .then(issueTicket("c2"))
}

// 変種 0: 素朴な設計。発券は支払い済みかどうかだけを見る。
module v0_naive {
  import emergency_sale(GUARD_ISSUE = false, FREEZE_HOLD = false).*

  // 反例: c1 は支払い済みで券がなく、復旧後に c1 にも発券されて二重販売になる。
  run doubleSaleTest =
    raceUntilSecondSale
      .expect(not(paidIsTracked))
      .then(issueTicket("c1"))
      .expect(not(seatExclusive))
}

// 変種 1: 発券のときに仮確保を確かめる。二重販売は消えるが、支払い済みの取引が取り残される。
module v1_guarded {
  import emergency_sale(GUARD_ISSUE = true, FREEZE_HOLD = false).*

  // 反例: c1 は支払い済み・未発券・座席なし。発券はできず、この変種に返金の操作はない。
  run orphanedPaymentTest =
    raceUntilSecondSale
      .expect(seatExclusive and not(paidIsTracked))
      .then(issueTicket("c1"))
      .fail()
}

// 変種 2: 「決済済み・発券保留取引」を導入する。
module v2_pending_issuance {
  import emergency_sale(GUARD_ISSUE = true, FREEZE_HOLD = true).*

  // 同じ筋書きは、仮確保の期限切れのところで止まる。
  run holdIsFrozenTest =
    init
      .then(reserve("c1"))
      .then(startPayment("c1"))
      .then(vulnerabilityDetected)
      .then(applyCutoff)
      .then(paymentSucceeds("c1"))
      .expect(Safety and not(noPaymentWhileBlocked))
      .then(holdExpires("c1"))
      .fail()

  // 復旧後は発券で解決できる。遮断中でも返金で解決できる。
  run resolvedByTicketTest =
    init
      .then(reserve("c1")).then(startPayment("c1"))
      .then(vulnerabilityDetected).then(applyCutoff)
      .then(paymentSucceeds("c1"))
      .then(recover)
      .then(issueTicket("c1"))
      .expect(Safety and ticket.get("c1"))

  run resolvedByRefundTest =
    init
      .then(reserve("c1")).then(startPayment("c1"))
      .then(vulnerabilityDetected).then(applyCutoff)
      .then(paymentSucceeds("c1"))
      .then(refund("c1"))
      .expect(Safety and holder == Nobody)
}
