import json

raw_interface = '{"version":"0.1.0","name":"VotingProgram","instructions":[{"name":"initialize","accounts":[{"name":"voteAccount","isMut":true,"isSigner":false},{"name":"user","isMut":true,"isSigner":true},{"name":"systemProgram","isMut":false,"isSigner":false}],"args":[{"name":"owner","type":"publicKey"},{"name":"bump","type":"u8"}]},{"name":"castVote","accounts":[{"name":"voteAccount","isMut":true,"isSigner":false}],"args":[{"name":"partyname","type":"string"}]},{"name":"calculateWinner","accounts":[{"name":"voteAccount","isMut":false,"isSigner":false}],"args":[]}],"accounts":[{"name":"VoteAccount","type":{"kind":"struct","fields":[{"name":"owner","type":"publicKey"},{"name":"bump","type":"u8"},{"name":"parties","type":{"vec":{"defined":"Party"}}}]}},{"name":"Winner","type":{"kind":"struct","fields":[{"name":"winner","type":"string"},{"name":"votes","type":"u64"},{"name":"isWinner","type":"bool"}]}}],"types":[{"name":"Party","type":{"kind":"struct","fields":[{"name":"name","type":"string"},{"name":"votes","type":"u64"}]}}],"errors":[{"code":6000,"name":"InvalidParty","msg":"Invalid party name provided"},{"code":6001,"name":"NoParties","msg":"No parties initialized"}]}'

# try:
#     # with open("voting_program.json", "r") as f:
#     #     raw_idl = json.loads(str(f))
    
#     raw_idl = json.loads(raw_interface)

# except Exception as error:
#     print("Error::", error)