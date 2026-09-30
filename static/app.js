// ABI: the functions of MessageBoard.sol that the website uses
const ABI = [
  "function message() view returns (string)",
  "function lastSender() view returns (address)",
  "function updateCount() view returns (uint256)",
  "function setMessage(string newMessage)"
];

const SEPOLIA_CHAIN_ID = "0xaa36a7"; // 11155111

let signer = null;

// Read-only connection: lets anyone see the message, even without a wallet
const readProvider = new ethers.JsonRpcProvider(RPC_URL);
const readContract = new ethers.Contract(CONTRACT_ADDRESS, ABI, readProvider);

// On a phone without a wallet, show a button to open this page in the MetaMask app
if (!window.ethereum && /Android|iPhone|iPad/i.test(navigator.userAgent)) {
  const link = document.getElementById("mobileLink");
  link.href = "https://metamask.app.link/dapp/" + location.host + location.pathname;
  link.classList.remove("hidden");
}

// 1. Connect MetaMask and switch to Sepolia
async function connectWallet() {
  if (!window.ethereum) {
    alert("Please install MetaMask!");
    return;
  }
  await window.ethereum.request({ method: "eth_requestAccounts" });
  await window.ethereum.request({
    method: "wallet_switchEthereumChain",
    params: [{ chainId: SEPOLIA_CHAIN_ID }]
  });

  const provider = new ethers.BrowserProvider(window.ethereum);
  signer = await provider.getSigner();
  const address = await signer.getAddress();
  document.getElementById("account").innerText = "Connected: " + address;
  document.getElementById("connectBtn").innerText = "Connected";
}

// 2. Read the message from the blockchain (free, no gas)
async function loadMessage() {
  try {
    document.getElementById("message").innerText = await readContract.message();
    document.getElementById("lastSender").innerText = await readContract.lastSender();
    document.getElementById("updateCount").innerText = (await readContract.updateCount()).toString();
  } catch (err) {
    document.getElementById("message").innerText = "Could not load the message.";
    console.error(err);
  }
}

// 3. Write a new message to the blockchain (needs a transaction + gas)
async function setMessage() {
  const status = document.getElementById("status");
  const newMessage = document.getElementById("newMessage").value.trim();

  if (!signer) {
    status.innerText = "Please connect your wallet first.";
    return;
  }
  if (newMessage === "") {
    status.innerText = "Please type a message.";
    return;
  }

  try {
    const contract = new ethers.Contract(CONTRACT_ADDRESS, ABI, signer);
    status.innerText = "Please confirm in MetaMask...";
    const tx = await contract.setMessage(newMessage);

    status.innerText = "Waiting for the transaction to be confirmed...";
    await tx.wait();

    status.innerText = "✅ Message updated!";
    document.getElementById("newMessage").value = "";
    loadMessage();
  } catch (err) {
    status.innerText = "❌ " + (err.shortMessage || err.message);
  }
}

document.getElementById("connectBtn").onclick = connectWallet;
document.getElementById("refreshBtn").onclick = loadMessage;
document.getElementById("setBtn").onclick = setMessage;

loadMessage();
