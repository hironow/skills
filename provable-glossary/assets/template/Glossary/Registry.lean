import Glossary.Render
import Glossary.Starter

/-!
# Registry

List here every glossary that the checks and the generated documents cover.

To add a glossary: add its `import` line above, and add `<Domain>.book.view labels` to `books`.
To choose the language of the generated documents: change the one line `def labels` below
(`Labels.en`, `Labels.ja`, or your own).
-/

namespace Glossary

def labels : Labels := Labels.en

def books : List BookView := [Starter.book.view labels]

end Glossary
