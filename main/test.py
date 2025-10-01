import os
import re
import argparse

# --- Definição das Regras de Verificação ---

# Dicionário de tags que frequentemente ficam sem fechamento.
TAGS_TO_BALANCE = [
    'Callout', 'Warning', 'Note', 'CodeGroup'
]

# Lista de verificações baseadas em expressões regulares.
REGEX_CHECKS = [
    {
        "name": "Unclosed <thead> in List Item",
        "pattern": re.compile(r'^\s*[-*]\s+.*<thead.*(?!.*</thead>)', re.IGNORECASE),
        "message": "Possível tag `<thead>` não fechada dentro de um item de lista. Verifique a tabela."
    },
    {
        "name": "Invalid JSX Attribute with Dot",
        "pattern": re.compile(r'<\w+\s+[^>]*\w+\.\w+\s*=[^>]*>'),
        "message": "Atributo JSX/HTML inválido contendo um '.' (ponto). Ex: `user.name` deve ser `userName` ou `data-user-name`."
    },
    {
        "name": "Invalid Character Before Tag Name",
        "pattern": re.compile(r'<\s*[!%=`]\s*[^>]+>'),
        "message": "Caractere inesperado encontrado no início de uma tag. Comentários em MDX são {/* ... */}."
    },
    {
        "name": "Malformed Self-Closing Tag",
        "pattern": re.compile(r'<\w+\s+[^>]*\/[^>]*>'),
        "message": "Tag pode estar mal formatada. A barra de auto-fechamento deve ser `/>` no final."
    },
    {
        "name": "Unclosed Generic Tag",
        "pattern": re.compile(r'<(\w+)\s*[^>]*>(?!.*<\/\1>)', re.IGNORECASE),
        "message": "Possível tag genérica não fechada na mesma linha."
    },
     {
        "name": "Acorn Parsing Error Signature",
        "pattern": re.compile(r'\{\s*[\w\.]+\s*:\s*[^\'"\{\}\s,]+?\s*\}'),
        "message": "Potencial erro de parsing Acorn: valor de objeto em JSX pode não estar entre aspas."
    }
]

def sanitize_content(content):
    """
    Remove o conteúdo de blocos de código para evitar falsos positivos.
    - Substitui blocos ```...``` por newlines para manter a contagem de linhas.
    - Substitui `...` por espaços para manter o layout da linha.
    """
    # Expressão para encontrar blocos de código cercados por ```
    fenced_code_block_regex = re.compile(r'```.*?```', re.DOTALL)
    # Expressão para encontrar código inline cercado por `
    inline_code_regex = re.compile(r'`[^`]*`')

    # Função para substituir o bloco de código pelo mesmo número de novas linhas
    def replace_fenced_block(match):
        block_content = match.group(0)
        num_lines = block_content.count('\n')
        return '\n' * num_lines

    # Função para substituir o código inline por espaços
    def replace_inline_block(match):
        return ' ' * len(match.group(0))

    sanitized = fenced_code_block_regex.sub(replace_fenced_block, content)
    sanitized = inline_code_regex.sub(replace_inline_block, sanitized)
    
    return sanitized


def check_file_for_errors(filepath):
    """
    Verifica um único arquivo em busca de erros definidos nas regras.
    """
    errors_found = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            full_content = f.read()
        
        # Cria uma versão "limpa" do conteúdo, sem código
        clean_content = sanitize_content(full_content)
        clean_lines = clean_content.splitlines()

        # 1. Verificação de balanceamento de tags no conteúdo limpo
        for tag in TAGS_TO_BALANCE:
            open_tag_pattern = re.compile(f'<{tag}[^>]*?(?<!/)>', re.IGNORECASE)
            close_tag_pattern = re.compile(f'</{tag}>', re.IGNORECASE)

            open_count = len(re.findall(open_tag_pattern, clean_content))
            close_count = len(re.findall(close_tag_pattern, clean_content))

            if open_count != close_count:
                error_msg = f"Erro de balanceamento: A tag `<{tag}>` tem {open_count} aberturas e {close_count} fechamentos (verificado fora de blocos de código)."
                # Reporta o erro no arquivo, sem um número de linha específico
                errors_found.append(f"Balanceamento de Tag: {filepath} - {error_msg}")

        # 2. Verificação baseada em Regex linha por linha (nas linhas limpas)
        for i, line in enumerate(clean_lines):
            for check in REGEX_CHECKS:
                if check['pattern'].search(line):
                    error_msg = f"{check['name']}: {filepath}:{i+1} - {check['message']}"
                    errors_found.append(error_msg)

    except Exception as e:
        errors_found.append(f"Erro ao processar o arquivo {filepath}: {e}")

    return errors_found

def main(root_dir):
    """
    Função principal que percorre o diretório e verifica os arquivos .mdx.
    """
    all_errors = []
    print(f"🔍 Verificando arquivos .mdx em '{root_dir}' (ignorando blocos de código)...")

    for subdir, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.mdx'):
                filepath = os.path.join(subdir, file)
                errors = check_file_for_errors(filepath)
                if errors:
                    all_errors.extend(errors)

    if all_errors:
        print("\n--- 🚨 Erros de Parsing Encontrados ---")
        for error in sorted(all_errors):
            print(error)
        print(f"\nTotal de {len(all_errors)} problemas encontrados.")
    else:
        print("\n✅ Nenhum erro de parsing comum foi encontrado!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Verifica arquivos .mdx em busca de erros comuns de parsing que causam falhas no Mintlify."
    )
    parser.add_argument(
        "directory",
        type=str,
        help="O diretório raiz para começar a busca por arquivos .mdx."
    )
    args = parser.parse_args()
    main(args.directory)