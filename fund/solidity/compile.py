import json
import solcx

solcx.install_solc("0.8.18")

with open("voting.sol", "r") as file:
    source = file.read()

compiled = solcx.compile_source(
    source,
    output_values=["abi", "bin"],
    solc_version="0.8.18",
)

contract_interface = compiled["<stdin>:Voting"]

with open("output/Voting.abi", "w") as file:
    file.write(json.dumps(contract_interface["abi"]))

with open("output/Voting.bin", "w") as file:
    file.write(contract_interface["bin"])