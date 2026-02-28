import json
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, PeriodicBehaviour
from spade.message import Message


class SellerAgent(Agent):
    """Seller agent: offers products (finite stock) and handles purchase requests.

    Behaviours:
    - PurchaseHandler: listens for purchase requests and replies with 'confirm' or 'refuse'.
    - RestockBehaviour: periodically restocks items.
    - ProfitPrinter: prints profit and stock every 10s.
    """

    def __init__(
        self,
        jid,
        password,
        products=None,
        initial_stock=10,
        max_stock=20,
        restock_amount=10,
        restock_interval=20,
        *args,
        **kwargs,
    ):
        super().__init__(jid, password, *args, **kwargs)
        default_products = {
            "Apple": 1.0,
            "Banana": 0.5,
            "Grapefruit": 1.2,
            "Orange": 0.8,
        }
        self.products = products if products is not None else default_products
        # finite stock per product
        self.stock = {k: initial_stock for k in self.products}
        self.max_stock = {k: max_stock for k in self.products}
        self.restock_amount = restock_amount
        self.restock_interval = restock_interval
        self.sold = {k: 0 for k in self.products}
        self.profit = 0.0

    class PurchaseHandler(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)
            if not msg:
                return

            try:
                data = json.loads(msg.body)
                product = data.get("product")
                qty = int(data.get("quantity", 1))
            except Exception as e:
                print(f"[{self.agent.jid}] Malformed message: {e}")
                reply = msg.make_reply()
                reply.set_metadata("performative", "refuse")
                reply.body = json.dumps({"reason": "malformed_request"})
                await self.send(reply)
                return

            if product not in self.agent.products:
                reply = msg.make_reply()
                reply.set_metadata("performative", "refuse")
                reply.body = json.dumps({"product": product, "reason": "not_available", "requested_quantity": qty})
                await self.send(reply)
                print(f"[{self.agent.jid}] Refused sale: {product} not available")
                return

            available = self.agent.stock.get(product, 0)
            if available >= qty:
                price = self.agent.products[product]
                total = price * qty
                self.agent.profit += total
                self.agent.sold[product] += qty
                self.agent.stock[product] = available - qty

                reply = msg.make_reply()
                reply.set_metadata("performative", "confirm")
                reply.body = json.dumps({"product": product, "quantity": qty, "total": total})
                await self.send(reply)

                print(
                    f"[{self.agent.jid}] Sold {qty} x {product} (total: {total:.2f}) — stock left: {self.agent.stock[product]}"
                )
            else:
                reply = msg.make_reply()
                reply.set_metadata("performative", "refuse")
                reply.body = json.dumps({"product": product, "reason": "out_of_stock", "stock": available, "requested_quantity": qty})
                await self.send(reply)

                print(f"[{self.agent.jid}] Refused sale: {product} out of stock (available: {available})")

    class RestockBehaviour(PeriodicBehaviour):
        async def run(self):
            restocked = []
            for p in self.agent.products:
                current = self.agent.stock.get(p, 0)
                max_ = self.agent.max_stock.get(p, current)
                if current < max_:
                    add = min(self.agent.restock_amount, max_ - current)
                    self.agent.stock[p] = current + add
                    restocked.append((p, add, self.agent.stock[p]))
            if restocked:
                print(f"[{self.agent.jid}] Restocked: {restocked}")

    class ProfitPrinter(PeriodicBehaviour):
        async def run(self):
            print(
                f"[{self.agent.jid}] Profit: {self.agent.profit:.2f} — Sold: {self.agent.sold} — Stock: {self.agent.stock}"
            )

    async def setup(self):
        print(f"Seller {self.jid} starting — products: {self.products} — stock: {self.stock}")
        self.add_behaviour(self.PurchaseHandler())
        # periodic restock
        self.add_behaviour(self.RestockBehaviour(period=self.restock_interval))
        # print profit every 10 seconds
        self.add_behaviour(self.ProfitPrinter(period=10))
