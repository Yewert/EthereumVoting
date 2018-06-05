import logging
from typing import Tuple, Optional, List, Callable

from backend.VotingContract import VotingContractFactory, VotingContract

logger = logging.getLogger(__name__)

class Voting:
    _contract: VotingContract

    def __init__(self, contract: VotingContract,
                 finalizer: Callable[[VotingContract, int], Optional[List[Tuple[str, int]]]]):
        self._finalizer = finalizer
        self._contract = contract

    @property
    def address(self) -> str:
        return self._contract.address

    def get_candidates(self) -> Optional[List[str]]:
        res = self._contract.get_candidates()
        if not res:
            return
        return [c.decode() for c in res]

    def has_voted(self, voter_id: int) -> Optional[bool]:
        return self._contract.has_voted(voter_id)

    def vote_and_get_results(self, voter_id: int, candidate_index: int) -> Optional[List[Tuple[str, int]]]:
        if not self._contract.vote(voter_id, candidate_index):
            return
        return self.get_candidates_votes()

    def get_candidates_votes(self) -> Optional[List[Tuple[str, int]]]:
        res = self._contract.get_candidates_and_votes()
        if not res:
            return
        return [(c.decode(), v) for c, v in self._contract.get_candidates_and_votes()]

    def finalize(self, callie_id: int) -> Optional[List[Tuple[str, int]]]:
        return self._finalizer(self._contract, callie_id)

class VotingManager:

    def __init__(self, ip_address: Tuple[int, int, int, int], port: int):
        self._contract_factory = VotingContractFactory(ip_address, port)

    def _try_get_contract_by_address(self, address: str) -> Optional[VotingContract]:
        return self._contract_factory.restore_from_address(address)

    def _create_new_contract(self, candidates: bytes, owner_id: int) -> VotingContract:
        contract = self._contract_factory.create(candidates, owner_id)
        return contract

    def get_voting_from_address(self, address: str) -> Optional[Voting]:
        contract = self._try_get_contract_by_address(address)
        if contract:
            return Voting(contract, self._finalize_voting)

    def create_new_voting(self, candidates: List[str], owner_id) -> Voting:
        candidates_bytes = b'\x00'.join((candidate.encode() for candidate in candidates))
        contract = self._create_new_contract(candidates_bytes, owner_id)
        return Voting(contract, self._finalize_voting)

    def _finalize_voting(self, contract: Optional[VotingContract], callie_id: int) -> Optional[List[Tuple[str, int]]]:
        if contract:
            results: List[Tuple[bytes, int]] = contract.get_candidates_and_votes()
            if not contract.kill(callie_id):
                return
            return [(c.decode(), v) for c, v in results]
