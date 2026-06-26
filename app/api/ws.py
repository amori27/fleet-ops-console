import asyncio

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.auth.ops_auth import verify_token
from app.services.pubsub import PubSub

ws_router = APIRouter()


@ws_router.websocket("/ws/fleet/updates")
async def fleet_updates(
    websocket: WebSocket,
    token: str = Query(...),
):
    try:
        ops_user = verify_token(token)
    except Exception:
        await websocket.close(code=1008)
        return

    await websocket.accept()
    pubsub: PubSub = websocket.app.state.pubsub

    q_telemetry = await pubsub.subscribe("fleet:telemetry")
    q_actions = await pubsub.subscribe("fleet:actions:*")

    async def relay(queue: asyncio.Queue) -> None:
        while True:
            msg = await queue.get()
            try:
                await websocket.send_text(msg)
            except WebSocketDisconnect:
                return

    tasks = [
        asyncio.create_task(relay(q_telemetry)),
        asyncio.create_task(relay(q_actions)),
    ]
    try:
        await asyncio.gather(*tasks)
    except WebSocketDisconnect:
        pass
    finally:
        pubsub.unsubscribe("fleet:telemetry", q_telemetry)
        pubsub.unsubscribe("fleet:actions:*", q_actions)
        for t in tasks:
            t.cancel()
