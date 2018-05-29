from typing import Tuple, List, Callable
from web3 import Web3, HTTPProvider
from web3.eth import Contract


class VotingContract:
    _number_of_candidates: int

    def __init__(self, await_transaction: Callable[bytes], contract_api: Contract, number_of_candidates: int):
        self.__await_transaction = await_transaction
        self.__contract_api = contract_api
        self._number_of_candidates = number_of_candidates

    def get_candidate(self, candidate_index: int) -> bytes:
        if not (0 <= candidate_index < self._number_of_candidates):
            raise IndexError('invalid candidate_index')
        return self.__contract_api.functions.getCandidate(candidate_index).call()

    def get_candidate_votes(self, candidate_index: int) -> int:
        if not (0 <= candidate_index < self._number_of_candidates):
            raise IndexError('invalid candidate_index')
        return self.__contract_api.functions.getCandidateVotes(candidate_index).call()

    def get_candidates_and_votes(self) -> List[Tuple[bytes, int]]:
        result: List[Tuple[bytes, int]] = []
        for i in range(self._number_of_candidates):
            candidate = self.get_candidate(i)
            votes = self.get_candidate_votes(i)
            result.append((candidate, votes))
        return result

    def begin_vote(self, voter_id: int, candidate_index: int) -> bytes:
        if not (0 <= candidate_index < self._number_of_candidates):
            raise IndexError('invalid candidate_index')
        return self.__contract_api.functions.vote(voter_id, candidate_index).transact()

    def wait_vote(self, transaction_hash: bytes) -> None:
        # TODO: Do we need to do smth with tx_receipt?
        tx_receipt = self.__await_transaction(transaction_hash)


class VotingContractFactory:
    w3: Web3
    url: str
    address: Tuple[int]
    port: int
    __abi = '[{"constant":true,"inputs":[{"name":"index","type":"uint256"}],"name":"getCandidate","outputs":[{"name":"","type":"bytes"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"getNumberOfCandidates","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"name":"index","type":"uint256"}],"name":"getCandidateVotes","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"voterId","type":"uint256"},{"name":"candidateIndex","type":"uint256"}],"name":"vote","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"inputs":[{"name":"candidates","type":"bytes"}],"payable":false,"stateMutability":"nonpayable","type":"constructor"}]'
    __bytecode = '608060405234801561001057600080fd5b506040516108d63803806108d6833981018060405281019080805182019291905050506000336000806101000a81548173ffffffffffffffffffffffffffffffffffffffff021916908373ffffffffffffffffffffffffffffffffffffffff160217905550600260006040519080825280601f01601f1916602001820160405280156100ab5781602001602082028038833980820191505090505b5090806001815401808255809150509060018203906000526020600020016000909192909190915090805190602001906100e6929190610356565b5050600090505b815181101561034f5760007f010000000000000000000000000000000000000000000000000000000000000002828281518110151561012857fe5b9060200101517f010000000000000000000000000000000000000000000000000000000000000090047f0100000000000000000000000000000000000000000000000000000000000000027effffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff1916141561021357600260006040519080825280601f01601f1916602001820160405280156101d15781602001602082028038833980820191505090505b50908060018154018082558091505090600182039060005260206000200160009091929091909150908051906020019061020c929190610356565b5050610342565b600260016002805490500381548110151561022a57fe5b90600052602060002001828281518110151561024257fe5b9060200101517f010000000000000000000000000000000000000000000000000000000000000090047f01000000000000000000000000000000000000000000000000000000000000000290808054603f811680603e81146102c0576002830184556001831615156102b2578192505b6001600284040193506102da565b83600052602060002060ff19841681556041855560209450505b50505090600182038154600116156103015790600052602060002090602091828204019190065b90919290919091601f036101000a81548160ff021916907f010000000000000000000000000000000000000000000000000000000000000084040217905550505b80806001019150506100ed565b50506103fb565b828054600181600116156101000203166002900490600052602060002090601f016020900481019282601f1061039757805160ff19168380011785556103c5565b828001600101855582156103c5579182015b828111156103c45782518255916020019190600101906103a9565b5b5090506103d291906103d6565b5090565b6103f891905b808211156103f45760008160009055506001016103dc565b5090565b90565b6104cc8061040a6000396000f300608060405260043610610062576000357c0100000000000000000000000000000000000000000000000000000000900463ffffffff16806335b8e820146100675780637a84d13e1461010d578063866163c014610138578063b384abef14610179575b600080fd5b34801561007357600080fd5b50610092600480360381019080803590602001909291905050506101b0565b6040518080602001828103825283818151815260200191508051906020019080838360005b838110156100d25780820151818401526020810190506100b7565b50505050905090810190601f1680156100ff5780820380516001836020036101000a031916815260200191505b509250505060405180910390f35b34801561011957600080fd5b506101226102c6565b6040518082815260200191505060405180910390f35b34801561014457600080fd5b50610163600480360381019080803590602001909291905050506102d3565b6040518082815260200191505060405180910390f35b34801561018557600080fd5b506101ae600480360381019080803590602001909291908035906020019092919050505061034b565b005b60606000809054906101000a900473ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff163373ffffffffffffffffffffffffffffffffffffffff1614151561020d57600080fd5b60028281548110151561021c57fe5b906000526020600020018054600181600116156101000203166002900480601f0160208091040260200160405190810160405280929190818152602001828054600181600116156101000203166002900480156102ba5780601f1061028f576101008083540402835291602001916102ba565b820191906000526020600020905b81548152906001019060200180831161029d57829003601f168201915b50505050509050919050565b6000600280549050905090565b60008060009054906101000a900473ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff163373ffffffffffffffffffffffffffffffffffffffff1614151561033057600080fd5b60016000838152602001908152602001600020549050919050565b6000809054906101000a900473ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff163373ffffffffffffffffffffffffffffffffffffffff161480156103ad57506103ab8261041b565b155b80156103bd575060028054905081105b15156103c857600080fd5b60016003600084815260200190815260200160002060006101000a81548160ff02191690831515021790555060016000828152602001908152602001600020600081548092919060010191905055505050565b60008060009054906101000a900473ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff163373ffffffffffffffffffffffffffffffffffffffff1614151561047857600080fd5b6003600083815260200190815260200160002060009054906101000a900460ff1690509190505600a165627a7a723058200878afdd5c3262ed0e67121c89c1e8729efb1e23d8602fd0710c36ff15df31030029'

    def __init__(self, address: Tuple[int], port: int):
        self.port = port
        self.address = address
        addr = '.'.join((str(x) for x in address))
        self.url = f'http://{addr}:{port}'
        self.w3 = Web3(HTTPProvider(self.url))
        self.w3.eth.defaultAccount = self.w3.eth.accounts[0]

    def create(self, *contract_args, **contract_kwargs) -> VotingContract:
        contract = self.w3.eth.contract(abi=VotingContractFactory.__abi, bytecode=VotingContractFactory.__bytecode)
        tx_hash = contract.constructor(*contract_args, **contract_kwargs).transact()
        tx_receipt = self.w3.eth.waitForTransactionReceipt(tx_hash)
        contract_instance = self.w3.eth.contract(address=tx_receipt.contractAddress, abi=VotingContractFactory.__abi)
        number_of_candidates = contract_instance.functions.getNumberOfCandidates().call()
        return VotingContract(self.w3.eth.waitForTransactionReceipt, contract_instance, number_of_candidates)
