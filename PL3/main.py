#!/usr/bin/env python3
"""
Main script to run the multi-agent taxi transportation system

System initialization:
- 1 Manager Agent
- 5 Taxi Agents
- 10 initial Client Agents
- 10 new Client Agents every second
- Transport duration: 3 seconds
"""

import asyncio
import random
from pathlib import Path
from Client import ClientAgent
from Taxi import TaxiAgent
from Manager import ManagerAgent

# XMPP Server configurations
XMPP_SERVER = "localhost"
XMPP_PORT = 5222

# Agent credentials (modify if using different XMPP server)
DOMAIN = "localhost"
PASSWORD = "password"

# System parameters
NUM_INITIAL_CLIENTS = 10
NUM_TAXIS = 5
NEW_CLIENTS_PER_SECOND = 10
SPAWN_INTERVAL = 1  # seconds


class TransportSystem:
    """Multi-agent taxi transportation system controller"""
    
    def __init__(self):
        self.manager = None
        self.taxis = []
        self.clients = []
        self.client_counter = 0
        self.running = True
        
    async def setup_manager(self):
        """Setup Manager Agent"""
        manager_jid = f"manager@{DOMAIN}"
        self.manager = ManagerAgent(manager_jid, PASSWORD)
        
        await self.manager.start()
        print(f"[SYSTEM] Manager Agent started: {manager_jid}\n")
        return manager_jid
    
    async def setup_taxis(self, manager_jid, num_taxis=NUM_TAXIS):
        """Setup Taxi Agents"""
        for i in range(num_taxis):
            taxi_jid = f"taxi{i}@{DOMAIN}"
            taxi = TaxiAgent(taxi_jid, PASSWORD, manager_jid)
            await taxi.start()
            self.taxis.append(taxi)
            print(f"[SYSTEM] Taxi Agent {i} started: {taxi_jid}")
        print()
    
    async def setup_initial_clients(self, manager_jid, num_clients=NUM_INITIAL_CLIENTS):
        """Setup initial Client Agents"""
        for i in range(num_clients):
            client_jid = f"client{self.client_counter}@{DOMAIN}"
            client = ClientAgent(client_jid, PASSWORD, manager_jid)
            await client.start()
            self.clients.append(client)
            self.client_counter += 1
            
            # Stagger client creation
            await asyncio.sleep(0.1)
        print(f"[SYSTEM] {num_clients} initial Client Agents created\n")
    
    async def spawn_new_clients(self, manager_jid):
        """Spawn new clients periodically"""
        while self.running:
            await asyncio.sleep(SPAWN_INTERVAL)
            
            for i in range(NEW_CLIENTS_PER_SECOND):
                try:
                    client_jid = f"client{self.client_counter}@{DOMAIN}"
                    client = ClientAgent(client_jid, PASSWORD, manager_jid)
                    await client.start()
                    self.clients.append(client)
                    self.client_counter += 1
                    print(f"[SYSTEM] New Client created: {client_jid}")
                except Exception as e:
                    print(f"[SYSTEM] Error creating client: {e}")
                
                await asyncio.sleep(0.05)
    
    async def run(self):
        """Run the complete system"""
        try:
            # Setup manager
            manager_jid = await self.setup_manager()
            await asyncio.sleep(2)  # Wait for manager to fully start
            
            # Setup taxis
            await self.setup_taxis(manager_jid)
            await asyncio.sleep(2)  # Wait for taxis to register
            
            # Setup initial clients
            await self.setup_initial_clients(manager_jid)
            await asyncio.sleep(1)
            
            print("\n" + "="*60)
            print("   ALL AGENTS INITIALIZED - SYSTEM RUNNING")
            print("="*60 + "\n")
            
            # Run client spawning in background
            spawn_task = asyncio.create_task(self.spawn_new_clients(manager_jid))
            
            # Keep system running
            try:
                while self.running:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                print("\n[SYSTEM] Shutting down...")
                self.running = False
                spawn_task.cancel()
        
        except KeyboardInterrupt:
            print("\n[SYSTEM] Interrupted by user")
        
        except Exception as e:
            print(f"[SYSTEM] Error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Shutdown all agents"""
        print("[SYSTEM] Stopping all agents...")
        
        # Stop clients
        for client in self.clients:
            try:
                await client.stop()
            except Exception as e:
                print(f"[SYSTEM] Error stopping client: {e}")
        
        # Stop taxis
        for taxi in self.taxis:
            try:
                await taxi.stop()
            except Exception as e:
                print(f"[SYSTEM] Error stopping taxi: {e}")
        
        # Stop manager
        if self.manager:
            try:
                await self.manager.stop()
            except Exception as e:
                print(f"[SYSTEM] Error stopping manager: {e}")
        
        print("[SYSTEM] All agents stopped")


async def main():
    """Main entry point"""
    print("\n" + "="*60)
    print("   MULTI-AGENT TAXI TRANSPORTATION SYSTEM")
    print("="*60 + "\n")
    
    system = TransportSystem()
    await system.run()


if __name__ == "__main__":
    asyncio.run(main())
