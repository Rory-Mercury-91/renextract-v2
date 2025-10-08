# test_nested_extraction.rpy
# Test spécifique pour les imbrications d'astérisques et tildes

# ============================================================
# TEST 1: IMBRICATIONS SIMPLES
# ============================================================

# game/script.rpy:10
translate french nested_001:

    # "Nested: **bold with *italic* inside**"
    "Imbrication: **gras avec *italique* dedans**"

# game/script.rpy:12
translate french nested_002:

    # "Triple: ***strong with **bold** inside***"
    "Triple: ***fort avec **gras** dedans***"

# game/script.rpy:14
translate french nested_003:

    # "Complex: ****level4 with ***level3 and **level2** inside*** end****"
    "Complexe: ****niveau4 avec ***niveau3 et **niveau2** dedans*** fin****"

# ============================================================
# TEST 2: IMBRICATIONS MULTIPLES
# ============================================================

# game/script.rpy:20
translate french multi_001:

    # "Multiple: **first** and **second with *nested***"
    "Multiple: **premier** et **deuxième avec *imbriqué***"

# game/script.rpy:22
translate french multi_002:

    # "Mixed: *simple* **double** ***triple***"
    "Mixte: *simple* **double** ***triple***"

# ============================================================
# TEST 3: TILDES IMBRIQUÉS
# ============================================================

# game/script.rpy:30
translate french tilde_nested_001:

    # "Tilde nested: ~~strike with ~simple~ inside~~"
    "Tilde imbriqué: ~~barré avec ~simple~ dedans~~"

# game/script.rpy:32
translate french tilde_nested_002:

    # "Triple tilde: ~~~level3 with ~~level2~~ inside~~~"
    "Triple tilde: ~~~niveau3 avec ~~niveau2~~ dedans~~~"

# ============================================================
# TEST 4: COMBINAISONS ASTÉRISQUES + TILDES
# ============================================================

# game/script.rpy:40
translate french combo_nested_001:

    # "Combo: **bold with ~tilde~ inside** and ~~strike with *italic***"
    "Combo: **gras avec ~tilde~ dedans** et ~~barré avec *italique***"

# game/script.rpy:42
translate french combo_nested_002:

    # "Complex combo: ***strong with ~~strike and *italic*~~ inside***"
    "Combo complexe: ***fort avec ~~barré et *italique*~~ dedans***"

# ============================================================
# TEST 5: CAS EXTRÊMES
# ============================================================

# game/script.rpy:50
translate french extreme_001:

    # "Extreme: ****a with ***b with **c with *d* inside** inside*** inside****"
    "Extrême: ****a avec ***b avec **c avec *d* dedans** dedans*** dedans****"

# game/script.rpy:52
translate french extreme_002:

    # jessica "Character dialogue with **bold and *italic* nested** inside"
    jessica "Dialogue personnage avec **gras et *italique* imbriqué** dedans"

# ============================================================
# TEST 6: AVEC VARIABLES
# ============================================================

# game/script.rpy:60
translate french var_nested_001:

    # "With var: **bold with [player_name] and *italic* inside**"
    "Avec var: **gras avec [player_name] et *italique* dedans**"

# game/script.rpy:62
translate french var_nested_002:

    # "Complex: ***strong with [var] and ~~strike with *italic*~~ inside***"
    "Complexe: ***fort avec [var] et ~~barré avec *italique*~~ dedans***"
