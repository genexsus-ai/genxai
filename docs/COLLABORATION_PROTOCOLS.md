# Collaboration Protocols

GenXAI provides simple collaboration strategies for agents.

## Available Protocols
- **VotingProtocol**: majority vote across agent outputs.
- **NegotiationProtocol**: returns consensus or fallback.
- **AuctionProtocol**: chooses max bid.

## Shared Memory Bus

The `SharedMemoryBus` is a lightweight pub/sub key‑value store for
cross‑agent coordination.

```python
from genxai.core.memory import SharedMemoryBus

bus = SharedMemoryBus()

async def on_update(entry):
    print(entry.key, entry.value)

bus.subscribe("plan", on_update)
await bus.set("plan", {"step": 1})
```