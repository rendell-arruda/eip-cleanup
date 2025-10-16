#!/usr/bin/env python3
# Indica ao sistema operacional que o script deve ser executado com o interpretador Python 3.

"""
eip_cleanup.py
Detecta Elastic IPs não associados (ociosos) por região.

Uso:
    python eip_cleanup.py
        → Verifica apenas a região padrão (us-east-1)
    python eip_cleanup.py --regions us-east-1,sa-east-1
        → Verifica múltiplas regiões
    python eip_cleanup.py --whitelist whitelist.txt
        → Usa uma lista de exceção de AllocationIds que não devem ser removidos
"""

# Importação de bibliotecas padrão e da AWS
import boto3        # SDK oficial da AWS para Python (usado para interagir com serviços AWS)
import argparse     # Biblioteca que permite ler argumentos passados via linha de comando
import logging      # Biblioteca padrão para registrar logs e mensagens de status

# Configuração básica do sistema de logs
logging.basicConfig(
    level=logging.INFO,  # Define o nível mínimo de mensagens que serão exibidas (INFO)
    format="%(asctime)s %(levelname)s: %(message)s",  # Define o formato da mensagem de log
)
logger = logging.getLogger(__name__)  # Cria um logger com o nome do módulo atual

# ---------------------------------------------------------------------
def parse_arguments():
    """
    Analisa os argumentos da linha de comando.
    Retorna um objeto com os argumentos processados.
    """
    p = argparse.ArgumentParser(description="Detecta EIPs não associados (dry-run por padrão).")
    
    # Flag opcional --apply: se presente, executa a remoção real
    p.add_argument("--apply", action="store_true", help="Libera EIPs não associados (cuidado).")
    
    # Argumento opcional --regions: lista de regiões separadas por vírgula
    p.add_argument("--regions", help="Regiões CSV (ex: us-east-1,us-west-2). Se omitido, usa us-east-1 como padrão.", default=None)
    
    # Argumento opcional --whitelist: caminho para um arquivo de exceções
    p.add_argument("--whitelist", help="Caminho para o arquivo com AllocationId por linha que nao devem ser removidos.", default=None)
    
    return p.parse_args()  # Retorna os argumentos processados como um objeto
# ---------------------------------------------------------------------

def get_regions(region_arg):
    """
    Define quais regiões devem ser verificadas.
    Se o argumento --regions for informado, divide por vírgulas.
    Caso contrário, retorna apenas ['us-east-1'].
    """
    if region_arg:
        # Divide a string em uma lista e remove espaços extras
        return [r.strip() for r in region_arg.split(",") if r.strip()]
    
    # Valor padrão se nenhuma região for especificada
    return ["us-east-1"]

# ---------------------------------------------------------------------
def find_unassociated_in_region(region, whitelist):
    """
    Percorre os Elastic IPs de uma região e retorna os que estão ociosos (sem associação).
    """
    logger.info(f"[{region}] Procurando EIPs não associados...")
    
    # Cria um cliente EC2 na região informada
    client = boto3.client("ec2", region_name=region)
    
    try:
        # Recupera todos os Elastic IPs alocados na conta
        resp = client.describe_addresses()
    except Exception as e:
        # Caso ocorra erro na chamada da API, registra o erro e retorna lista vazia
        logger.error(f"[{region}] Erro ao chamar describe_addresses: {e}")
        return []
    
    results = []  # Lista para armazenar os EIPs ociosos encontrados
    
    # Percorre todos os endereços retornados pela API
    for addr in resp.get("Addresses", []):
        # Verifica se o EIP está associado a algum recurso (instância, interface, etc.)
        associated = bool(addr.get("AssociationId") or addr.get("InstanceId") or addr.get("NetworkInterfaceId"))
        
        allocation_id = addr.get("AllocationId")  # Identificador único do EIP
        
        # Se o EIP estiver listado na whitelist, ele é ignorado
        if allocation_id and allocation_id in whitelist:
            logger.info(f"[{region}] EIP {addr['PublicIp']} (AllocationId: {allocation_id}) está na whitelist. Ignorando.")
            continue
        
        # Se não estiver associado, adiciona à lista de resultados
        if not associated:
            results.append({
                "Region": region,
                "PublicIp": addr.get("PublicIp"),
                "AllocationId": allocation_id
            })
                
    return results  # Retorna a lista de EIPs ociosos encontrados

# ---------------------------------------------------------------------
def load_whitelist(path):
    """
    Lê o arquivo de whitelist e retorna um conjunto (set) de AllocationIds.
    Se o caminho for None ou o arquivo não existir, retorna um set vazio.
    """
    if not path:
        logger.info("Nenhum arquivo de whitelist fornecido.")
        return set()
    
    wl = set()
    try:
        # Abre o arquivo e adiciona cada linha (AllocationId) ao set
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

# ---------------------------------------------------------------------
# Ponto de entrada principal do script
if __name__ == "__main__":
    # Lê os argumentos da linha de comando
    args = parse_arguments()
    
    # Determina quais regiões verificar
    regions = get_regions(args.regions)
    logger.info("\n🔍 Iniciando varredura de Elastic IPs por região...\n")
    logger.info(f"Regiões a serem verificadas: {regions}")
    
    # Carrega a whitelist, se informada
    whitelist = load_whitelist(args.whitelist)
    
    all_unassociated_eips = []  # Lista geral de todos os EIPs ociosos
    
    # Percorre todas as regiões informadas
    for region in regions:
        logger.info(f"\n===== Região: {region} =====")
        unassociated_eips = find_unassociated_in_region(region, whitelist)
        logger.info(f"[{region}] {len(unassociated_eips)} EIPs não associados encontrados.")
        logger.info("-" * 50)  # linha horizontal para separar regiões
        all_unassociated_eips.extend(unassociated_eips)
        
    # Exibe o resumo final
    if all_unassociated_eips:
        logger.info("\n\n📊 --- Resumo Geral ---\n")
       
        logger.info(f"Total de EIPs não associados encontrados: {len(all_unassociated_eips)}")
        for eip in all_unassociated_eips:
            logger.info(f"- IP: {eip['PublicIp']} ({eip['Region']}) - AllocationId: {eip['AllocationId']}")
    else:
        logger.info("Nenhum EIP não associado encontrado em todas as regiões verificadas.")
        
    logger.info("\n✅ Varredura concluída!\n")