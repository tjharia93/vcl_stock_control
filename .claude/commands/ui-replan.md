---
description: Replan a VCL Stock Portal screen's UI/UX before touching code
argument-hint: [screen: dashboard|entry|review|brand|all]
allowed-tools: Read, Bash, Glob, Grep, AskUserQuestion, Agent, mcp__5ec79ce7-5c8f-45e8-a499-035f4e21de5c__notion-search, mcp__5ec79ce7-5c8f-45e8-a499-035f4e21de5c__notion-fetch, mcp__5ec79ce7-5c8f-45e8-a499-035f4e21de5c__notion-create-pages, mcp__5ec79ce7-5c8f-45e8-a499-035f4e21de5c__notion-update-page
---

You are helping the user replan a screen of the VCL Stock Portal. **Do not write or edit any code in this command — this is a planning loop only.** The user will explicitly ask you to implement after a plan is agreed.

## Argument

The user invoked `/ui-replan` with: `$ARGUMENTS`

Map the argument to one or more screens:

| Arg | Screens |
|---|---|
| `dashboard` | `vcl_stock_control/www/stock-portal/index.html` + `.py` |
| `entry` | `vcl_stock_control/www/stock-portal/sheet/[name].html` + `.py` + `vcl_stock_control/public/js/portal_sheet.js` |
| `review` | `vcl_stock_control/www/stock-portal/review/[name].html` + `.py` + `vcl_stock_control/public/js/portal_review.js` |
| `brand` | `vcl_stock_control/public/css/portal.css` |
| `all` (or empty) | every file above |

If the argument is missing or unclear, use `AskUserQuestion` to ask which screen(s) the user wants to replan and why.

## Step 1 — Ground yourself in the current state

For each in-scope screen:

1. **Read** the template, controller, CSS and JS files. Don't summarise from memory.
2. Note the current layout, the data it depends on, the API endpoints it calls, and any constraints baked into the architecture (state machine, coverage check, kill switch, Item Map indirection — these are non-negotiable from the dev brief).
3. Build a one-paragraph "what this screen does today" summary you can show the user.

## Step 2 — Gather what the user wants different

Use `AskUserQuestion` (one question per topic, max 4 at a time) to surface what specifically they're unhappy with. Useful prompts:

- What's the single biggest pain point on this screen?
- Density vs. clarity — too cramped, too sparse, or right?
- Which workflow takes too many clicks / taps?
- Mobile vs. desktop — which is the primary device?
- Any reference designs or competitors they like?

If they say "I'll know it when I see it", offer 2–3 concrete redesign directions and let them pick.

## Step 3 — Look for references

Ask if there's a prototype HTML, Figma link, screenshot, or competitor app to mirror. The dev brief mentioned `vcl_stock_portal_prototype.html` as the visual spec — check whether it now exists in the repo at `vcl_stock_control/docs/prototype.html` or anywhere reachable. If the user pastes a URL or path, fetch it.

## Step 4 — Draft a redesign plan, not code

Produce a structured plan per screen:

```
## <screen> redesign

### Problem
<2–3 sentences on what's wrong today>

### Direction
<the chosen approach in 2–3 sentences>

### Layout
<bulleted list of regions / components / interactions>

### Data + behaviour
<which API endpoints, what changes (if any), state transitions involved>

### What stays
<the non-negotiables that survive — state machine, coverage check, Item Map, brand colors>

### Open questions
<things still ambiguous>
```

Show the plan(s) to the user. Iterate until they approve.

## Step 5 — Save the plan

Once the user approves a direction, ask whether to save it to Notion as a child of the Dev Brief (page id `35c8e0265cd5813db2f0c1017e245f61`). If yes, create a page titled "UI Replan — <screen> — <YYYY-MM-DD>" and write the plan into it. Return the URL.

Do **not** start implementing. End with: *"Plan saved. Ask me to implement when you're ready."*

## Style

- Be brief. Plans should fit on one screen each.
- Don't dress up uncertain ideas as decisions — flag open questions explicitly.
- Don't add features the user didn't ask for. The brief is already large.
- If the user starts asking for code changes mid-plan, stop and confirm: "Want me to implement the current draft, or keep planning?"
