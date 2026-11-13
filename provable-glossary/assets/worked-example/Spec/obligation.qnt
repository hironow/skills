// Take 2・3 (要約からの再構成): 履行義務と、その解決に必要な責任・権限・進行可能性
//
// Take 2 の要約: 購入後には顧客への履行義務が残る。
// Take 3 の要約: 義務の解決には責任・権限・進行可能性が必要。
//
// 範囲: 入場権を持つ顧客 1 人、上映回 1 つ。上映が中止になりうる。
// 解決の手段は 2 つ。振替は販売の文脈が行い、空席とサイトの稼働が要る。
// 返金は決済の文脈だけが行える。
//
// 設計の変種を 3 つのスイッチで表す。
//   TRACK         上映中止のとき、入場権を「履行義務あり」に変える
//   ASSIGN_OWNER  履行義務に解決責任者を割り当てる (最初は販売)
//   HANDOFF       販売が振替できないとき、決済に引き継げる
module obligation {
  const TRACK: bool
  const ASSIGN_OWNER: bool
  const HANDOFF: bool

  type Ob = Sold | Attended | Owed | Rebooked | Refunded
  type Owner = NoOwner | Sales | Payment
  type Site = Open | Blocked

  var ob: Ob
  var owner: Owner
  var site: Site
  var cancelled: bool
  var spare: bool   // 振替に使える空席があるか

  action init = all {
    ob' = Sold,
    owner' = NoOwner,
    site' = Open,
    cancelled' = false,
    nondet s = Set(true, false).oneOf()
    spare' = s,
  }

  action attend = all {
    ob == Sold, not(cancelled),
    ob' = Attended,
    owner' = owner, site' = site, cancelled' = cancelled, spare' = spare,
  }

  action cancelScreening = all {
    ob == Sold, not(cancelled),
    cancelled' = true,
    ob' = if (TRACK) Owed else Sold,
    owner' = if (ASSIGN_OWNER) Sales else NoOwner,
    site' = site, spare' = spare,
  }

  action rebook = all {
    ob == Owed, owner == Sales, site == Open, spare,
    ob' = Rebooked,
    spare' = false,
    owner' = owner, site' = site, cancelled' = cancelled,
  }

  // 返金の権限は決済の文脈だけにある。
  action refund = all {
    ob == Owed, owner == Payment,
    ob' = Refunded,
    owner' = owner, site' = site, cancelled' = cancelled, spare' = spare,
  }

  action handoff = all {
    HANDOFF, ob == Owed, owner == Sales, not(spare),
    owner' = Payment,
    ob' = ob, site' = site, cancelled' = cancelled, spare' = spare,
  }

  action emergency = all {
    site == Open, site' = Blocked,
    ob' = ob, owner' = owner, cancelled' = cancelled, spare' = spare,
  }

  action recover = all {
    site == Blocked, site' = Open,
    ob' = ob, owner' = owner, cancelled' = cancelled, spare' = spare,
  }

  action step = any { attend, cancelScreening, rebook, refund, handoff, emergency, recover }

  // Take 2: 中止になった上映回の入場権は、履行義務として数えられている。
  val cancelledIsOwed = cancelled implies (ob == Owed or ob == Rebooked or ob == Refunded)

  // Take 3 (責任): 未解決の履行義務には解決責任者がいる。
  val owedHasOwner = ob == Owed implies owner != NoOwner

  // Take 3 (権限と進行可能性): 未解決の履行義務には、責任者が実行できる解決の道がある。
  // 振替はサイトの復旧を待つことがあるが、道そのものは残っている。
  val owedCanProgress = ob == Owed implies or {
    owner == Sales and spare,
    owner == Payment,
    HANDOFF and owner == Sales and not(spare),
  }

  val Safety = cancelledIsOwed and owedHasOwner and owedCanProgress

  // 活性: 解決の操作が公平に実行されるなら、履行義務はいつか必ず解決する。
  // 振替は緊急メンテナンスで何度も止められうるので、強い公平性を仮定する。
  val vars = (ob, owner, site, cancelled, spare)
  temporal fairResolution =
    weakFair(refund, vars) and weakFair(handoff, vars) and strongFair(rebook, vars)
  temporal resolves = always(ob == Owed implies eventually(ob != Owed))
  temporal Liveness = fairResolution implies resolves

  // 復旧がいつか必ず来る、という仮定を足した版。
  temporal LivenessGivenRecovery = (fairResolution and weakFair(recover, vars)) implies resolves
}

// 変種 0: 購入完了を終点とみなす。履行義務という概念がない。
module ob0_no_obligation {
  import obligation(TRACK = false, ASSIGN_OWNER = false, HANDOFF = false).*

  run cancelledTicketIsForgottenTest =
    init.then(cancelScreening).expect(cancelled and ob == Sold and not(cancelledIsOwed))
}

// 変種 1: 履行義務はあるが、誰のものでもない。
module ob1_no_owner {
  import obligation(TRACK = true, ASSIGN_OWNER = false, HANDOFF = false).*

  run nobodyOwnsItTest =
    init.then(cancelScreening).expect(cancelledIsOwed and not(owedHasOwner))
      .then(refund).fail()
}

// 変種 2: 責任者はいるが、解決する権限がない (空席がなく、返金は決済だけができる)。
module ob2_no_authority {
  import obligation(TRACK = true, ASSIGN_OWNER = true, HANDOFF = false).*
}

// 変種 3: 引き継ぎを入れる。
module ob3_handoff {
  import obligation(TRACK = true, ASSIGN_OWNER = true, HANDOFF = true).*
}
