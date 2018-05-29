from VotingContract import VotingContractFactory

factory = VotingContractFactory((127, 0, 0, 1), 7545)
factory.w3.eth.defaultAccount = factory.w3.eth.accounts[0]
con = factory.create(b'0\x001\x002')


def print_results(contract):
    global candidate, votes
    for candidate, votes in contract.get_candidates_and_votes():
        print(f'{candidate.decode()}: {votes}')


for i in range(2):
    print_results(con)
    con.vote(voter_id=0, candidate_index=0)
    print('')
else:
    print_results(con)

con.kill()
