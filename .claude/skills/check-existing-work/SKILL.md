---
name: check-existing-work
description: >-
  Use before starting any new task in ADIRO, when starting work on an existing issue, and before creating a new
  issue or Discussion. Search the repository's issues (open and closed), pull requests and Discussions for the same
  topic first, read the hits including their comments, and reuse what was already decided, so the work is not
  duplicated and an earlier conclusion is not reopened by accident.
---

# ADIRO — check what already exists before you start

The rule is in [`AGENTS.md`](../../../AGENTS.md) ("Look before you write"); this skill is the Claude Code procedure
for it. Do it at three moments: **before a new task**, **when you pick up an existing issue**, and **before you create
an issue or a Discussion**. ADIRO's decisions live in issue and Discussion threads, often in a comment and not in
the issue's closed state, so a search by title alone is not enough.

## 1. Pick the search terms

Take 3 to 5 from the task: the **term names** (`layoutScale`, `ReferenceExpression`), the **module** (`aec_drawing_metadata`),
the **use case** (`UC-03`) and the plain words and synonyms for the idea ("scale", "units", "measuring system"). Search
each separately: one broad query returns noise, and a decision may use a different word from yours.

## 2. Search all three places

```bash
# Issues (open AND closed); the search also matches the body and comments
gh issue list --state all --search "layoutScale" --limit 20 --json number,title,state,updatedAt \
  --jq '.[]|"#\(.number) \(.state) \(.title)"'

# Pull requests, closed ones too: a merged PR's description records what was decided and why
gh search prs --repo BuroHappoldMachineLearning/ADIRO --state all "layoutScale" --limit 10 \
  --json number,title,state --jq '.[]|"PR#\(.number) \(.state) \(.title)"'

# Discussions (design notes, research write-ups and decisions live here)
gh api graphql -f q='repo:BuroHappoldMachineLearning/ADIRO layoutScale' \
  -f query='query($q:String!){search(query:$q,type:DISCUSSION,first:10){discussionCount nodes{... on Discussion{number title closed category{name}}}}}' \
  --jq '.data.search.nodes[]|"D#\(.number) \(.category.name) \(.title)"'
```

Also search the repository for the term (`grep` over `src/`, `docs/specification/`, `docs/design-decisions/`,
`changelogs/`): a decision is often recorded in a design-decision page and not only in a thread.

## 3. Read what you found, comments included

For each plausible hit, read the whole thread, not the title:

```bash
gh issue view <N> --comments
gh pr view <N> --comments
gh api graphql -f query='query{repository(owner:"BuroHappoldMachineLearning",name:"ADIRO"){discussion(number:<N>){title body comments(first:50){nodes{body author{login}}}}}}'
```

Look for a **decision** (a comment that settles a question), an **open question** nobody has answered, a **rejected
option** and the reason it was rejected, and a **hand-off** ("left for #N").

## 4. Decide, and say what you found

| What you find | What to do |
|---|---|
| An open issue or Discussion that covers the same thing | Do not open another. Work on it, or add your point as a comment there. |
| A closed issue or Discussion with a decision | Follow it and cite it (`as decided in #N`). If you disagree, raise it as a question on that thread, with a reason. Do not reopen it silently by building the opposite. |
| A related issue (same area, different question) | Link it (`Related: #N`) in your issue or PR, and reuse its conclusions. |
| Two threads that disagree | Ask the user which stands before you build on either. |
| Nothing | Say so, and name what you searched for, so the user can judge how hard you looked. |

Start your reply to the user with a short list: each hit as `#N` and one line of what it settles, or "nothing found"
with the search terms. A search that was run but not reported cannot be checked.

## Rules

- **Link every issue and Discussion you mention** as a full URL, as `AGENTS.md` requires.
- **Verify before you cite.** An issue reference is a claim about current state: read the thread, do not trust the title.
- **Public repository.** Everything you write on an issue or a Discussion is world-readable: no internal tool names, no
  internal tracker IDs, no client or project names (`AGENTS.md`, "Keep YouTrack out of every public place").
- **A new issue still follows the issue rules.** Once the search shows the topic is new, open it on GitHub, with the
  related issues linked.
