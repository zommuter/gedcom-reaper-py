#!/usr/bin/env python
# coding: utf-8

import sys
import gedcom.parser
from gedcom.element.individual import IndividualElement



gedcom_parser = gedcom.parser.Parser()
gedcom_parser.parse_file(sys.argv[1])
root_elements = gedcom_parser.get_root_child_elements()

dct = gedcom_parser.get_element_dictionary()

def get_kids(individual):
    kids = []
    for child in individual.get_child_elements():
        if child.get_tag() == gedcom.tags.GEDCOM_TAG_FAMILY_SPOUSE:
            family_id = child.get_value()
            family = dct[family_id]
            #print(family.to_gedcom_string(recursive=True))
            for children in family.get_child_elements():
                #print(children.get_tag())
                if children.get_tag() == gedcom.tags.GEDCOM_TAG_CHILD:
                    kids.append(dct[children.get_value()])
    
    return kids

def get_parents(individual):
    parents = []
    for child in individual.get_child_elements():
        if child.get_tag() == gedcom.tags.GEDCOM_TAG_FAMILY_CHILD:
            family_id = child.get_value()
            family = dct[family_id]
            #print(family.to_gedcom_string(recursive=True))
            for element in family.get_child_elements():
                if element.get_tag() in (gedcom.tags.GEDCOM_TAG_HUSBAND, gedcom.tags.GEDCOM_TAG_WIFE):
                    parents.append(dct[element.get_value()])
                    
    return parents
            
def get_latest_possible_birth_year(individual, add_per_generation=10, max_per_generation=50, checked=None):
    checked = [] if checked is None else checked
    #year = -1  # Rather bad idea assumung one day genealogy might reach back to 1 BC
    #print(individual.get_name(), individual.get_birth_year())
    year = individual.get_birth_year()
    checked.append(individual)
    if year == -1:  # i.e. none, that's not a good feature of python-gedcom
        kids = get_kids(individual)
        #print(kids)
        year = 9999  # that's just as bad...
        for kid in kids:
            if kid in checked:  # prevent infinite recursion
                continue
            kid_year = get_latest_possible_birth_year(
                           kid,
                           add_per_generation=add_per_generation,
                           max_per_generation=max_per_generation,
                           checked=checked
                           )
            if -1 < kid_year < 9000:
                year = min(year, kid_year - add_per_generation)
    # not enough information about kids? check their parents then and assume no more than max_per_generation years difference
    if year > 9000:  # still too magical...
        year = -9999  # magic numbers all around...
        parents = get_parents(individual)
        for parent in parents:
            if parent in checked:  # prevent infinite recursion
                continue
            parent_year = get_latest_possible_birth_year(
                           parent,
                           add_per_generation=add_per_generation,
                           max_per_generation=max_per_generation,
                           checked=checked
                           )
            if -1 < parent_year < 9000:
                year = max(year, parent_year + max_per_generation)
        if year >= 9000 or year <= -1:
            year = -1  # still no luck then...
        
    return year

# now the magic...
print("The following entries will be updated to dead based on their estimated death date")
for index, element in enumerate(root_elements):
    if isinstance(element, IndividualElement):
        if not element.is_deceased() and get_latest_possible_birth_year(element) <= 1900:
            print(index, element.get_pointer(), element.get_name(), element.get_birth_data())
            element.new_child_element(gedcom.tags.GEDCOM_TAG_DEATH)

# python-gedcom's .to_gedcom_string(recursive=True) seems to fail misearbly at nested levels
def recustr(element):
    recstr = element.to_gedcom_string()
    recstr = recstr + ''.join([recustr(child) for child in element.get_child_elements()])
    return recstr

print(recustr(gedcom_parser.get_root_element()))
