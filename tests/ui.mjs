// Optional UI verification: npm install --no-save playwright, then node tests/ui.mjs.
// A local EIP-1193 test wallet forwards requests to Ganache; no browser extension required.
import { chromium } from 'playwright';
import assert from 'node:assert/strict';
import fs from 'node:fs';
const config = JSON.parse(fs.readFileSync(new URL('../deployment.json', import.meta.url)));
const rpc = async (method, params = []) => (await (await fetch(config.rpcUrl, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ jsonrpc: '2.0', id: 1, method, params }) })).json()).result;
const accounts = await rpc('eth_accounts');
const browser = await chromium.launch({ headless: true, ...(process.env.CHROME_PATH ? { executablePath: process.env.CHROME_PATH } : {}) });
try {
  const context = await browser.newContext({ viewport: { width: 1440, height: 1100 } });
  await context.addInitScript(({ rpcUrl, accounts }) => {
    window.testAccount = accounts[0];
    window.ethereum = {
      on() {},
      async request({ method, params = [] }) {
        if (method === 'eth_requestAccounts' || method === 'eth_accounts') return [window.testAccount];
        const response = await fetch(rpcUrl, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ jsonrpc: '2.0', id: 1, method, params }) });
        const result = await response.json();
        if (result.error) throw Object.assign(new Error(result.error.message), result.error);
        return result.result;
      }
    };
  }, { rpcUrl: config.rpcUrl, accounts });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('http://127.0.0.1:3000');
  await page.locator('#connect').click();
  await page.waitForFunction(() => document.querySelector('#status').textContent.startsWith('Đã kết nối'));
  await page.locator('#title').fill('Trồng cây tại công viên');
  await page.locator('#description').fill('Thêm bóng mát và không gian xanh cho cộng đồng.');
  await page.locator('#submit').click();
  await page.waitForFunction(() => document.querySelector('#status').textContent.includes('ProposalCreated'));
  const card = page.locator('.proposal').first();
  await card.getByRole('button', { name: 'Đóng đề xuất' }).waitFor();
  await page.evaluate(address => { window.testAccount = address; }, accounts[1]);
  await page.locator('#connect').click();
  await card.getByRole('button', { name: 'Ủng hộ ↗' }).click();
  await page.waitForFunction(() => document.querySelector('#status').textContent.includes('ProposalEndorsed'));
  assert.equal(await card.locator('strong').textContent(), '1');
  assert.equal(await card.getByRole('button', { name: '✓ Đã ủng hộ' }).isDisabled(), true);
  fs.mkdirSync(new URL('../screenshots/', import.meta.url), { recursive: true });
  await page.screenshot({ path: new URL('../screenshots/desktop.png', import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1'), fullPage: true });
  await page.evaluate(address => { window.testAccount = address; }, accounts[0]);
  await page.locator('#connect').click();
  await card.getByRole('button', { name: 'Đóng đề xuất' }).click();
  await page.waitForFunction(() => document.querySelector('#status').textContent.includes('ProposalClosed'));
  assert.equal(await card.getByRole('button', { name: 'Đã đóng', exact: true }).isDisabled(), true);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({ path: new URL('../screenshots/mobile.png', import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1'), fullPage: true });
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
  assert.deepEqual(errors, []);
  console.log('UI PASS: connect, create, switch wallet, endorse, duplicate disabled, close, mobile overflow and screenshots.');
} finally { await browser.close(); }
