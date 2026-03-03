import json
import asyncio
import math
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message


class ManagerAgent(Agent):
    """
    Manager Agent - Gerencia sistema de transporte
    - Recebe contacto de Client (Pedidos)
    - Verifica localização de Taxis e depois disponibilidade
    - Solicita Taxi escolhido para transportar Cliente para Destino
    """

    def __init__(self, jid, password):
        super().__init__(jid, password)
        
        # Registry of available taxis
        self.taxis = {}  # {taxi_jid: {"x_loc": x, "y_loc": y, "available": bool}}
        
        # Queue of pending transport requests
        self.pending_requests = []

    async def setup(self):
        """Initialize manager agent"""
        print("[MANAGER] Starting Manager Agent")
        
        # Add behaviour for receiving taxi registrations
        register_behaviour = ReceiveTaxiRegistrationBehaviour()
        self.add_behaviour(register_behaviour)
        
        # Add behaviour for receiving client requests
        request_behaviour = ReceiveClientRequestBehaviour()
        self.add_behaviour(request_behaviour)
        
        # Add behaviour for receiving taxi status updates
        status_behaviour = ReceiveTaxiStatusBehaviour()
        self.add_behaviour(status_behaviour)
        
        # Add behaviour for processing pending requests
        process_behaviour = ProcessPendingRequestsBehaviour()
        self.add_behaviour(process_behaviour)

    def calculate_distance(self, x1, y1, x2, y2):
        """Calculate Euclidean distance between two points"""
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

    async def find_closest_available_taxi(self, client_x, client_y):
        """Find the closest available taxi to the client"""
        closest_taxi = None
        min_distance = float('inf')
        
        for taxi_jid, taxi_info in self.taxis.items():
            if taxi_info.get("available"):
                distance = self.calculate_distance(
                    client_x, client_y,
                    taxi_info["x_loc"], taxi_info["y_loc"]
                )
                if distance < min_distance:
                    min_distance = distance
                    closest_taxi = (taxi_jid, taxi_info, distance)
        
        return closest_taxi

    async def request_taxi_transport(self, taxi_jid, client_info):
        """Request taxi to transport client"""
        msg = Message(to=taxi_jid)
        msg.set_metadata("performative", "request")
        msg.set_metadata("ontology", "transport_request")
        
        msg.body = json.dumps(client_info)
        
        await self.send(msg)
        print(f"[MANAGER] Requested transport from {taxi_jid} for {client_info['client_jid']}")


class ReceiveTaxiRegistrationBehaviour(CyclicBehaviour):
    """Behaviour for receiving taxi registrations"""
    
    async def run(self):
        msg = await self.receive(timeout=1)
        
        if msg:
            performative = msg.get_metadata("performative")
            ontology = msg.get_metadata("ontology")
            
            if performative == "subscribe" and ontology == "taxi_service":
                # Register new taxi
                data = json.loads(msg.body)
                taxi_jid = data.get("taxi_jid")
                
                self.agent.taxis[taxi_jid] = {
                    "x_loc": data.get("x_loc"),
                    "y_loc": data.get("y_loc"),
                    "available": data.get("available", True)
                }
                
                print(f"[MANAGER] Registered taxi {taxi_jid} at ({data.get('x_loc'):.2f}, {data.get('y_loc'):.2f})")


class ReceiveClientRequestBehaviour(CyclicBehaviour):
    """Behaviour for receiving client transport requests"""
    
    async def run(self):
        msg = await self.receive(timeout=1)
        
        if msg:
            performative = msg.get_metadata("performative")
            ontology = msg.get_metadata("ontology")
            
            if performative == "request" and ontology == "transport":
                # Receive client request
                client_request = json.loads(msg.body)
                
                # Add to pending requests
                self.agent.pending_requests.append(client_request)
                
                print(f"[MANAGER] Received transport request from {client_request['client_jid']}")


class ReceiveTaxiStatusBehaviour(CyclicBehaviour):
    """Behaviour for receiving taxi status updates"""
    
    async def run(self):
        msg = await self.receive(timeout=1)
        
        if msg:
            performative = msg.get_metadata("performative")
            ontology = msg.get_metadata("ontology")
            
            if performative == "inform" and ontology == "taxi_status":
                # Update taxi status
                data = json.loads(msg.body)
                taxi_jid = data.get("taxi_jid")
                
                if taxi_jid in self.agent.taxis:
                    self.agent.taxis[taxi_jid].update({
                        "x_loc": data.get("x_loc"),
                        "y_loc": data.get("y_loc"),
                        "available": data.get("available", True)
                    })


class ProcessPendingRequestsBehaviour(CyclicBehaviour):
    """Behaviour for processing pending transport requests"""
    
    async def run(self):
        # Process one pending request
        if self.agent.pending_requests:
            client_request = self.agent.pending_requests.pop(0)
            
            # Find closest available taxi
            closest_taxi_info = await self.agent.find_closest_available_taxi(
                client_request["x_pos"],
                client_request["y_pos"]
            )
            
            if closest_taxi_info:
                taxi_jid, taxi_info, distance = closest_taxi_info
                
                print(f"[MANAGER] Found taxi {taxi_jid} at distance {distance:.2f}")
                
                # Request taxi to transport client
                await self.agent.request_taxi_transport(taxi_jid, client_request)
            else:
                # No available taxi, add back to queue
                print(f"[MANAGER] No available taxi for {client_request['client_jid']}, will retry...")
                self.agent.pending_requests.append(client_request)
        
        await asyncio.sleep(0.5)