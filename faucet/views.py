from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import Throttled
from django.utils.timezone import now, timedelta
from faucet.models import TransactionLog
from web3 import Web3
import os

# Connect to Sepolia
w3 = Web3(Web3.HTTPProvider(os.getenv('SEPOLIA_RPC_URL')))
PRIVATE_KEY = os.getenv('PRIVATE_KEY')
FAUCET_ADDRESS = os.getenv('FAUCET_ADDRESS')

class FundView(APIView):
    throttle_scope = 'fund'

    def post(self, request):
        wallet_address = request.data.get("wallet_address")
        if not Web3.is_address(wallet_address):
            return Response({"error": "Invalid wallet address."}, status=400)
        
        recent_transaction = TransactionLog.objects.filter(
            wallet_address=wallet_address, 
            timestamp__gte=now() - timedelta(minutes=1)
        ).exists()
        if recent_transaction:
            return Response({"error": "Rate limit exceeded. Try again later."}, status=429)

        try:
            transaction = {
                'to': wallet_address,
                'value': w3.to_wei(0.0001, 'ether'),
                'gas': 21000,
                'gasPrice': w3.to_wei(10, 'gwei'),
                'nonce': w3.eth.get_transaction_count(FAUCET_ADDRESS),
            }
            signed_tx = w3.eth.account.sign_transaction(transaction, PRIVATE_KEY)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            tx_id = w3.to_hex(tx_hash)
            TransactionLog.objects.create(wallet_address=wallet_address, transaction_id=tx_id, status="success")
            return Response({"transaction_id": tx_id}, status=200)
        except Exception as e:
            TransactionLog.objects.create(wallet_address=wallet_address, status="failed")
            return Response({"error": str(e)}, status=500)

class StatsView(APIView):
    def get(self, request):
        past_24_hours = now() - timedelta(hours=24)
        success_count = TransactionLog.objects.filter(status="success", timestamp__gte=past_24_hours).count()
        failed_count = TransactionLog.objects.filter(status="failed", timestamp__gte=past_24_hours).count()
        return Response({"success_count": success_count, "failed_count": failed_count})
