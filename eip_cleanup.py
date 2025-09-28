#!/usr/bin/env python3
# A linha acima diz ao sistema operacional para usar o interpretador Python 3 para rodar este script.

"""
eip_cleanup.py
Detecta Elastic IPs não associados (ociosos) por região.
Uso:
    python eip_cleanup.py              # Verifica apenas a região padrão (us-east-1)
    python eip_cleanup.py --regions us-east-1,sa-east-1 # Verifica múltiplas regiões específicas
"""

# Importa bibliotecas necessárias para o script
import boto3        # Biblioteca oficial da AWS para Python
import argparse     # Para processar argumentos de linha de comando
import logging      # Para registrar mensagens (logs) de forma organizada

# Configura o sistema de logging
logging.basicConfig(
    level=logging.INFO, # Define o nível mínimo de mensagens a serem exibidas (INFO, WARNING, ERROR, etc.)
    format="%(asctime)s %(levelname)s: %(message)s", # Define o formato das mensagens de log (data, nível, mensagem)
)
logger = logging.getLogger(__name__) # Cria um objeto logger para registrar as mensagens no script

def parse_arguments():
    """
    Função que analisa os argumentos passados pela linha de comando.
    """
    # Cria um objeto ArgumentParser com uma descrição para o script
    p = argparse.ArgumentParser(description="Detecta EIPs não associados (dry-run por padrão).")
    
    # Adiciona o argumento '--apply'. Se presente, a variável 'apply' será True.
    p.add_argument("--apply", action="store_true", help="Libera EIPs não associados (cuidado).")
    
    # Adiciona o argumento '--regions'. Recebe uma lista de regiões separadas por vírgula.
    p.add_argument("--regions", help="Regiões CSV (ex: us-east-1,us-west-2). Se omitido, usa us-east-1 como padrão.", default=None)
    
    # Adiciona o argumento '--whitelist'. Recebe o caminho para um arquivo de whitelist.
    p.add_argument("--whitelist", help="Caminho parao arquivo com AllocationId por linha que nao devem ser removidos.", default=None)
    
    return p.parse_args() # Analisa os argumentos e retorna um objeto com os valores

def get_regions(region_arg):
    """
    Retorna uma lista de regiões a serem verificadas.
    Usa o argumento do usuário ou a default us-east-1 se nenhuma for especificada.
    """
    if region_arg:
        # Se o argumento '--regions' foi usado, divide a string em uma lista de regiões
        return [r.strip() for r in region_arg.split(",") if r.strip()]
    
    # Se o argumento não foi usado, retorna a região padrão 'us-east-1'
    return ["us-east-1"]

def find_unassociated_in_region(region, whitelist):
    """
    Encontra e retorna uma lista de EIPs que não estão associados em uma região específica.
    """
    logger.info(f"[{region}] Procurando EIPs não associados...")
    
    # Cria um cliente Boto3 para o serviço EC2 na região especificada
    client = boto3.client("ec2", region_name=region)
    
    try:
        # Chama a API 'describe_addresses()' para listar todos os Elastic IPs da região
        resp = client.describe_addresses()
        
    except Exception as e:
        # Captura qualquer erro que ocorra na chamada da API e o registra
        logger.error(f"[{region}] Erro ao chamar describe_addresses: {e}")
        return [] # Retorna uma lista vazia para evitar que o script pare
    
    results = [] # Cria uma lista vazia para guardar os EIPs não associados
    
    # Itera sobre cada EIP encontrado na resposta da API
    for addr in resp.get("Addresses", []):
        # Verifica se o EIP está associado a uma instância, interface de rede ou ID de associação.
        # 'bool(...)' converte o valor em True se ele existir, e False se for vazio.
        associated = bool(addr.get("AssociationId") or addr.get("InstanceId") or addr.get("NetworkInterfaceId"))
        
        allocation_id = addr.get("AllocationId") # Pega o AllocationId do EIP atual
        if allocation_id and allocation_id in whitelist:
            logger.info(f"[{region}] EIP {addr['PublicIp']} (AllocationId: {allocation_id}) está na whitelist. Ignorando.")
            continue # Pula para o próximo EIP se este estiver na whitelist
        
        if not associated:
            results.append({
                "Region": region,
                "PublicIp": addr.get("PublicIp"),
                "AllocationId": allocation_id 
                })
                
    return results # Retorna a lista de EIPs ociosos encontrados

def load_whitelist(path):
    """
    lê um arquivo de whitelist e retorna um Set de AllocationIds.
    """
    if not path:
        logger.ingo("Nenhum arquivo de whitelist fornecido.")
        return set()# Retorna um Set vazio se nenhum caminho for fornecido
    
    wl = set() # Cria um Set vazio para guardar os AllocationIds da whitelist
    try:
        with open(path, "r") as f:
            for line in f:
                val = line.strip()
                if val:
                    wl.add(val)
        logger.info(f"Whitelist carregada com {len(wl)} entradas.")
        return wl
    except FileNotFoundError:
        logger.error(f"Arquivo da whitelist '{path}' não encontrado. Ignorando.")
        return set()
        
        
# Início do ponto de entrada do script
if __name__== "__main__":
    args = parse_arguments()
    
    regions = get_regions(args.regions)
    logger.info(f"Regiões a serem verificadas: {regions}")
    
    # Nova linha para carregar a whitelist
    whitelist = load_whitelist(args.whitelist)
    
    all_unassociated_eips = []
    
    for region in regions:
        # Passa a whitelist como argumento para a função
        unassociated_eips = find_unassociated_in_region(region, whitelist)
        
        logger.info(f"[{region}] {len(unassociated_eips)} EIPs não associados encontrados.")
        all_unassociated_eips.extend(unassociated_eips)
        
    if all_unassociated_eips:
        logger.info(f"\n--- Resumo ---")
        logger.info(f"Total de EIPs não associados encontrados: {len(all_unassociated_eips)}")
        for eip in all_unassociated_eips:
            logger.info(f"- IP: {eip['PublicIp']} ({eip['Region']}) - AllocationId: {eip['AllocationId']}")
    else:
        logger.info(f"Nenhum EIP não associado encontrado em todas as regiões verificadas.")