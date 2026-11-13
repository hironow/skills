// Take 4 (要約からの再構成): 最終的な解決だけでは、時間制約のある顧客の目的を守れない
//
// 範囲: 決済済み・発券保留取引が 1 つ。顧客の目的は「この上映回を観る」。
// 時刻は 0..3。上映開始 (履行期限) は 2。期限を過ぎると発券しても意味がなく、返金だけが残る。
// 緊急メンテナンスはいつでも始まり、いつ終わるかは決まっていない。
//
// 仮定: システムは最後の機会を見送らない。目的を守る操作が実行できる最後の時刻では、
// 時計を進める前にその操作を実行する。
//
// スイッチ:
//   BOX_OFFICE  販売経路を通さない窓口発券を認める
module deadline {
  const BOX_OFFICE: bool

  type Ob = Owed | Admitted | Refunded
  type Site = Open | Blocked

  pure val DEADLINE = 2
  pure val MAX = 3

  var now: int
  var site: Site
  var ob: Ob
  var issuedWhileBlocked: bool

  val goalPreservingEnabled = ob == Owed and now < DEADLINE and (site == Open or BOX_OFFICE)

  action init = all {
    now' = 0, site' = Open, ob' = Owed, issuedWhileBlocked' = false,
  }

  action tick = all {
    now < MAX,
    not(now == DEADLINE - 1 and goalPreservingEnabled),
    now' = now + 1,
    site' = site, ob' = ob, issuedWhileBlocked' = issuedWhileBlocked,
  }

  action issueOnline = all {
    ob == Owed, now < DEADLINE, site == Open,
    ob' = Admitted,
    now' = now, site' = site, issuedWhileBlocked' = issuedWhileBlocked,
  }

  action issueAtBoxOffice = all {
    BOX_OFFICE, ob == Owed, now < DEADLINE,
    ob' = Admitted,
    issuedWhileBlocked' = (issuedWhileBlocked or site == Blocked),
    now' = now, site' = site,
  }

  // 目的が果たせなくなった後の解決。
  action refund = all {
    ob == Owed, now >= DEADLINE,
    ob' = Refunded,
    now' = now, site' = site, issuedWhileBlocked' = issuedWhileBlocked,
  }

  action emergency = all {
    site == Open, site' = Blocked,
    now' = now, ob' = ob, issuedWhileBlocked' = issuedWhileBlocked,
  }

  action recover = all {
    site == Blocked, site' = Open,
    now' = now, ob' = ob, issuedWhileBlocked' = issuedWhileBlocked,
  }

  action step = any { tick, issueOnline, issueAtBoxOffice, refund, emergency, recover }

  // 最終的な解決: 未解決の取引には、いつでも先へ進む道がある。
  val owedCanProgress = ob == Owed implies (goalPreservingEnabled or now >= DEADLINE or now < MAX)

  // 顧客の目的: 期限を過ぎた時点で、観られなかった顧客はいない。
  val goalNotLostToTime = not(now >= DEADLINE and ob != Admitted)

  // Take 1 の性質: 遮断完了後に発券は起きない。
  val noTicketWhileBlocked = not(issuedWhileBlocked)
}

// オンライン発券だけ。最終的には返金で解決するが、顧客は映画を観られない。
module online_only {
  import deadline(BOX_OFFICE = false).*

  run maintenanceOutlastsScreeningTest =
    init.then(emergency).then(tick).then(tick)
      .expect(owedCanProgress and not(goalNotLostToTime))
      .then(refund)
      .expect(ob == Refunded and not(goalNotLostToTime))
}

// 窓口発券を認める。目的は守れるが、遮断中に発券が起きる。
module box_office {
  import deadline(BOX_OFFICE = true).*

  run lastChanceIsTakenTest =
    init.then(emergency).then(tick)
      .then(tick).fail()

  run issuedDuringCutoffTest =
    init.then(emergency).then(tick).then(issueAtBoxOffice)
      .expect(goalNotLostToTime and not(noTicketWhileBlocked))
}
