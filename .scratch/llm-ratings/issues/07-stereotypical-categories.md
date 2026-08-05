# 07 Stereotypical categories

Type: grilling
Blocked by: 05
Status: resolved

## Question

What are the stereotypical use-case categories — generalized from OMP's smol/default/plan/slow — and how does each map onto the data axes (quality, price, speed, reasoning effort)? Context: the user's selection mental model is "do I need it cheap? fast? reasoning at which effort?"; anchor example: DeepSeek Flash ≈ ChatGPT Luna 5.6 at high/extra-high effort but far cheaper, yet the expensive model wins when the best reasoning matters.

## Answer

Five categories, consolidated from OMP's actual consumption slots (10 model roles — default, smol, slow, vision, plan, designer, commit, tiny, task, advisor — and 7 bundled agents — scout, designer, reviewer, security-reviewer, librarian, task, sonic), named by stereotype rather than OMP naming. Each category maps onto the data axes as a profile; the OMP slots that consume it are folded in:

| Category | Axis profile | OMP slots |
|---|---|---|
| Chores | cheap >> fast; minimal reasoning; quality floor only | smol, tiny, commit, scout, sonic |
| Everyday | balanced on all four | default, task |
| Deliberate | high reasoning; quality over price; speed flexible | plan |
| Deep | max reasoning; best quality wins; price/speed irrelevant | slow, reviewer, security-reviewer, librarian |
| Best Value | best intelligence per dollar at high effort | advisor |

- **Vision is a tag, not a category**: image-input support is a hard capability orthogonal to the quality/price/speed/effort axes; it filters models rather than ranking them. designer + vision slots are served by picking from the other categories among vision-tagged models.
- The anchor example splits across two categories: Best Value is DeepSeek Flash ≈ ChatGPT Luna at high/extra-high effort but far cheaper; Deep is where the expensive model still wins.
- Named per grilling: Quick → Chores, Value → Best Value, Vision → tag.
- Glossary updated in CONTEXT.md.
