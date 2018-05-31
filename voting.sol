pragma solidity ^0.4.21;

contract Voting{
    address admin;
    mapping (uint256=>uint256) votes;
    bytes[] candidateList;
    mapping (uint256=>bool) votedIds;
    uint256 owner;

    constructor (bytes candidates, uint256 ownerId) public{
        admin = msg.sender;
        owner = ownerId;
        candidateList.push(new bytes(0));
        for (uint256 index = 0; index < candidates.length; index++) {
            if (candidates[index] == 0) {
                candidateList.push(new bytes(0));
            } else {
                candidateList[candidateList.length - 1].push(candidates[index]);   
            }
        }
    }
    
    function getOwner() public view returns (uint256){
        return owner;
    }
    
    function getCandidate(uint256 index) public view returns (bytes){
        require(msg.sender == admin);
        return candidateList[index];
    }
    
    function getNumberOfCandidates() public view returns (uint256){
        return candidateList.length;
    }
    
    function getCandidateVotes(uint256 index) public view returns(uint256){
        require(msg.sender == admin);
        return votes[index];
    }

    function vote(uint256 voterId, uint256 candidateIndex) public {
        require(msg.sender == admin && !hasVoted(voterId) && candidateIndex < candidateList.length);
        votedIds[voterId] = true;
        votes[candidateIndex]++;
    }

    function hasVoted(uint256 voter) private view returns (bool){
        require(msg.sender == admin);
        return votedIds[voter];
    }
    
    function kill() public{
        require(msg.sender == admin);
        selfdestruct(admin);
    }
}