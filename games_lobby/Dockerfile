# Imagem base oficial do Python
FROM python:3.10-slim

# Define o diretório de trabalho
WORKDIR /app

# Copia o arquivo requirements.txt contendo as dependências
COPY requirements.txt .

# Instala as dependências do projeto
RUN pip install --no-cache-dir -r requirements.txt

# Copia os arquivos da aplicação para o diretório de trabalho
COPY . .

# Expondo a porta do serviço
EXPOSE 9002

# Comando para iniciar a aplicação
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "9002", "--reload"]
