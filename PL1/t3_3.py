import spade
import asyncio
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour


class AgenteContador(Agent):
    class Contar(CyclicBehaviour):
        async def run(self):
            self.agent.contador += 1
            print(f"Contador = {self.agent.contador}")

            if self.agent.contador >= 5:
                print("Agente terminou")
                await self.agent.stop()
            else:
                await asyncio.sleep(1)  # pausa de 1 segundo entre ciclos

    async def setup(self):
        print("Agente Contador iniciado")
        self.contador = 0
        self.add_behaviour(self.Contar())


async def main():
    agente = AgenteContador("contador@localhost", "SENHA_CONTADOR")
    await agente.start()

    # Mantém o programa vivo até o agente terminar
    while agente.is_alive():
        await asyncio.sleep(1)


if __name__ == "__main__":
    spade.run(main())
