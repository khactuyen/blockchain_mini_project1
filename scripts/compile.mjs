import fs from 'node:fs';
import solc from 'solc';
import { fileURLToPath } from 'node:url';

export function compile() {
  const source = fs.readFileSync(new URL('../contracts/CommunityProposalBoard.sol', import.meta.url), 'utf8');
  const output = JSON.parse(solc.compile(JSON.stringify({
    language: 'Solidity', sources: { 'CommunityProposalBoard.sol': { content: source } },
    settings: { optimizer: { enabled: true, runs: 200 }, evmVersion: 'paris', outputSelection: { '*': { '*': ['abi', 'evm.bytecode.object'] } } }
  })));
  for (const issue of output.errors ?? []) {
    if (issue.severity === 'error') throw new Error(issue.formattedMessage);
    console.warn(issue.formattedMessage);
  }
  const contract = output.contracts['CommunityProposalBoard.sol'].CommunityProposalBoard;
  const artifact = { contractName: 'CommunityProposalBoard', compiler: solc.version(), abi: contract.abi, bytecode: `0x${contract.evm.bytecode.object}` };
  fs.mkdirSync(new URL('../artifacts/', import.meta.url), { recursive: true });
  fs.writeFileSync(new URL('../artifacts/CommunityProposalBoard.json', import.meta.url), JSON.stringify(artifact, null, 2));
  return artifact;
}
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  compile();
  console.log('Compiled CommunityProposalBoard (Paris EVM, Ganache compatible).');
}
