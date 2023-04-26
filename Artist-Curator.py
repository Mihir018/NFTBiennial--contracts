import smartpy as sp
FA2_contract = sp.io.import_stored_contract('FA2.py')
addresses = sp.io.import_stored_contract('addresses.py')


class MainContract(sp.Contract):
    
    def __init__(self,  nft_contract_address=addresses.NFT, mint_index = sp.nat(0)):
        self.init(

            #The admin who will be able to accept the curators
            admin = sp.address("tz1QXAR4RsVTXYU75XBU9ctMYkWYFnZYbgzk"),
            
            pause = sp.bool(False),

            nft_contract_address=nft_contract_address,   
            
            curators=sp.set(t=sp.TAddress),

            #The art ids that can be minted
            minted_art_ids=sp.set(t=sp.TNat),

            mint_index = mint_index,

            # Minimum percentage of votes set by the user
            min_voting_percent = sp.nat(70),

            # It will map the ids of the proposed arts of the artist to their address
            art_proposal_ids = sp.big_map(l ={},tkey = sp.TAddress, tvalue = sp.TSet(t=sp.TNat)),

            art_proposal_details = sp.big_map(l ={},tkey = sp.TNat, tvalue = sp.TRecord(artist = sp.TAddress,art_metadata = sp.TString,price=sp.TNat,time_of_creation=sp.TTimestamp,time_of_expiration=sp.TTimestamp,curators_in_favour=sp.TSet(t=sp.TAddress),curators_in_against=sp.TSet(t=sp.TAddress),is_accepted=sp.TBool,is_minted=sp.TBool)),
            
            art_proposal_counter = sp.nat(0),
            
            #curator proposal mapped to their address
            curator_proposal_details = sp.big_map(l ={},tkey = sp.TAddress, tvalue = sp.TRecord(curator_description_cid = sp.TString,time_of_creation = sp.TTimestamp,is_voted=sp.TBool)),
            
        )


    def check_is_curator(self):
        """Checks that the address that called the entry point is from one of
        the curators.

        """
        sp.verify(self.data.curators.contains(sp.sender) , message="NOT_CURATOR")


    def check_is_admin(self):
        """Checks that the address that called the entry point is from of the admin.

        """
        sp.verify(self.data.admin == sp.sender, message="NOT_ADMIN")

    def check_is_paused(self):
        """Checks that the address that called the entry point is from of the admin.

        """
        sp.verify(self.data.pause == False, message="CONTRACT_PAUSED")


    # Creating art proposal
    @sp.entry_point
    def art_proposal(self,params):
            
        #Checking if the contract is allowed to run by the admin
        self.check_is_paused()

        #Take from params the time of expiration
        sp.set_type(params, sp.TRecord(_art_metadata =sp.TString,_art_price=sp.TNat,_time_of_expiration=sp.TTimestamp))

        self.data.art_proposal_counter+=1
        
        self.data.art_proposal_details[self.data.art_proposal_counter] = sp.record(artist = sp.sender,art_metadata = params._art_metadata, price = params._art_price,time_of_creation = sp.now, time_of_expiration = params._time_of_expiration, curators_in_favour = sp.set(),curators_in_against = sp.set(),is_accepted=False,is_minted=False)

        sp.if ~self.data.art_proposal_ids.contains(sp.sender):
            
            self.data.art_proposal_ids[sp.sender] = sp.set([self.data.art_proposal_counter], t = sp.TNat)
          
        sp.else:

            self.data.art_proposal_ids[sp.sender].add(self.data.art_proposal_counter)

    # Creating curator proposal
    @sp.entry_point
    def curator_proposal(self,_curator_description_cid):

        #Checking if the contract is allowed to run by the admin
        self.check_is_paused()

        sp.verify(~self.data.curators.contains(sp.sender), message="Already a curator")
        
        self.data.curator_proposal_details[sp.sender] = sp.record(curator_description_cid = _curator_description_cid,time_of_creation=sp.now,is_voted=False)


    # Voting in favour of the art by the curator
    @sp.entry_point
    def vote_on_artproposal(self,_art_proposal_id):

        #Checking if the contract is allowed to run by the admin
        self.check_is_paused()

        # Check that one of the curators executed the entry point 
        self.check_is_curator()
        
        #Check if the art proposal id is valid
        sp.verify(_art_proposal_id<=self.data.art_proposal_counter)
        
        #Checking if the time the curator is voting is less than the art_voting_time
        sp.verify(self.data.art_proposal_details[_art_proposal_id].time_of_expiration>sp.now,"Time for voting has expired")

        #Checking if already voted in favour of the art
        sp.verify(~ self.data.art_proposal_details[_art_proposal_id].curators_in_favour.contains(sp.sender),"You have already voted in favour")

        #Adding the curator address in the list of in favour votes
        sp.if sp.len(self.data.art_proposal_details[_art_proposal_id].curators_in_favour) == 0:
            
            self.data.art_proposal_details[_art_proposal_id].curators_in_favour = sp.set([sp.sender], t = sp.TAddress)
            
        sp.else:

            self.data.art_proposal_details[_art_proposal_id].curators_in_favour.add(sp.sender)


    # Voting against the art by the curator
    @sp.entry_point
    def vote_against_artproposal(self,_art_proposal_id):

        #Checking if the contract is allowed to run by the admin
        self.check_is_paused()

        # Check that one of the curators executed the entry point 
        self.check_is_curator()

        #Check if the art proposal id is valid
        sp.verify(_art_proposal_id<=self.data.art_proposal_counter)
        
        #Checking if the time the curator is voting is less than the art_voting_time
        sp.verify(self.data.art_proposal_details[_art_proposal_id].time_of_expiration>sp.now,"Time for voting has expired")

        #Checking if already voted against the art
        sp.verify(~ self.data.art_proposal_details[_art_proposal_id].curators_in_against.contains(sp.sender),"You have already voted against the art proposal")

        #Adding the curator address in the list of against the artwork votes
        sp.if sp.len(self.data.art_proposal_details[_art_proposal_id].curators_in_against) == 0:
            
            self.data.art_proposal_details[_art_proposal_id].curators_in_against = sp.set([sp.sender], t = sp.TAddress)
            
        sp.else:

            self.data.art_proposal_details[_art_proposal_id].curators_in_against.add(sp.sender)


    # Accepting the curator( by the admin )
    @sp.entry_point
    def accept_curator(self,_curator_address):

        #Checking if the contract is allowed to run by the admin
        self.check_is_paused()

        # Check if the admin executed the entry point 
        self.check_is_admin()

        #Checking if already voted by the admin
        sp.verify(self.data.curator_proposal_details[_curator_address].is_voted == False,"Already voted by the admin")

        #Adding the curator to the list of the curators
        sp.if sp.len(self.data.curators) == 0:
            
            self.data.curators = sp.set([_curator_address], t = sp.TAddress)
            
        sp.else:

            self.data.curators.add(_curator_address)

        
        #Changing the value of is_voted to note the voting done by the admin
        self.data.curator_proposal_details[_curator_address].is_voted = True

    # Rejecting the curator( by the admin )
    @sp.entry_point
    def reject_curator(self,_curator_address):

        #Checking if the contract is allowed to run by the admin
        self.check_is_paused()

        # Check if the admin executed the entry point 
        self.check_is_admin()

        #Checking if already voted by the admin
        sp.verify(self.data.curator_proposal_details[_curator_address].is_voted == False,"Already voted by the admin")

        #Changing the value of is_voted to note the voting done by the admin
        self.data.curator_proposal_details[_curator_address].is_voted = True

    # Removing the curator from the current list of curators( by the admin )
    @sp.entry_point
    def revoke_curator(self,_curator_address):

        #Checking if the contract is allowed to run by the admin
        self.check_is_paused()

        # Check if the admin executed the entry point 
        self.check_is_admin()

        #Removing the curator from the curator list
        self.data.curators.remove(_curator_address)   

    #Minting the art if the artwork has passed the minimum percentage of votes
    @sp.entry_point
    def art_mint(self,_art_proposal_id):
        
        #Checking if the contract is allowed to run by the admin
        self.check_is_paused()
        
        
        #Checking if the time the curator is voting is less than the art_voting_time
        sp.verify(self.data.art_proposal_details[_art_proposal_id].time_of_expiration<sp.now,"Minting is only possible once the expiration time has crossed")

        #Check if the artist is calling
        sp.verify(self.data.art_proposal_ids[sp.sender].contains(_art_proposal_id))

        sp.verify(sp.len(self.data.art_proposal_details[_art_proposal_id].curators_in_favour)/sp.len(self.data.curators)*100>=self.data.min_voting_percent)

        #Check if already minted
        sp.verify(self.data.art_proposal_details[_art_proposal_id].is_minted == False,"Already minted")

        ##Changing the value of is_minted to note the minting done by the artist
        self.data.art_proposal_details[_art_proposal_id].is_minted = True

        #Noting the minted art ids
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
                        token_id=self.data.mint_index,
                        amount=self.data.art_proposal_details[_art_proposal_id].price,
                        address=sp.sender,
                        metadata={"": sp.utils.bytes_of_string('self.data.art_proposal_details[_art_proposal_id].art_metadata')},
                    ),
                    sp.tez(0),
                    c,
                )
        self.data.mint_index += 1

        
    #To toggle the current status of the contract so that it can be stopped or resumed
    @sp.entry_point
    def toggle_pause(self):

        # Check if the admin executed the entry point 
        self.check_is_admin()

        # Toggling the value of the pause variable
        self.data.pause = ~self.data.pause
        


@sp.add_test(name="main")
def test():
    scenario = sp.test_scenario()

    # Test address
    admin = sp.address("tz1QXAR4RsVTXYU75XBU9ctMYkWYFnZYbgzk")
    alice = sp.test_account("alice")
    bob = sp.test_account("bob")
    charles = sp.test_account("charles")


    # Create contract
    dao = MainContract() 
    scenario += dao

    # change_num_values
    scenario.h2("dao Test 1")

    scenario += dao.toggle_pause().run(sender=admin)
    scenario += dao.toggle_pause().run(sender=admin)
    
    scenario += dao.art_proposal(_art_metadata = "ipfs://bafkreibionfgfh3rswqgrkpzqh5c7ztrlla2nkjwtbk37m6vmngljdtpw4",_art_price=5,_time_of_expiration = sp.timestamp(28)).run(sender = alice)
    scenario += dao.art_proposal(_art_metadata = "abncjdklfjs",_art_price=5,_time_of_expiration = sp.timestamp(28)).run(sender = charles)
    scenario += dao.curator_proposal("xyzjloiufd").run(sender = bob)
    scenario += dao.accept_curator(sp.address("tz1hJgZdhnRGvg5XD6pYxRCsbWh4jg5HQ476")).run(sender = admin)
    scenario += dao.reject_curator(sp.address("tz1hJgZdhnRGvg5XD6pYxRCsbWh4jg5HQ476")).run(sender = admin,valid=False)
    scenario += dao.vote_on_artproposal(1).run(sender = bob,now= sp.timestamp(20))
    scenario += dao.vote_on_artproposal(2).run(sender = bob, now = sp.timestamp(20))
    scenario += dao.art_mint(1).run(sender = alice,now = sp.timestamp(32))
    scenario += dao.art_mint(2).run(sender = charles, now = sp.timestamp(32))
    scenario += dao.revoke_curator(sp.address("tz1hJgZdhnRGvg5XD6pYxRCsbWh4jg5HQ476")).run(sender = admin)
    