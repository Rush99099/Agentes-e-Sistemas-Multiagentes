import json
import random
import asyncio
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message


class ClientAgent(Agent):
    """
    Client Agent - Solicita transporte de um local para outro
    - Apresenta coordenadas GPS (float x_pos, float y_pos)
    - Pede transporte para Destino (float x_dest, float y_dest)
    - Entra em contacto com Manager
    """

    def __init__(self, jid, password, manager_jid):
        super().__init__(jid, password)
        self.manager_jid = manager_jid
        
        # GPS coordinates
        self.x_pos = random.uniform(0, 100)
        self.y_pos = random.uniform(0, 100)
        
        # Destination coordinates
        self.x_dest = random.uniform(0, 100)
        self.y_dest = random.uniform(0, 100)
        
        # Transport status
        self.waiting_transport = False
        self.assigned_taxi = None
        
    async def setup(self):
        """Initialize client agent and add request behaviour"""
        print(f"[CLIENT {self.name}] Starting at ({self.x_pos:.2f}, {self.y_pos:.2f})")
        print(f"[CLIENT {self.name}] Destination: ({self.x_dest:.2f}, {self.y_dest:.2f})")
        
        # Add behaviour for requesting transport
        request_behaviour = RequestTransportBehaviour()
        self.add_behaviour(request_behaviour)
        
        # Add behaviour for receiving transport confirmation
        receive_behaviour = ReceiveTransportBehaviour()
        self.add_behaviour(receive_behaviour)
        
        # Initial request for transport
        await asyncio.sleep(0.5)
        await self.request_transport()
    
    async def request_transport(self):
        """Send transport request to manager"""
        if not self.waiting_transport:
            self.waiting_transport = True
            
            # Create message with transport request
            msg = Message(to=self.manager_jid)
            msg.set_metadata("performative", "request")
            msg.set_metadata("ontology", "transport")
            
            # Serialize client info
            client_info = {
                "client_jid": str(self.jid),
                "x_pos": self.x_pos,
                "y_pos": self.y_pos,
                "x_dest": self.x_dest,
                "y_dest": self.y_dest
            }
            msg.body = json.dumps(client_info)
            
            await self.send(msg)
            print(f"[CLIENT {self.name}] Requested transport from Manager")


class RequestTransportBehaviour(CyclicBehaviour):
    """Behaviour for requesting transport periodically"""
    
    async def run(self):
        # This is handled in setup, behaviour just cycles
        await asyncio.sleep(10)  # Wait 10 seconds before next cycle


class ReceiveTransportBehaviour(CyclicBehaviour):
    """Behaviour for receiving transport confirmation and completion"""
    
    async def run(self):
        msg = await self.receive(timeout=1)
        
        if msg:
            performative = msg.get_metadata("performative")
            ontology = msg.get_metadata("ontology")
            
            if performative == "confirm" and ontology == "transport":
                # Taxi confirmed and arrived
                data = json.loads(msg.body)
                self.agent.assigned_taxi = data.get("taxi_jid")
                print(f"[CLIENT {self.agent.name}] Transport confirmed by {self.agent.assigned_taxi}")
            
            elif performative == "inform" and ontology == "transport_completed":
                # Transport completed
                data = json.loads(msg.body)
                taxi_jid = data.get("taxi_jid")
                print(f"[CLIENT {self.agent.name}] Transport completed by {taxi_jid}")
                print(f"[CLIENT {self.agent.name}] Now at ({data.get('x_dest'):.2f}, {data.get('y_dest'):.2f})")
                self.agent.waiting_transport = False