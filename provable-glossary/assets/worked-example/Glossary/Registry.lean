import Glossary.Render
import Glossary.OrderBook
import Glossary.Cinema

/-!
# 用語集の登録

検査と生成物の対象にする用語集を、ここに並べる。生成物の言語もここで選ぶ。
-/

namespace Glossary

def labels : Labels := Labels.ja

def books : List BookView := [OrderBook.book.view labels, Cinema.book.view labels]

/-- 対照実験 (道具を使わないモデルとの比較) を行った。記録は `experiments/` にある。 -/
def control : Control := .run

end Glossary
