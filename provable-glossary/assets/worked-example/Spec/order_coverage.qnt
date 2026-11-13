// 実験 3: 仕様の空白
//
// 書かれている業務ルールは 2 つだけ。
//   - 支払い済みの注文は発送できる。
//   - 未払いの注文はキャンセルできる。
// (未払いの注文は支払える、は暗黙の前提として足した。)
// 「支払い済みで発送前の注文はキャンセルできるか」は書かれていない。
// 書かれていない組み合わせを Unspecified として残し、到達できるかを調べる。
module order_coverage {
  type Status = Unpaid | Paid | Shipped | Cancelled
  type Op = Pay | Ship | Cancel
  type Decision = Allowed | Forbidden | Unspecified

  pure val Ops = Set(Pay, Ship, Cancel)

  pure def isTerminal(s: Status): bool = s == Shipped or s == Cancelled

  // 書かれたルールだけを写す。推測で埋めない。
  pure def rule(s: Status, op: Op): Decision =
    if (isTerminal(s)) Forbidden
    else if (s == Unpaid and op == Pay) Allowed
    else if (s == Unpaid and op == Cancel) Allowed
    else if (s == Paid and op == Ship) Allowed
    else Unspecified

  pure def after(s: Status, op: Op): Status =
    match op {
      | Pay => Paid
      | Ship => Shipped
      | Cancel => Cancelled
    }

  var status: Status

  action init = status' = Unpaid

  action step = any {
    nondet op = Ops.oneOf()
    all {
      rule(status, op) == Allowed,
      status' = after(status, op),
    },
    all { isTerminal(status), status' = status },
  }

  // 議論が挙げた網羅性: どれかの操作ができるか、終端である。
  val discussionCoverage =
    rule(status, Ship) == Allowed or rule(status, Cancel) == Allowed or isTerminal(status)

  // より強い網羅性: すべての操作について、許可か禁止かが決まっている。
  val everyOpDecided = Ops.forall(op => rule(status, op) != Unspecified)

  // 個別の空白。破れれば、その組み合わせに到達できて、かつ未決定。
  val unpaidShipDecided = not(status == Unpaid and rule(status, Ship) == Unspecified)
  val paidPayDecided = not(status == Paid and rule(status, Pay) == Unspecified)
  val paidCancelDecided = not(status == Paid and rule(status, Cancel) == Unspecified)

  // 議論の空白を固定する: 支払い済み・発送前のキャンセルは未決定。
  run paidCancelIsUndecidedTest =
    init
      .then(all { rule(status, Pay) == Allowed, status' = after(status, Pay) })
      .expect(status == Paid and rule(status, Cancel) == Unspecified)
}
