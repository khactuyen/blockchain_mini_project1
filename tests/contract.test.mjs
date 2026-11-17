import { test } from 'node:test';
import assert from 'node:assert/strict';
import ganache from 'ganache';
import { BrowserProvider, ContractFactory } from 'ethers';
import { compile } from '../scripts/compile.mjs';

test('proposal lifecycle, permissions, events and independent endorsements', async () => {
  const rpc = ganache.provider({ logging: { quiet: true }, wallet: { totalAccounts: 3 }, chain: { hardfork: 'shanghai' } });
  const provider = new BrowserProvider(rpc);
  provider.pollingInterval = 50;
  try {
    const [author, supporter, other] = await Promise.all([0, 1, 2].map(i => provider.getSigner(i)));
    const { abi, bytecode } = compile();
    const board = await new ContractFactory(abi, bytecode, author).deploy();
    await board.waitForDeployment();
    const invalid = async (action, reason) => {
      await assert.rejects(action, error => String(error.reason || error.message).includes(reason));
    };
    await invalid(() => board.getProposal(0), 'Proposal does not exist');
    await invalid(() => board.createProposal.staticCall('', 'Details'), 'Title must');
    await invalid(() => board.createProposal.staticCall('Title', ''), 'Description must');
    await invalid(() => board.createProposal.staticCall('a'.repeat(121), 'Details'), 'Title must');
    await invalid(() => board.createProposal.staticCall('Title', 'a'.repeat(2001)), 'Description must');
    const created = await (await board.createProposal('Plant trees', 'Add shade in our park')).wait();
    const createdEvent = board.interface.parseLog(created.logs[0]);
    assert.equal(createdEvent.name, 'ProposalCreated');
    assert.equal(createdEvent.args.author, await author.getAddress());
    assert.equal(await board.proposalCount(), 1n);
    await invalid(() => board.endorseProposal.staticCall(0), 'Author cannot');
    const endorsed = await (await board.connect(supporter).endorseProposal(0)).wait();
    assert.equal(board.interface.parseLog(endorsed.logs[0]).name, 'ProposalEndorsed');
    assert.equal(await board.hasEndorsed(0, await supporter.getAddress()), true);
    await invalid(() => board.connect(supporter).endorseProposal.staticCall(0), 'Already endorsed');
    await invalid(() => board.connect(supporter).closeProposal.staticCall(0), 'Only author');
    assert.equal((await board.getProposal(0)).endorsementCount, 1n);
    // A duplicate also reverts as a mined transaction when bypassing gas estimation.
    await assert.rejects(async () => (await board.connect(supporter).endorseProposal(0, { gasLimit: 200000 })).wait());
    const closed = await (await board.closeProposal(0)).wait();
    assert.equal(board.interface.parseLog(closed.logs[0]).name, 'ProposalClosed');
    await invalid(() => board.connect(other).endorseProposal.staticCall(0), 'Proposal is closed');
    await invalid(() => board.closeProposal.staticCall(0), 'Proposal is closed');
    assert.equal((await board.getProposal(0)).closed, true);
    assert.equal((await board.getProposal(0)).endorsementCount, 1n);
    await (await board.connect(other).createProposal('Community library', 'Share books')).wait();
    await (await board.connect(supporter).endorseProposal(1)).wait();
    await (await board.endorseProposal(1)).wait();
    assert.equal((await board.getProposal(1)).endorsementCount, 2n);
    await invalid(() => board.endorseProposal.staticCall(999), 'Proposal does not exist');
    await invalid(() => board.closeProposal.staticCall(999), 'Proposal does not exist');
  } finally { provider.destroy(); await rpc.disconnect(); }
});
