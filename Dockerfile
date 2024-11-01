# Use uma imagem base oficial do Python
FROM python:3.9-slim

# Defina o diretório de trabalho
WORKDIR /app

# Copie o arquivo de requisitos e instale as dependências
COPY requirements_api.txt .
RUN pip install --no-cache-dir -r requirements_api.txt

# Copie o restante do código da aplicação
COPY . .

# Exponha a porta que o FastAPI usará
EXPOSE 5001

# Defina a variável de ambiente para desativar o buffer de saída do Python
ENV PYTHONUNBUFFERED=1

# Comando para iniciar o servidor FastAPI
CMD ["uvicorn", "service:app", "--reload", "--port", "5001", "--host", "0.0.0.0"]