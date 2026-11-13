// 時間つきのチケット販売モデル。上映回 1 つ、座席 1 つ、顧客 2 人 (c1, c2)。
// 時間は tick で進む。仮確保には残り時間があり、決済サービスの応答と緊急メンテナンスには上限がある。
module timed_sale {
  const TTL: int          // 仮確保の有効期間
  const EXT: int          // 決済を始めたときに仮確保へ足す延長
  const LAT: int          // 決済サービスが結果を返すまでの最大 tick
  const MAINT: int        // 緊急メンテナンスの最大継続 tick (0 なら起きない)
  const FREEZE: bool      // メンテナンス中は仮確保の残り時間を減らさない
  const REACQUIRE: bool   // 仮確保を失った顧客の決済成功を処理するとき、座席が空いていれば取り直す

  type Pay = NoPay | Pending(int) | Paid | Ticketed | Refunded
  type Hold = Free | Held({ who: str, left: int }) | Sold(str)
  type Site = Up | Down(int)

  pure val Customers = Set("c1", "c2")

  var site: Site
  var hold: Hold
  var pay: str -> Pay
  var maintenanceUsed: bool   // 緊急メンテナンスは 1 回だけ起きる

  pure def heldBy(h: Hold, c: str): bool =
    match h {
      | Free => false
      | Held(x) => x.who == c
      | Sold(w) => w == c
    }

  // c が仮確保しているなら残り時間、そうでなければ 0
  pure def holdLeft(h: Hold, c: str): int =
    match h {
      | Held(x) => if (x.who == c) x.left else 0
      | _ => 0
    }

  pure def isPending(p: Pay): bool =
    match p {
      | Pending(_) => true
      | _ => false
    }

  pure def pendingAtLimit(p: Pay, limit: int): bool =
    match p {
      | Pending(e) => e >= limit
      | _ => false
    }

  pure def canSucceed(p: Pay): bool =
    match p {
      | Pending(e) => e >= 1
      | _ => false
    }

  pure def tickPay(p: Pay): Pay =
    match p {
      | Pending(e) => Pending(e + 1)
      | _ => p
    }

  pure def isDown(s: Site): bool =
    match s {
      | Up => false
      | Down(_) => true
    }

  val someoneTicketed = Customers.exists(c => pay.get(c) == Ticketed)

  // 決済成功の処理で座席を得られるか: 確保中である、または取り直せる。
  def getsSeat(c: str): bool =
    heldBy(hold, c) or (REACQUIRE and hold == Free and not(someoneTicketed))

  action init = all {
    site' = Up,
    hold' = Free,
    pay' = Customers.mapBy(c => NoPay),
    maintenanceUsed' = false,
  }

  action reserve(c: str): bool = all {
    site == Up,
    hold == Free,
    pay.get(c) == NoPay,
    not(someoneTicketed),
    hold' = Held({ who: c, left: TTL }),
    pay' = pay, site' = site, maintenanceUsed' = maintenanceUsed,
  }

  action startPayment(c: str): bool = all {
    site == Up,
    pay.get(c) == NoPay,
    holdLeft(hold, c) > 0,
    hold' = Held({ who: c, left: holdLeft(hold, c) + EXT }),
    pay' = pay.set(c, Pending(0)),
    site' = site, maintenanceUsed' = maintenanceUsed,
  }

  // 決済サービスが成功を返す。サイトの状態に関係なく起きる。開始から 1 tick 以上かかる。
  action providerSucceeds(c: str): bool = all {
    canSucceed(pay.get(c)),
    pay' = pay.set(c, Paid),
    hold' = hold, site' = site, maintenanceUsed' = maintenanceUsed,
  }

  // 決済サービスが失敗を返す。失敗した顧客がまだ仮確保を持っていれば、その仮確保は解放される。
  action providerFails(c: str): bool = all {
    canSucceed(pay.get(c)),
    pay' = pay.set(c, NoPay),
    hold' = if (holdLeft(hold, c) > 0) Free else hold,
    site' = site, maintenanceUsed' = maintenanceUsed,
  }

  // 決済成功を処理する。サイトが動いているときだけ。
  action settle(c: str): bool = all {
    site == Up,
    pay.get(c) == Paid,
    pay' = pay.set(c, if (getsSeat(c)) Ticketed else Refunded),
    hold' = if (getsSeat(c)) Sold(c) else hold,
    site' = site, maintenanceUsed' = maintenanceUsed,
  }

  action detectVulnerability = all {
    site == Up,
    MAINT > 0,
    not(maintenanceUsed),
    site' = Down(0),
    maintenanceUsed' = true,
    hold' = hold, pay' = pay,
  }

  // 復旧する。メンテナンスは少なくとも 1 tick 続く。
  action recover = all {
    match site {
      | Up => false
      | Down(m) => m >= 1
    },
    site' = Up,
    hold' = hold, pay' = pay, maintenanceUsed' = maintenanceUsed,
  }

  // 時間が 1 tick 進む。次の 3 つの場合は進まない (先に別の操作が起きる)。
  //   - サイトが動いていて、処理待ちの決済成功がある。
  //   - 応答待ちの決済が上限 LAT に達している。
  //   - メンテナンスが上限 MAINT に達している。
  action tick = all {
    not(site == Up and Customers.exists(c => pay.get(c) == Paid)),
    not(Customers.exists(c => pendingAtLimit(pay.get(c), LAT))),
    match site {
      | Up => true
      | Down(m) => m < MAINT
    },
    pay' = pay.keys().mapBy(c => tickPay(pay.get(c))),
    site' = match site {
      | Up => Up
      | Down(m) => Down(m + 1)
    },
    hold' = match hold {
      | Held(x) =>
        if (FREEZE and isDown(site)) hold
        else if (x.left <= 1) Free
        else Held({ who: x.who, left: x.left - 1 })
      | _ => hold
    },
    maintenanceUsed' = maintenanceUsed,
  }

  action step = any {
    nondet c = Customers.oneOf()
    any { reserve(c), startPayment(c), providerSucceeds(c), providerFails(c), settle(c) },
    detectVulnerability, recover, tick,
  }

  // Q1: 入場権を得た顧客は高々 1 人。
  val Q1 = Customers.filter(c => pay.get(c) == Ticketed).size() <= 1

  // Q2: 返金された顧客はいない。
  val Q2 = Customers.forall(c => pay.get(c) != Refunded)

  // Q3: 決済が成功して処理待ちの顧客は、座席を確保している。
  val Q3 = Customers.forall(c => pay.get(c) == Paid implies heldBy(hold, c))

  // Q4: 決済の応答待ちの顧客は、座席を確保している。
  val Q4 = Customers.forall(c => isPending(pay.get(c)) implies heldBy(hold, c))
}
