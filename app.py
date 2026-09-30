"""
Flask dApp - On-chain Guestbook.

The Guestbook smart contract (Guestbook.sol) stores messages, likes and tips
on the blockchain. This Flask app serves the web page and tells the frontend
which contract and network to use. Reading and writing to the chain happens
in the browser with ethers.js and the user's wallet (e.g. MetaMask).
"""
import os

from flask import Flask, jsonify, render_template

app = Flask(__name__)


def get_config():
    """Network + contract settings, read from environment variables."""
    return {
        "contractAddress": os.environ.get("CONTRACT_ADDRESS", "").strip(),
        "chainId": int(os.environ.get("CHAIN_ID", "11155111")),  # Sepolia testnet
        "chainName": os.environ.get("CHAIN_NAME", "Sepolia"),
        "rpcUrl": os.environ.get("RPC_URL", "https://ethereum-sepolia-rpc.publicnode.com"),
        "explorerUrl": os.environ.get("EXPLORER_URL", "https://sepolia.etherscan.io"),
    }


@app.get("/")
def index():
    return render_template("index.html", config=get_config())


@app.get("/api/config")
def api_config():
    return jsonify(get_config())


@app.get("/health")
def health():
    return jsonify(status="ok")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
