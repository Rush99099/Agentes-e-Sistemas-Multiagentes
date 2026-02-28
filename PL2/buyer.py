import json
import random
import asyncio
from spade.agent import Agent
from spade.behaviour import PeriodicBehaviour, CyclicBehaviour, OneShotBehaviour
from spade.message import Message


class BuyerAgent(Agent):
    """Buyer agent: every second sends a purchase request to the seller and
    listens for confirmations/refusals. If refused due to stock, may retry later.
    """

    def __init__(self, jid, password, seller_jid, products=None, retry_probability=0.5, retry_delay_range=(3, 10), *args, **kwargs):
        super().__init__(jid, password, *args, **kwargs)
        self.seller_jid = seller_jid
        self.products = (
            products
            if products is not None
            else [
                "Apple",
                "Banana",
                "Grapefruit",
                "Orange",
                "Pear",
                "Melon",
                "Strawberry",
            ]
        )
        self.retry_probability = float(retry_probability)
        self.retry_delay_range = tuple(retry_delay_range)

    class SendRequest(PeriodicBehaviour):
        async def run(self):
            product = random.choice(self.agent.products)
            qty = random.randint(1, 5)

            msg = Message(to=str(self.agent.seller_jid))
            msg.set_metadata("performative", "request")
            msg.body = json.dumps({"product": product, "quantity": qty})

            await self.send(msg)
            print(f"[{self.agent.jid}] Sent REQUEST -> {self.agent.seller_jid}: {product} x{qty}")

    class RetryPurchase(OneShotBehaviour):
        def __init__(self, product, qty, delay, **kwargs):
            super().__init__(**kwargs)
            self.product = product
            self.qty = qty
            self.delay = delay

        async def run(self):
            await asyncio.sleep(self.delay)
            msg = Message(to=str(self.agent.seller_jid))
            msg.set_metadata("performative", "request")
            msg.body = json.dumps({"product": self.product, "quantity": self.qty})
            await self.send(msg)
            print(f"[{self.agent.jid}] Retrying REQUEST -> {self.agent.seller_jid}: {self.product} x{self.qty} (after {self.delay:.1f}s)")

    class ListenResponse(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=5)
            if not msg:
                return

            perf = msg.get_metadata("performative") or ""
            try:
                data = json.loads(msg.body)
            except Exception:
                data = msg.body

            if perf.lower() == "confirm":
                print(f"[{self.agent.jid}] Purchase CONFIRMED: {data}")
            elif perf.lower() == "refuse":
                print(f"[{self.agent.jid}] Purchase REFUSED: {data}")
                reason = data.get("reason") if isinstance(data, dict) else None
                product = data.get("product") if isinstance(data, dict) else None
                requested_qty = int(data.get("requested_quantity", 1)) if isinstance(data, dict) else 1
                if reason in ("out_of_stock", "not_available") and product:
                    if random.random() < self.agent.retry_probability:
                        delay = random.uniform(*self.agent.retry_delay_range)
                        beh = self.agent.RetryPurchase(product, requested_qty, delay)
                        self.agent.add_behaviour(beh)
                        print(f"[{self.agent.jid}] Will retry for {product} after {delay:.1f}s")
                    else:
                        print(f"[{self.agent.jid}] Will not retry for {product}")
            else:
                print(f"[{self.agent.jid}] Received message: performative={perf}, body={msg.body}")

    async def setup(self):
        print(f"Buyer {self.jid} starting — contacting {self.seller_jid}")
        # send request every 1 second
        self.add_behaviour(self.SendRequest(period=1))
        # listen for replies
        self.add_behaviour(self.ListenResponse())
