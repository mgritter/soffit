# Ideas on rule application

Given a set of rules

```
X -> [A, B, C]
Y -> [D, E]
```

how should we choose which possible application to apply next?

1. Equal weighting by complete rule

Pick a left and right hand uniformly from the available pairs, then try to apply it.
If no match exists, pick another rule from the bag and try again.

Pick the match uniformly from all constraint satisfaction outputs.

This is uniform choice across [X->A, X->B, X->C, Y->D, Y->E], then uniform choice across all
possible X's or Y's.

In the example, if all are available, then we do each with 20% probability.

This could easily be expanded with a "share" influencing which rule gets picked more.

2. Equal weighting by left-hand graphs

Pick a left hand, try to apply it.  Pick one of the results uniformly.

This gets a little tricky with A deletes but B and C don't because they could be applied
in different situations.  We could initially select uniformly from {X, Y}.  Then uniformly from
{A, B, C}.  If we fail with X->A then we try X->C, then X->B, then back up to the next level of
the "tree" and try again.

Uniformly at "root" = left hand sides
Uniformly at "intermediate" = right hand sides
Uniformly at "leaf" = possible matches

In the example, if all are avaialable, then we do the B rules with 25% probability each and the
A rules with 16.7% probability.

A user-controlled "share" would only impact the choice of left sides, or the choice of right
sides, not both simultaneously.

3. Equal weighting by application site and right-hand side.

Find all possible matches G<-(L->R), and pick uniformly from those tuples.

This seems very expensive.  A rule which can be applied in many locations would then get
a higher probability of firing, compared to one which has a unique condition.
This seems possibly bad?

4a + 4b. Round-robin application across left-hand sides, or around pairs

Give every rule a chance to fire in some order; if it doesn't match, it'll get another chance later.

## Other systems

What the heck do other software packages do?

### AGG

http://www.user.tu-berlin.de/o.runge/agg/AGG-ShortManual/node29.html

> The order of rules to be applied is defined non-deterministically in general. Starting the interpretation by clicking on the Start button in menu Transform, a rule is chosen randomly and applied. Thereafter, the next rule is chosen randomly and applied, and soon. 

This corresponds to option 1, I think?  Different rules can be defined with the same left graph.

### HOPS

http://www.cas.mcmaster.ca/~kahl/HOPS/

Deterministic, I think?

