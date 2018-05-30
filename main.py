from VotingManager import VotingManager

manager = VotingManager((127, 0, 0, 1), 14228)
voting = manager.create_new_voting(['Диджей e-ban', 'ur mom'], 1337)
for can in voting.get_all_candidates():
    print(can)
print('-' * 10)

voting.vote_and_get_results(0, 0)
voting.vote_and_get_results(0, 0)
voting.vote_and_get_results(1, 0)

print('-' * 10)
print(voting.finalize(0))
print('-' * 10)
for can, vot in voting.finalize(1337):
    print(f"{can}: {vot}")
