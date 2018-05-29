from typing import Tuple, Optional, Set, List

from VotingContract import VotingContractFactory, VotingContract


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
            # TODO: logging?
            print(str(e))
            return None, False

    def _create_new_contract(self, candidates: bytes, owner_id: int):
        contract = self._contract_factory.create(candidates, owner_id)
        self._existing_contracts.add(contract.address)

    def create_new_voting(self, candidates: List[str], owner_id):
        candidates_bytes = b'\x00'.join((candidate.encode() for candidate in candidates))
        self._create_new_contract(candidates_bytes, owner_id)

    def _finalize_voting(self, address: str, callie_id: int) -> Optional[List[Tuple[str, int]]]:
        contract, success = self._try_get_contract_by_address(address)
        if success:
            results: List[Tuple[bytes, int]] = contract.get_candidates_and_votes()
            contract.kill(callie_id)
            self._existing_contracts.remove(address)
            return [(c.decode(), v) for c, v in results]
