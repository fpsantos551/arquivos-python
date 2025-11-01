# Dockerfile para a API de Processamento de PDF (FastAPI)

# Usar uma imagem base Python otimizada para aplicações web
FROM python:3.11-slim

# Definir o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copiar o arquivo de requisitos e instalar as dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o código da aplicação
COPY app.py .

# Expor a porta que o Uvicorn irá usar
EXPOSE 8000

# Comando para iniciar a aplicação com Uvicorn
# --host 0.0.0.0 é necessário para que o contêiner seja acessível externamente
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
