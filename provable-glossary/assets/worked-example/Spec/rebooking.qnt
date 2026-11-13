// 実験 5 (Experiment 005): 上映中止の振替と公平性
//
// 13:00 に 2 席、16:00 に 1 席。A・B は 13:00 だけ、C はどちらでも、D は 13:00 の新規購入。
// A・B・C は中止の影響を受けた既存購入者 (保護対象)。
// 何が不可能かは Lean (Glossary/Fairness.lean) で証明した。
// ここでは、正しい割当てが存在しても、処理の順番によって届かなくなることを調べる。
module rebooking {
  // true なら「回復可能性を守る」方針。false なら先着順。
  const PRESERVE: bool

  type Seat = S13a | S13b | S16a
  type Slot = NoSeat | Got(Seat)

  pure val Seats = Set(S13a, S13b, S16a)
  pure val Customers = Set("A", "B", "C", "D")

  pure def acceptable(c: str, s: Seat): bool = c == "C" or s != S16a

  pure def taken(m: str -> Slot, s: Seat): bool = Customers.exists(c => m.get(c) == Got(s))

  // 保護対象 p に席 s を充てる完成形と、いまの割当て m が両立するか
  pure def fits(m: str -> Slot, p: str, s: Seat): bool =
    acceptable(p, s) and (m.get(p) == Got(s) or (m.get(p) == NoSeat and not(taken(m, s))))

  // 回復可能: いまの割当てを延長して、A・B・C の全員を振り替えられる。
  pure def recoverable(m: str -> Slot): bool =
    tuples(Seats, Seats, Seats).exists(((a, b, c)) =>
      a != b and a != c and b != c and fits(m, "A", a) and fits(m, "B", b) and fits(m, "C", c))

  var assigned: str -> Slot

  action init = assigned' = Customers.mapBy(c => NoSeat)

  // 顧客 c の取引照合が終わり、席 s を確定する。順番は非決定的。
  action confirmSeat(c: str, s: Seat): bool = all {
    assigned.get(c) == NoSeat,
    not(taken(assigned, s)),
    acceptable(c, s),
    PRESERVE implies recoverable(assigned.set(c, Got(s))),
    assigned' = assigned.set(c, Got(s)),
  }

  action step = any {
    nondet c = Customers.oneOf()
    nondet s = Seats.oneOf()
    confirmSeat(c, s),
    assigned' = assigned,
  }

  // 席の排他性。どの方針でも成り立つ。
  val seatExclusive = Seats.forall(s => Customers.filter(c => assigned.get(c) == Got(s)).size() <= 1)

  // 回避可能な損失がない: 確定した割当ては、保護対象全員の振替をまだ可能にしている。
  val noAvoidableLoss = recoverable(assigned)

  // 必須の性質
  val Safety = seatExclusive and noAvoidableLoss

  // 方針の代償: 新規購入の D は席を得られない。
  val dNeverServed = assigned.get("D") == NoSeat

  // 守る方針のもとで、振替がまだの保護対象には、確定できる席が必ず残っている。
  val rescueNeverStuck = Set("A", "B", "C").forall(p =>
    assigned.get(p) == NoSeat implies
      Seats.exists(s => not(taken(assigned, s)) and acceptable(p, s)
        and recoverable(assigned.set(p, Got(s)))))
}

// 先着順。個々の確定はすべて有効だが、全体として失敗する順番がある。
module fcfs {
  import rebooking(PRESERVE = false).*

  // 議論の反例: C が先に 13:00 を取ると、A と B のどちらかが振り替えられない。
  run cTakes13Test =
    init
      .then(confirmSeat("C", S13a))
      .expect(seatExclusive and not(noAvoidableLoss))
      .then(confirmSeat("A", S13b))
      // B に渡せる席はもうない: 残りは 16:00 だけで、B は 16:00 に来られない。
      .expect(Seats.forall(s => taken(assigned, s) or not(acceptable("B", s))))

  // 新規購入の D が 13:00 を取っても同じ損失が起きる。
  run dTakes13Test =
    init
      .then(confirmSeat("D", S13a))
      .expect(seatExclusive and not(noAvoidableLoss))
}

// 回復可能性を守る方針。
module preserving {
  import rebooking(PRESERVE = true).*

  run cIsSteeredTo16Test =
    init
      .then(confirmSeat("C", S13a))
      .fail()

  run allProtectedServedTest =
    init
      .then(confirmSeat("C", S16a))
      .then(confirmSeat("A", S13a))
      .then(confirmSeat("B", S13b))
      .expect(noAvoidableLoss and dNeverServed)
}
