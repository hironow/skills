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

end Glossary
