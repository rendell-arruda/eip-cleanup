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

def find_unassociated_in_region(region):
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
        
        # Se a variável 'associated' for False, significa que o EIP está ocioso
        if not associated:
            results.append({
                "Region": region,
                "PublicIp": addr.get("PublicIp"),
                "AllocationId": addr.get("AllocationId"),
            })
            
    return results # Retorna a lista de EIPs ociosos encontrados

# Início do ponto de entrada do script
if __name__== "__main__":
    # Chama a função para analisar os argumentos de linha de comando
    args = parse_arguments()
    
    # Pega a lista de regiões a serem verificadas (usando o argumento ou o padrão)
    regions = get_regions(args.regions)
    logger.info(f"Regiões a serem verificadas: {regions}")
    
    all_unassociated_eips = [] # Lista para guardar os resultados de todas as regiões
    
    # Itera sobre cada região na lista
    for region in regions:
        # Chama a função que busca EIPs ociosos para a região atual
        unassociated_eips = find_unassociated_in_region(region)
        
        logger.info(f"[{region}] {len(unassociated_eips)} EIPs não associados encontrados.\n")
        
        # Adiciona os EIPs encontrados nesta região à lista geral
        all_unassociated_eips.extend(unassociated_eips)
        
    # Verifica se algum EIP ocioso foi encontrado em todas as regiões
    if all_unassociated_eips:
        logger.info(f"\n--- Resumo ---")
        logger.info(f"Total de EIPs não associados encontrados: {len(all_unassociated_eips)}")
        for eip in all_unassociated_eips:
            logger.info(f"- IP: {eip['PublicIp']} ({eip['Region']})")
    else:
        logger.info(f"Nenhum EIP não associado encontrado em todas as regiões verificadas.")