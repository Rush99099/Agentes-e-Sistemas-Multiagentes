import spade
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour, CyclicBehaviour
from spade.message import Message
from spade.template import Template


class AgenteA(Agent):
    class Enviar(OneShotBehaviour):
        async def run(self):
            msg = Message(
                to="agenteb@localhost",
                body="Olá Agente B!",
                metadata={"performative": "inform"}
            )
            await self.send(msg)
            print("Agente A enviou mensagem")
            await self.agent.stop()

    async def setup(self):
        print("Agente A iniciado")
        self.add_behaviour(self.Enviar())


class AgenteB(Agent):
    class Receber(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)
            if msg:
                print("Agente B recebeu:", msg.body)
                await self.agent.stop()

    async def setup(self):
        print("Agente B iniciado")
        template = Template(metadata={"performative": "inform"})
        self.add_behaviour(self.Receber(), template)


async def main():
    # IMPORTANTE: iniciar B primeiro e deixá-lo online
    b = AgenteB("agenteb@localhost", "SENHA_B")
    await b.start()

    # A só entra depois
    a = AgenteA("agentea@localhost", "SENHA_A")
    await a.start()


if __name__ == "__main__":
    spade.run(main())
