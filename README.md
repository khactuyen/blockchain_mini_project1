# Community Proposal Board

Individual mini project for **DS 441 A — Blockchain: Theory & Practices**.  
Student: **Võ Khắc Tuyên** · Student ID: **30219042961**.

Build a blockchain application that allows community members to propose and endorse local ideas.

## Project rules

- Any wallet address may submit a proposal.
- Each address other than the author may endorse a proposal once.
- Only the author may close their proposal.
- Closed proposals must reject further endorsements.
- Display each proposal and its endorsement count.

## Technical requirements

Write and deploy a Solidity smart contract on a local Ganache blockchain using test accounts and test Ether only. Build a simple HTML/JavaScript Web3 interface using ethers.js or web3.js that displays the connected account, contract data, transaction status, and errors. Enforce all project rules and address-based permissions in the contract, emit events for important state changes, and reflect the resulting state in the interface.

## Demonstration requirements

Demonstrate proposal creation, endorsement, duplicate-endorsement rejection, and closure. Use at least two Ganache accounts and explain at least one successful transaction and one rejected invalid or unauthorized action.

## Assessment

Contract logic and project rules: 35 points. Ganache deployment and Web3 interaction: 25 points. Interface and usability: 15 points. Tests and demonstration: 15 points. README and individual explanation: 10 points.
