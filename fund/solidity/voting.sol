pragma solidity ^0.8.18;

contract Voting {
    mapping(address => bool) private allowedVoters;
    mapping(address => bool) private hasVoted;

    uint256 private approveCnt;
    uint256 private rejectCnt;
    uint256 private majority;

    bool public finished;
    bool public approved;

    event Finished(bool approved);

    constructor(address[] memory voters) {
        for (uint256 i = 0; i < voters.length; i++) {
            allowedVoters[voters[i]] = true;
        }
        majority = (voters.length / 2) + 1;
    }

    function approve() external {
        require(!finished, "Voting ended.");
        require(allowedVoters[msg.sender], "Invalid address.");
        require(!hasVoted[msg.sender], "Already voted.");

        hasVoted[msg.sender] = true;
        approveCnt++;

        if (approveCnt >= majority) {
            finished = true;
            approved = true;
            emit Finished(true);
        }
    }

    function reject() external {
        require(!finished, "Voting ended.");
        require(allowedVoters[msg.sender], "Invalid address.");
        require(!hasVoted[msg.sender], "Already voted.");

        hasVoted[msg.sender] = true;
        rejectCnt++;

        if (rejectCnt >= majority) {
            finished = true;
            approved = false;
            emit Finished(false);
        }
    }
}