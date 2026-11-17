import { BrowserProvider, Contract } from '/ethers.js';

const $ = (id) => document.getElementById(id);
let config, provider, contract, account, busy = false;
const status = (message, error = false) => { $('status').textContent = message; $('status').classList.toggle('error', error); };
const errorText = (err) => err.reason || err.info?.error?.message || err.shortMessage || err.message;
const short = (address) => `${address.slice(0, 6)}…${address.slice(-4)}`;
function setBusy(value) {
  busy = value;
  $('connect').disabled = value;
  $('refresh').disabled = value || !contract;
  $('submit').disabled = value || !contract;
  document.querySelectorAll('[data-action]').forEach(button => { button.disabled = value || button.dataset.allowed !== 'true'; });
}
async function loadConfig() {
  const response = await fetch('/deployment.json');
  if (!response.ok) throw new Error('Chưa có cấu hình contract. Chạy npm run deploy trước.');
  config = await response.json();
  $('contract').textContent = config.address;
  $('chain').textContent = config.chainId;
}
async function connect() {
  setBusy(true);
  try {
    await loadConfig();
    if (!window.ethereum) throw new Error('Cài MetaMask và thêm mạng Ganache để kết nối ví.');
    provider = new BrowserProvider(window.ethereum);
    await provider.send('eth_requestAccounts', []);
    const network = await provider.getNetwork();
    if (network.chainId !== BigInt(config.chainId)) throw new Error(`Sai mạng. Chọn Ganache: RPC ${config.rpcUrl}, Chain ID ${config.chainId}.`);
    if (await provider.getCode(config.address) === '0x') throw new Error('Không tìm thấy contract. Ganache có thể đã khởi động lại; chạy npm run deploy.');
    const signer = await provider.getSigner();
    account = await signer.getAddress();
    contract = new Contract(config.address, config.abi, signer);
    $('account').textContent = account;
    $('connect').textContent = short(account);
    await render();
    status('Đã kết nối Ganache. Bạn có thể đăng đề xuất và ủng hộ ý tưởng.');
  } catch (err) { contract = null; status(errorText(err), true); }
  finally { setBusy(false); }
}
function element(tag, className, text) {
  const node = document.createElement(tag); node.className = className; node.textContent = text; return node;
}
async function render() {
  const count = Number(await contract.proposalCount());
  const cards = [];
  for (let id = count - 1; id >= 0; id--) {
    const proposal = await contract.getProposal(id);
    const endorsed = await contract.hasEndorsed(id, account);
    const isAuthor = proposal.author.toLowerCase() === account.toLowerCase();
    const card = element('article', 'proposal', '');
    const top = element('div', 'card-top', '');
    top.append(element('span', '', `ĐỀ XUẤT #${id + 1}`), element('span', `badge ${proposal.closed ? 'closed' : ''}`, proposal.closed ? 'Đã đóng' : 'Đang mở'));
    card.append(top, element('h3', '', proposal.title), element('p', 'description', proposal.description), element('p', 'author', `Tác giả: ${proposal.author}`));
    const bottom = element('div', 'card-bottom', '');
    const votes = element('span', 'support-count', '');
    votes.append(element('strong', '', String(proposal.endorsementCount)), document.createTextNode('lượt ủng hộ'));
    const allowed = !proposal.closed && (isAuthor || !endorsed);
    const button = element('button', isAuthor ? 'secondary' : '', proposal.closed ? 'Đã đóng' : isAuthor ? 'Đóng đề xuất' : endorsed ? '✓ Đã ủng hộ' : 'Ủng hộ ↗');
    button.dataset.action = isAuthor ? 'close' : 'endorse'; button.dataset.allowed = String(allowed); button.disabled = busy || !allowed;
    button.onclick = () => transact(() => isAuthor ? contract.closeProposal(id) : contract.endorseProposal(id));
    bottom.append(votes, button); card.append(bottom); cards.push(card);
  }
  $('count').textContent = count;
  $('proposals').replaceChildren(...(cards.length ? cards : [element('div', 'empty', 'Chưa có đề xuất. Hãy chia sẻ ý tưởng đầu tiên!')]));
}
async function transact(send, onSuccess) {
  if (busy) return;
  setBusy(true);
  try {
    status('Vui lòng xác nhận giao dịch trong ví…');
    const transaction = await send();
    status(`Đang chờ xác nhận · ${transaction.hash}`);
    const receipt = await transaction.wait();
    if (!receipt || receipt.status !== 1) throw new Error('Giao dịch không thành công.');
    onSuccess?.();
    await render();
    const names = receipt.logs.map(log => { try { return contract.interface.parseLog(log)?.name; } catch { return null; } }).filter(Boolean);
    status(`Thành công · ${names.join(', ')} · Block ${receipt.blockNumber} · ${transaction.hash}`);
  } catch (err) { status(errorText(err), true); }
  finally { setBusy(false); }
}
$('connect').onclick = connect;
$('refresh').onclick = async () => {
  if (!contract || busy) return;
  setBusy(true);
  try { await render(); status('Đã cập nhật dữ liệu từ contract.'); } catch (err) { status(errorText(err), true); } finally { setBusy(false); }
};
$('create').onsubmit = (event) => {
  event.preventDefault();
  if (!contract || busy) return;
  const title = $('title').value.trim(), description = $('description').value.trim();
  const bytes = text => new TextEncoder().encode(text).length;
  if (!title || bytes(title) > 120 || !description || bytes(description) > 2000) { status('Tiêu đề cần 1–120 byte; nội dung cần 1–2.000 byte UTF-8.', true); return; }
  transact(() => contract.createProposal(title, description), () => $('create').reset());
};
window.ethereum?.on('accountsChanged', () => location.reload());
window.ethereum?.on('chainChanged', () => location.reload());
loadConfig().catch(err => status(errorText(err), true));
setBusy(false);
