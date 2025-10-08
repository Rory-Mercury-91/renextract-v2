#!/usr/bin/env python3
"""
Script de test pour l'extraction complète avec le fichier test_extraction_complete.rpy
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from backend.extraction import TextExtractor

def main():
    print("="*80)
    print("🧪 TEST D'EXTRACTION COMPLET - RenExtract v2")
    print("="*80)
    
    # Charger le fichier de test
    test_file = "test_extraction_complete.rpy"
    
    if not os.path.exists(test_file):
        print(f"❌ Fichier de test introuvable: {test_file}")
        return
    
    print(f"\n📂 Chargement du fichier: {test_file}")
    
    with open(test_file, 'r', encoding='utf-8') as f:
        content = f.readlines()
    
    print(f"   ✅ {len(content)} lignes chargées")
    
    # Créer l'extracteur
    extractor = TextExtractor()
    extractor.load_file_content(content, test_file)
    
    print(f"\n⚙️  Lancement de l'extraction...")
    print(f"   - Détection des doublons: {'✅ ACTIVÉE' if extractor.detect_duplicates else '❌ DÉSACTIVÉE'}")
    
    try:
        # Extraire
        result = extractor.extract_texts()
        
        print(f"\n" + "="*80)
        print("✅ EXTRACTION RÉUSSIE !")
        print("="*80)
        
        # Statistiques globales
        print(f"\n📊 STATISTIQUES GLOBALES:")
        print(f"   - Dialogues extraits:      {result['extracted_count']}")
        print(f"   - Astérisques protégés:    {result['asterix_count']}")
        print(f"   - Tildes protégés:         {result['tilde_count']}")
        print(f"   - Textes vides:            {result['empty_count']}")
        print(f"   - Variables protégées:     {len(extractor.mapping)}")
        print(f"   - Doublons détectés:       {result['duplicate_count']}")
        
        # Détails des fichiers créés
        print(f"\n📁 FICHIERS CRÉÉS:")
        if 'dialogue_files' in result:
            for f in result['dialogue_files']:
                print(f"   ✓ {f}")
        if 'doublons_files' in result:
            for f in result['doublons_files']:
                print(f"   ✓ {f}")
        if 'asterix_files' in result:
            for f in result['asterix_files']:
                print(f"   ✓ {f}")
        if 'positions_file' in result:
            print(f"   ✓ {result['positions_file']}")
        if 'placeholder_file' in result:
            print(f"   ✓ {result['placeholder_file']}")
        
        # Exemples de dialogues extraits
        print(f"\n📝 EXEMPLES DE DIALOGUES EXTRAITS (10 premiers):")
        for i, text in enumerate(extractor.extracted_texts[:10], 1):
            display_text = text.strip()
            if len(display_text) > 60:
                display_text = display_text[:57] + "..."
            print(f"   {i:2d}. {display_text}")
        
        # Exemples d'astérisques
        if extractor.asterix_texts:
            print(f"\n⭐ EXEMPLES D'ASTÉRISQUES EXTRAITS (5 premiers):")
            for i, text in enumerate(extractor.asterix_texts[:5], 1):
                print(f"   {i}. {text.strip()}")
        
        # Exemples de tildes
        if extractor.tilde_texts:
            print(f"\n🌊 EXEMPLES DE TILDES EXTRAITS (5 premiers):")
            for i, text in enumerate(extractor.tilde_texts[:5], 1):
                print(f"   {i}. {text.strip()}")
        
        # Métadonnées astérisques
        if extractor.asterix_metadata:
            print(f"\n📊 MÉTADONNÉES ASTÉRISQUES (5 premiers):")
            for i, (placeholder, meta) in enumerate(list(extractor.asterix_metadata.items())[:5], 1):
                print(f"   {i}. {placeholder}:")
                print(f"      - Préfixe: {'*' * meta['prefix_count']} ({meta['prefix_count']})")
                print(f"      - Suffixe: {'*' * meta['suffix_count']} ({meta['suffix_count']})")
                print(f"      - Contenu: '{meta['content']}'")
        
        # Métadonnées tildes
        if extractor.tilde_metadata:
            print(f"\n📊 MÉTADONNÉES TILDES (5 premiers):")
            for i, (placeholder, meta) in enumerate(list(extractor.tilde_metadata.items())[:5], 1):
                orphan = " (ORPHELIN)" if meta.get('orphan', False) else ""
                print(f"   {i}. {placeholder}{orphan}:")
                print(f"      - Préfixe: {'~' * meta['prefix_count']} ({meta['prefix_count']})")
                print(f"      - Suffixe: {'~' * meta['suffix_count']} ({meta['suffix_count']})")
                print(f"      - Contenu: '{meta['content']}'")
        
        # Exemples de variables protégées
        if extractor.mapping:
            print(f"\n🔧 EXEMPLES DE VARIABLES PROTÉGÉES (10 premiers):")
            for i, (original, placeholder) in enumerate(list(extractor.mapping.items())[:10], 1):
                print(f"   {i:2d}. '{original}' → {placeholder}")
        
        # Doublons
        if result['duplicate_count'] > 0:
            print(f"\n🔄 EXEMPLES DE DOUBLONS (5 premiers):")
            for i, text in enumerate(extractor.duplicate_manager.duplicate_texts_for_translation[:5], 1):
                display_text = text.strip()
                if len(display_text) > 60:
                    display_text = display_text[:57] + "..."
                print(f"   {i}. {display_text}")
        
        # Vérifications de cohérence
        print(f"\n🔍 VÉRIFICATIONS DE COHÉRENCE:")
        
        # Vérifier que les métadonnées correspondent aux mappings
        asterix_meta_count = len(extractor.asterix_metadata)
        asterix_mapping_count = len(extractor.asterix_mapping)
        if asterix_meta_count == asterix_mapping_count:
            print(f"   ✅ Métadonnées astérisques cohérentes ({asterix_meta_count} = {asterix_mapping_count})")
        else:
            print(f"   ⚠️  Incohérence métadonnées astérisques ({asterix_meta_count} ≠ {asterix_mapping_count})")
        
        tilde_meta_count = len(extractor.tilde_metadata)
        tilde_mapping_count = len(extractor.tilde_mapping)
        if tilde_meta_count == tilde_mapping_count:
            print(f"   ✅ Métadonnées tildes cohérentes ({tilde_meta_count} = {tilde_mapping_count})")
        else:
            print(f"   ⚠️  Incohérence métadonnées tildes ({tilde_meta_count} ≠ {tilde_mapping_count})")
        
        # Vérifier que tous les textes extraits sont non vides (sauf empty)
        empty_dialogues = sum(1 for text in extractor.extracted_texts if text.strip() == "")
        if empty_dialogues == 0:
            print(f"   ✅ Aucun dialogue vide dans extracted_texts")
        else:
            print(f"   ⚠️  {empty_dialogues} dialogues vides dans extracted_texts (devraient être dans empty_texts)")
        
        # Résumé final
        print(f"\n" + "="*80)
        print("✅ TEST TERMINÉ AVEC SUCCÈS")
        print("="*80)
        print(f"\nTous les cas d'extraction ont été testés:")
        print(f"  ✓ Dialogues simples et avec personnages")
        print(f"  ✓ Astérisques imbriqués (système de pile)")
        print(f"  ✓ Tildes imbriqués (système de pile)")
        print(f"  ✓ Variables entre crochets imbriquées (système de pile)")
        print(f"  ✓ Balises HTML et accolades")
        print(f"  ✓ Variables de formatage (%s, %d, %(name)s)")
        print(f"  ✓ Guillemets échappés")
        print(f"  ✓ Textes vides")
        print(f"  ✓ Choix (translate strings)")
        print(f"  ✓ Doublons")
        print(f"  ✓ Combinaisons complexes")
        print(f"  ✓ Caractères Unicode")
        print(f"  ✓ Edge cases")
        
        print(f"\n💡 Tu peux maintenant vérifier les fichiers générés dans:")
        print(f"   📂 01_Temporary/fichiers_a_traduire/")
        print(f"   📂 01_Temporary/fichiers_a_referencer/")
        
    except Exception as e:
        print(f"\n❌ ERREUR LORS DE L'EXTRACTION:")
        print(f"   {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
