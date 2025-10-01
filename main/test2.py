import os
import re

# --- Configuração ---
# Diretório raiz onde o script será executado
base_dir = '.' 
# Diretório da documentação em inglês
english_docs_dir = os.path.join(base_dir, 'docs')
# Diretório da documentação em francês
french_docs_dir = os.path.join(english_docs_dir, 'fr-ca')

def find_code_groups(content):
    """Encontra e extrai todos os blocos <CodeGroup> do conteúdo."""
    # Regex para encontrar o bloco <CodeGroup>...</CodeGroup> de forma "non-greedy"
    # O flag re.DOTALL faz com que o '.' também corresponda a quebras de linha
    pattern = re.compile(r'<CodeGroup>.*?</CodeGroup>', re.DOTALL)
    return pattern.findall(content)

def replace_file_content(file_path, replacements):
    """Substitui os blocos de código em um arquivo."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            french_content = f.read()
    except FileNotFoundError:
        print(f"  - ATENÇÃO: Arquivo francês não encontrado em {file_path}")
        return

    # Encontra os CodeGroups "quebrados" no arquivo francês
    french_code_groups = find_code_groups(french_content)
    
    # Verifica se a quantidade de blocos é a mesma para evitar substituições erradas
    if len(french_code_groups) != len(replacements):
        print(f"  - ATENÇÃO: Disparidade no número de CodeGroups em {file_path}. Inglês: {len(replacements)}, Francês: {len(french_code_groups)}. Pulando...")
        return

    # Substitui cada bloco quebrado pelo bloco correto
    for i, good_block in enumerate(replacements):
        bad_block = french_code_groups[i]
        french_content = french_content.replace(bad_block, good_block, 1) # O '1' garante que apenas a primeira ocorrência seja substituída
        
    # Salva o arquivo com o conteúdo corrigido
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(french_content)
    print(f"  - Arquivo corrigido: {file_path}")

def sync_code_groups():
    """Função principal para sincronizar os CodeGroups."""
    print("Iniciando a sincronização dos blocos de código...")
    
    # Percorre a árvore de diretórios da documentação em inglês
    for root, _, files in os.walk(english_docs_dir):
        # Ignora o próprio diretório francês para não usar ele como fonte
        if french_docs_dir in root:
            continue
            
        for file in files:
            # Processa apenas arquivos .md e .mdx
            if file.endswith(('.md', '.mdx')):
                english_file_path = os.path.join(root, file)
                
                with open(english_file_path, 'r', encoding='utf-8') as f:
                    english_content = f.read()

                # Extrai os CodeGroups do arquivo em inglês
                english_code_groups = find_code_groups(english_content)
                
                # Se não houver CodeGroups no arquivo, pode pular
                if not english_code_groups:
                    continue
                
                print(f"\nProcessando: {english_file_path}")
                print(f"  - Encontrados {len(english_code_groups)} CodeGroups.")
                
                # Constrói o caminho para o arquivo francês correspondente
                relative_path = os.path.relpath(english_file_path, english_docs_dir)
                french_file_path = os.path.join(french_docs_dir, relative_path)
                
                # Realiza a substituição no arquivo francês
                replace_file_content(french_file_path, english_code_groups)

    print("\nSincronização concluída! ✅")

# --- Execução ---
if __name__ == '__main__':
    sync_code_groups()