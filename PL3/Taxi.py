import json
import random
import asyncio
import math
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message


class TaxiAgent(Agent):
    """
    Taxi Agent - Fornece transporte de clientes
    - Apresenta coordenadas GPS (float x_loc, float y_loc)
    - Apresenta disponibilidade (bool available)
    - Quando chega a um destino, atualiza localização e disponibilidade
    """

    def __init__(self, jid, password, manager_jid):
        super().__init__(jid, password)
        self.manager_jid = manager_jid
        
        # GPS coordinates
        self.x_loc = random.uniform(0, 100)
        self.y_loc = random.uniform(0, 100)
        
        # Availability status
        self.available = True
        
        # Current client being transported
        self.current_client = None
        self.transport_destination = None
        self.transport_end_time = None
        
    async def setup(self):
        """Initialize taxi agent and add behaviours"""
        print(f"[TAXI {self.name}] Starting at ({self.x_loc:.2f}, {self.y_loc:.2f})")
        
        # Register with manager
        await self.register_with_manager()
        
        # Add behaviour for receiving transport requests
        transport_behaviour = ReceiveTransportRequestBehaviour()
        self.add_behaviour(transport_behaviour)
        
        # Add behaviour for managing active transport
        manage_behaviour = ManageTransportBehaviour()
        self.add_behaviour(manage_behaviour)
    
    async def register_with_manager(self):
        """Register taxi with manager"""
        msg = Message(to=self.manager_jid)
        msg.set_metadata("performative", "subscribe")
        msg.set_metadata("ontology", "taxi_service")
        
        taxi_info = {
            "taxi_jid": str(self.jid),
            "x_loc": self.x_loc,
            "y_loc": self.y_loc,
            "available": self.available
        }
        msg.body = json.dumps(taxi_info)
        
        await self.send(msg)
        print(f"[TAXI {self.name}] Registered with Manager")
    
    async def update_manager(self):
        """Update manager with current status"""
        msg = Message(to=self.manager_jid)
        msg.set_metadata("performative", "inform")
        msg.set_metadata("ontology", "taxi_status")
        
        taxi_info = {
            "taxi_jid": str(self.jid),
            "x_loc": self.x_loc,
            "y_loc": self.y_loc,
            "available": self.available
        }
        msg.body = json.dumps(taxi_info)
        
        await self.send(msg)
    
    async def accept_transport(self, client_jid, x_dep, y_dep, x_dest, y_dest):
        """Accept transport request"""
        self.available = False
        self.current_client = client_jid
        self.transport_destination = (x_dest, y_dest)
        
        # Calculate transport time (3 seconds)
        self.transport_end_time = asyncio.get_event_loop().time() + 3
        
        # Update locations
        self.x_loc = x_dep
        self.y_loc = y_dep
        
        print(f"[TAXI {self.name}] Accepted transport for {client_jid}")
        print(f"[TAXI {self.name}] Going from ({self.x_loc:.2f}, {self.y_loc:.2f}) to ({x_dest:.2f}, {y_dest:.2f})")
        
        # Confirm transport to client
        msg = Message(to=client_jid)
        msg.set_metadata("performative", "confirm")
        msg.set_metadata("ontology", "transport")
        
        confirm_info = {
            "taxi_jid": str(self.jid),
            "status": "on_the_way"
        }
        msg.body = json.dumps(confirm_info)
        
        await self.send(msg)
        await self.update_manager()
    
    def calculate_distance(self, x1, y1, x2, y2):
        """Calculate Euclidean distance between two points"""
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


class ReceiveTransportRequestBehaviour(CyclicBehaviour):
    """Behaviour for receiving transport requests from manager"""
    
    async def run(self):
        msg = await self.receive(timeout=1)
        
        if msg:
            performative = msg.get_metadata("performative")
            ontology = msg.get_metadata("ontology")
            
            if performative == "request" and ontology == "transport_request":
                # Decode transport request
                data = json.loads(msg.body)
                client_jid = data.get("client_jid")
                x_dep = data.get("x_pos")
                y_dep = data.get("y_pos")
                x_dest = data.get("x_dest")
                y_dest = data.get("y_dest")
                
                # Accept and start transport
                await self.agent.accept_transport(client_jid, x_dep, y_dep, x_dest, y_dest)


class ManageTransportBehaviour(CyclicBehaviour):
    """Behaviour for managing active transport"""
    
    async def run(self):
        # Check if transport is completed
        if self.agent.current_client and self.agent.transport_end_time:
            current_time = asyncio.get_event_loop().time()
            
            if current_time >= self.agent.transport_end_time:
                # Transport completed
                x_dest, y_dest = self.agent.transport_destination
                self.agent.x_loc = x_dest
                self.agent.y_loc = y_dest
                self.agent.available = True
                
                # Notify client
                msg_client = Message(to=self.agent.current_client)
                msg_client.set_metadata("performative", "inform")
                msg_client.set_metadata("ontology", "transport_completed")
                
                completion_info = {
                    "taxi_jid": str(self.agent.jid),
                    "x_dest": x_dest,
                    "y_dest": y_dest
                }
                msg_client.body = json.dumps(completion_info)
                
                await self.send(msg_client)
                
                # Notify manager
                await self.agent.update_manager()
                
                print(f"[TAXI {self.agent.name}] Transport completed at ({x_dest:.2f}, {y_dest:.2f})")
                
                # Reset
                self.agent.current_client = None
                self.agent.transport_destination = None
                self.agent.transport_end_time = None
        
        await asyncio.sleep(0.5)