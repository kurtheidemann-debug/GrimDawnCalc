"""Verified ordinary material classification; unknown special inputs stay costly.

No virtual stock is created. Recipes and finite ingredients remain authoritative.
The game labels Aether Crystals QuestItem, which is not a rarity/tier signal.
"""
ORDINARY_MATERIALS=frozenset({'records/items/materia/compa_aethercrystal.dbr'})

def default_recipes(database, level):
    menu=set(database.get('records/ui/inventor/craftingpanel/crafting_table.dbr',{}).get('craftingDefaultRecipes',[]))
    for path,recipe in database.items():
        if '/crafting/' not in path or recipe.get('Class')!='ItemArtifactFormula':continue
        if path not in menu and not recipe.get('defaultRecipe'):continue
        result=recipe.get('artifactName')
        if isinstance(result,str) and result in database and recipe.get('levelRequirement',0)<=level:
            yield result,recipe

def ingredient_cost_units(database, path):
    return 1 if path in ORDINARY_MATERIALS or database.get(path,{}).get('Class')=='ItemRelic' else 15
