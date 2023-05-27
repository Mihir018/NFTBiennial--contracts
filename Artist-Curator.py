import smartpy as sp
FA2_contract = sp.io.import_stored_contract('FA2.py')
addresses = sp.io.import_stored_contract('addresses.py')


class MainContract(sp.Contract):
    
    def __init__(self,  nft_contract_address=addresses.NFT):
    # def __init__(self):
        self.init(

            #The admin who will be able to accept the curators
            admin = sp.address("tz1QXAR4RsVTXYU75XBU9ctMYkWYFnZYbgzk"),

            #Contract is paused or not
            pause = sp.bool(False),

            # It contains the contract address of the NFT contract
            nft_contract_address=nft_contract_address,   

            # For storing curator addresses
            curators=sp.set(t=sp.TAddress),

            #Unique id of each minted NFT
            mint_index = sp.nat(0),

            # Minimum percentage of votes set by the user
            min_voting_percent = sp.nat(40),
            
            # For storing profile details
            profile = sp.map(l ={},tkey = sp.TAddress, tvalue = sp.TBytes),

            # It will map the ids of the proposed arts of the artist to their address
            art_proposal_ids = sp.map(l ={},tkey = sp.TAddress, tvalue = sp.TSet(t=sp.TNat)),

            # For storing art proposal details
            art_proposal_details = sp.map(l ={},tkey = sp.TNat, tvalue = sp.TRecord(artist = sp.TAddress,art_metadata = sp.TBytes,price=sp.TNat, mint_index = sp.TNat, time_of_creation=sp.TTimestamp,time_of_expiration=sp.TTimestamp,curators_in_favour=sp.TSet(t=sp.TAddress),curators_in_against=sp.TSet(t=sp.TAddress),is_minted=sp.TBool)),

            # For storing the number of art proposals
            art_proposal_counter = sp.nat(0),
            
            #curator proposal mapped to their address
            # curator_proposal_details = sp.map(l ={},tkey = sp.TAddress, tvalue = sp.TRecord(curator_description_cid = sp.TString,time_of_creation = sp.TTimestamp,is_voted=sp.TBool)),
            
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

    @sp.onchain_view()
    def getCuratorDetails(self):
        return sp.result(self.data.curators)
        # sp.result(sp.len(self.data.curators))

    # For creating profile of artist, curators and collectors
    @sp.entry_point
    def create_profile(self,_profile_metadata):
        
        #Checking if the contract is allowed to run by the admin
        self.check_is_paused()

        self.data.profile[sp.sender] = _profile_metadata
        

    # Creating art proposal
    @sp.entry_point
    def art_proposal(self,params):
            
        #Checking if the contract is allowed to run by the admin
        self.check_is_paused()

        #Take from params the time of expiration
        sp.set_type(params, sp.TRecord(_art_metadata =sp.TBytes,_art_price=sp.TNat,_time_of_expiration=sp.TTimestamp))

        self.data.art_proposal_counter+=1
        
        self.data.art_proposal_details[self.data.art_proposal_counter] = sp.record(artist = sp.sender,art_metadata = params._art_metadata, price = params._art_price, mint_index = sp.nat(0), time_of_creation = sp.now, time_of_expiration = params._time_of_expiration, curators_in_favour = sp.set(),curators_in_against = sp.set(),is_minted=False)

        sp.if ~self.data.art_proposal_ids.contains(sp.sender):
            
            self.data.art_proposal_ids[sp.sender] = sp.set([self.data.art_proposal_counter], t = sp.TNat)
          
        sp.else:

            self.data.art_proposal_ids[sp.sender].add(self.data.art_proposal_counter)

    # Creating curator proposal
    # @sp.entry_point
    # def curator_proposal(self,_curator_description_cid):

    #     #Checking if the contract is allowed to run by the admin
    #     self.check_is_paused()

    #     sp.verify(~self.data.curators.contains(sp.sender), message="Already a curator")
        
    #     self.data.curator_proposal_details[sp.sender] = sp.record(curator_description_cid = _curator_description_cid,time_of_creation=sp.now,is_voted=False)


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

        # Check if already a curator
        sp.verify(~self.data.curators.contains(_curator_address))

        #Checking if already voted by the admin
        # sp.verify(self.data.curator_proposal_details[_curator_address].is_voted == False,"Already voted by the admin")

        #Adding the curator to the list of the curators
        sp.if sp.len(self.data.curators) == 0:
            
            self.data.curators = sp.set([_curator_address], t = sp.TAddress)
            
        sp.else:

            self.data.curators.add(_curator_address)

        
        #Changing the value of is_voted to note the voting done by the admin
        # self.data.curator_proposal_details[_curator_address].is_voted = True

    # Rejecting the curator( by the admin )
    # @sp.entry_point
    # def reject_curator(self,_curator_address):

    #     #Checking if the contract is allowed to run by the admin
    #     self.check_is_paused()

    #     # Check if the admin executed the entry point 
    #     self.check_is_admin()

    #     #Checking if already voted by the admin
    #     sp.verify(self.data.curator_proposal_details[_curator_address].is_voted == False,"Already voted by the admin")

    #     #Changing the value of is_voted to note the voting done by the admin
    #     self.data.curator_proposal_details[_curator_address].is_voted = True

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

        sp.verify((sp.len(self.data.art_proposal_details[_art_proposal_id].curators_in_favour)*100)/(sp.len(self.data.art_proposal_details[_art_proposal_id].curators_in_favour)+sp.len(self.data.art_proposal_details[_art_proposal_id].curators_in_against))>=self.data.min_voting_percent)

        #Check if already minted
        sp.verify(self.data.art_proposal_details[_art_proposal_id].is_minted == False,"Already minted")

        ##Changing the value of is_minted to note the minting done by the artist
        self.data.art_proposal_details[_art_proposal_id].is_minted = True
        self.data.art_proposal_details[_art_proposal_id].mint_index = self.data.mint_index
        

        # Inter-contract call take place here to mint the artwork
        
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
                        metadata={"": self.data.art_proposal_details[_art_proposal_id].art_metadata},
                    ),
                    sp.tez(0),
                    c,
                )
        
        self.data.mint_index += 1


    #To change the minimum voting percent
    @sp.entry_point
    def change_min_voting(self,_min_voting_percent):

        # Check if the admin executed the entry point 
        self.check_is_admin()

        # Changing minimum voting percentage
        self.data.min_voting_percent = _min_voting_percent;

    #To change the admin
    @sp.entry_point
    def change_admin(self,_admin):

        # Check if the admin executed the entry point 
        self.check_is_admin()

        # Changing admin address
        self.data.admin = _admin

        
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
    david = sp.test_account("david")


    # Create contract
    dao = MainContract() 
    scenario += dao

    # change_num_values
    scenario.h2("dao Test 1")

    scenario += dao.toggle_pause().run(sender=admin)
    scenario += dao.toggle_pause().run(sender=admin)
    
    scenario += dao.art_proposal(_art_metadata = sp.bytes("0xdaad"),_art_price=5,_time_of_expiration = sp.timestamp(28)).run(sender = alice)
    scenario += dao.art_proposal(_art_metadata = sp.bytes('0x30'),_art_price=5,_time_of_expiration = sp.timestamp(28)).run(sender = charles)
    # scenario += dao.curator_proposal("xyzjloiufd").run(sender = bob)
    # scenario += dao.curator_proposal("xyzjloiufd").run(sender = charles)
    scenario += dao.accept_curator(sp.address("tz1hJgZdhnRGvg5XD6pYxRCsbWh4jg5HQ476")).run(sender = admin)
    scenario += dao.accept_curator(sp.address("tz1Yo685WVc1KNP4NXQ7JR9sxLxxBhn3LBVA")).run(sender = admin)
    scenario += dao.accept_curator(sp.address("tz1SRacrDH9VUbaqWSL68TYNiC6UMHZS7KHB")).run(sender = admin)
    # curator_details = dao.getCuratorDetails().open_some().item
    # curator_set = sp.set()  # Initialize an empty set
    # curator_set = sp.set(curator_details.value)  # Convert to set if some value exists
    # scenario.verify(curator_set == set(dao.storage.curators))

    
    # scenario += dao.reject_curator(sp.address("tz1hJgZdhnRGvg5XD6pYxRCsbWh4jg5HQ476")).run(sender = admin,valid=False)
    scenario += dao.vote_on_artproposal(1).run(sender = bob,now= sp.timestamp(20))
    scenario += dao.vote_against_artproposal(1).run(sender = charles,now= sp.timestamp(20))
    scenario += dao.vote_against_artproposal(1).run(sender = david,now= sp.timestamp(20))
    scenario += dao.vote_on_artproposal(2).run(sender = bob, now = sp.timestamp(20))
    scenario += dao.art_mint(1).run(sender = alice,now = sp.timestamp(32),valid=False)
    scenario += dao.art_mint(2).run(sender = charles, now = sp.timestamp(32))
    scenario += dao.revoke_curator(sp.address("tz1hJgZdhnRGvg5XD6pYxRCsbWh4jg5HQ476")).run(sender = admin)
    scenario += dao.change_min_voting(30).run(sender = admin)
    scenario += dao.change_admin(sp.address("tz1hJgZdhnRGvg5XD6pYxRCsbWh4jg5HQ476")).run(sender = admin)

    scenario += dao.create_profile(sp.bytes('0x30')).run(sender = charles)
    scenario += dao.create_profile(sp.bytes('0x31')).run(sender = charles)
    scenario += dao.create_profile(sp.bytes('0x32')).run(sender = bob)
