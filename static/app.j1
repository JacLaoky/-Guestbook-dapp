// ---------------- Config (injected by Flask in index.html) ----------------
const CONFIG = window.CONFIG;

// Guestbook.sol ABI in ethers.js "human-readable" format
const ABI = [
  "function post(string text)",
  "function like(uint256 id)",
  "function tip(uint256 id) payable",
  "function count() view returns (uint256)",
  "function getAll() view returns (tuple(address author, string text, uint256 timestamp, uint256 likes, uint256 tips)[])",
  "function hasLiked(uint256 id, address user) view returns (bool)",
  "event NewEntry(uint256 indexed id, address indexed author, string text)",
  "event Liked(uint256 indexed id, address indexed user)",
  "event Tipped(uint256 indexed id, address indexed from, uint256 amount)"
];
const MAX_BYTES = 280;
const $ = (id) => document.getElementById(id);

let readContract = null;   // read-only (public RPC, no wallet needed)
let writeContract = null;  // signs transactions with the user's wallet
let account = null;

// ---------------- Helpers ----------------
function setStatus(el, msg, type = "") {
  el.innerHTML = msg;
  el.className = "status " + type;
}
const short = (a) => a.slice(0, 6) + "..." + a.slice(-4);
const escapeHtml = (s) => s.replace(/[&<>"']/g, (c) => (
  { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const byteLength = (s) => new TextEncoder().encode(s).length;
const txLink = (hash) =>
  `<a href="${CONFIG.explorerUrl}/tx/${hash}" target="_blank" rel="noopener">View transaction ↗</a>`;
const fmtEth = (wei) => {
  const n = Number(ethers.formatEther(wei));
  return n === 0 ? "0" : n < 0.0001 ? "<0.0001" : String(+n.toFixed(4));
};

function errorMessage(e) {
  if (e?.code === "ACTION_REJECTED" || e?.code === 4001) return "Transaction rejected in wallet.";
  return e?.reason || e?.shortMessage || e?.info?.error?.message || e?.message || "Something went wrong.";
}

// ---------------- Wallet ----------------
const isMobile = /Android|iPhone|iPad|iPod|Mobile/i.test(navigator.userAgent);
$("metamaskLink").href = "https://metamask.app.link/dapp/" + location.host + location.pathname;
if (isMobile && !window.ethereum) $("mobileHelp").classList.remove("hidden");

async function ensureNetwork() {
  const hexId = "0x" + CONFIG.chainId.toString(16);
  const current = await window.ethereum.request({ method: "eth_chainId" });
  if (current === hexId) return;
  try {
    await window.ethereum.request({ method: "wallet_switchEthereumChain", params: [{ chainId: hexId }] });
  } catch (e) {
    if (e.code === 4902) {
      await window.ethereum.request({
        method: "wallet_addEthereumChain",
        params: [{
          chainId: hexId, chainName: CONFIG.chainName, rpcUrls: [CONFIG.rpcUrl],
          nativeCurrency: { name: "Ether", symbol: "ETH", decimals: 18 },
          blockExplorerUrls: [CONFIG.explorerUrl]
        }]
      });
    } else {
      throw e;
    }
  }
}

async function refreshWallet() {
  if (!account) return;
  const provider = new ethers.BrowserProvider(window.ethereum);
  const [network, balance] = await Promise.all([provider.getNetwork(), provider.getBalance(account)]);
  const onRightChain = Number(network.chainId) === CONFIG.chainId;
  $("address").textContent = account;
  $("network").textContent = onRightChain
    ? CONFIG.chainName
    : `Chain ${network.chainId} (please switch to ${CONFIG.chainName})`;
  $("balance").textContent = `${fmtEth(balance)} ETH`;
  $("walletInfo").classList.remove("hidden");
  $("connectBtn").textContent = "Connected: " + short(account);

  if (readContract && onRightChain) {
    const signer = await provider.getSigner();
    writeContract = new ethers.Contract(CONFIG.contractAddress, ABI, signer);
  } else {
    writeContract = null;
  }
  $("postBtn").disabled = !writeContract;
  loadEntries();
}

async function connect() {
  if (!window.ethereum) {
    if (isMobile) {
      setStatus($("walletStatus"), "No wallet detected. Tap “Open in MetaMask App”.", "err");
      $("mobileHelp").classList.remove("hidden");
    } else {
      setStatus($("walletStatus"), "No wallet found. Please install MetaMask or another browser wallet.", "err");
    }
    return;
  }
  try {
    const accounts = await window.ethereum.request({ method: "eth_requestAccounts" });
    account = accounts[0];
    await ensureNetwork();
    setStatus($("walletStatus"), "Wallet connected.", "ok");
    await refreshWallet();
  } catch (e) {
    setStatus($("walletStatus"), errorMessage(e), "err");
    if (account) refreshWallet();
  }
}

// ---------------- Contract actions ----------------
async function sendTx(statusEl, action, successMsg) {
  try {
    setStatus(statusEl, "Please confirm in your wallet...");
    const tx = await action();
    setStatus(statusEl, `Waiting for confirmation... ${txLink(tx.hash)}`);
    await tx.wait();
    setStatus(statusEl, `${successMsg} ✔ ${txLink(tx.hash)}`, "ok");
    await Promise.all([loadEntries(), refreshWallet()]);
    return true;
  } catch (e) {
    setStatus(statusEl, errorMessage(e), "err");
    return false;
  }
}

async function post() {
  const text = $("text").value.trim();
  if (!text) return setStatus($("postStatus"), "Please write a message first.", "err");
  if (byteLength(text) > MAX_BYTES) return setStatus($("postStatus"), "Message is too long.", "err");
  $("postBtn").disabled = true;
  const ok = await sendTx($("postStatus"), () => writeContract.post(text), "Posted on-chain!");
  if (ok) { $("text").value = ""; updateCounter(); }
  $("postBtn").disabled = !writeContract;
}

async function like(id) {
  await sendTx($("entryStatus"), () => writeContract.like(id), `Liked message #${id}!`);
}

async function tip(id) {
  let value;
  try {
    value = ethers.parseEther(String($("tipAmount").value || "0"));
  } catch {
    return setStatus($("entryStatus"), "Invalid tip amount.", "err");
  }
  if (value <= 0n) return setStatus($("entryStatus"), "Tip must be greater than 0.", "err");
  await sendTx($("entryStatus"), () => writeContract.tip(id, { value }),
    `Tipped ${ethers.formatEther(value)} ETH to message #${id}!`);
}

// ---------------- Read messages ----------------
async function loadEntries() {
  if (!readContract) {
    $("entries").innerHTML = '<p class="empty">Contract not configured yet.</p>';
    return;
  }
  try {
    const all = await readContract.getAll();
    const entries = all.map((e, id) => ({
      id, author: e.author, text: e.text, timestamp: Number(e.timestamp),
      likes: Number(e.likes), tips: e.tips
    })).reverse(); // newest first

    // Stats
    $("statPosts").textContent = entries.length;
    $("statLikes").textContent = entries.reduce((s, e) => s + e.likes, 0);
    $("statTips").textContent = fmtEth(entries.reduce((s, e) => s + e.tips, 0n));

    // Which ones has the connected user already liked?
    let liked = new Set();
    if (account && entries.length) {
      const flags = await Promise.all(entries.map((e) => readContract.hasLiked(e.id, account)));
      entries.forEach((e, i) => flags[i] && liked.add(e.id));
    }

    const me = account?.toLowerCase();
    $("entries").innerHTML = entries.length
      ? entries.map((e) => {
          const mine = e.author.toLowerCase() === me;
          const hasLiked = liked.has(e.id);
          const canAct = !!writeContract;
          return `
            <div class="entry">
              <div class="text">${escapeHtml(e.text)}</div>
              <div class="meta">#${e.id} · <span class="mono">${short(e.author)}</span>${mine ? " (you)" : ""} ·
                ${new Date(e.timestamp * 1000).toLocaleString("en-US")}</div>
              <div class="actions">
                <button class="small ${hasLiked ? "liked" : ""}" data-like="${e.id}"
                  ${!canAct || hasLiked ? "disabled" : ""}>❤️ ${e.likes}</button>
                <button class="small" data-tip="${e.id}" ${!canAct || mine ? "disabled" : ""}
                  title="${mine ? "You cannot tip yourself" : ""}">💰 Tip</button>
                ${e.tips > 0n ? `<span class="tips">${fmtEth(e.tips)} ETH received</span>` : ""}
              </div>
            </div>`;
        }).join("")
      : '<p class="empty">No messages yet. Be the first!</p>';
  } catch (e) {
    console.error(e);
    $("entries").innerHTML = '<p class="empty">Could not load messages from the blockchain.</p>';
  }
}

function updateCounter() {
  const n = byteLength($("text").value);
  $("byteCount").textContent = n;
  $("byteCount").style.color = n > MAX_BYTES ? "var(--err)" : "";
}

// ---------------- Init ----------------
$("connectBtn").addEventListener("click", connect);
$("postBtn").addEventListener("click", post);
$("text").addEventListener("input", updateCounter);
$("entries").addEventListener("click", (ev) => {
  const btn = ev.target.closest("button");
  if (!btn || btn.disabled) return;
  if (btn.dataset.like) like(Number(btn.dataset.like));
  if (btn.dataset.tip) tip(Number(btn.dataset.tip));
});

if (window.ethereum) {
  window.ethereum.on?.("accountsChanged", (accs) => {
    account = accs[0] || null;
    if (account) return refreshWallet();
    writeContract = null;
    $("walletInfo").classList.add("hidden");
    $("connectBtn").textContent = "Connect Wallet";
    $("postBtn").disabled = true;
    loadEntries();
  });
  window.ethereum.on?.("chainChanged", () => refreshWallet());
}

(async function init() {
  if (!CONFIG.contractAddress) {
    $("configBanner").classList.remove("hidden");
    loadEntries();
    return;
  }
  $("contractLink").textContent = short(CONFIG.contractAddress);
  $("contractLink").href = `${CONFIG.explorerUrl}/address/${CONFIG.contractAddress}`;
  const readProvider = new ethers.JsonRpcProvider(CONFIG.rpcUrl, CONFIG.chainId, { staticNetwork: true });
  readContract = new ethers.Contract(CONFIG.contractAddress, ABI, readProvider);
  loadEntries();
})();
