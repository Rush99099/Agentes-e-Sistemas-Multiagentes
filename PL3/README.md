# Multi-Agent Taxi Transportation System

Um sistema multiagente que implementa um serviço de transporte de táxis com comunicação entre agentes.

## 📋 Descrição do Sistema

O sistema simula uma plataforma de serviço de transporte com os seguintes componentes:

### Agentes

#### 🚕 Taxi Agent
- **Responsabilidades:**
  - Apresenta coordenadas GPS (float x_loc, float y_loc)
  - Apresenta disponibilidade (boolean available)
  - Regista-se junto do Manager
  - Aceita pedidos de transporte
  - Atualiza localização e disponibilidade após transporte
  
- **Comportamentos:**
  - `ReceiveTransportRequestBehaviour`: Recebe pedidos do Manager
  - `ManageTransportBehaviour`: Controla transportes em curso (duração: 3 segundos)

#### 👤 Client Agent
- **Responsabilidades:**
  - Apresenta coordenadas GPS (float x_pos, float y_pos)
  - Pede transporte para destino (float x_dest, float y_dest)
  - Entra em contacto com o Manager
  
- **Comportamentos:**
  - `RequestTransportBehaviour`: Envia pedido de transporte
  - `ReceiveTransportBehaviour`: Recebe confirmação e notificação de conclusão

#### 🏢 Manager Agent
- **Responsabilidades:**
  - Recebe contacto de Clients (Pedidos)
  - Verifica localização de Taxis e disponibilidade
  - Solicita ao Taxi selecionado transportar Cliente
  - Coordena comunicação entre Clients e Taxis
  
- **Comportamentos:**
  - `ReceiveTaxiRegistrationBehaviour`: Recebe registos de taxis
  - `ReceiveClientRequestBehaviour`: Recebe pedidos de clientes
  - `ReceiveTaxiStatusBehaviour`: Recebe updates de status dos taxis
  - `ProcessPendingRequestsBehaviour`: Processa pedidos pendentes

## ⚙️ Parâmetros do Sistema

```python
NUM_INITIAL_CLIENTS = 10         # Clientes iniciais
NUM_TAXIS = 5                    # Número de táxis
NEW_CLIENTS_PER_SECOND = 10      # Novos clientes por segundo
TRANSPORT_DURATION = 3           # Duração do transporte (segundos)
SPAWN_INTERVAL = 1               # Intervalo de criação de clientes (segundos)

GPS_RANGE = [0, 100]            # Intervalo de coordenadas GPS (x, y)
```

## 🔄 Fluxo de Comunicação

```
1. Taxi → Manager: subscribe
   └─ Regista-se como disponível

2. Manager → Manager: register_taxi
   └─ Armazena informação do taxi

3. Client → Manager: request
   └─ Pedido de transporte com coordenadas

4. Manager → Taxi: request
   └─ Solicita transporte ao taxi mais próximo

5. Taxi → Client: confirm
   └─ Confirma aceitação do transporte

6. [3 segundos de transporte...]

7. Taxi → Client: inform (transport_completed)
   └─ Notifica conclusão do transporte

8. Taxi → Manager: inform (taxi_status)
   └─ Atualiza status de disponibilidade
```

## 📊 Ontologias de Mensagens

| Performative | Ontology | Origem | Destino | Conteúdo |
|---|---|---|---|---|
| subscribe | taxi_service | Taxi | Manager | taxi_id, x_loc, y_loc, available |
| request | transport | Client | Manager | client_id, x_pos, y_pos, x_dest, y_dest |
| request | transport_request | Manager | Taxi | client_id, x_pos, y_pos, x_dest, y_dest |
| confirm | transport | Taxi | Client | taxi_id, status |
| inform | taxi_status | Taxi | Manager | taxi_id, x_loc, y_loc, available |
| inform | transport_completed | Taxi | Client | taxi_id, x_dest, y_dest |

## 🚀 Como Executar

### Opção 1: Versão Simplificada (Recomendada)

A versão simplificada não requer um servidor XMPP externo.

```bash
# Instalar dependências (apenas asyncio, já incluído em Python 3.7+)
python main_simple.py
```

**Vantagens:**
- ✅ Não requer servidor XMPP
- ✅ Fácil de testar localmente
- ✅ Apenas dependências padrão de Python
- ✅ Ideal para demonstração e debugging

### Opção 2: Versão SPADE (XMPP)

A versão SPADE usa comunicação XMPP autêntica entre agentes.

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Instalar e executar served XMPP (ex: ejabberd)
# Consulte documentação do SPADE para setup do servidor XMPP

# 3. Correr o sistema
python main.py
```

**Requer:**
- Servidor XMPP (ejabberd, Prosody, etc.)
- Python 3.7+

## 📁 Estrutura de Ficheiros

```
PL3/
├── Client.py              # Agente Cliente
├── Taxi.py                # Agente Táxi
├── Manager.py             # Agente Gestor
├── main.py                # Sistema com SPADE/XMPP
├── main_simple.py         # Sistema simplificado (sem servidor)
├── requirements.txt       # Dependências SPADE
└── README.md             # Este ficheiro
```

## 🎯 Conceitos Implementados

### Serialização de Objetos
Todas as mensagens usam JSON para serializar informações:
```python
client_info = {
    "client_id": "client_0",
    "x_pos": 45.23,
    "y_pos": 67.89,
    "x_dest": 12.34,
    "y_dest": 56.78
}
msg.body = json.dumps(client_info)
```

### Cálculo de Distância Euclidiana
Usado para encontrar o táxi mais próximo:
```python
distance = sqrt((x2 - x1)² + (y2 - y1)²)
```

### Coordenadas GPS Aleatórias
Inicialização com coordenadas aleatórias (0-100):
```python
self.x_pos = random.uniform(0, 100)
self.y_pos = random.uniform(0, 100)
```

## 📊 Exemplo de Saída

```
============================================================
   MULTI-AGENT TAXI TRANSPORTATION SYSTEM (Simplified)
============================================================

[MANAGER] Manager Agent started

[TAXI taxi_0] Starting at (34.56, 78.91)
[TAXI taxi_1] Starting at (12.34, 45.67)
[TAXI taxi_2] Starting at (89.12, 56.78)
[TAXI taxi_3] Starting at (23.45, 67.89)
[TAXI taxi_4] Starting at (78.90, 12.34)

[MANAGER] Registered taxi taxi_0 at (34.56, 78.91)
[MANAGER] Registered taxi taxi_1 at (12.34, 45.67)
...

[CLIENT client_0] Starting at (45.67, 23.45)
[CLIENT client_0] Destination: (78.90, 12.34)
[CLIENT client_0] Requested transport from Manager

[MANAGER] Received transport request from client_0
[MANAGER] Found taxi taxi_2 at distance 34.21
[TAXI taxi_2] Accepted transport for client_0
[TAXI taxi_2] Transport: (45.67, 23.45) -> (78.90, 12.34)
[CLIENT client_0] Transport confirmed by taxi_2
[TAXI taxi_2] Transport completed at (78.90, 12.34)
[CLIENT client_0] Transport completed by taxi_2
[CLIENT client_0] Now at (78.90, 12.34)

============================================================
   ALL AGENTS INITIALIZED - SYSTEM RUNNING
============================================================
```

## 🔧 Personalização

### Alterar Número de Agentes
Editar `main_simple.py`:
```python
NUM_INITIAL_CLIENTS = 10        # Aumentar/diminuir
NUM_TAXIS = 5                   # Aumentar/diminuir
NEW_CLIENTS_PER_SECOND = 10     # Aumentar/diminuir
```

### Alterar Duração do Transporte
Editar `Taxi.py`:
```python
self.transport_end_time = asyncio.get_event_loop().time() + 3  # Alterar 3 para outro valor
```

### Alterar Intervalo de Criação de Clientes
Editar `main_simple.py`:
```python
SPAWN_INTERVAL = 1  # Alterarem segundos
```

## ⚠️ Notas Importantes

1. **GPS Aleatórias**: Todas as coordenadas são geradas aleatoriamente entre 0-100
2. **Transporte de 3 segundos**: Simula tempo realista de transporte
3. **Criação Periódica**: 10 novos clientes a cada segundo
4. **Fila de Espera**: Se não houver taxis disponíveis, pedidos entram em fila