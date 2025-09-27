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
    
if __name__== "__main__":
    args = parse_arguments()
    logger.info(f"Args recebidos: {args}")