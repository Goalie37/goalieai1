# Situation Relationship Graph

Traversable model of how **situations**, **cues**, **threats**, **reads**, and **outcomes** connect. The agent and teach-back flow cite edges from this graph.

Machine-readable mirror: [situation_graph.json](situation_graph.json)

---

## Node Types

| Type | Examples |
|------|----------|
| `situation_family` | odd_man_rush, east_west_seam, point_shot_traffic |
| `cue` | middle_drive_stick_ready, open_seam, layered_screen |
| `threat` | cross_crease_pass, one_timer, tip_redirect, wrap |
| `goalie_read` | delay, challenge, post_lean_rvh, lateral_load |
| `outcome` | goal, save_rebound, freeze, second_chance |

---

## Edge Types

| Edge | Meaning | Example |
|------|---------|---------|
| `often_follows` | Trend in play development | oz_cycle_low → low_to_high |
| `enables` | Cue makes threat live | open_seam → one_timer |
| `supports_read` | Cue + situation favor read | late_backchecker + odd_man_rush → delay |
| `contradicts_read` | Cue + situation break read | open_middle + challenge → cross_crease |
| `branches_to` | Option tree | delay → shot_branch \| pass_branch \| deke_branch |

---

## Core Relationships by Situation Family

### odd_man_rush

```
odd_man_rush --often_follows--> controlled_entry
middle_drive_stick_ready --enables--> cross_crease_pass
cross_crease_pass --contradicts_read--> challenge_carrier
late_backchecker --supports_read--> delay
delay --branches_to--> shot_branch
delay --branches_to--> pass_branch
delay --branches_to--> deke_branch
challenge_carrier --contradicts_read--> delay (when pass lane open)
```

### east_west_seam

```
east_west_seam --often_follows--> low_to_high
open_seam --enables--> one_timer
pass_across_royal_road --enables--> one_timer
lateral_load --supports_read--> east_west_seam
challenge_carrier --contradicts_read--> east_west_seam (when seam open)
```

### point_shot_traffic

```
point_shot_traffic --often_follows--> controlled_entry
layered_screen --enables--> tip_redirect
tip_redirect --contradicts_read--> aggressive_challenge
deep_set --supports_read--> point_shot_traffic
hands_high --supports_read--> point_shot_traffic
```

### oz_cycle_low

```
oz_cycle_low --often_follows--> net_front_chaos
puck_below_goal_line --enables--> wrap
wrap --supports_read--> post_lean_rvh
poke_behind_net --contradicts_read--> post_lean_rvh (when you don't own puck)
```

### low_to_high

```
low_to_high --often_follows--> oz_cycle_low
low_to_high --often_follows--> point_shot_traffic
puck_to_point --enables--> point_shot_traffic
reset_depth --supports_read--> low_to_high
```

### net_front_chaos

```
net_front_chaos --branches_to--> rebound_branch
net_front_chaos --branches_to--> freeze_branch
net_front_chaos --branches_to--> steer_safe_branch
crash_present --enables--> second_chance
```

### breakaway

```
breakaway --branches_to--> shot_branch
breakaway --branches_to--> deke_branch
patient_delay --supports_read--> breakaway
early_drop --contradicts_read--> breakaway (deke high)
```

---

## Read Template Relationships

| Read | Supports when | Contradicted when |
|------|---------------|-------------------|
| delay | Pass lane live, backchecker late | Carrier alone, shot committed |
| challenge | No pass option, shot imminent | Open seam, middle drive ready |
| lateral_load | East-west pass in flight or imminent | Puck static on wall, no seam |
| post_lean_rvh | Puck below goal line, wrap threat | Quick pass out to point |
| deep_set | Screen layers, tip threat | Clean point shot, no traffic |

---

## Agent Usage

On **coach reveal**, output **Relationship Map** — 3–5 edges from this graph that apply to the still, formatted:

> `[situation]` + `[cue]` → **enables** `[threat]` → **supports** or **contradicts** `[read]`

On **teach-back review**, validate whether the user stated at least one valid edge; flag missing `enables` or `contradicts_read` links.

---

*Graph version: 1.0*
