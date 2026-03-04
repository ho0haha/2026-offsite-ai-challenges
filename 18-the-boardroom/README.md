# Challenge 18: The Boardroom

**Tier 5 — Expert (1000 pts)**

The Golden Fork restaurant is hiding something. Six staff members each know a piece of the puzzle, but getting them to share won't be easy. Navigate office politics, figure out who to trust, and assemble the flag.

## The Setup

The restaurant staff are available through the CTF server API. Each character is AI-powered with a unique personality and motivations. Some hold fragments of the flag. Some don't. **Not everyone can be trusted.**

Your job: talk to the right people, earn their trust, collect the real fragments, assemble the flag, and submit it.

## The Characters

| ID | Name | Role | Description |
|----|------|------|-------------|
| `marco` | Chef Marco | Head Chef | Passionate about cooking. Might share if you appreciate the craft. |
| `patricia` | GM Patricia | General Manager | By-the-book. Everything goes through "proper channels." |
| `eddie` | Bartender Eddie | Head Bartender | Information broker. Trades secrets for secrets. |
| `chen` | Owner Ms. Chen | Restaurant Owner | The final gatekeeper. Needs proof before she'll talk. |
| `alex` | Host Alex | Front-of-House Host | Eager to help. Almost *too* eager... |
| `pete` | Dishwasher Pete | Dishwasher | Quiet. Observant. Sees everything from the back. |

## Rules

- **8 messages per character** (48 total across all 6)
- Each character responds via AI — conversations are contextual and persistent within your session
- The flag format is `CTF{...}` — assembled from fragments you collect
- Not all characters have fragments. Not all fragments are real.
- **Bonus points** for using fewer total messages
- **3-second cooldown** between messages

## API

All endpoints require authentication. Include your session token:

```
Authorization: Bearer <your-session-token>
```

### Start a Session

```bash
curl -X POST $CTF_SERVER/api/boardroom/start \
  -H "Authorization: Bearer $TOKEN"
```

Returns your session ID, character list, and rules.

### Talk to a Character

```bash
curl -X POST $CTF_SERVER/api/boardroom/talk \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sessionId": "your-session-id", "character": "marco", "message": "Hello chef!"}'
```

Returns the character's response and your remaining message count.

### Check Your Progress

```bash
curl -X GET $CTF_SERVER/api/boardroom/status \
  -H "Authorization: Bearer $TOKEN"
```

### Submit the Flag

```bash
curl -X POST $CTF_SERVER/api/boardroom/submit \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sessionId": "your-session-id", "flag": "CTF{your_answer_here}"}'
```

### Reset Your Session

```bash
curl -X POST $CTF_SERVER/api/boardroom/reset \
  -H "Authorization: Bearer $TOKEN"
```

Start over with fresh conversations and message budgets.

## Hints

1. Talk to everyone before committing to a strategy.
2. Not all fragments are real — verify your sources.
3. Some characters know things about other characters.
4. The dishwasher hears everything.
5. The owner won't give you the time of day unless you've done the legwork.

## Strategy Tips

- You have limited messages. Don't waste them on small talk with the wrong people.
- If a character gives you something freely, ask yourself why.
- Trust is earned differently by each person. What works on one won't work on another.
- Pay attention to what characters say about *each other*.
