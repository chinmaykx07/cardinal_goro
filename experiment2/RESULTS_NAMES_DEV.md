# P0-4 dev result: name and place checking

**Status: a dev result on synthetic names, not a final one.** The list of allowed case endings is a draft that a native speaker has not yet reviewed (issues #4 and #9).

Run: 31 Oct 2026. Command: `python3 -I name_eval.py 10000 20261031`. Full output: `name_run.txt`.

## The rule (fail-closed)
A record's name counts as present only if **the whole name appears in one piece**:
- its words are in the record's order, separated only by spaces;
- it is not preceded by a letter;
- after the last word, at most one ending from `src/marathi_suffixes.txt` is allowed, followed by a word boundary.

Anything else counts as absent, the draft is rejected, and the template is used instead. Places follow the same rule.

## What changed, and why
The previous check looked for each name part separately, anywhere in the message. A control run shows how dangerous that was: for a message naming **the wrong person** (अनिता पाटील) that also mentions "सुनीता नगर" in an address, **the old check accepted 500 of 500**. The new check rejects all of them.

## Result (10,000 synthetic records per class)
| | Classes | Wrong decisions | 95% upper bound per class |
|---|---|---|---|
| **Must pass** (wrong = false reject): exact name and place; name or place + allowed ending; extra spaces | 4 | 0 | 0.04% |
| **Must fail** (wrong = false accept): letter substituted, deleted or inserted inside a word; vowel sign changed; different person; surname replaced; name inside a longer word (राम / रामचंद्र); surname belongs to someone else with the first name elsewhere; different place | 13 | 0 | 0.04% to 0.05% |

**Rejected by design**: correct Marathi that the rule refuses, which costs only a template fallback.
- Oblique vowel + ending (रामाला, सुनीताने with ा): rejected 100%.
- Name parts in another order (पाटील सुनीता): rejected 100%.
- Stem changes (पाटील → पाटलांना, पुणे → पुण्याला): rejected (unit tests).

These are false rejects we accept on purpose. Allowing the oblique vowel would let राज match inside राजाला, which names a different person (राजा).

## Collision check
No name, surname or place in the test lists equals another one plus an allowed ending.

## What this does NOT show
- **Real names.** The names are synthetic combinations of 40 first names, 30 surnames and 25 places. A large real list could contain collisions (A + ending = B). Before relying on this, run the collision check on a real list.
- **Native review of the endings.** Until the ending list is reviewed, a correct form may be missing (a false reject) or a risky one present (a possible false accept).
- **Real generated text.** The wording comes from the three provisional templates.
- **Transliterated or English names**, initials (स. रा. पाटील), honorifics and spelling variants that are the same person: all are rejected (fail-closed), and their real-world frequency is unknown.
