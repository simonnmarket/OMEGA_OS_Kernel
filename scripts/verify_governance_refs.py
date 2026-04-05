import os
import re
import json
import argparse

# Configurações
GOVERNANCE_PATH = 'governance'
README_FILE = os.path.join(GOVERNANCE_PATH, 'README.md')
MANIFEST_FILE = os.path.join(GOVERNANCE_PATH, 'MANIFESTO_DOCUMENTOS.json')

def get_readme_ids():
    """Extrai IDs de documentos do README.md na coluna ID."""
    if not os.path.exists(README_FILE):
        return []
    
    with open(README_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Procura tokens no formato DOC-OFC-*** ou IDs explícitos nas tabelas
    ids = re.findall(r'`(DOC-OFC-[\w-]+)`', content)
    return sorted(list(set(ids)))

def get_files_ids():
    """Lista IDs baseados nos nomes de arquivos físicos (sem a extensão .md)."""
    if not os.path.exists(GOVERNANCE_PATH):
        return []
    
    files = [f for f in os.listdir(GOVERNANCE_PATH) if f.startswith('DOC-OFC-') and f.endswith('.md')]
    return sorted([f.replace('.md', '') for f in files])

def run_audit():
    """Verifica desvios entre o README e o disco."""
    readme_ids = get_readme_ids()
    files_ids = get_files_ids()
    
    errors = []
    
    # 1. IDs no README que NÃO existem no disco
    for rid in readme_ids:
        if rid not in files_ids:
            # Ignora redirecionamentos manuais ou placeholders conhecidos
            if 'Arquivo' not in rid:
                 errors.append(f"ERRO: ID no README não possui arquivo físico correspondente: {rid}")
    
    # 2. Arquivos no disco que NÃO estão no README
    for fid in files_ids:
        if fid not in readme_ids:
             errors.append(f"AVISO: Arquivo físico não listado ou com ID diferente no README: {fid}")
             
    if not errors:
        print("SISTEMA DE GOVERNANÇA: OK - Referências auditadas e alinhadas.")
        return True
    else:
        for err in errors:
            print(err)
        return False

def write_manifest():
    """Gera o manifesto JSON baseado na verdade do README."""
    readme_ids = get_readme_ids()
    manifest = {
        "versao": "1.0",
        "total_documentos": len(readme_ids),
        "documentos": readme_ids
    }
    
    with open(MANIFEST_FILE, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=4, ensure_ascii=False)
    
    print(f"MANIFESTO ATUALIZADO: {MANIFEST_FILE}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Auditoria de Referências de Governança OMEGA.")
    parser.add_argument("--write-manifest", action="store_true", help="Gera o manifesto documental.")
    args = parser.parse_args()
    
    if args.write_manifest:
        write_manifest()
    else:
        success = run_audit()
        if not success:
            exit(1)
