import smartpy as sp
FA2_contract = sp.io.import_stored_contract('FA2.py')
addresses = sp.io.import_stored_contract('addresses.py')


class MainContract(sp.Contract):
    
    def __init__(self,  nft_contract_address=addresses.NFT):
        self.init(

            #The admin who will be able to accept the curators
            admin = sp.address("tz1UyQDepgtUBnWjyzzonqeDwaiWoQzRKSP5"),

            nft_contract_address=nft_contract_address,   
            
            curators=sp.set(t=sp.TAddress),

            #The art ids that can be minted
            minted_art_ids=sp.set(t=sp.TNat),

            # Minimum percentage of votes set by the user
            min_voting_percent = sp.nat(10),

            #The time in which the curator can vote. It has to be ensured from frontend that the time hasn't expired
            art_voting_time = sp.timestamp(10),

            # It will map the ids of the proposed arts of the artist to their address
            art_proposal_ids = sp.big_map(l ={},tkey = sp.TAddress, tvalue = sp.TSet(t=sp.TNat)),

            art_proposal_details = sp.big_map(l ={},tkey = sp.TNat, tvalue = sp.TRecord(artist = sp.TAddress,art_description_cid = sp.TString,time_of_creation=sp.TTimestamp,time_of_expiration=sp.TTimestamp,curators_in_favour=sp.TSet(t=sp.TAddress),curators_in_against=sp.TSet(t=sp.TAddress),is_accepted=sp.TBool,is_minted=sp.TBool)),
            
            art_proposal_counter = sp.nat(0),
            
            #curator proposal mapped to their address
            curator_proposal_details = sp.big_map(l ={},tkey = sp.TAddress, tvalue = sp.TRecord(curator_description_cid = sp.TString,time_of_creation = sp.TTimestamp,is_voted=sp.TBool)),
            
        )


    def check_is_curator(self):
        """Checks that the address that called the entry point is from one of
        the curators.

        """
        sp.verify(self.data.curators.contains(sp.sender), message="MS_NOT_USER")


    def check_is_admin(self):
        """Checks that the address that called the entry point is from of the admin.

        """
        sp.verify(self.data.admin == sp.sender, message="MS_NOT_ADMIN")


    @sp.entry_point
    def art_proposal(self,params):

        #Take from params the time of expiration
        sp.set_type(params, sp.TRecord(_art_description_cid =sp.TString,_time_of_expiration=sp.TTimestamp))

        self.data.art_proposal_counter+=1
        
        self.data.art_proposal_details[self.data.art_proposal_counter] = sp.record(artist = sp.sender,art_description_cid = params._art_description_cid, time_of_creation = sp.now, time_of_expiration = params._time_of_expiration, curators_in_favour = sp.set(),curators_in_against = sp.set(),is_accepted=False,is_minted=False)

        sp.if ~self.data.art_proposal_ids.contains(sp.sender):
            
            self.data.art_proposal_ids[sp.sender] = sp.set([self.data.art_proposal_counter], t = sp.TNat)
          
        sp.else:

            self.data.art_proposal_ids[sp.sender].add(self.data.art_proposal_counter)

    @sp.entry_point
    def curator_proposal(self,_curator_description_cid):

        sp.verify(~self.data.curators.contains(sp.sender), message="Already a curator")
        
        self.data.curator_proposal_details[sp.sender] = sp.record(curator_description_cid = _curator_description_cid,time_of_creation=sp.now,is_voted=False)


    @sp.entry_point
    def vote_on_artproposal(self,_art_proposal_id):

        # Check that one of the curators executed the entry point 
        self.check_is_curator()

        sp.verify(_art_proposal_id<=self.data.art_proposal_counter)

        sp.verify(self.data.art_proposal_details[_art_proposal_id].time_of_expiration>sp.now,"Time for voting has expired")

        #Checking if the time the curator is voting is less than the art_voting_time
        
        sp.verify(~ self.data.art_proposal_details[_art_proposal_id].curators_in_favour.contains(sp.sender),"You have already voted in favour")

        sp.if sp.len(self.data.art_proposal_details[_art_proposal_id].curators_in_favour) == 0:
            
            self.data.art_proposal_details[_art_proposal_id].curators_in_favour = sp.set([sp.sender], t = sp.TAddress)
            
        sp.else:

            self.data.art_proposal_details[_art_proposal_id].curators_in_favour.add(sp.sender)

    @sp.entry_point
    def vote_against_artproposal(self,_art_proposal_id):

        # Check that one of the curators executed the entry point 
        self.check_is_curator()

        sp.verify(_art_proposal_id<=self.data.art_proposal_counter)

        sp.verify(self.data.art_proposal_details[_art_proposal_id].time_of_expiration>sp.now,"Time for voting has expired")

        #Checking if the time the curator is voting is less than the art_voting_time
        
        sp.verify(~ self.data.art_proposal_details[_art_proposal_id].curators_in_against.contains(sp.sender),"You have already voted against the art proposal")

        sp.if sp.len(self.data.art_proposal_details[_art_proposal_id].curators_in_against) == 0:
            
            self.data.art_proposal_details[_art_proposal_id].curators_in_against = sp.set([sp.sender], t = sp.TAddress)
            
        sp.else:

            self.data.art_proposal_details[_art_proposal_id].curators_in_against.add(sp.sender)
        
    @sp.entry_point
    def accept_curator(self,_curator_address):
        self.check_is_admin()

        sp.verify(self.data.curator_proposal_details[_curator_address].is_voted == False,"Already voted by the admin")

        sp.if sp.len(self.data.curators) == 0:
            
            self.data.curators = sp.set([_curator_address], t = sp.TAddress)
            
        sp.else:

            self.data.curators.add(_curator_address)

        self.data.curator_proposal_details[_curator_address].is_voted = True

    @sp.entry_point
    def reject_curator(self,_curator_address):
        self.check_is_admin()

        sp.verify(self.data.curator_proposal_details[_curator_address].is_voted == False,"Already voted by the admin")

        self.data.curator_proposal_details[_curator_address].is_voted = True

    @sp.entry_point
    def revoke_curator(self,_curator_address):

        self.check_is_admin()

        self.data.curators.remove(_curator_address)   

    @sp.entry_point
    def art_mint(self,_art_proposal_id):
        
        
        #Checking if the time the curator is voting is less than the art_voting_time
        sp.verify(self.data.art_proposal_details[_art_proposal_id].time_of_expiration<sp.now,"Minting is only possible once the expiration time has crossed")

        #Check if the artist is calling
        sp.verify(self.data.art_proposal_ids[sp.sender].contains(_art_proposal_id))

        sp.verify(sp.len(self.data.art_proposal_details[_art_proposal_id].curators_in_favour)/sp.len(self.data.curators)*100>=self.data.min_voting_percent)

        #Check if already minted
        sp.verify(self.data.art_proposal_details[_art_proposal_id].is_minted == False,"Already minted")

        self.data.art_proposal_details[_art_proposal_id].is_minted = True
        
        sp.if sp.len(self.data.minted_art_ids) == 0:
            
            self.data.minted_art_ids = sp.set([_art_proposal_id], t = sp.TNat)
            
        sp.else:

            self.data.minted_art_ids.add(_art_proposal_id)

        #Inter-contract call take place here to mint the artwork
        c = sp.contract(
            sp.TRecord(
                token_id=sp.TNat,
                amount=sp.TNat,
                address=sp.TAddress,
                metadata=sp.TMap(sp.TString, sp.TBytes),
            ),
            self.data.nft_contract_address,
            "mint",
        ).open_some()

        sp.transfer(
                    sp.record(
                        token_id=_art_proposal_id,
                        amount=sp.nat(3),
                        address=sp.sender,
                        metadata={"": sp.utils.bytes_of_string("https://example.com")},
                    ),
                    sp.tez(0),
                    c,
                )
        


@sp.add_test(name="main")
def test():
    scenario = sp.test_scenario()

    # Test address
    admin = sp.test_account("admin")
    alice = sp.test_account("alice")
    bob = sp.test_account("bob")
    charles = sp.test_account("charles")


    # Create contract
    dao = MainContract() 
    scenario += dao

    # change_num_values
    scenario.h2("dao Test 1")
    
    scenario += dao.art_proposal(_art_description_cid = "lkdsfjdklsdjfkl",_time_of_expiration = sp.timestamp(28)).run(sender = alice)
    scenario += dao.art_proposal(_art_description_cid = "abncjdklfjs",_time_of_expiration = sp.timestamp(28)).run(sender = charles)
    scenario += dao.curator_proposal("xyzjloiufd").run(sender = bob)
    scenario += dao.accept_curator(sp.address("tz1hJgZdhnRGvg5XD6pYxRCsbWh4jg5HQ476")).run(sender = admin)
    scenario += dao.reject_curator(sp.address("tz1hJgZdhnRGvg5XD6pYxRCsbWh4jg5HQ476")).run(sender = admin,valid=False)
    scenario += dao.vote_on_artproposal(1).run(sender = bob,now= sp.timestamp(20))
    scenario += dao.art_mint(1).run(sender = alice,now = sp.timestamp(32))
    scenario += dao.revoke_curator(sp.address("tz1hJgZdhnRGvg5XD6pYxRCsbWh4jg5HQ476")).run(sender = admin)
 
