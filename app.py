from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import os
import torch
from torchvision import transforms
from PIL import Image
import numpy as np

# Inicjalizacja aplikacji Flask
app = Flask(__name__)
app.secret_key = 'some_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'  # Folder do przesyłania plików
db = SQLAlchemy(app)

# Ładowanie modelu PyTorch
model = torch.load('models/covid_model.pth')
model.eval()  # Ustawienie modelu w tryb ewaluacji

# Definicja modelu User
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# Inicjalizacja bazy danych
with app.app_context():
    db.create_all()

# Strona główna z logowaniem
@app.route('/')
def home():
    return render_template('home.html')

# Strona logowania
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            return redirect(url_for('diagnosis'))
        else:
            flash('Nie ma takiego użytkownika!')
            return redirect(url_for('login'))

    return render_template('login.html')

# Strona diagnozy z możliwością przesyłania obrazu
@app.route('/diagnosis', methods=['GET', 'POST'])
def diagnosis():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Brak pliku!')
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            flash('Nie wybrano pliku!')
            return redirect(request.url)

        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Przetwarzanie obrazu
            img = Image.open(filepath).convert('RGB')
            transform = transforms.Compose([
                transforms.Resize((224, 224)),  # Dopasowanie do rozmiaru modelu
                transforms.ToTensor(),
                transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
            ])
            img_tensor = transform(img).unsqueeze(0)  # Dodanie wymiaru wsadowego

            # Predykcja
            with torch.no_grad():
                output = model(img_tensor)
                _, predicted = torch.max(output, 1)

            if predicted.item() == 1:  # Zakładamy, że 1 oznacza brak COVID
                result = 'Nie masz COVID! (Normal)'
            else:
                result = 'Masz COVID!'

            # Przekazujemy nazwę pliku do strony wyników
            return render_template('diagnosis_result.html', result=result, uploaded_image=filename)

    return render_template('diagnosis.html')

# Wyświetlanie załadowanego obrazu w widoku wyników diagnozy
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Uruchomienie aplikacji
if __name__ == '__main__':
    # Tworzymy folder 'uploads', jeśli nie istnieje
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)
