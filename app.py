import os

from flask import Flask, render_template

app = Flask(__name__)

# Set these in Render -> Environment
CONTRACT_ADDRESS = os.environ.get("CONTRACT_ADDRESS", "")
RPC_URL = os.environ.get("RPC_URL", "https://ethereum-sepolia-rpc.publicnode.com")


@app.route("/")
def index():
    return render_template("index.html", contract_address=CONTRACT_ADDRESS, rpc_url=RPC_URL)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
