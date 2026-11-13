import Glossary

/-! 証明が使う公理を出力する。`just lean-check` が `sorryAx` などを拒否する。 -/

#print axioms Glossary.check_sound
#print axioms Glossary.check_add
#print axioms Glossary.PaidStages.paid_is_not_one_notion
#print axioms Glossary.OrderBook.book
#print axioms Glossary.OrderBook.book_check
#print axioms Glossary.OrderBook.terms_wellFormed
#print axioms Glossary.Cinema.book
#print axioms Glossary.Cinema.book_check
#print axioms Glossary.Cinema.terms_wellFormed
#print axioms Glossary.Cinema.pendingIssuance_added
#print axioms Glossary.Cinema.sales_payment_depend_on_each_other
#print axioms Glossary.Progress.resolvable
#print axioms Glossary.Autonomy.enough_determined
#print axioms Glossary.Autonomy.short_not_determined
