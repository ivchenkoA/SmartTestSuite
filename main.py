from typing import Any, Dict, List
from web3 import Web3, HTTPProvider
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel, Field
from abis import ABI
from addresses import address_wallet,address_contract, private_key_wallet, API_URL
from eth_account import Account
from fastapi.openapi.models import Example, Schema, Response
from typing import List, Mapping, Sequence
from logging import getLogger, basicConfig, INFO, StreamHandler
import json
from eth_interface import EthContract, EthInterface

app = FastAPI()
web3 = Web3(Web3.HTTPProvider(API_URL)) 

contract_address = address_contract
contract_abi = json.loads(ABI)
contract_instance =  web3.eth.contract(address=contract_address, abi=contract_abi)

app = FastAPI()

def create_endpoint(fn_abi: Dict[str, Any]):
    fn_name = fn_abi["name"]
    inputs = fn_abi["inputs"]
    outputs = fn_abi["outputs"]
    stateMutability = fn_abi["stateMutability"]

    if len(inputs) == 0:
        @app.get(f"/{fn_name}")
        def fn_handler():
            args = []
            fn = getattr(contract_instance.functions, fn_name)    
            result = fn(*args).call()
            print(result)
            return {"result": result}

    else:    
        list_params = []
        for i in inputs:
            list_params.append({str(i): ""})

        @app.post(f"/{fn_name}")
        def fn_handler(params: List[Any] = Body(..., example=list_params
    )):
            list_inputs = []
            for p,i in enumerate(params):
                for j in i:
                    list_inputs.append(params[p][j])
            params = list_inputs   
            if len(params) != len(inputs):
                raise HTTPException(status_code=400, detail="Invalid number of parameters")

            for fn_abi in contract_abi:
                if fn_abi["type"] == "function":
                    if fn_abi["name"] == fn_name:
                        state_mutability = fn_abi["stateMutability"]           
            args = []
            for i, input_def in enumerate(inputs):
                arg_value = params[i]
                
                if input_def["type"] == "address":
                    arg_value = web3.to_checksum_address(arg_value)
                elif input_def["type"].startswith("uint"):
                    arg_value = int(arg_value)

                args.append(arg_value)

            if state_mutability == "nonpayable":
                initialized_chain = EthInterface(private_key=private_key_wallet, address=address_wallet)
                contract = EthContract(interface=initialized_chain, address=contract_address,
                                                abi=contract_abi)
                tx = contract.call_function(fn_name, args)
                return {"result": tx.hex()}
            elif state_mutability == "view":
                fn = getattr(contract_instance.functions, fn_name)
                result = fn(*args).call()
                return {"result": result}


for fn_abi in contract_abi:
    if fn_abi["type"] == "function":
        create_endpoint(fn_abi)