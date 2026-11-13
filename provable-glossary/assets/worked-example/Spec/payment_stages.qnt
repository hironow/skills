// 「支払い済み」を分ける。
//
// 業界の実務では、「支払い済み」は 1 つの状態ではない。
//   - 与信済み: カード会社が枠を押さえた。期限がある。まだお金は動いていない。
//   - 売上確定済み: 事業者が請求を確定した。
// 事業者は与信だけ取って発送する。問題は、売上の確定をいつ行うかである。
module payment_stages {
  const AUTH_TTL: int             // 与信の有効期間 (tick)
  const CAPTURE_AT_SHIP: bool     // true: 発送と同時に売上を確定する。false: 発送の後で確定する。

  type Payment = NotPaid | Authorized(int) | Captured | Expired

  var payment: Payment
  var shipped: bool

  pure def isAuthorized(p: Payment): bool =
    match p {
      | Authorized(_) => true
      | _ => false
    }

  action init = all { payment' = NotPaid, shipped' = false }

  action authorize = all {
    payment == NotPaid,
    not(shipped),
    payment' = Authorized(AUTH_TTL),
    shipped' = shipped,
  }

  // 与信が生きているあいだだけ発送できる。
  action ship = all {
    isAuthorized(payment),
    not(shipped),
    shipped' = true,
    payment' = if (CAPTURE_AT_SHIP) Captured else payment,
  }

  action capture = all {
    isAuthorized(payment),
    payment' = Captured,
    shipped' = shipped,
  }

  // 時間が進む。与信の残りが尽きると、与信は失効する。
  action tick = all {
    payment' = match payment {
      | Authorized(left) => if (left <= 1) Expired else Authorized(left - 1)
      | _ => payment
    },
    shipped' = shipped,
  }

  action step = any { authorize, ship, capture, tick }

  // 発送した注文の代金は、回収できなくなっていない。
  val shippedIsCollectible = not(shipped and payment == Expired)

  // 発送した注文は、売上が確定している。
  val shippedIsCaptured = shipped implies payment == Captured
}

// 発送と同時に売上を確定する。
module capture_at_ship {
  import payment_stages(AUTH_TTL = 2, CAPTURE_AT_SHIP = true).*
}

// 発送の後で売上を確定する。
module capture_after_ship {
  import payment_stages(AUTH_TTL = 2, CAPTURE_AT_SHIP = false).*

  // 与信で発送し、確定する前に与信が切れる。
  run shippedButExpiredTest =
    init.then(authorize).then(ship).then(tick).then(tick)
      .expect(shipped and payment == Expired)
}
