"""
Deploy MatchRegistry.sol to configured EVM Blockchain (Polygon Amoy / Ethereum Sepolia / Local).
Compiles Solidity source, deploys the contract, writes artifacts to contracts/MatchRegistry.json,
and prints explorer links.
"""

import os
import sys
import json

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from dotenv import load_dotenv
from web3 import Web3

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

load_dotenv()

CONTRACT_SOURCE_PATH = os.path.join(os.path.dirname(__file__), "..", "contracts", "MatchRegistry.sol")
CONTRACT_JSON_PATH = os.path.join(os.path.dirname(__file__), "..", "contracts", "MatchRegistry.json")


def compile_solidity_contract():
    """Compile MatchRegistry.sol using py-solc-x or return existing compiled json."""
    try:
        import solcx
        print("[1/3] Compiling Solidity smart contract...")
        
        try:
            solcx.install_solc("0.8.20")
        except Exception:
            pass

        res = solcx.compile_files([CONTRACT_SOURCE_PATH], output_values=["abi", "bin"], solc_version="0.8.20")
        key = list(res.keys())[0]
        abi = res[key]["abi"]
        bytecode = res[key]["bin"]

        artifact = {
            "contractName": "MatchRegistry",
            "abi": abi,
            "bytecode": bytecode
        }

        with open(CONTRACT_JSON_PATH, "w") as f:
            json.dump(artifact, f, indent=2)

        print("  [OK] Compilation successful -> saved to contracts/MatchRegistry.json")
        return abi, bytecode
    except Exception as e:
        print(f"  [Notice] solc compilation note: {e}")
        if os.path.exists(CONTRACT_JSON_PATH):
            with open(CONTRACT_JSON_PATH, "r") as f:
                data = json.load(f)
                return data["abi"], data["bytecode"]
        raise e


def deploy_contract():
    """Deploy MatchRegistry contract to blockchain."""
    rpc_url = os.getenv("RPC_URL", "https://rpc-amoy.polygon.technology/")
    private_key = os.getenv("PRIVATE_KEY")
    chain_id = int(os.getenv("CHAIN_ID", "80002"))
    explorer_url = os.getenv("EXPLORER_URL", "https://amoy.polygonscan.com")

    abi, bytecode = compile_solidity_contract()

    print(f"\n[2/3] Connecting to RPC endpoint: {rpc_url} (Chain ID: {chain_id})")
    
    is_live = (
        rpc_url and
        private_key and
        not private_key.startswith("your_") and
        len(private_key.replace("0x", "")) == 64
    )

    w3 = None
    account = None

    if is_live:
        try:
            w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 5}))
            if w3.is_connected():
                clean_key = private_key if private_key.startswith("0x") else f"0x{private_key}"
                account = w3.eth.account.from_key(clean_key)
                deployer_addr = account.address
        except Exception:
            w3 = None

    if w3 is None or not w3.is_connected():
        print("  [Notice] Live private key or RPC not active. Deploying to Local In-Memory Web3 Provider.")
        from web3.providers.eth_tester import EthereumTesterProvider
        w3 = Web3(EthereumTesterProvider())
        deployer_addr = w3.eth.accounts[0]
        account = None

    print(f"  [OK] Connected! Deployer address: {deployer_addr}")

    print("\n[3/3] Deploying MatchRegistry contract...")
    contract_factory = w3.eth.contract(abi=abi, bytecode=bytecode)

    if account:
        nonce = w3.eth.get_transaction_count(deployer_addr)
        gas_price = w3.eth.gas_price
        construct_tx = contract_factory.constructor().build_transaction({
            "from": deployer_addr,
            "nonce": nonce,
            "gas": 1500000,
            "gasPrice": gas_price,
            "chainId": chain_id
        })
        signed_tx = w3.eth.account.sign_transaction(construct_tx, private_key=account.key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        print(f"  -> Deployment tx broadcasted: {tx_hash.hex()}")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        deployed_address = receipt.contractAddress
    else:
        tx_hash = contract_factory.constructor().transact({"from": deployer_addr})
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        deployed_address = receipt.contractAddress

    print("\n" + "=" * 60)
    print("MATCH REGISTRY SMART CONTRACT DEPLOYED SUCCESSFULLY!")
    print("=" * 60)
    print(f" Contract Address : {deployed_address}")
    print(f" Transaction Hash : {receipt.transactionHash.hex() if hasattr(receipt.transactionHash, 'hex') else receipt.transactionHash}")
    print(f" Block Number     : {receipt.blockNumber}")
    print(f" Gas Used         : {receipt.gasUsed}")
    if explorer_url:
        print(f" Explorer Link    : {explorer_url}/address/{deployed_address}")
    print("=" * 60)
    print(f"\nAdd this to your .env file:\nCONTRACT_ADDRESS={deployed_address}\n")

    return deployed_address


if __name__ == "__main__":
    deploy_contract()
