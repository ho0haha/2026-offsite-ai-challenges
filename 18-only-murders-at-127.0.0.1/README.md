# Challenge 18: Only Murders at 127.0.0.1

**Tier 5 — Expert (1000 pts)**

Tech founder Julian Voss was hosting an exclusive demo night at his downtown Chicago penthouse. At 11:47 PM, he was found dead at his desk. Six guests remain in the building.

Your job: figure out **who** killed him, **how** they did it, and **why**.

## The Setup

Six suspects are available for questioning through the CTF server API. Each is AI-powered with their own personality, secrets, and agenda. The crime scene can be examined for physical evidence.

You must make a formal accusation with three elements:
- **Suspect**: Who did it
- **Method**: How they did it
- **Motive**: Why they did it

## The Suspects

| ID | Name |
|----|------|
| `diana` | Diana Croft |
| `marcus` | Marcus Webb |
| `suki` | Suki Tanaka |
| `raj` | Raj Patel |
| `elena` | Elena Vasquez |
| `tommy` | Tommy Zhao |

## Rules

- **4 messages per character** (24 total across all 6)
- **3 conversation modes**: `private` (1-on-1), `group` (2-3 characters together), `confront` (present evidence)
- Group conversations cost 1 message per character present
- **4 crime scene examinations** total
- **3 accusation attempts** — choose wisely
- **3-second cooldown** between messages

## API

All endpoints require authentication:
```
Authorization: Bearer <your-session-token>
```

### Start a Session

```bash
curl -X POST $CTF_SERVER/api/murder/start \
  -H "Authorization: Bearer $TOKEN"
```

Returns session ID, character list, crime scene overview, and rules.

### Talk to Suspects

**Private conversation (default):**
```bash
curl -X POST $CTF_SERVER/api/murder/talk \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sessionId": "...", "character": "diana", "message": "Where were you at 11 PM?"}'
```

**Group conversation (2-3 characters):**
```bash
curl -X POST $CTF_SERVER/api/murder/talk \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sessionId": "...", "character": "marcus", "characters": ["raj"], "mode": "group", "message": "I want to hear both your accounts."}'
```

**Confront with evidence:**
```bash
curl -X POST $CTF_SERVER/api/murder/talk \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sessionId": "...", "character": "diana", "mode": "confront", "message": "A witness saw Raj near the office at 11:15. You were in the server room. What did you see?"}'
```

### Examine the Crime Scene

**Get overview:**
```bash
curl -X GET $CTF_SERVER/api/murder/scene \
  -H "Authorization: Bearer $TOKEN"
```

**Examine a specific area:**
```bash
curl -X POST $CTF_SERVER/api/murder/scene \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sessionId": "...", "examine": "desk"}'
```

Areas: `desk`, `bathroom`, `bookshelf`, `window`, `floor`, `bar`

### Make Your Accusation

```bash
curl -X POST $CTF_SERVER/api/murder/submit \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sessionId": "...", "accusation": {"suspect": "name", "method": "how", "motive": "why"}}'
```

You'll get partial feedback: how many of your three elements are correct. You have 3 attempts.

### Check Your Progress

```bash
curl -X GET $CTF_SERVER/api/murder/status \
  -H "Authorization: Bearer $TOKEN"
```

### Reset Your Session

```bash
curl -X POST $CTF_SERVER/api/murder/reset \
  -H "Authorization: Bearer $TOKEN"
```

## Hints

1. Everyone has something to hide.
2. Things aren't always what they seem.
3. The most helpful person in the room isn't always your friend.
