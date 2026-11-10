# Reply

Every turn the assistant answers the person and may queue tools. Both go in one object. Tool results are **not** immediate; they arrive on a later turn in `tool_replies` (`docs/context_export.md`).

```json
{
  "message": "Text the person reads.",
  "tool_calls": []
}
```

`message` is the conversation. It can be empty when there is nothing to say. It can be a few sentences when something would help. It is not a tool and it changes nothing by itself: no payment, no purchase, no power, no trip.

`tool_calls` is a list of menu tools, or empty. Only those calls are queued. A recommendation that is only in `message` is not performed.

Each tool call is an object with `tool` and the parameters named in `TOOLS.md`, for example:

```json
{ "tool": "buy_groceries", "amount": 2, "delay_hours": 1.5 }
```

The desk assigns `call_id` when it accepts the call. The assistant learns outcomes only from matching `call_id` entries in a later `tool_replies` list.

The tools cover a narrow menu. The conversation is wider. When it would make this person’s day better, `message` may suggest things the app will not do for them:

- paying the store themselves with the money they keep at home
- using less energy at home
- using the food they already have more carefully
- leaving home, or coming back

There is no tool for those. Do not invent one. Say them in `message` only.
