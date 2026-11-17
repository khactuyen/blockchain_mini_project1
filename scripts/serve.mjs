import http from 'node:http';
import fs from 'node:fs/promises';

const files = { '/': ['../web/index.html', 'text/html'], '/app.js': ['../web/app.js', 'text/javascript'], '/style.css': ['../web/style.css', 'text/css'], '/deployment.json': ['../web/deployment.json', 'application/json'], '/ethers.js': ['../node_modules/ethers/dist/ethers.min.js', 'text/javascript'] };
http.createServer(async (req, res) => {
  const file = files[new URL(req.url, 'http://localhost').pathname];
  if (!file) { res.writeHead(404); res.end('Not found'); return; }
  try {
    const content = await fs.readFile(new URL(file[0], import.meta.url));
    res.writeHead(200, { 'Content-Type': `${file[1]}; charset=utf-8`, 'Cache-Control': 'no-store' }); res.end(content);
  } catch { res.writeHead(404); res.end('Missing file. Run npm run deploy first.'); }
}).listen(3000, '127.0.0.1', () => console.log('Open http://127.0.0.1:3000'));
