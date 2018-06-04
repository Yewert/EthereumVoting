import logging
from typing import Tuple, Optional, Set, List, Callable

from backend.VotingContract import VotingContractFactory, VotingContract

logger = logging.getLogger(__name__)

class Voting:
    _contract: VotingContract

    def __init__(self, contract: VotingContract, finalizer: Callable[[str, int], Optional[List[Tuple[str, int]]]]):
        self._finalizer = finalizer
        self._contract = contract

    @property
    def address(self) -> str:
        return self._contract.address

    def get_all_candidates(self) -> Optional[List[str]]:
        res = self._contract.get_candidates()
        if not res:
            return None
        return [c.decode() for c in res]

    def vote_and_get_results(self, voter_id: int, candidate_index: int) -> Optional[List[Tuple[str, int]]]:
        if not self._contract.vote(voter_id, candidate_index):
            return None
        return [(c.decode(), v) for c, v in self._contract.get_candidates_and_votes()]

    def finalize(self, callie_id: int) -> Optional[List[Tuple[str, int]]]:
        return self._finalizer(self.address, callie_id)

class VotingManager:
    _existing_contracts: Set[str]

    def __init__(self, ip_address: Tuple[int, int, int, int], port: int):
        self._contract_factory = VotingContractFactory(ip_address, port)
        self._existing_contracts = set()

    def _try_get_contract_by_address(self, address: str) -> Tuple[Optional[VotingContract], bool]:
        try:
            if address not in self._existing_contracts:
                return None, False
            return self._contract_factory.restore_from_address(address), True
        except Exception as e:
            logger.error(str(e))
            return None, False

    def _create_new_contract(self, candidates: bytes, owner_id: int) -> VotingContract:
        contract = self._contract_factory.create(candidates, owner_id)
        self._existing_contracts.add(contract.address)
        return contract

    def create_new_voting(self, candidates: List[str], owner_id) -> Voting:
        candidates_bytes = b'\x00'.join((candidate.encode() for candidate in candidates))
        contract = self._create_new_contract(candidates_bytes, owner_id)
        return Voting(contract, self._finalize_voting)

    def _finalize_voting(self, address: str, callie_id: int) -> Optional[List[Tuple[str, int]]]:
        contract, success = self._try_get_contract_by_address(address)
        if success:
            results: List[Tuple[bytes, int]] = contract.get_candidates_and_votes()
            if not contract.kill(callie_id):
                return
            self._existing_contracts.remove(address)
            return [(c.decode(), v) for c, v in results]
