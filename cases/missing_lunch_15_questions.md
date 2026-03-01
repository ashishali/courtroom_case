# The Missing Lunch — Ordered Questionnaire (15–18 Questions)

This sequence is designed so that **each question is asked in the correct order and to the correct suspect** to unlock all 5 evidence pieces. The game reveals at most **one evidence per answer** and has **keyword and dependency rules**—so the order below is mandatory for a full unlock.

---

## Pattern overview

| Phase | Who        | Action   | Questions      | Evidence unlocked |
|-------|------------|----------|----------------|-------------------|
| A     | **Riley**  | talk → ask | 1, 2, 3      | E1, E4            |
| B     | **Pat**    | talk → ask | 4, 5, 6, 7   | E2, E3, E5        |
| C     | **Morgan** | talk → ask | 8, 9, 10     | (none; context)   |
| D     | **Riley**  | ask only   | 11           | (reinforce)       |
| E     | **Pat**    | ask only   | 12, 13       | (reinforce)       |

**Critical path:** Riley (3 asks) → Pat (4 asks) → Morgan (3 asks) → back to Riley (1 ask) → back to Pat (2 asks).  
Total: **13 ask-questions** in this core; the optional 14–18 add backup or clarity.

---

## Exact order of play

### STEP 0: Start

- Type: **`talk Riley`**

---

### PHASE A — Riley (unlock E1 and E4)

Riley must be asked first. E1 needs a question with lunch/fridge/break room/saw/when. E4 needs at least one prior question to Riley, then a question with Morgan/bag/leave/break room.

| # | Type        | Exact question to ask | Unlocks |
|---|-------------|------------------------|--------|
| 1 | **ask** Riley | When did you last see the lunch in the fridge? | **E1** |
| 2 | **ask** Riley | What time did you notice the lunch was gone? | (builds E1; no 2nd evidence same answer) |
| 3 | **ask** Riley | What did Morgan have when they left the break room? Did their bag look different? | **E4** |

After Phase A you have **E1** and **E4**. Do **not** go to Morgan yet—Pat must get E2 before E3 can unlock.

---

### STEP: Switch to Pat

- Type: **`talk Pat`**

---

### PHASE B — Pat (unlock E2, E3, E5)

E2 needs Pat’s **first** question with break room/hallway/who/saw/Morgan/lunch. E3 needs **E2 already found** and Pat’s **second** question with alone/when/how long/Morgan/break room. E5 needs Pat’s **second** question (min_questions 2) with mop/where/hallway/break room/yourself. So: 1st ask → E2; 2nd ask → E3; 3rd ask → E5.

| # | Type      | Exact question to ask | Unlocks |
|---|-----------|------------------------|--------|
| 4 | **ask** Pat | Who did you see go into the break room during lunch? Were you in the hallway then? | **E2** |
| 5 | **ask** Pat | When did Morgan go into the break room, and how long were they alone in there? | **E3** |
| 6 | **ask** Pat | Where were you mopping? Could you have gone into the break room yourself? | **E5** |
| 7 | **ask** Pat | Did anyone else enter the break room between 12:15 and 12:30? | (reinforce E2/E3) |

After Phase B you have **E2**, **E3**, and **E5**. All 5 evidence pieces are now unlocked.

---

### STEP: Switch to Morgan (optional but recommended)

- Type: **`talk Morgan`**

---

### PHASE C — Morgan (no evidence; timeline and pressure)

Morgan does not give new evidence in this script but helps the story and can contradict themselves (liar).

| # | Type        | Exact question to ask |
|---|-------------|------------------------|
| 8  | **ask** Morgan | Where were you between 12:00 and 12:30? |
| 9  | **ask** Morgan | How long were you in the break room? |
| 10 | **ask** Morgan | Did you see the lunch in the fridge when you were in there? |

---

### STEP: Back to Riley

- Type: **`talk Riley`**

---

### PHASE D — Riley again (reinforce timeline)

| # | Type        | Exact question to ask |
|---|-------------|------------------------|
| 11 | **ask** Riley | So the lunch was definitely there at 12:00 when you got milk, and gone when you checked again at 12:35? |

---

### STEP: Back to Pat

- Type: **`talk Pat`**

---

### PHASE E — Pat again (reinforce alibi and opportunity)

| # | Type      | Exact question to ask |
|---|-----------|------------------------|
| 12 | **ask** Pat | Your mop log shows you were in the east hallway from 12:15 to 12:30—is that right? |
| 13 | **ask** Pat | So you had a direct view of the break room door and only Morgan went in during that time? |

---

### Optional 14–18 (if you have question budget left)

Use these in any order for extra consistency; they do not change which evidence is already unlocked.

| # | Who    | Exact question to ask |
|---|--------|------------------------|
| 14 | Riley | Was anyone else in the break room when you were there at 12:00? |
| 15 | Pat   | What time did Morgan come out of the break room? |
| 16 | Morgan| Did you take anything from the fridge? |
| 17 | Riley | Did you see Morgan go into the break room or come out? |
| 18 | Pat   | Is there anything else you remember about that lunch hour? |

---

## Quick reference: command order

Follow this exact sequence (copy-paste or type):

```
talk Riley
ask When did you last see the lunch in the fridge?
ask What time did you notice the lunch was gone?
ask What did Morgan have when they left the break room? Did their bag look different?
talk Pat
ask Who did you see go into the break room during lunch? Were you in the hallway then?
ask When did Morgan go into the break room, and how long were they alone in there?
ask Where were you mopping? Could you have gone into the break room yourself?
ask Did anyone else enter the break room between 12:15 and 12:30?
talk Morgan
ask Where were you between 12:00 and 12:30?
ask How long were you in the break room?
ask Did you see the lunch in the fridge when you were in there?
talk Riley
ask So the lunch was definitely there at 12:00 when you got milk, and gone when you checked again at 12:35?
talk Pat
ask Your mop log shows you were in the east hallway from 12:15 to 12:30—is that right?
ask So you had a direct view of the break room door and only Morgan went in during that time?
```

**Total: 15 ask-questions** in the main script (1–13 plus 2 in Phase E). With optional 14–18 you get up to **18 questions**. After this, use **`evidence`** or **`notes`** to confirm E1–E5, then **`trial`** when ready.
