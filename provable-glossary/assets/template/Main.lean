import Glossary.Registry

/-!
Prints the list of checks and writes the generated documents.
  claims gate        the Quint checks, tab-separated: expectation, kind, file, module, property
  claims docs <dir>  write the generated documents into <dir>
  claims anchors     the code anchors, tab-separated: term ID, anchor
  claims terms       every term ID, one per line

This file is the same for every domain. Register glossaries in `Glossary/Registry.lean`.
-/

open Glossary

def main (args : List String) : IO UInt32 := do
  match args with
  | ["gate"] =>
    for l in books.flatMap (·.gate) do
      IO.println l
    return 0
  | ["docs", dir] =>
    IO.FS.createDirAll dir
    let docs := generatedDocs labels books
    -- Drop files that are no longer generated, so the folder holds exactly the current output.
    for entry in (← System.FilePath.readDir dir) do
      if !(docs.any (·.1 == entry.fileName)) && !(← entry.path.isDir) then
        IO.FS.removeFile entry.path
    for (name, lines) in docs do
      IO.FS.writeFile (System.FilePath.mk dir / name) ("\n".intercalate lines ++ "\n")
    return 0
  | ["anchors"] =>
    for l in anchorLines books do
      IO.println l
    return 0
  | ["terms"] =>
    for l in termIds books do
      IO.println l
    return 0
  | _ =>
    IO.eprintln "usage: claims (gate | docs <dir> | anchors | terms)"
    return 2
