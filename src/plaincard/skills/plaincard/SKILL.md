---
name: plaincard
description: Use when a project needs an image people will see - a project card for a portfolio or a repo's social preview, a header banner for a README, a diagram for a README, doc or post, or a square icon - or when replacing such an image. plaincard draws it in one plain, consistent style from a few lines of spec. It is the first option for any image whose audience is people or a community, not the only one.
---

# plaincard

plaincard makes plain, consistent images from a short spec: a dark background, the name in a
monospace face, one line in plain words, and a small flat line drawing of what the thing does, with
one accent colour. Every image made with it looks like it belongs with the others.

## When to use it

- A project needs a card (a portfolio page, GitHub's social preview, a post about the project).
- A README needs a header banner, or an architecture or flow diagram.
- An existing image in a README or on a project page is the generic GitHub card, a screenshot of
  nothing, or missing.
- Something needs a small square icon.

It is the first option, not the only one. A real screenshot of a real interface usually says more
than a drawing; use plaincard when there is nothing to screenshot or the screenshot says little.

## How

1. Write a spec, in the project at `.plaincard/<name>.yaml`:

   ```yaml
   kind: card                  # card 1280x640 | banner 1600x400 | diagram 1200x480 | icon 512x512
   name: sqlgate               # cards and banners
   line: "Serve a database you host yourself to serverless apps over HTTPS."
   accent: green               # clay blue amber green violet teal rose sky, or #rrggbb
   footer: github.com/drkostas/sqlgate      # optional, cards
   caption: How a request reaches the database   # optional, diagrams
   diagram:                    # parts left to right, joined by edges
     - cloud
     - arrow: https            # arrow | dots | line, with an optional label
     - gate                    # a gate, lock, check and remote are lit by default
     - line
     - db: {label: postgres, accent: true}
   ```

   `plaincard parts` lists every part and its options (`panes: {rows, cols, highlight}`,
   `phone: {model: ios|android, rows, shows: lock|check}`, `tv: {tiles, crossed, highlight}`,
   `laptop: {shows}`, `box: {text}` and the rest). `plaincard example card|banner|diagram|icon`
   prints a starting spec.

2. Render it: `plaincard render .plaincard/<name>.yaml -o <images folder>`, or the MCP tool
   `render_image`. It writes `<name>.svg` and `<name>.png` (twice the size, for sharp screens).

3. **Open the PNG and look at it** before using it. Check that the drawing says what the project
   does, that the one accented part is the point, and that nothing is crowded.

4. Reference the PNG from the README or page, and commit the spec with it so the image can be drawn
   again later.

## Writing the line and the drawing

- The line says what the project does for the reader, in plain words. One or two short sentences.
  Put it in quotes when it contains a colon.
- Draw what the thing does, not what it is built with: the request going through the gate, the
  message reaching one chat among many, the item moving from one phone to the other.
- One accent per image. Accent the part that is the point; everything else stays quiet.
- Fewer parts read better. Three to five items is usually right.
- No gradients, glows, emoji or clip art. If a part is missing, use `box: {text: ...}` rather than
  inventing decoration.

## Errors

plaincard refuses rather than drawing something broken: an unknown part or option, two edges in a
row, a name too long for the kind, a line too long for two or three lines, or YAML it cannot read
(usually a colon in unquoted text). The message says what to change.
