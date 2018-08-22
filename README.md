# python-flask_quandl_stock-tracker

## Pre-requisitos:
  * Credenciais da API Quandl (serviço gratuito)
  * Todas dependências em `required.txt` são instaladas automaticamente pela VM instanciada na IBM Cloud
  
## Rodando na IBM Cloud
#### Para instanciar a aplicação basta seguir os passos abaixo:
  
  * Copiar o repositório para a sua máquina
  * Editar as configurações desejadas para a sua instância do app no arquivo `manifest.yml`
  * Editar a sua credencial da API Quandl no arquivo `run.py` (linhas 36 e 167)
  * Simplesmente fazer upload da aplicação utilizando o seguinte comando na IBM CLI (após login): `bluemix app push <app_name>`
