import logging
from functools import wraps
from typing import Tuple, List, Callable, Optional

from web3 import Web3, HTTPProvider
from web3.eth import Contract

logger = logging.getLogger(__name__)

def wrap_vm_exception(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(str(e))

    return wrapper


class VotingContract:
    address: str

    def __init__(self, await_transaction: Callable, contract_api: Contract):
        self.__await_transaction = await_transaction
        self._contract_api = contract_api
        self.address = contract_api.address

    def _get_candidate(self, candidate_index: int) -> bytes:
        if not (0 <= candidate_index < self._contract_api.functions.getNumberOfCandidates().call()):
            raise IndexError('invalid candidate_index')
        return self._contract_api.functions.getCandidate(candidate_index).call()

    def _get_candidate_votes(self, candidate_index: int) -> int:
        if not (0 <= candidate_index < self._contract_api.functions.getNumberOfCandidates().call()):
            raise IndexError('invalid candidate_index')
        return self._contract_api.functions.getCandidateVotes(candidate_index).call()

    @wrap_vm_exception
    def get_candidates_and_votes(self) -> Optional[List[Tuple[bytes, int]]]:
        result: List[Tuple[bytes, int]] = []
        for i in range(self._contract_api.functions.getNumberOfCandidates().call()):
            candidate = self._get_candidate(i)
            votes = self._get_candidate_votes(i)
            result.append((candidate, votes))
        return result

    @wrap_vm_exception
    def get_candidates(self) -> Optional[List[bytes]]:
        return [self._get_candidate(i) for i in range(self._contract_api.functions.getNumberOfCandidates().call())]

    def _begin_vote(self, voter_id: int, candidate_index: int) -> bytes:
        if not (0 <= candidate_index < self._contract_api.functions.getNumberOfCandidates().call()):
            raise IndexError('invalid candidate_index')
        return self._contract_api.functions.vote(voter_id, candidate_index).transact()

    def wait_for_transaction(self, transaction_hash: bytes) -> None:
        # TODO: Do we need to do smth with tx_receipt?
        tx_receipt = self.__await_transaction(transaction_hash)

    @wrap_vm_exception
    def has_voted(self, voter_id: int) -> Optional[bool]:
        return self._contract_api.functions.hasVoted(voter_id).call()

    @wrap_vm_exception
    def vote(self, voter_id: int, candidate_index: int) -> Optional[bool]:
        self.wait_for_transaction(self._begin_vote(voter_id, candidate_index))
        return True

    def _begin_kill(self) -> bytes:
        return self._contract_api.functions.kill().transact()

    @wrap_vm_exception
    def kill(self, callie_id: int) -> Optional[bool]:
        # TODO: consider moving this validation into the contract
        if callie_id != self._contract_api.functions.getOwner().call():
            return False
        self.wait_for_transaction(self._begin_kill())
        return True


class VotingContractFactory:
    w3: Web3
    url: str
    address: Tuple[int, int, int, int]
    port: int
    _abi = '[{"constant":true,"inputs":[{"name":"index","type":"uint256"}],"name":"getCandidate","outputs":[{"name":"","type":"bytes"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[],"name":"kill","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"getNumberOfCandidates","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"name":"index","type":"uint256"}],"name":"getCandidateVotes","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"getOwner","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"voterId","type":"uint256"},{"name":"candidateIndex","type":"uint256"}],"name":"vote","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[{"name":"voterId","type":"uint256"}],"name":"hasVoted","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"view","type":"function"},{"inputs":[{"name":"candidates","type":"bytes"},{"name":"ownerId","type":"uint256"}],"payable":false,"stateMutability":"nonpayable","type":"constructor"}]'
    _bytecode = '0x608060405234801561001057600080fd5b50604051610a32380380610a3283398101806040528101908080518201929190602001805190602001909291905050506000336000806101000a81548173ffffffffffffffffffffffffffffffffffffffff021916908373ffffffffffffffffffffffffffffffffffffffff16021790555081600481905550600260006040519080825280601f01601f1916602001820160405280156100bf5781602001602082028038833980820191505090505b5090806001815401808255809150509060018203906000526020600020016000909192909190915090805190602001906100fa92919061036b565b5050600090505b82518110156103635760007f010000000000000000000000000000000000000000000000000000000000000002838281518110151561013c57fe5b9060200101517f010000000000000000000000000000000000000000000000000000000000000090047f0100000000000000000000000000000000000000000000000000000000000000027effffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff1916141561022757600260006040519080825280601f01601f1916602001820160405280156101e55781602001602082028038833980820191505090505b50908060018154018082558091505090600182039060005260206000200160009091929091909150908051906020019061022092919061036b565b5050610356565b600260016002805490500381548110151561023e57fe5b90600052602060002001838281518110151561025657fe5b9060200101517f010000000000000000000000000000000000000000000000000000000000000090047f01000000000000000000000000000000000000000000000000000000000000000290808054603f811680603e81146102d4576002830184556001831615156102c6578192505b6001600284040193506102ee565b83600052602060002060ff19841681556041855560209450505b50505090600182038154600116156103155790600052602060002090602091828204019190065b90919290919091601f036101000a81548160ff021916907f010000000000000000000000000000000000000000000000000000000000000084040217905550505b8080600101915050610101565b505050610410565b828054600181600116156101000203166002900490600052602060002090601f016020900481019282601f106103ac57805160ff19168380011785556103da565b828001600101855582156103da579182015b828111156103d95782518255916020019190600101906103be565b5b5090506103e791906103eb565b5090565b61040d91905b808211156104095760008160009055506001016103f1565b5090565b90565b6106138061041f6000396000f300608060405260043610610083576000357c0100000000000000000000000000000000000000000000000000000000900463ffffffff16806335b8e8201461008857806341c0e1b51461012e5780637a84d13e14610145578063866163c014610170578063893d20e8146101b1578063b384abef146101dc578063ecca031f14610213575b600080fd5b34801561009457600080fd5b506100b360048036038101908080359060200190929190505050610258565b6040518080602001828103825283818151815260200191508051906020019080838360005b838110156100f35780820151818401526020810190506100d8565b50505050905090810190601f1680156101205780820380516001836020036101000a031916815260200191505b509250505060405180910390f35b34801561013a57600080fd5b5061014361036e565b005b34801561015157600080fd5b5061015a610403565b6040518082815260200191505060405180910390f35b34801561017c57600080fd5b5061019b60048036038101908080359060200190929190505050610410565b6040518082815260200191505060405180910390f35b3480156101bd57600080fd5b506101c6610488565b6040518082815260200191505060405180910390f35b3480156101e857600080fd5b506102116004803603810190808035906020019092919080359060200190929190505050610492565b005b34801561021f57600080fd5b5061023e60048036038101908080359060200190929190505050610562565b604051808215151515815260200191505060405180910390f35b60606000809054906101000a900473ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff163373ffffffffffffffffffffffffffffffffffffffff161415156102b557600080fd5b6002828154811015156102c457fe5b906000526020600020018054600181600116156101000203166002900480601f0160208091040260200160405190810160405280929190818152602001828054600181600116156101000203166002900480156103625780601f1061033757610100808354040283529160200191610362565b820191906000526020600020905b81548152906001019060200180831161034557829003601f168201915b50505050509050919050565b6000809054906101000a900473ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff163373ffffffffffffffffffffffffffffffffffffffff161415156103c957600080fd5b6000809054906101000a900473ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff16ff5b6000600280549050905090565b60008060009054906101000a900473ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff163373ffffffffffffffffffffffffffffffffffffffff1614151561046d57600080fd5b60016000838152602001908152602001600020549050919050565b6000600454905090565b6000809054906101000a900473ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff163373ffffffffffffffffffffffffffffffffffffffff161480156104f457506104f282610562565b155b8015610504575060028054905081105b151561050f57600080fd5b60016003600084815260200190815260200160002060006101000a81548160ff02191690831515021790555060016000828152602001908152602001600020600081548092919060010191905055505050565b60008060009054906101000a900473ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff163373ffffffffffffffffffffffffffffffffffffffff161415156105bf57600080fd5b6003600083815260200190815260200160002060009054906101000a900460ff1690509190505600a165627a7a72305820f8fc6dcd2fcf20cf832cb62f3242e11304f91e63804754faa2cce79e213694610029'

    def __init__(self, address: Tuple[int, int, int, int], port: int):
        self.port = port
        self.address = address
        addr = '.'.join((str(x) for x in address))
        self.url = f'http://{addr}:{port}'
        self.w3 = Web3(HTTPProvider(self.url))
        self.w3.eth.defaultAccount = self.w3.eth.accounts[0]

    @wrap_vm_exception
    def create(self, *contract_args, **contract_kwargs) -> Optional[VotingContract]:
        contract = self.w3.eth.contract(abi=VotingContractFactory._abi, bytecode=VotingContractFactory._bytecode)
        tx_hash = contract.constructor(*contract_args, **contract_kwargs).transact()
        tx_receipt = self.w3.eth.waitForTransactionReceipt(tx_hash)
        return self._init_contract(tx_receipt.contractAddress)

    def _init_contract(self, address):
        contract_instance = self.w3.eth.contract(address=address, abi=VotingContractFactory._abi)
        return VotingContract(self.w3.eth.waitForTransactionReceipt, contract_instance)

    @wrap_vm_exception
    def restore_from_address(self, address: str) -> Optional[VotingContract]:
        code = self.w3.eth.getCode(address).hex()
        if len(code) <= 2:
            logger.warning(f'address {address} got {code}')
            return
        return self._init_contract(address)
