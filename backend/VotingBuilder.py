from typing import Optional, List

from backend.VotingManager import VotingManager, Voting


# TODO: this class is very raw
class VotingBuilder:
    __candidate_list: List[str]

    def __init__(self, owner: int, manager: VotingManager):
        self.__owner = owner
        self.__manager = manager
        self.__counter = -1
        self.__candidate_list = []

    def add_candidate(self, candidate: str) -> Optional[Voting]:
        self.__counter += 1
        if candidate == '' or self.__counter == 10:
            return self.__manager.create_new_voting(self.__candidate_list, self.__owner)
        self.__candidate_list.append(candidate)
