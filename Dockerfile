# Utilisation d'une image Python
FROM python:3.9

# Dossier de travail
WORKDIR /app

# Copier les fichiers nécessaires
COPY requirements.txt requirements.txt

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Copier le contenu du projet dans le conteneur
COPY . .

# Exécuter le script principal
CMD ["python", "main.py"]
