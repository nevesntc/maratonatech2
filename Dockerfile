# Use a imagem base do Python
FROM python:3.11-slim

# Defina o diretório de trabalho
WORKDIR /app

# Copie o arquivo requirements.txt para dentro do contêiner
COPY requirements.txt .

# Instale as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copie o restante do código para dentro do contêiner
COPY . .

# Exponha a porta que o Flask vai usar
EXPOSE 5000

# Defina a variável de ambiente para o Flask
ENV FLASK_APP=app/app.py
ENV FLASK_RUN_HOST=0.0.0.0

# Comando para iniciar o Flask
CMD ["flask", "run"]
