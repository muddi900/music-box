import os
import json
from typing import List
from .music_box_reaction import Reaction, Branched, Arrhenius, Tunneling, Troe_Ternary
from .music_box_reactant import Reactant
from .music_box_product import Product

class ReactionList:
    """
    Represents a list of chemical reactions.

    Attributes:
        reactions (List[Reaction]): A list of Reaction instances.
    """

    def __init__(self, name=None, reactions=None):
        """
        Initializes a new instance of the ReactionList class.

        Args:
            reactions (List[Reaction]): A list of Reaction instances. Default is an empty list.
        """

        self.name = name
        self.reactions = reactions if reactions is not None else []

    @classmethod
    def from_UI_JSON(cls, UI_JSON, species_list):
        """
        Create a new instance of the ReactionList class from a JSON object.

        Args:
            UI_JSON (dict): A JSON object representing the reaction list.

        Returns:
            ReactionList: A new instance of the ReactionList class.
        """
        list_name = UI_JSON['mechanism']['reactions']['camp-data'][0]['name']

        reactions = []

        for reaction in UI_JSON['mechanism']['reactions']['camp-data'][0]['reactions']:

            reactions.append(ReactionList.get_reactions_from_JSON(reaction, species_list))

        return cls(list_name, reactions)
    
    @classmethod
    def from_config_JSON(cls, path_to_json, config_JSON, species_list):

        reactions = []
        list_name = None

        #gets config file path
        config_file_path = os.path.dirname(path_to_json) + "/" + config_JSON['model components'][0]['configuration file']

        #opnens config path to read reaction file
        with open(config_file_path, 'r') as json_file:
            config = json.load(json_file)

            #assumes reactions file is second in the list
            if(len(config['camp-files']) > 1):
                reaction_file_path = os.path.dirname(config_file_path) + "/" + config['camp-files'][1]
                with open(reaction_file_path, 'r') as reaction_file:
                    reaction_data = json.load(reaction_file)
                    
                    #assumes there is only one mechanism

                    list_name = reaction_data['camp-data'][0]['name']
                    for reaction in reaction_data['camp-data'][0]['reactions']:
                        reactions.append(ReactionList.get_reactions_from_JSON(reaction, species_list))

       

        return cls(list_name, reactions)

    def add_reaction(self, reaction):
        """
        Add a Reaction instance to the ReactionList.

        Args:
            reaction (Reaction): The Reaction instance to be added.
        """
        self.reactions.append(reaction)

    @classmethod
    def get_reactants_from_JSON(self, reaction, species_list):
        reactants = []

        for reactant, reactant_info in reaction['reactants'].items():
            match = filter(lambda x: x.name == reactant, species_list.species)
            species = next(match, None)
            quantity = reactant_info['qty'] if 'qty' in reactant_info else None

            reactants.append(Reactant(species, quantity))
        return reactants
    
    @classmethod
    def get_products_from_JSON(self, reaction, species_list):
        products = []
        if 'products' in reaction:
                for product, product_info in reaction['products'].items():
                    match = filter(lambda x: x.name == product, species_list.species)
                    species = next(match, None)
                    yield_value = product_info['yield'] if 'yield' in product_info else None

                    products.append(Product(species, yield_value))
        return products
    
    @classmethod
    def get_reactions_from_JSON(self, reaction, species_list):

        name = reaction['MUSICA name'] if 'MUSICA name' in reaction else None
        reaction_type = reaction['type']
    
        reactants = ReactionList.get_reactants_from_JSON(reaction, species_list)
        products = ReactionList.get_products_from_JSON(reaction, species_list)
                
        if reaction_type == 'WENNBERG_NO_RO2':
            alkoxy_products = []

            for alkoxy_product, alkoxy_product_info in reaction.get('alkoxy products', {}).items():
                match = filter(lambda x: x.name == alkoxy_product, species_list.species)
                species = next(match, None)
                yield_value = alkoxy_product_info.get('yield')

                alkoxy_products.append(Product(species, yield_value))

            nitrate_products = []

            for nitrate_product, nitrate_product_info in reaction.get('nitrate products', {}).items():
                match = filter(lambda x: x.name == nitrate_product, species_list.species)
                species = next(match, None)
                yield_value = nitrate_product_info.get('yield')

                nitrate_products.append(Product(species, yield_value))

            X = reaction.get('X')
            Y = reaction.get('Y')
            a0 = reaction.get('a0')
            n = reaction.get('n')
            return Branched(name, reaction_type, reactants, alkoxy_products, nitrate_products, X, Y, a0, n)
        elif reaction_type == 'ARRHENIUS':
            A = reaction.get('A')
            B = reaction.get('B')
            D = reaction.get('D')
            E = reaction.get('E')
            Ea = reaction.get('Ea')
            return Arrhenius(name, reaction_type, reactants, products, A, B, D, E, Ea)
        elif reaction_type == 'WENNBERG_TUNNELING':
            A = reaction.get('A')
            B = reaction.get('B')
            C = reaction.get('C')
            return Tunneling(name, reaction_type, reactants, products, A, B, C)
        elif reaction_type == 'TROE' or reaction_type == 'TERNARY_CHEMICAL_ACTIVATION':
            k0_A = reaction.get('k0_A')
            k0_B = reaction.get('k0_B')
            k0_C = reaction.get('k0_C')
            kinf_A = reaction.get('kinf_A')
            kinf_B = reaction.get('kinf_B')
            kinf_C = reaction.get('kinf_C')
            Fc = reaction.get('Fc')
            N = reaction.get('N')
            return Troe_Ternary(name, reaction_type, reactants, products, k0_A, k0_B, k0_C, kinf_A, kinf_B, kinf_C, Fc, N)
        else:
            return Reaction(name, reaction_type, reactants, products)
