#!/usr/bin/env python3
"""
eip.cleanup.py - detecta Elastic Ips não associados (dry run por padrão)
Uso:
    python eip_cleanup.py  #dry-run
    python eip_cleanup.py --apply #fará realease (com confirmação)
    
"""

import boto3
import argparse
import logging  

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)

def parse_arguments():
    p = argparse.ArgumentParser(description="Detecta EIPs não associados (dry-run por padrão).")
    p.add_argument("--apply", action="store_true", help="Libera EIPs não associados (cuidado).")
    return p.parse_args()

def find_unassociated_in_region(region):
    """
    Encontra EIPs não associados em uma região específica.
    """
    logger.info(f"[{region}]")
    
    #cria um cliente EC2 para a região
    client= boto3.client("ec2", region_name=region)
    
    try:
        #obtém todos os EIPs com o metodo describe_addresses
        resp = client.describe_addresses()
    except Exception as e:
        #se houver um erro
        logger.error(f"[{region}] Erro ao chamar describe_addresses: {e}")
        return []
    #lista para armazenar EIPs que achamos
    results = []    
    
    #itera sobre os EIPs retornados
    for addr in resp.get("Addresses",[]):
        # A API retorna vários dados, mas queremos saber se o EIP está associado.
        # Ele está associado se tiver um ID de associação, uma instância ou uma interface de rede.
        associated = bool(addr.get("AssociationId") or addr.get("InstanceId") or addr.get("NetworkInterfaceId"))
        if not associated:
        # Se o EIP NÃO estiver associado, ele é um candidato a ser liberado
            results.append({
                "Region": region,
                "PublicIp": addr.get("PublicIp"),
                "AllocationId": addr.get("AllocationId"),
            })
            return results
        
        
if __name__== "__main__":
    args = parse_arguments()
    
    # Por enquanto, vamos usar uma região fixa para testar
    target_region = "us-east-1"
    
    # Chamamos a nova função e guardamos os resultados
    unassociated_eips = find_unassociated_in_region(target_region)
    # Imprimimos os resultados para ver o que encontramos
    if unassociated_eips:
        logger.info(f"EIPs não associados encontrados ({len(unassociated_eips)}):")
        for eip in unassociated_eips:
            logger.info(f"- IP: {eip['PublicIp']}, ID: {eip['AllocationId']}")
    else:
        logger.info(f"Nenhum EIP não associado encontrado na região {target_region}.")