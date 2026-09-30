# On-chain Guestbook dApp

A decentralized guestbook built with **Solidity + Flask + ethers.js**, deployable on **Render**.

## Features

- **Post** a message (up to 280 bytes) that is stored permanently on the blockchain
- **Like** a message (each wallet can like a message only once)
- **Tip** the author of a message with ETH (sent directly to the author's wallet)
- Live stats: total messages, likes and ETH tipped
- Anyone can read messages without a wallet (via a public RPC)
- Mobile friendly, with an "Open in MetaMask App" deep link for phones
- Links to every transaction on the block explorer

## Smart contract concepts used (`Guestbook.sol`)

| Concept             | Where                                                    |
|---------------------|----------------------------------------------------------|
| `struct` + array    | `Entry[] public entries` stores every message            |
| Nested `mapping`    | `hasLiked[id][user]` prevents double likes               |
| `payable` + ETH transfer | `tip()` forwards ETH to the author                  |
| `require` validation | empty / too long messages, self-tips, zero tips         |
| `event`             | `NewEntry`, `Liked`, `Tipped` (visible on Etherscan)     |
| `msg.sender`, `msg.value`, `block.timestamp` | author, tip amount, post time   |
| `view` functions    | `count()`, `getAll()`                                    |

## Project structure

```
guestbook-dapp/
├── app.py                    # Flask backend: serves the page + contract config
├── Guestbook.sol             # Solidity smart contract
├── requirements.txt
├── render.yaml               # Render deployment config
├── README.md
├── static/
│   ├── Guestbook.abi.json    # Contract ABI (compiled from Guestbook.sol)
│   └── ethers.umd.min.js     # ethers.js v6
└── templates/
    └── index.html            # Frontend
```

## Step 1 — Deploy the contract (Remix + MetaMask, Sepolia testnet)

1. Get some free Sepolia test ETH from a faucet (e.g. Google Cloud Web3 faucet or Alchemy faucet).
2. Open https://remix.ethereum.org and create a file `Guestbook.sol`; paste the contract code.
3. **Solidity Compiler** tab → compiler `0.8.20` or newer → **Compile Guestbook.sol**.
4. **Deploy & Run** tab → Environment: **Injected Provider - MetaMask** (make sure MetaMask is on Sepolia).
5. Click **Deploy** and confirm in MetaMask.
6. Copy the deployed contract address (e.g. `0xAbC...123`).

> If you change the contract, copy the new ABI from Remix (Compiler tab → ABI button)
> into `static/Guestbook.abi.json`.

## Step 2 — Run locally

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export CONTRACT_ADDRESS=0xYourContractAddress   # Windows: set CONTRACT_ADDRESS=0x...
python app.py
```

Open http://localhost:5000

## Step 3 — Deploy to Render

1. Push this folder to a GitHub repository.
2. On https://dashboard.render.com click **New → Blueprint** and select the repository.
3. Render reads `render.yaml`. When asked, paste your contract address into `CONTRACT_ADDRESS`.
4. Click **Apply** and open the `.onrender.com` URL when the build finishes.

**Manual setup (alternative):** New → Web Service → select the repo, then:

| Setting        | Value                                   |
|----------------|-----------------------------------------|
| Runtime        | Python 3                                |
| Build Command  | `pip install -r requirements.txt`       |
| Start Command  | `gunicorn app:app --bind 0.0.0.0:$PORT` |
| Env variable   | `CONTRACT_ADDRESS` = your contract address |

## Environment variables

| Name               | Default                                        | Description                  |
|--------------------|------------------------------------------------|------------------------------|
| `CONTRACT_ADDRESS` | *(required)*                                   | Deployed Guestbook address   |
| `CHAIN_ID`         | `11155111`                                     | Sepolia testnet              |
| `CHAIN_NAME`       | `Sepolia`                                      | Shown in the UI              |
| `RPC_URL`          | `https://ethereum-sepolia-rpc.publicnode.com`  | Used to read messages        |
| `EXPLORER_URL`     | `https://sepolia.etherscan.io`                 | Transaction / address links  |

## Using it on a phone

Normal mobile browsers (Safari, Chrome) cannot talk to a wallet. Tap **Open in MetaMask App**
on the page, or open the site URL inside your wallet app's built-in browser
(MetaMask, Trust Wallet, OKX Wallet, Coinbase Wallet, etc.).

## API

| Method | Path          | Description                                  |
|--------|---------------|----------------------------------------------|
| GET    | `/`           | The dApp web page                            |
| GET    | `/api/config` | Contract address, network settings and ABI   |
| GET    | `/health`     | Health check for Render                      |
