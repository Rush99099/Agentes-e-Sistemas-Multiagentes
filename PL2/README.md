Sistema SPADE — Seller / Buyer
Sistema SPADE — Seller / Buyer

Descrição
- Implementação de um agente `Seller` e vários agentes `Buyer` usando SPADE.
- `Seller` disponibiliza uma lista de produtos (stock finito) e responde a pedidos
  de compra com `confirm` ou `refuse`. O `Seller` repõe stock periodicamente (configurável).
- `Buyer` envia, a cada segundo, um pedido de compra (`REQUEST`) ao `Seller` e
  espera pela resposta; se o pedido for recusado por falta de stock, o `Buyer` pode
  optar por tentar novamente mais tarde com uma probabilidade configurável.

Arquivos
- seller.py — implementação do agente `Seller`
- buyer.py — implementação do agente `Buyer`
- run_agents.py — script para arrancar os agentes
- requirements.txt — dependências

Requisitos
1. Ter um servidor XMPP (ex.: OpenFire / ejabberd) com contas criadas para os agentes.
2. Criar contas JID e passwords (por exemplo: seller@localhost / sellerpwd, buyer1@localhost / b1pwd, ...).

Execução (exemplo)

1) Instalar dependências

```bash
python -m pip install -r "Agentes e Sistemas Multiagentes/PL2/requirements.txt"
```

2) Executar exemplo (substitua JIDs/passwords pelos das suas contas XMPP)

```bash
python "Agentes e Sistemas Multiagentes/PL2/run_agents.py" \
  --seller-jid seller@localhost --seller-pwd sellerpwd \
  --buyers "buyer1@localhost:b1pwd,buyer2@localhost:b2pwd" \
  --initial-stock 5 --max-stock 20 --restock-amount 10 --restock-interval 20 \
  --buyer-retry-prob 0.6 --buyer-retry-delay-min 4 --buyer-retry-delay-max 12
```

Notas
- As contas XMPP devem existir no servidor e os JIDs devem ser válidos.
- O `Seller` interpreta o corpo das mensagens como JSON: {"product":"Apple","quantity":2}.
- O `Seller` usa stock finito e repõe stock periodicamente conforme os argumentos de execução.
- O `Buyer` pode reagir a recusas (`refuse`) por `out_of_stock` ou `not_available` e decidir
  com probabilidade se vai tentar novamente mais tarde.

Se quiser, eu posso: 1) adaptar os agentes para registar contas automaticamente (quando o servidor permitir), ou 2) executar um teste local se me fornecer as credenciais XMPP.
