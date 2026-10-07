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
    const message = await readContract.message();
    const lastSender = await readContract.lastSender();
    document.getElementById("message").innerText = message;
    document.getElementById("lastSender").innerText = lastSender;
    const updateCount = Number(await readContract.updateCount());
    document.getElementById("updateCount").innerText = updateCount;

    // If the message was changed outside this website, add it to the history too
    const res = await fetch("/api/messages/sync", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content: message, sender: lastSender, update_count: updateCount })
    });
    if ((await res.json()).added) loadHistory();
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
    const updateCount = Number(await contract.updateCount());

    // Save a copy to the database (Create)
    await fetch("/api/messages", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        content: newMessage,
        sender: await signer.getAddress(),
        tx_hash: tx.hash,
        update_count: updateCount
      })
    });

    status.innerText = "✅ Message updated!";
    document.getElementById("newMessage").value = "";
    loadMessage();
    loadHistory();
  } catch (err) {
    status.innerText = "❌ " + (err.shortMessage || err.message);
  }
}

// 4. Read the message history from the database (Read)
async function loadHistory() {
  const list = document.getElementById("history");
  const rows = await (await fetch("/api/messages")).json();
  list.innerHTML = "";
  if (rows.length === 0) {
    list.innerHTML = '<li class="small">No records yet.</li>';
    return;
  }
  for (const row of rows) {
    const li = document.createElement("li");
    const text = document.createElement("div");
    text.innerHTML = '<div class="history-msg"></div><div class="small"></div>';
    text.children[0].innerText = row.content;
    text.children[1].innerText = row.sender.slice(0, 8) + "... · " + row.created_at;

    const btn = document.createElement("button");
    btn.className = "danger";
    btn.innerText = "Delete";
    btn.onclick = () => deleteHistory(row.id);

    li.append(text, btn);
    list.append(li);
  }
}

// 5. Delete a record from the database (Delete)
// Note: this only removes the database copy; the blockchain itself cannot be changed.
async function deleteHistory(id) {
  if (!confirm("Delete this record?")) return;
  await fetch("/api/messages/" + id, { method: "DELETE" });
  loadHistory();
}

document.getElementById("connectBtn").onclick = connectWallet;
document.getElementById("refreshBtn").onclick = loadMessage;
document.getElementById("setBtn").onclick = setMessage;

loadMessage();
loadHistory();
