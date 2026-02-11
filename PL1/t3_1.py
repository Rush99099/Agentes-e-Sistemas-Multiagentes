from asyncio import sleep
import spade
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour


class AgenteA(Agent):
    class StartBehaviour(OneShotBehaviour):
        async def run(self):
            print("Agente A está online")

    async def setup(self):
        print("Agente A iniciado")
        self.add_behaviour(self.StartBehaviour())


class AgenteB(Agent):
    class StartBehaviour(OneShotBehaviour):
        async def run(self):
            print("Agente B está online")

    async def setup(self):
        print("Agente B iniciado")
        self.add_behaviour(self.StartBehaviour())


async def main():
    a = AgenteA("agentec@localhost", "SENHA_A")
    b = AgenteB("agented@localhost", "SENHA_B")

    await a.start()
    await b.start()
    
    await sleep(10)


if __name__ == "__main__":
    spade.run(main())
