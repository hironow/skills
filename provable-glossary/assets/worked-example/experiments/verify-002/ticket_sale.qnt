// チケット販売の状態遷移モデル。上映回 1 つ、座席 1 つ、顧客 2 人 (c1, c2)。
// 決済は外部サービスで行われ、販売サイトの状態に関係なく成功・失敗する。
// 設計の選択肢を 6 つのスイッチで表す。
module ticket_sale {
  const GUARD_ISSUE: bool
  const FREEZE_HOLD: bool
  const REFUND: bool
  const FAIL_RELEASES: bool
  const DRAIN_WAITS: bool
  const RESERVE_CHECKS_TICKET: bool

  type Site = Open | Draining | CutoffOrdered | Blocked
  type Pay = NoPay | Pending | Succeeded | Refunded
  type Holder = Nobody | HeldBy(str)

  pure val Customers = Set("c1", "c2")

  var site: Site
  var emergency: bool
  var holder: Holder
  var pay: str -> Pay
  var ticket: str -> bool

  val ticketCount = Customers.filter(c => ticket.get(c)).size()
  val channelsRunning = site != Blocked
  val unresolvedPayment =
    Customers.exists(c => pay.get(c) == Pending or (pay.get(c) == Succeeded and not(ticket.get(c))))

  action init = all {
    site' = Open,
    emergency' = false,
    holder' = Nobody,
    pay' = Customers.mapBy(c => NoPay),
    ticket' = Customers.mapBy(c => false),
  }

  action reserve(c: str): bool = all {
    site == Open or site == CutoffOrdered,
    holder == Nobody,
    RESERVE_CHECKS_TICKET implies ticketCount == 0,
    pay.get(c) == NoPay,
    holder' = HeldBy(c),
    pay' = pay, ticket' = ticket, site' = site, emergency' = emergency,
  }

  action startPayment(c: str): bool = all {
    channelsRunning,
    holder == HeldBy(c),
    pay.get(c) == NoPay,
    pay' = pay.set(c, Pending),
    holder' = holder, ticket' = ticket, site' = site, emergency' = emergency,
  }

  action paymentSucceeds(c: str): bool = all {
    pay.get(c) == Pending,
    pay' = pay.set(c, Succeeded),
    holder' = holder, ticket' = ticket, site' = site, emergency' = emergency,
  }

  action paymentFails(c: str): bool = all {
    pay.get(c) == Pending,
    pay' = pay.set(c, NoPay),
    holder' = if (FAIL_RELEASES and holder == HeldBy(c)) Nobody else holder,
    ticket' = ticket, site' = site, emergency' = emergency,
  }

  action issueTicket(c: str): bool = all {
    channelsRunning,
    pay.get(c) == Succeeded,
    not(ticket.get(c)),
    GUARD_ISSUE implies holder == HeldBy(c),
    ticket' = ticket.set(c, true),
    holder' = holder, pay' = pay, site' = site, emergency' = emergency,
  }

  action holdExpires(c: str): bool = all {
    holder == HeldBy(c),
    not(ticket.get(c)),
    FREEZE_HOLD implies pay.get(c) == NoPay,
    holder' = Nobody,
    pay' = pay, ticket' = ticket, site' = site, emergency' = emergency,
  }

  action refund(c: str): bool = all {
    REFUND,
    pay.get(c) == Succeeded,
    not(ticket.get(c)),
    pay' = pay.set(c, Refunded),
    holder' = if (holder == HeldBy(c)) Nobody else holder,
    ticket' = ticket, site' = site, emergency' = emergency,
  }

  action startPlannedMaintenance = all {
    site == Open,
    site' = Draining, emergency' = false,
    holder' = holder, pay' = pay, ticket' = ticket,
  }

  action completeDrain = all {
    site == Draining,
    DRAIN_WAITS implies not(unresolvedPayment),
    site' = Blocked, emergency' = false,
    holder' = holder, pay' = pay, ticket' = ticket,
  }

  action vulnerabilityDetected = all {
    site == Open or site == Draining,
    site' = CutoffOrdered, emergency' = true,
    holder' = holder, pay' = pay, ticket' = ticket,
  }

  action applyCutoff = all {
    site == CutoffOrdered,
    site' = Blocked, emergency' = emergency,
    holder' = holder, pay' = pay, ticket' = ticket,
  }

  action recover = all {
    site == Blocked,
    site' = Open, emergency' = false,
    holder' = holder, pay' = pay, ticket' = ticket,
  }

  action step = any {
    nondet c = Customers.oneOf()
    any {
      reserve(c), startPayment(c), paymentSucceeds(c), paymentFails(c),
      issueTicket(c), holdExpires(c), refund(c),
    },
    startPlannedMaintenance, completeDrain, vulnerabilityDetected, applyCutoff, recover,
  }

  // P1: 入場権は高々 1 つ。
  val P1 = ticketCount <= 1

  // P2: 決済が成功して未発券の顧客は、座席を確保している。
  val P2 = Customers.forall(c =>
    (pay.get(c) == Succeeded and not(ticket.get(c))) implies holder == HeldBy(c))

  // P3: 緊急でない遮断の間、未解決の決済はない。
  val P3 = (site == Blocked and not(emergency)) implies not(unresolvedPayment)

  // P4: 入場権を持つ顧客は、座席を確保している。
  val P4 = Customers.forall(c => ticket.get(c) implies holder == HeldBy(c))

  // P5: 座席が空いているなら、決済中・決済済み未発券・発券済みの顧客はいない。
  val P5 = holder == Nobody implies Customers.forall(c =>
    pay.get(c) != Pending and not(pay.get(c) == Succeeded and not(ticket.get(c))) and not(ticket.get(c)))

  // P6: 決済が成功した顧客が 2 人同時にいることはない (返金済みは数えない)。
  val P6 = Customers.filter(c => pay.get(c) == Succeeded).size() <= 1
}
