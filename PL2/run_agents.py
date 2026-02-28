import asyncio
import argparse
import os
import sys

# Ensure local folder is on path when running from repository root
sys.path.append(os.path.dirname(__file__))

from seller import SellerAgent
from buyer import BuyerAgent


async def start_agents(
    seller_jid,
    seller_pwd,
    buyer_pairs,
    initial_stock=10,
    max_stock=20,
    restock_amount=10,
    restock_interval=20,
    buyer_retry_prob=0.5,
    buyer_retry_delay_min=3.0,
    buyer_retry_delay_max=10.0,
):
    seller = SellerAgent(
        seller_jid,
        seller_pwd,
        initial_stock=initial_stock,
        max_stock=max_stock,
        restock_amount=restock_amount,
        restock_interval=restock_interval,
    )
    await seller.start()

    buyers = []
    for jid, pwd in buyer_pairs:
        b = BuyerAgent(
            jid,
            pwd,
            seller_jid,
            retry_probability=buyer_retry_prob,
            retry_delay_range=(buyer_retry_delay_min, buyer_retry_delay_max),
        )
        await b.start()
        buyers.append(b)

    print("Agents started — press Ctrl+C to stop")

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("Stopping agents...")
    finally:
        for b in buyers:
            await b.stop()
        await seller.stop()


def parse_buyers_spec(spec):
    # spec: "buyer1@server:pwd,buyer2@server:pwd"
    pairs = []
    if not spec:
        return pairs
    for token in spec.split(','):
        if ':' not in token:
            raise ValueError('Each buyer must be specified as jid:password')
        jid, pwd = token.split(':', 1)
        pairs.append((jid.strip(), pwd.strip()))
    return pairs


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run SPADE Seller and Buyer agents')
    parser.add_argument('--seller-jid', required=True)
    parser.add_argument('--seller-pwd', required=True)
    parser.add_argument('--buyers', required=True, help='Comma-separated buyer_jid:pwd pairs')
    parser.add_argument('--initial-stock', type=int, default=10, help='Initial stock per product')
    parser.add_argument('--max-stock', type=int, default=20, help='Maximum stock per product')
    parser.add_argument('--restock-amount', type=int, default=10, help='Amount added at each restock')
    parser.add_argument('--restock-interval', type=int, default=20, help='Restock period (seconds)')
    parser.add_argument('--buyer-retry-prob', type=float, default=0.5, help='Probability buyer retries after refuse')
    parser.add_argument('--buyer-retry-delay-min', type=float, default=3.0, help='Min retry delay (seconds)')
    parser.add_argument('--buyer-retry-delay-max', type=float, default=10.0, help='Max retry delay (seconds)')

    args = parser.parse_args()

    buyers = parse_buyers_spec(args.buyers)

    asyncio.run(
        start_agents(
            args.seller_jid,
            args.seller_pwd,
            buyers,
            args.initial_stock,
            args.max_stock,
            args.restock_amount,
            args.restock_interval,
            args.buyer_retry_prob,
            args.buyer_retry_delay_min,
            args.buyer_retry_delay_max,
        )
    )
