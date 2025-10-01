# Elastic IP Cleaner – AWS Elastic IP Idle Automation

Automação em Python para detectar e (opcionalmente) liberar Elastic IPs (EIPs) ociosos que estão alocados mas **não associados** a instâncias ou interfaces de rede. Ideal para equipes de FinOps e CloudOps que desejam reduzir custos recorrentes com EIPs não utilizados.

## 📁 Estrutura do Projeto
idle_ip_cleaner/
├── idle_ip_cleaner.py
├── README.md
├── requirements.txt
└── LICENSE

## 🚀 Funcionalidades Atuais
- ✅ **Varredura multi-região**: verifica uma ou várias regiões AWS passadas por parâmetro (`--regions us-east-1,sa-east-1`), padrão `us-east-1`.  
- ✅ **Whitelist de AllocationIds**: arquivo externo para ignorar EIPs que não devem ser removidos (`--whitelist path/to/file.txt`).  
- ✅ **Dry-run por padrão**: apenas lista EIPs não associados, sem liberar endereços.  
- ✅ **Liberação opcional**: `--apply` libera EIPs não associados.  
- ✅ **Logs estruturados** com `logging` e resumo final por região.  

## 🔮 Próximas Funcionalidades Planejadas
- 🚧 Integração com **AWS STS Assume Role** para execução cross-account.  
- 🚧 Geração de **relatório CSV** com todos os EIPs identificados.  
- 🚧 Envio de alertas para **Slack/Teams** ou integração com sistemas de monitoramento.  
- 🚧 Deploy serverless em **AWS Lambda + EventBridge** para agendamento automático.  
- 🚧 Filtro por **tags** (ex.: `do-not-delete`) além de AllocationId.  
- 🚧 Suporte a **dashboards** (CloudWatch/Datadog) com métricas de EIPs liberados e custos evitados.

## 💸 Custos e Motivação FinOps
- **Elastic IP associado a instância em execução**: 1 EIP por instância é geralmente gratuito.  
- **Elastic IP alocado e não associado**: cerca de **$0,005/hora (~$3,60/mês)** por EIP ocioso.  
- O script ajuda a eliminar cobranças desnecessárias, aplicando guardrails de FinOps.

## 🛠️ Requisitos
- Python 3.7+  
- Bibliotecas: `boto3`, `botocore`  
Instale com:  
```bash
pip install -r requirements.txt

## 📚 Explicação dos Arquivos
idle_ip_cleaner.py: script principal com as funções de listagem e liberação dos Elastic IPs ociosos  
requirements.txt: dependências Python necessárias (boto3)  
LICENSE: licença do projeto (MIT)  
README.md: este arquivo que você está lendo

## 🧠 Conceitos Utilizados
Elastic IP Management – uso do método describe_addresses para identificar IPs e release_address para liberar recursos  
FinOps Ready – automação para reduzir custos com IPs elásticos ociosos  
Tratamento de Erros – captura de exceções usando botocore.exceptions.ClientError  
Execução Serverless – integração com AWS Lambda para execução automática e escalável

## 📝 Licença
Distribuído sob a licença MIT. Veja LICENSE para mais informações.

## 🤝 Contribuição
Quer contribuir? Faça um fork ou entre em contato comigo!

Feito pelo IlustreDev para ajudar na jornada FinOps!