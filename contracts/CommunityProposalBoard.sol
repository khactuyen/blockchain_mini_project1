// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/// @title Community Proposal Board - DS 441 A individual mini project
/// @notice Permissions are per wallet address, not per real-world person.
contract CommunityProposalBoard {
    struct Proposal {
        uint256 id;
        address author;
        string title;
        string description;
        uint256 endorsementCount;
        bool closed;
    }

    uint256 public proposalCount;
    mapping(uint256 => Proposal) private proposals;
    mapping(uint256 => mapping(address => bool)) public hasEndorsed;

    event ProposalCreated(uint256 indexed proposalId, address indexed author, string title);
    event ProposalEndorsed(uint256 indexed proposalId, address indexed supporter, uint256 endorsementCount);
    event ProposalClosed(uint256 indexed proposalId, address indexed author);

    modifier exists(uint256 proposalId) {
        require(proposalId < proposalCount, "Proposal does not exist");
        _;
    }

    function createProposal(string calldata title, string calldata description) external returns (uint256 id) {
        require(bytes(title).length > 0 && bytes(title).length <= 120, "Title must be 1-120 bytes");
        require(bytes(description).length > 0 && bytes(description).length <= 2000, "Description must be 1-2000 bytes");
        id = proposalCount++;
        proposals[id] = Proposal(id, msg.sender, title, description, 0, false);
        emit ProposalCreated(id, msg.sender, title);
    }

    function endorseProposal(uint256 proposalId) external exists(proposalId) {
        Proposal storage proposal = proposals[proposalId];
        require(!proposal.closed, "Proposal is closed");
        require(msg.sender != proposal.author, "Author cannot endorse own proposal");
        require(!hasEndorsed[proposalId][msg.sender], "Already endorsed");
        hasEndorsed[proposalId][msg.sender] = true;
        proposal.endorsementCount++;
        emit ProposalEndorsed(proposalId, msg.sender, proposal.endorsementCount);
    }

    function closeProposal(uint256 proposalId) external exists(proposalId) {
        Proposal storage proposal = proposals[proposalId];
        require(msg.sender == proposal.author, "Only author can close proposal");
        require(!proposal.closed, "Proposal is closed");
        proposal.closed = true;
        emit ProposalClosed(proposalId, msg.sender);
    }

    function getProposal(uint256 proposalId) external view exists(proposalId) returns (Proposal memory) {
        return proposals[proposalId];
    }
}
