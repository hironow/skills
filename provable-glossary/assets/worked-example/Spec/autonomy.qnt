// Experiment 006: 自律的に実行できる判断と、人の意思決定が必要な判断の境界
//
// 方針は「保護対象 (A・B・C) の振替人数を最大にする」。実験 5 と同じ顧客と希望。
// 境界の定義: いまの割当てを延長する最善の完成形のすべてで顧客 p が席を得るなら、
// p への確定は方針だけで決まる。そうでなければ、方針は誰を選ぶかを決めていない。
//
// スイッチ:
//   TWO_AT_13  13:00 の席が 2 つあるか。false なら 1 つ (A と B のどちらかしか観られない)
//   ESCALATE   方針で決まらない確定を、人の決定に限るか
module autonomy {
  const TWO_AT_13: bool
  const ESCALATE: bool

  type Seat = S13a | S13b | S16a
  type Slot = NoSeat | Got(Seat)

  pure val Seats = if (TWO_AT_13) Set(S13a, S13b, S16a) else Set(S13a, S16a)
  pure val Slots = Seats.map(s => Got(s)).union(Set(NoSeat))
  pure val Protected = Set("A", "B", "C")
  pure val Customers = Set("A", "B", "C", "D")

  pure def acceptable(c: str, s: Seat): bool = c == "C" or s != S16a
  pure def taken(m: str -> Slot, s: Seat): bool = Customers.exists(c => m.get(c) == Got(s))

  // 保護対象 p の行き先 x が、いまの割当て m と両立するか
  pure def slotFits(m: str -> Slot, p: str, x: Slot): bool =
    match x {
      | NoSeat => m.get(p) == NoSeat
      | Got(s) => acceptable(p, s) and (m.get(p) == x or (m.get(p) == NoSeat and not(taken(m, s))))
    }

  pure def apart(x: Slot, y: Slot): bool = x == NoSeat or x != y

  // m を延長する完成形 (A, B, C の行き先)
  pure def completions(m: str -> Slot): Set[(Slot, Slot, Slot)] =
    tuples(Slots, Slots, Slots).filter(((a, b, c)) => and {
      slotFits(m, "A", a), slotFits(m, "B", b), slotFits(m, "C", c),
      apart(a, b), apart(a, c), apart(b, c),
    })

  pure def served(t: (Slot, Slot, Slot)): int =
    (if (t._1 != NoSeat) 1 else 0) + (if (t._2 != NoSeat) 1 else 0) + (if (t._3 != NoSeat) 1 else 0)

  pure def best(m: str -> Slot): int =
    completions(m).fold(0, (acc, t) => if (served(t) > acc) served(t) else acc)

  pure def optimal(m: str -> Slot): Set[(Slot, Slot, Slot)] =
    completions(m).filter(t => served(t) == best(m))

  pure def servedIn(t: (Slot, Slot, Slot), p: str): bool =
    if (p == "A") t._1 != NoSeat else if (p == "B") t._2 != NoSeat else t._3 != NoSeat

  // 方針だけで決まる: 最善の完成形のすべてで p が席を得る
  pure def mustServe(m: str -> Slot, p: str): bool = optimal(m).forall(t => servedIn(t, p))
  // 方針が許す: 最善の完成形のどれかで p が席を得る
  pure def mayServe(m: str -> Slot, p: str): bool = optimal(m).exists(t => servedIn(t, p))

  pure val empty = Customers.mapBy(c => NoSeat)
  pure val initialBest = best(empty)

  var assigned: str -> Slot
  var arbitrary: bool   // 方針で決まらない確定を、人の決定なしに行った (履歴)
  var asked: bool       // 人に決定を求めた (履歴)

  action init = all { assigned' = empty, arbitrary' = false, asked' = false }

  pure def keepsBest(m: str -> Slot, c: str, s: Seat): bool = best(m.set(c, Got(s))) == best(m)

  pure def canConfirm(m: str -> Slot, c: str, s: Seat): bool = and {
    m.get(c) == NoSeat, not(taken(m, s)), acceptable(c, s), keepsBest(m, c, s),
  }

  // システムが自分で確定する。
  action confirmSeat(c: str, s: Seat): bool = all {
    canConfirm(assigned, c, s),
    (ESCALATE and Protected.contains(c)) implies mustServe(assigned, c),
    assigned' = assigned.set(c, Got(s)),
    arbitrary' = (arbitrary or (Protected.contains(c) and not(mustServe(assigned, c)))),
    asked' = asked,
  }

  // 方針で決まらないときだけ、権限を持つ人が決める。
  action humanDecides(c: str, s: Seat): bool = all {
    ESCALATE,
    Protected.contains(c),
    canConfirm(assigned, c, s),
    not(mustServe(assigned, c)),
    assigned' = assigned.set(c, Got(s)),
    arbitrary' = arbitrary,
    asked' = true,
  }

  action step = any {
    nondet c = Customers.oneOf()
    nondet s = Seats.oneOf()
    any { confirmSeat(c, s), humanDecides(c, s) },
    all { assigned' = assigned, arbitrary' = arbitrary, asked' = asked },
  }

  val seatExclusive = Seats.forall(s => Customers.filter(c => assigned.get(c) == Got(s)).size() <= 1)

  // 方針は保たれる: 振替できる保護対象の最大人数は減らない。
  val policyKept = best(assigned) == initialBest

  // システムは、方針で決まらない選択を自分でしていない。
  val noArbitraryChoice = not(arbitrary)

  // 人に決定を求める場面はない。
  val humanNeverAsked = not(asked)

  // 新規購入の D は席を得ない (断るのは方針だけで決まる)。
  val dNeverServed = assigned.get("D") == NoSeat

  // 行き詰まらない: 方針が席を許す保護対象には、システムか人が確定できる席がある。
  val neverStuck = Protected.forall(p =>
    (assigned.get(p) == NoSeat and mayServe(assigned, p)) implies
      Seats.exists(s => canConfirm(assigned, p, s)))

  val Safety = seatExclusive and policyKept and neverStuck
}

// 席が足りる場面 (13:00 に 2 席)。システムは人に聞かずに全部決められる。
module enough_auto {
  import autonomy(TWO_AT_13 = true, ESCALATE = false).*
}

module enough_escalate {
  import autonomy(TWO_AT_13 = true, ESCALATE = true).*
}

// 席が足りない場面 (13:00 に 1 席)。A と B のどちらを選ぶかは方針で決まらない。
module short_auto {
  import autonomy(TWO_AT_13 = false, ESCALATE = false).*

  run systemPicksAOverBTest =
    init
      .expect(not(mustServe(assigned, "A")) and not(mustServe(assigned, "B")) and mustServe(assigned, "C"))
      .then(confirmSeat("A", S13a))
      .expect(Safety and not(noArbitraryChoice))
}

module short_escalate {
  import autonomy(TWO_AT_13 = false, ESCALATE = true).*

  // システムは A も B も自分では選べない。C の 16:00 は自分で確定できる。
  run systemCannotPickTest =
    init.then(confirmSeat("A", S13a)).fail()

  run cIsAutonomousTest =
    init.then(confirmSeat("C", S16a)).expect(Safety and humanNeverAsked)

  run humanPicksTest =
    init.then(humanDecides("B", S13a)).then(confirmSeat("C", S16a))
      .expect(Safety and noArbitraryChoice and not(humanNeverAsked))
}
