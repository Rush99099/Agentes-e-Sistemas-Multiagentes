#!/usr/bin/env python3
"""
Simplified Multi-Agent Taxi Transportation System (no XMPP required)

This is a simplified version using asyncio and threading instead of SPADE/XMPP
Makes it easier to run without external server dependencies.

System initialization:
- 1 Manager Agent
- 5 Taxi Agents
- 10 initial Client Agents
- 10 new Client Agents every second
- Transport duration: 3 seconds
"""

import asyncio
import random
import math
import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional


class Message:
    """Simple message class for inter-agent communication"""
    
    def __init__(self, sender: str, receiver: str, performative: str, ontology: str, content: dict):
        self.sender = sender
        self.receiver = receiver
        self.performative = performative
        self.ontology = ontology
        self.content = content
        self.timestamp = datetime.now()
    
    def __repr__(self):
        return f"Message({self.sender} -> {self.receiver}, {self.performative}/{self.ontology})"


class MessageBroker:
    """Central message broker for agent communication"""
    
    def __init__(self):
        self.mailboxes: Dict[str, asyncio.Queue] = {}
    
    def register_agent(self, agent_id: str):
        """Register an agent with a mailbox"""
        if agent_id not in self.mailboxes:
            self.mailboxes[agent_id] = asyncio.Queue()
    
    async def send_message(self, message: Message):
        """Send a message to an agent"""
        if message.receiver in self.mailboxes:
            await self.mailboxes[message.receiver].put(message)
    
    async def receive_message(self, agent_id: str, timeout: float = 1.0) -> Optional[Message]:
        """Receive a message from an agent's mailbox"""
        try:
            return await asyncio.wait_for(self.mailboxes[agent_id].get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None


class ClientAgent:
    """Client Agent - Solicita transporte"""
    
    def __init__(self, agent_id: str, manager_id: str, broker: MessageBroker):
        self.agent_id = agent_id
        self.name = agent_id.split("_")[0]
        self.manager_id = manager_id
        self.broker = broker
        
        # GPS coordinates
        self.x_pos = random.uniform(0, 100)
        self.y_pos = random.uniform(0, 100)
        
        # Destination coordinates
        self.x_dest = random.uniform(0, 100)
        self.y_dest = random.uniform(0, 100)
        
        # Status
        self.waiting_transport = False
        self.assigned_taxi = None
        
        # Register with broker
        self.broker.register_agent(self.agent_id)
        
        print(f"[CLIENT {self.name}] Starting at ({self.x_pos:.2f}, {self.y_pos:.2f})")
        print(f"[CLIENT {self.name}] Destination: ({self.x_dest:.2f}, {self.y_dest:.2f})")
    
    async def run(self):
        """Main client loop"""
        # Request transport
        await self.request_transport()
        
        # Listen for messages
        while True:
            msg = await self.broker.receive_message(self.agent_id, timeout=1.0)
            
            if msg:
                if msg.performative == "confirm" and msg.ontology == "transport":
                    self.assigned_taxi = msg.content.get("taxi_id")
                    print(f"[CLIENT {self.name}] Transport confirmed by {self.assigned_taxi}")
                
                elif msg.performative == "inform" and msg.ontology == "transport_completed":
                    taxi_id = msg.content.get("taxi_id")
                    x_dest = msg.content.get("x_dest")
                    y_dest = msg.content.get("y_dest")
                    print(f"[CLIENT {self.name}] Transport completed by {taxi_id}")
                    print(f"[CLIENT {self.name}] Now at ({x_dest:.2f}, {y_dest:.2f})")
                    self.waiting_transport = False
                    break  # Task completed
    
    async def request_transport(self):
        """Request transport from manager"""
        msg = Message(
            sender=self.agent_id,
            receiver=self.manager_id,
            performative="request",
            ontology="transport",
            content={
                "client_id": self.agent_id,
                "x_pos": self.x_pos,
                "y_pos": self.y_pos,
                "x_dest": self.x_dest,
                "y_dest": self.y_dest
            }
        )
        await self.broker.send_message(msg)
        print(f"[CLIENT {self.name}] Requested transport from Manager")
        self.waiting_transport = True


class TaxiAgent:
    """Taxi Agent - Fornece transporte"""
    
    def __init__(self, agent_id: str, manager_id: str, broker: MessageBroker):
        self.agent_id = agent_id
        self.name = agent_id.split("_")[0]
        self.manager_id = manager_id
        self.broker = broker
        
        # GPS coordinates
        self.x_loc = random.uniform(0, 100)
        self.y_loc = random.uniform(0, 100)
        
        # Availability
        self.available = True
        
        # Current transport
        self.current_client = None
        self.transport_destination = None
        self.transport_end_time = None
        
        # Register with broker
        self.broker.register_agent(self.agent_id)
        
        print(f"[TAXI {self.name}] Starting at ({self.x_loc:.2f}, {self.y_loc:.2f})")
    
    async def run(self):
        """Main taxi loop"""
        # Register with manager
        await self.register_with_manager()
        
        # Listen for messages
        while True:
            msg = await self.broker.receive_message(self.agent_id, timeout=0.5)
            
            if msg:
                if msg.performative == "request" and msg.ontology == "transport_request":
                    # Accept transport
                    await self.accept_transport(msg.content)
            
            # Check if transport is completed
            if self.current_client and self.transport_end_time:
                current_time = asyncio.get_event_loop().time()
                
                if current_time >= self.transport_end_time:
                    # Transport completed
                    await self.complete_transport()
            
            await asyncio.sleep(0.1)
    
    async def register_with_manager(self):
        """Register with manager"""
        msg = Message(
            sender=self.agent_id,
            receiver=self.manager_id,
            performative="subscribe",
            ontology="taxi_service",
            content={
                "taxi_id": self.agent_id,
                "x_loc": self.x_loc,
                "y_loc": self.y_loc,
                "available": self.available
            }
        )
        await self.broker.send_message(msg)
        print(f"[TAXI {self.name}] Registered with Manager")
    
    async def update_manager(self):
        """Update manager with status"""
        msg = Message(
            sender=self.agent_id,
            receiver=self.manager_id,
            performative="inform",
            ontology="taxi_status",
            content={
                "taxi_id": self.agent_id,
                "x_loc": self.x_loc,
                "y_loc": self.y_loc,
                "available": self.available
            }
        )
        await self.broker.send_message(msg)
    
    async def accept_transport(self, request_data: dict):
        """Accept transport request"""
        self.available = False
        self.current_client = request_data.get("client_id")
        x_dep = request_data.get("x_pos")
        y_dep = request_data.get("y_pos")
        x_dest = request_data.get("x_dest")
        y_dest = request_data.get("y_dest")
        
        # Move to client location and set destination
        self.x_loc = x_dep
        self.y_loc = y_dep
        self.transport_destination = (x_dest, y_dest)
        
        # Set 3-second transport time
        self.transport_end_time = asyncio.get_event_loop().time() + 3
        
        print(f"[TAXI {self.name}] Accepted transport for {self.current_client}")
        print(f"[TAXI {self.name}] Transport: ({self.x_loc:.2f}, {self.y_loc:.2f}) -> ({x_dest:.2f}, {y_dest:.2f})")
        
        # Confirm to client
        msg = Message(
            sender=self.agent_id,
            receiver=self.current_client,
            performative="confirm",
            ontology="transport",
            content={"taxi_id": self.agent_id, "status": "on_the_way"}
        )
        await self.broker.send_message(msg)
        await self.update_manager()
    
    async def complete_transport(self):
        """Complete transport"""
        x_dest, y_dest = self.transport_destination
        self.x_loc = x_dest
        self.y_loc = y_dest
        self.available = True
        
        # Notify client
        msg_client = Message(
            sender=self.agent_id,
            receiver=self.current_client,
            performative="inform",
            ontology="transport_completed",
            content={"taxi_id": self.agent_id, "x_dest": x_dest, "y_dest": y_dest}
        )
        await self.broker.send_message(msg_client)
        
        # Update manager
        await self.update_manager()
        
        print(f"[TAXI {self.name}] Transport completed at ({x_dest:.2f}, {y_dest:.2f})")
        
        # Reset
        self.current_client = None
        self.transport_destination = None
        self.transport_end_time = None


class ManagerAgent:
    """Manager Agent - Gerencia sistema de transporte"""
    
    def __init__(self, agent_id: str, broker: MessageBroker):
        self.agent_id = agent_id
        self.name = "MANAGER"
        self.broker = broker
        
        # Registry
        self.taxis: Dict[str, Dict] = {}
        self.pending_requests: List[dict] = []
        
        # Register with broker
        self.broker.register_agent(self.agent_id)
        
        print(f"[{self.name}] Manager Agent started")
    
    async def run(self):
        """Main manager loop"""
        while True:
            # Receive messages
            msg = await self.broker.receive_message(self.agent_id, timeout=0.5)
            
            if msg:
                if msg.performative == "subscribe" and msg.ontology == "taxi_service":
                    # Register taxi
                    self.register_taxi(msg.content)
                
                elif msg.performative == "request" and msg.ontology == "transport":
                    # Receive client request
                    self.pending_requests.append(msg.content)
                    print(f"[{self.name}] Received transport request from {msg.content['client_id']}")
                
                elif msg.performative == "inform" and msg.ontology == "taxi_status":
                    # Update taxi status
                    self.update_taxi_status(msg.content)
            
            # Process pending requests
            await self.process_pending_requests()
            
            await asyncio.sleep(0.1)
    
    def register_taxi(self, taxi_info: dict):
        """Register a taxi"""
        taxi_id = taxi_info.get("taxi_id")
        self.taxis[taxi_id] = {
            "x_loc": taxi_info.get("x_loc"),
            "y_loc": taxi_info.get("y_loc"),
            "available": taxi_info.get("available", True)
        }
        print(f"[{self.name}] Registered taxi {taxi_id} at ({taxi_info.get('x_loc'):.2f}, {taxi_info.get('y_loc'):.2f})")
    
    def update_taxi_status(self, status_info: dict):
        """Update taxi status"""
        taxi_id = status_info.get("taxi_id")
        if taxi_id in self.taxis:
            self.taxis[taxi_id].update({
                "x_loc": status_info.get("x_loc"),
                "y_loc": status_info.get("y_loc"),
                "available": status_info.get("available", True)
            })
    
    def find_closest_available_taxi(self, client_x: float, client_y: float) -> Optional[Tuple[str, dict, float]]:
        """Find closest available taxi"""
        closest_taxi = None
        min_distance = float('inf')
        
        for taxi_id, taxi_info in self.taxis.items():
            if taxi_info.get("available"):
                distance = math.sqrt((client_x - taxi_info["x_loc"]) ** 2 + 
                                    (client_y - taxi_info["y_loc"]) ** 2)
                if distance < min_distance:
                    min_distance = distance
                    closest_taxi = (taxi_id, taxi_info, distance)
        
        return closest_taxi
    
    async def process_pending_requests(self):
        """Process pending transport requests"""
        if not self.pending_requests:
            return
        
        client_request = self.pending_requests.pop(0)
        
        # Find closest available taxi
        closest_taxi_info = self.find_closest_available_taxi(
            client_request.get("x_pos"),
            client_request.get("y_pos")
        )
        
        if closest_taxi_info:
            taxi_id, taxi_info, distance = closest_taxi_info
            print(f"[{self.name}] Found taxi {taxi_id} at distance {distance:.2f}")
            
            # Request taxi
            msg = Message(
                sender=self.agent_id,
                receiver=taxi_id,
                performative="request",
                ontology="transport_request",
                content=client_request
            )
            await self.broker.send_message(msg)
        else:
            # Retry later
            print(f"[{self.name}] No available taxi for {client_request['client_id']}, will retry...")
            self.pending_requests.append(client_request)


class TransportSystem:
    """Multi-agent taxi transportation system"""
    
    def __init__(self):
        self.broker = MessageBroker()
        self.manager = None
        self.taxis = []
        self.clients = []
        self.client_counter = 0
        self.running = True
        self.tasks = []
    
    async def setup(self):
        """Setup the system"""
        print("\n" + "="*60)
        print("   MULTI-AGENT TAXI TRANSPORTATION SYSTEM (Simplified)")
        print("="*60 + "\n")
        
        # Create manager
        self.manager = ManagerAgent("manager", self.broker)
        manager_task = asyncio.create_task(self.manager.run())
        self.tasks.append(manager_task)
        print()
        
        await asyncio.sleep(0.5)
        
        # Create taxis
        for i in range(5):
            taxi = TaxiAgent(f"taxi_{i}", "manager", self.broker)
            self.taxis.append(taxi)
            taxi_task = asyncio.create_task(taxi.run())
            self.tasks.append(taxi_task)
        
        await asyncio.sleep(1)
        print()
        
        # Create initial clients
        for i in range(10):
            client = ClientAgent(f"client_{self.client_counter}", "manager", self.broker)
            self.clients.append(client)
            self.client_counter += 1
            
            client_task = asyncio.create_task(client.run())
            self.tasks.append(client_task)
            
            await asyncio.sleep(0.1)
        
        print("\n" + "="*60)
        print("   ALL AGENTS INITIALIZED - SYSTEM RUNNING")
        print("="*60 + "\n")
    
    async def spawn_new_clients(self):
        """Spawn new clients periodically"""
        while self.running:
            await asyncio.sleep(1)
            
            for _ in range(10):
                try:
                    client = ClientAgent(f"client_{self.client_counter}", "manager", self.broker)
                    self.clients.append(client)
                    self.client_counter += 1
                    
                    client_task = asyncio.create_task(client.run())
                    self.tasks.append(client_task)
                    
                    print(f"[SYSTEM] New Client created: client_{self.client_counter - 1}")
                    await asyncio.sleep(0.05)
                
                except Exception as e:
                    print(f"[SYSTEM] Error creating client: {e}")
    
    async def run(self):
        """Run the system"""
        try:
            await self.setup()
            
            # Start spawning new clients
            spawn_task = asyncio.create_task(self.spawn_new_clients())
            
            # Keep running until interrupted
            try:
                while self.running:
                    await asyncio.sleep(1)
            
            except KeyboardInterrupt:
                print("\n[SYSTEM] Shutting down...")
                self.running = False
        
        except Exception as e:
            print(f"[SYSTEM] Error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Shutdown the system"""
        print("[SYSTEM] Stopping all tasks...")
        
        # Cancel all tasks
        for task in self.tasks:
            task.cancel()
        
        # Wait for cancellation
        await asyncio.gather(*self.tasks, return_exceptions=True)
        
        print("[SYSTEM] All agents stopped")


async def main():
    """Main entry point"""
    system = TransportSystem()
    try:
        await system.run()
    except KeyboardInterrupt:
        print("\n[System] Interrupted by user")


if __name__ == "__main__":
    asyncio.run(main())
