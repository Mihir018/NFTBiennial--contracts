import smartpy as sp

class Error:
    TOKEN_UNDEFINED = "TOKEN_UNDEFINED"
    INSUFFICIENT_BALANCE = "INSUFFICIENT_BALANCE"
    NOT_OWNER = "NOT_OWNER"
    CANT_MINT_SAME_TOKEN_TWICE = "CANT_MINT_SAME_TOKEN_TWICE"
    CONTRACT_IS_NOT_ACTIVE = "CONTRACT_IS_NOT_ACTIVE"
    

class TokenMetadataValue:
    def get_type:
    return sp.TRecord(
        token_id = sp.TNat,
        name = sp.TString,
        ipfs_link = sp.TString,
        owner = sp.TAddress)



class NFTBIENNIAL(sp.contract)
def __init__(self, admin, metadata):
    self.init(
        administrator = admin,
        metadata = metadata,
        all_tokens = sp.set(t = sp.TNat),
        token_metadata = sp.big_map(tkey = sp.TNat, tvalue = TokenMetadataValue.get_type()),
        active = True,
    )

def is_administrator(self, sender):
    return sender == self.data.administrator

@sp.entry_point
def set_administrator(self, params):
    sp.verify(self.is_active(), message = FKBErrorMessage.CONTRACT_IS_NOT_ACTIVE)
    sp.verify(self.is_administrator(sp.sender), message = FA2ErrorMessage.NOT_OWNER)
    self.data.administrator = params

def is_active:
    return self.data.active

@sp.entry_point
def toggle_active(self):
    sp.verify(self.is_administrator(sp.sender), message = FA2ErrorMessage.NOT_OWNER)
    self.data.active = ~self.data.active

@sp.entry_point
    def mint_token(self, contract, amount, token_id, metadata):
        sp.set_type(contract, sp.TAddress)
        sp.set_type(amount, sp.TNat)
        sp.set_type(token_id, sp.TNat)
        sp.set_type(metadata, sp.TMap(sp.TString, sp.TBytes))
        sp.verify(self.data.contracts[sp.sender].contains(contract), "INVALID_CONTRACT")
        contractParams = sp.contract(sp.TRecord(address = sp.TAddress, amount = sp.TNat, metadata = sp.TMap(sp.TString, sp.TBytes), token_id = sp.TNat), contract, entry_point="mint").open_some()
        dataToBeSent = sp.record(address = sp.sender, amount = amount, metadata = metadata, token_id = token_id)
        sp.transfer(dataToBeSent,sp.mutez(0),contractParams)
        sp.emit(sp.record(event="TOKEN_MINTED",minted_by=sp.sender,amount=amount),tag="TOKEN_MINTED")
