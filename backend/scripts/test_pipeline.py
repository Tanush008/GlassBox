"""
Talks to a running Glassbox backend over the WebSocket, exactly like the
frontend does, and prints every message as it streams in.

Useful for testing the agent pipeline (context engine + Groq calls)
without needing the frontend running at all - handy for debugging things
like a bad model name or a missing API key, since you see the raw error
message immediately instead of digging through browser dev tools.

Usage:
    # 1. In one terminal: uvicorn app.main:app --reload
    # 2. In another terminal:
    python backend/scripts/test_pipeline.py "add email validation on signup"

Requires: pip install websockets  (already in requirements.txt)
"""
import asyncio
import json
import sys

import websockets

WS_URL = "ws://localhost:8000/ws/run"


async def main(request: str):
    print(f"Connecting to {WS_URL} ...")
    async with websockets.connect(WS_URL) as ws:
        await ws.send(json.dumps({"request": request}))
        print(f"Sent request: {request!r}\n")

        async for raw in ws:
            msg = json.loads(raw)
            msg_type = msg.get("type")

            if msg_type == "context":
                print(f"[context] {msg['compression_pct']}% saved "
                      f"({msg['included_tokens']}/{msg['full_repo_tokens']} tokens)")
                for f in msg["files"]:
                    mark = "IN " if f["included"] else "out"
                    print(f"   {mark} {f['path']:<25} score={f['score']}")
                print()

            elif msg_type == "agent_result":
                print(f"[{msg['agent']} · round {msg['round']}]")
                print(msg["content"])
                print()

            elif msg_type == "done":
                status = "APPROVED" if msg["approved"] else "shipped after max rounds"
                print(f"[done] {status}, {msg['rounds']} round(s)")
                print("--- final diff ---")
                print(msg["final_diff"])

            elif msg_type == "error":
                print(f"[ERROR] {msg['message']}")


if __name__ == "__main__":
    request = " ".join(sys.argv[1:]) or "Add email validation when a user signs up"
    asyncio.run(main(request))
