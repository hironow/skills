import Glossary.Core

/-!
# Claims and evidence

Every claim in a glossary carries exactly one piece of evidence.
- Lean evidence holds the proof itself as a value. Without a proof this file does not compile.
- Quint evidence names a spec file, a module, and an invariant. `just check` runs that list as it is.
- An undecided claim is a question for the domain experts.

This file is the same for every domain. Do not edit it per project.
-/

namespace Glossary

/-- Where a Quint invariant lives. -/
structure QuintRef where
  file : String
  main : String
  invariant : String
  /-- Whether this is a temporal (liveness) property. If false, it is an invariant. -/
  temporal : Bool := false

inductive Evidence where
  /-- Proved in Lean. -/
  | lean (name : String) (prop : Prop) (proof : prop)
  /-- The negation is proved in Lean. -/
  | leanRefutes (name : String) (prop : Prop) (proof : ¬ prop)
  /-- Holds in every reachable state of the model, checked by Quint + TLC. -/
  | holds (ref : QuintRef)
  /-- The Quint simulator finds a counterexample. -/
  | violated (ref : QuintRef)
  /-- A question for the business to decide, with counterexamples that show the gap if any. -/
  | question (witnesses : List QuintRef)

inductive Verdict where
  | proved | counterexample | undecided
  deriving DecidableEq, Repr

structure Claim (ι : Type) where
  about : List ι
  statement : String
  verdict : Verdict
  evidence : Evidence

def Evidence.verdict : Evidence → Verdict
  | .lean .. => .proved
  | .holds .. => .proved
  | .leanRefutes .. => .counterexample
  | .violated .. => .counterexample
  | .question .. => .undecided

/-- A glossary together with the claims made about it. -/
structure Book (ι κ : Type) where
  title : String
  terms : List (Entry ι κ)
  claims : List (Claim ι)

variable {ι κ : Type} [DecidableEq ι]

/-- Claims mention only terms in the glossary, and each verdict matches its kind of evidence. -/
def Book.claimsCheck (b : Book ι κ) : Bool :=
  b.claims.all fun c =>
    c.about.all (fun t => decide (t ∈ ids b.terms)) && decide (c.evidence.verdict = c.verdict)

def Book.check (b : Book ι κ) : Bool := Glossary.check b.terms && b.claimsCheck

end Glossary
