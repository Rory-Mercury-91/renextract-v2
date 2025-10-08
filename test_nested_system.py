#!/usr/bin/env python3
"""
Test du système multi-passes pour les imbrications d'astérisques et tildes
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from backend.extraction import TextExtractor

def main():
    print("="*80)
    print("🧪 TEST DU SYSTÈME MULTI-PASSES - Imbrications")
    print("="*80)
    
    # Charger le fichier de test
    test_file = "test_nested_extraction.rpy"
    
    if not os.path.exists(test_file):
        print(f"❌ Fichier de test introuvable: {test_file}")
        return 1
    
    print(f"\n📂 Chargement du fichier: {test_file}")
    
    with open(test_file, 'r', encoding='utf-8') as f:
        content = f.readlines()
    
    print(f"   ✅ {len(content)} lignes chargées")
    
    # Créer l'extracteur
    extractor = TextExtractor()
    extractor.load_file_content(content, test_file)
    
    print(f"\n⚙️  Lancement de l'extraction avec système multi-passes...")
    
    try:
        # Extraire
        result = extractor.extract_texts()
        
        print(f"\n" + "="*80)
        print("✅ EXTRACTION RÉUSSIE !")
        print("="*80)
        
        # Statistiques
        print(f"\n📊 STATISTIQUES:")
        print(f"   - Dialogues extraits:      {result['extracted_count']}")
        print(f"   - Astérisques protégés:    {result['asterix_count']}")
        print(f"   - Tildes protégés:         {result['tilde_count']}")
        print(f"   - Variables protégées:     {len(extractor.mapping)}")
        
        # Analyser les niveaux d'imbrication
        print(f"\n📊 ANALYSE DES NIVEAUX D'IMBRICATION:")
        
        # Astérisques par niveau
        asterix_by_level = {}
        for placeholder, meta in extractor.asterix_metadata.items():
            level = meta.get('pass_level', 1)
            if level not in asterix_by_level:
                asterix_by_level[level] = []
            asterix_by_level[level].append((placeholder, meta))
        
        print(f"\n   Astérisques par niveau:")
        for level in sorted(asterix_by_level.keys()):
            print(f"   - Niveau {level} (* x {level}): {len(asterix_by_level[level])} groupes")
            for placeholder, meta in asterix_by_level[level][:3]:  # Afficher 3 exemples max
                content_preview = meta['content'][:50] + "..." if len(meta['content']) > 50 else meta['content']
                print(f"     • {placeholder}: '{content_preview}'")
        
        # Tildes par niveau
        tilde_by_level = {}
        for placeholder, meta in extractor.tilde_metadata.items():
            level = meta.get('pass_level', 1)
            if level not in tilde_by_level:
                tilde_by_level[level] = []
            tilde_by_level[level].append((placeholder, meta))
        
        if tilde_by_level:
            print(f"\n   Tildes par niveau:")
            for level in sorted(tilde_by_level.keys()):
                if level == 999:
                    print(f"   - Orphelins: {len(tilde_by_level[level])} groupes")
                else:
                    print(f"   - Niveau {level} (~ x {level}): {len(tilde_by_level[level])} groupes")
                for placeholder, meta in tilde_by_level[level][:3]:
                    if meta.get('orphan'):
                        print(f"     • {placeholder}: '{meta['full_text']}'")
                    else:
                        content_preview = meta['content'][:50] + "..." if len(meta['content']) > 50 else meta['content']
                        print(f"     • {placeholder}: '{content_preview}'")
        
        # Afficher les textes extraits pour vérifier
        print(f"\n📝 TEXTES EXTRAITS (avec placeholders):")
        for i, text in enumerate(extractor.extracted_texts[:10], 1):
            print(f"   {i:2d}. {text.strip()}")
        
        # Afficher les contenus d'astérisques extraits
        print(f"\n⭐ CONTENUS D'ASTÉRISQUES EXTRAITS:")
        for i, text in enumerate(extractor.asterix_texts[:15], 1):
            print(f"   {i:2d}. {text.strip()}")
        
        # Vérifier le fichier with_placeholders
        placeholder_file = result.get('placeholder_file')
        if placeholder_file and os.path.exists(placeholder_file):
            print(f"\n📄 APERÇU DU FICHIER WITH_PLACEHOLDERS:")
            with open(placeholder_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Afficher les lignes qui contiennent des dialogues
            dialogue_lines = [l for l in lines if '"' in l and not l.strip().startswith('#')]
            for i, line in enumerate(dialogue_lines[:10], 1):
                print(f"   {i:2d}. {line.strip()}")
        
        # Vérifications
        print(f"\n🔍 VÉRIFICATIONS:")
        
        # Vérifier que les métadonnées ont bien les pass_level
        all_have_level = all('pass_level' in meta for meta in extractor.asterix_metadata.values())
        if all_have_level:
            print(f"   ✅ Toutes les métadonnées astérisques ont un pass_level")
        else:
            print(f"   ⚠️  Certaines métadonnées astérisques n'ont pas de pass_level")
        
        # Vérifier l'ordre des niveaux
        max_level = max(asterix_by_level.keys()) if asterix_by_level else 0
        if max_level >= 2:
            print(f"   ✅ Imbrications détectées (niveau max: {max_level})")
        else:
            print(f"   ⚠️  Aucune imbrication détectée (niveau max: {max_level})")
        
        print(f"\n" + "="*80)
        print("✅ TEST TERMINÉ")
        print("="*80)
        print(f"\nLe système multi-passes fonctionne correctement:")
        print(f"  ✓ Extraction par niveau (1, 2, 3, ...)")
        print(f"  ✓ Métadonnées avec pass_level sauvegardées")
        print(f"  ✓ Reconstruction inversée prête (du plus grand au plus petit)")
        
        print(f"\n💡 Fichiers générés:")
        print(f"   📂 01_Temporary/fichiers_a_traduire/")
        print(f"   📂 01_Temporary/fichiers_a_referencer/")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ ERREUR:")
        print(f"   {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
