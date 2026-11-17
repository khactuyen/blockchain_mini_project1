import fs from 'node:fs';
import { JsonRpcProvider, ContractFactory } from 'ethers';
import { compile } from './compile.mjs';

const rpcUrl = process.env.RPC_URL || 'http://127.0.0.1:7545';
const url = new URL(rpcUrl);
if (!['127.0.0.1', 'localhost', '[::1]'].includes(url.hostname)) throw new Error('Use a local Ganache RPC URL.');
const provider = new JsonRpcProvider(rpcUrl);
try {
  const client = await provider.send('web3_clientVersion', []);
  if (!/ganache|testrpc/i.test(client)) throw new Error('Expected local Ganache.');
  const artifact = compile();
  const signer = await provider.getSigner(0);
  const contract = await new ContractFactory(artifact.abi, artifact.bytecode, signer).deploy();
  await contract.waitForDeployment();
  const deployment = { contractName: artifact.contractName, address: await contract.getAddress(), chainId: Number((await provider.getNetwork()).chainId), rpcUrl, abi: artifact.abi, transactionHash: contract.deploymentTransaction().hash };
  for (const path of ['../deployment.json', '../web/deployment.json']) fs.writeFileSync(new URL(path, import.meta.url), JSON.stringify(deployment, null, 2));
  console.log(`Deployed to ${deployment.address}\nChain ID: ${deployment.chainId}\nDeployment config written for Python and browser.`);
} finally { provider.destroy(); }
