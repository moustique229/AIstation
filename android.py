import toga
from toga.style import Pack
from toga.style.pack import COLUMN, CENTER
import speech_recognition as sr
import pyttsx3 as ttx
import pywhatkit
import datetime
import requests
import wave
import io
import sounddevice as sd

# Clé API Google Places (remplacez par votre propre clé API)
API_KEY = "VOTRE_CLE_API_GOOGLE"

# Initialisation de la reconnaissance vocale et du moteur de synthèse vocale
listener = sr.Recognizer()
engine = ttx.init()

# Paramètres de la voix
voices = engine.getProperty('voices')
female_voice_found = False
for voice in voices:
    if 'female' in voice.name.lower() or 'feminin' in voice.name.lower():
        engine.setProperty('voice', voice.id)
        female_voice_found = True
        break

if not female_voice_found:
    engine.setProperty('voice', voices[0].id)

def parler(text):
    """Faire parler l'assistante"""
    engine.say(text)
    engine.runAndWait()

def ecouter():
    """Écouter la commande de l'utilisateur et la transcrire en texte"""
    try:
        # Enregistrement de l'audio
        audio_data = sd.rec(int(5 * 16000), samplerate=16000, channels=1, dtype='int16')
        sd.wait()

        # Conversion de l'audio en fichier .wav
        audio_file = io.BytesIO()
        with wave.open(audio_file, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(audio_data.tobytes())

        audio_file.seek(0)

        # Reconnaissance vocale
        audio = sr.AudioFile(audio_file)
        with audio as source:
            audio_data = listener.record(source)
        command = listener.recognize_google(audio_data, language='fr-FR')
        return command.lower()
    except sr.UnknownValueError:
        parler("Je n'ai pas pu comprendre ce que vous avez dit.")
    except sr.RequestError:
        parler("Erreur de connexion à Google.")
    return ""

def rechercher_musique(musique):
    """Rechercher de la musique sur YouTube via pywhatkit"""
    pywhatkit.playonyt(musique)

def recherche_lieu(lieu):
    """Rechercher un lieu via Google Places API"""
    url = f"https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {'query': lieu, 'key': API_KEY}
    response = requests.get(url, params=params)
    results = response.json().get('results', [])
    if results:
        place = results[0]
        name = place['name']
        address = place.get('formatted_address', 'Adresse non disponible')
        parler(f"Voici les informations sur {name}: {address}")
    else:
        parler("Lieu non trouvé.")

class AssistantVocalApp(toga.App):
    def startup(self):
        # Création du conteneur principal
        self.main_box = toga.Box(style=Pack(direction=COLUMN, alignment=CENTER, padding=10))

        # Texte d'état
        self.label_reponse = toga.Label("Assistant prêt à écouter...", style=Pack(padding=(10, 20)))
        self.main_box.add(self.label_reponse)

        # Chargement de l'image du microphone
        try:
            mic_image = toga.Image("icone.png")  # Assurez-vous que "microphone.png" est dans le même dossier
        except Exception as e:
            print(f"Erreur lors du chargement de l'image : {e}")
            mic_image = None  # En cas d'erreur, le bouton n'aura pas d'icône

        # Bouton d'écoute avec l'image du microphone
        mic_button = toga.Button(
            icon=mic_image,  # Utilisation de l'image
            on_press=self.lancer_assistant,
            style=Pack(width=100, height=100, padding=10)
        )
        self.main_box.add(mic_button)

        # Création de la fenêtre principale
        self.main_window = toga.MainWindow(title=self.name)
        self.main_window.content = self.main_box
        self.main_window.show()

    def lancer_assistant(self, widget):
        """Lancer l'assistant et analyser la commande"""
        command = ecouter()
        if command:
            if 'mets la chanson de' in command:
                chanteur = command.replace('mets la chanson de', '').strip()
                rechercher_musique(chanteur)
                self.label_reponse.text = f"Lecture de la chanson de {chanteur}."
            elif 'heure' in command:
                heure = datetime.datetime.now().strftime('%H:%M')
                parler(f"Il est {heure}")
                self.label_reponse.text = f"L'heure actuelle est {heure}."
            elif 'bonjour' in command:
                parler('Bonjour, comment puis-je vous aider ?')
                self.label_reponse.text = "Bonjour, comment puis-je vous aider ?"
            elif 'cherche' in command and 'lieu' in command:
                lieu = command.replace('cherche', '').replace('lieu', '').strip()
                recherche_lieu(lieu)
                self.label_reponse.text = f"Recherche d'informations sur {lieu}."
            else:
                self.label_reponse.text = "Je n'ai pas compris votre commande."
        else:
            self.label_reponse.text = "Je n'ai pas pu entendre de commande."

def main():
    return AssistantVocalApp("Assistant Vocal", "org.example.assistantvocal")

if __name__ == "__main__":
    main().main_loop()
