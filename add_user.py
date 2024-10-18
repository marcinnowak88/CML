from app import db, User, app
from werkzeug.security import generate_password_hash

# Funkcja do dodania nowego użytkownika
def add_user(username, password):
    # Sprawdzenie, czy użytkownik już istnieje
    if User.query.filter_by(username=username).first():
        print(f'Użytkownik {username} już istnieje.')
        return

    # Hashowanie hasła za pomocą domyślnej metody Werkzeug
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

    # Stworzenie nowego użytkownika
    new_user = User(username=username, password=hashed_password)

    # Dodanie użytkownika do bazy danych
    db.session.add(new_user)
    db.session.commit()

    print(f'Użytkownik {username} został dodany.')

# Główna funkcja skryptu
if __name__ == '__main__':
    # Uruchomienie kontekstu aplikacji Flask
    with app.app_context():
        # Pobieranie danych użytkownika z terminala
        username = input("Podaj nazwę użytkownika: ")
        password = input("Podaj hasło: ")
        add_user(username, password)

