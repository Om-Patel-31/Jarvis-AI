import os
import sys
import asyncio
import pygame
import random
import mtranslate as mt
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from groq import Groq
from json import load, dump
import datetime
from dotenv import dotenv_values
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QStackedWidget, QWidget, QLineEdit, QGridLayout, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QLabel, QSizePolicy
from PyQt5.QtGui import QIcon, QPainter, QMovie, QColor, QTextCharFormat, QFont, QPixmap, QTextBlockFormat
from PyQt5.QtCore import Qt, QSize, QTimer
import edge_tts

# Load environment variables
env_vars = dotenv_values(".env")
Username = env_vars.get("Username")
AssistantName = env_vars.get("AssistantName")
GroqAPIKey = env_vars.get("GroqAPIKey")
InputLanguage = env_vars.get("InputLanguage")
AssistantVoice = env_vars.get("AssistantVoice")

# Initialize paths
current_dir = os.getcwd()
TempDirPath = rf"{current_dir}\Frontend\Files"
GraphicsDirPath = rf"{current_dir}\Frontend\Graphics"
old_chat_message = ""

# Initialize Groq client
client = Groq(api_key=GroqAPIKey)
messages = []

# System prompt for the chatbot
System = f"""Hello, I am {Username}, You are a very accurate and advanced AI chatbot named {AssistantName} which also has real-time up-to-date information from the internet.
*** Do not tell time until I ask, do not talk too much, just answer the question.***
*** Reply in only English, even if the question is in Hindi, reply in English.***
*** Do not provide notes in the output, just answer the question and never mention your training data. ***
"""

SystemChatBot = [
    {"role": "system", "content": System}
]

# Initialize chat log
try:
    with open(r"Data\ChatLog.json", "r") as f:
        messages = load(f)
except:
    with open(r"Data\ChatLog.json", "w") as f:
        dump([], f)

# Speech recognition HTML
HtmlCode = '''<!DOCTYPE html>
<html lang="en">
<head>
    <title>Speech Recognition</title>
</head>
<body>
    <button id="start" onclick="startRecognition()">Start Recognition</button>
    <button id="end" onclick="stopRecognition()">Stop Recognition</button>
    <p id="output"></p>
    <script>
        const output = document.getElementById('output');
        let recognition;

        function startRecognition() {
            recognition = new webkitSpeechRecognition() || new SpeechRecognition();
            recognition.lang = '';
            recognition.continuous = true;

            recognition.onresult = function(event) {
                const transcript = event.results[event.results.length - 1][0].transcript;
                output.textContent += transcript;
            };

            recognition.onend = function() {
                recognition.start();
            };
            recognition.start();
        }

        function stopRecognition() {
            recognition.stop();
            output.innerHTML = "";
        }
    </script>
</body>
</html>'''

HtmlCode = str(HtmlCode).replace("recognition.lang = '';", f"recognition.lang = '{InputLanguage}';")

with open(r"Data\Voice.html", "w") as file:
    file.write(HtmlCode)

Link = f"{current_dir}/Data/Voice.html"

# Initialize Chrome options
chrome_options = Options()
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.142.86 Safari/537.36"
chrome_options.add_argument(f"user-agent={user_agent}")
chrome_options.add_argument("--use-fake-ui-for-media-stream")
chrome_options.add_argument("--use-fake-device-for-media-stream")
chrome_options.add_argument("--headless=new")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# Backend Functions
def RealtimeInformation():
    current_data_time = datetime.datetime.now()
    day = current_data_time.strftime("%A")
    date = current_data_time.strftime("%d")
    month = current_data_time.strftime("%B")
    year = current_data_time.strftime("%Y")
    hour = current_data_time.strftime("%H")
    minute = current_data_time.strftime("%M")
    second = current_data_time.strftime("%S")

    data = f"Please use this real-time information if needed, \n"
    data += f"Day: {day}\nDate: {date}\nMonth: {month}\nYear: {year}\n"
    data += f"Time: {hour} hours :{minute} minutes :{second} seconds.\n"
    return data

def AnswerModifier(Answer):
    lines = Answer.split("\n")
    non_empty_lines = [line for line in lines if line.strip()]
    modified_answer = "\n".join(non_empty_lines)
    return modified_answer

def ChatBot(Query):
    try:
        with open(r"Data\ChatLog.json", "r") as f:
            messages = load(f)
            
        messages.append({"role": "user", "content": f"{Query}"})
        
        completion = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=SystemChatBot + [{"role": "user", "content": RealtimeInformation()}] + messages,
            max_tokens=1024,
            temperature=0.7,
            top_p=1,
            stream=True,
            stop=None
        )
        
        Answer = ""
        
        for chunk in completion:
            if chunk.choices[0].delta.content:
                Answer += chunk.choices[0].delta.content
                
        Answer = Answer.replace("</s>", "")
        
        messages.append({"role": "assistant", "content": Answer})
        
        with open(r"Data\ChatLog.json", "w") as f:
            dump(messages, f, indent=4)
        
        return AnswerModifier(Answer=Answer)
    
    except Exception as e:
        print(f"Error: {e}")
        with open(r"Data\ChatLog.json", "w") as f:
            dump([], f, indent=4)
        return ChatBot(Query)

def SetAssistantStatus(Status):
    with open(rf'{TempDirPath}/Status.data', "w", encoding='utf-8') as file:
        file.write(Status)

def QueryModified(Query):
    new_query = Query.lower().strip()
    query_words = new_query.split()
    question_words = ["how", "what", "who", "where", "when", "why", "which", "whom", "whose", "can you", "what's", "who's", "where's", "when's", "why's", "which's", "whom's", "whose's"]
    
    if any(word + " " in new_query for word in question_words):
        if query_words[-1][-1] in ['.', '?', '!']:
            new_query = new_query[:-1] + "."
        else:
            new_query += "."
    
    return new_query.capitalize()

def UniversalTranslator(Text):
    english_translation = mt.translate(Text, "en", "auto")
    return english_translation.capitalize()

def SpeechRecognition():
    driver.get("file:///" + Link)
    driver.find_element(by=By.ID, value="start").click()
    
    while True:
        try:
            Text = driver.find_element(by=By.ID, value="output").text
            
            if Text:
                driver.find_element(by=By.ID, value="end").click()
                
                if InputLanguage.lower() == "en" or "en" in InputLanguage.lower():
                    return QueryModified(Text)
                else:
                    SetAssistantStatus("Translating...")
                    return QueryModified(UniversalTranslator(Text))
        
        except Exception as e:
            pass

async def TexttoAudioFile(text) -> None:
    file_path = r"Data\Speech.mp3"
    
    if os.path.exists(file_path):
        os.remove(file_path)
    
    communicate = edge_tts.Communicate(text, AssistantVoice, pitch='-15Hz', rate='+15%')
    await communicate.save(r'Data\Speech.mp3')
    
def TTS(Text, func=lambda r=None: True):
    while True:
        try:
            asyncio.run(TexttoAudioFile(Text))
            pygame.mixer.init()
            pygame.mixer.music.load(r"Data\Speech.mp3")
            pygame.mixer.music.play()
            
            while pygame.mixer.music.get_busy():
                if func() == False:
                    break
                pygame.time.Clock().tick(10)
    
            return True

        except Exception as e:
            print(f"Error in TTS: {e}")
            
        finally:
            try:
                func(False)
                pygame.mixer.music.stop()
                pygame.mixer.quit()
            
            except Exception as e:
                print(f"Error in finally block: {e}")
                
def TextToSpeech(Text, func=lambda r=None: True):
    Data = str(Text).split('.')
    
    responses = [
        "The rest of the result has been printed to the chat screen, kindly check it out sir.",
        "The rest of the text is now on the chat screen, sir, please check it.",
        "You can see the rest of the text on the chat screen, sir.",
        "The remaining part of the text is now on the chat screen, sir.",
        "Sir, you'll find more text on the chat screen for you to see.",
        "The rest of the answer is now on the chat screen, sir.",
        "Sir, please look at the chat screen, the rest of the answer is there.",
        "You'll find the complete answer on the chat screen, sir.",
        "The next part of the text is on the chat screen, sir.",
        "Sir, please check the chat screen for more information.",
        "There's more text on the chat screen for you, sir.",
        "Sir, take a look at the chat screen for additional text.",
        "You'll find more to read on the chat screen, sir.",
        "Sir, check the chat screen for the rest of the text.",
        "The chat screen has the rest of the text, sir.",
        "There's more to see on the chat screen, sir, please look.",
        "Sir, the chat screen holds the continuation of the text.",
        "You'll find the complete answer on the chat screen, kindly check it out sir.",
        "Please review the chat screen for the rest of the text, sir.",
        "Sir, look at the chat screen for the complete answer."
    ]
    
    if len(Data) > 4 and len(Text) >= 250:
        TTS(" ".join(Text.split('.')[0:2]) + ". " + random.choice(responses), func)
    
    else:
        TTS(Text, func)

# Frontend Classes
class ChatSelection(QWidget):
    def __init__(self):
        super(ChatSelection, self).__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(-10, 40, 40, 100)
        layout.setSpacing(-100)
        self.chat_text_edit = QTextEdit()
        self.chat_text_edit.setReadOnly(True)
        self.chat_text_edit.setTextInteractionFlags(Qt.NoTextInteraction)
        layout.addWidget(self.chat_text_edit)
        self.setStyleSheet("background-color: black;")
        layout.setSizeConstraint(QVBoxLayout.SetDefaultConstraint)
        layout.setStretch(1, 1)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))
        text_color = QColor(Qt.blue)
        text_color_text = QTextCharFormat()
        text_color_text.setForeground(text_color)
        self.chat_text_edit.setCurrentCharFormat(text_color_text)
        self.gif_label = QLabel()
        self.gif_label.setStyleSheet("border: none;")
        movie = QMovie(rf"{GraphicsDirPath}/Jarvis.gif")
        max_gif_size_W = 480
        max_gif_size_H = 270
        movie.setScaledSize(QSize(max_gif_size_W, max_gif_size_H))
        self.gif_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        self.gif_label.setMovie(movie)
        movie.start()
        layout.addWidget(self.gif_label)
        self.label = QLabel("")
        self.label.setStyleSheet("color: white; font-size: 16px; margin-right: 195px; border:none;  margin-top: -30px;")
        self.label.setAlignment(Qt.AlignRight)
        layout.addWidget(self.label)
        layout.setSpacing(-10)
        layout.addWidget(self.gif_label)
        font = QFont()
        font.setPointSize(13)
        self.chat_text_edit.setFont(font)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.SpeechRecogText)
        self.timer.start(5)
        self.chat_text_edit.viewport().installEventFilter(self)
        self.setStyleSheet("""
                            QScrollBar:vertical {
                               border: none;
                               background: black;
                               width: 10px;
                               margin: 0px 0px 0px 0px;
                           }
                           
                           QScrollBar::handle:vertical {
                               background: white;
                               min-height: 20px;
                           }
                           
                           QScrollBar::add-line:vertical {
                               background: black;
                               height: 10px;
                               subcontrol-position: bottom;
                               subcontrol-origin: margin;
                           }
                           
                           QScrollBar::sub-line:vertical {
                               background: black;
                               height: 10px;
                               subcontrol-position: top;
                               subcontrol-origin: margin;
                           }
                           
                           QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {
                               border: none;
                               background: none;
                               color: none;
                           }
                           
                           QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                               background: none;
                            }
                            """)

    def SpeechRecogText(self):
        with open(rf'{TempDirPath}/Status.data', "r", encoding='utf-8') as file:
            messages = file.read()
            self.label.setText(messages)

    def loadMessages(self):
        global old_chat_message
        
        with open(rf'{TempDirPath}/Responses.data', 'r', encoding='utf-8') as file:
            messages = file.read()
            
            if None == messages:
                pass
            
            elif len(messages) <= 1:
                pass
            
            elif str(old_chat_message) == str(messages):
                pass
            
            else:
                self.addMessage(message=messages, color='White')
                old_chat_message = messages
            
    def load_icons(self, path, width=60, height=60):
        pixmap = QPixmap(path)
        new_pixmap = pixmap.scaled(width, height)
        self.icon_label.setPixmap(new_pixmap)
        
    def toggle_icon(self, event=None):
        if self.toggled:
            self.load_icons(rf"{GraphicsDirPath}/voice.png", 60, 60)
            SetMicrophoneStatus("False")
        
        else:
            self.load_icons(rf"{GraphicsDirPath}/mic.png", 60, 60)
            SetMicrophoneStatus("True")
            
        self.toggled = not self.toggled
        
    def addMessage(self, message, color):
        cursor = self.chat_text_edit.textCursor()
        format = QTextCharFormat()
        formatm = QTextBlockFormat()
        formatm.setTopMargin(10)
        formatm.setLeftMargin(10)
        format.setForeground(QColor(color))
        cursor.setCharFormat(format)
        cursor.setBlockFormat(formatm)
        cursor.insertText(message + "\n")
        self.chat_text_edit.setTextCursor(cursor)

class InitialScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        desktop = QApplication.desktop()
        screen_width = desktop.screenGeometry().width()
        screen_height = desktop.screenGeometry().height()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0,0,0,0)
        gif_label = QLabel()
        movie = QMovie(rf"{GraphicsDirPath}/Jarvis.gif")
        gif_label.setMovie(movie)
        max_gif_size_H = int(screen_width / 16 * 9)
        movie.setScaledSize(QSize(screen_width, max_gif_size_H))
        gif_label.setAlignment(Qt.AlignCenter)
        movie.start()
        gif_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.icon_label = QLabel()
        pixmap = QPixmap(rf"{GraphicsDirPath}/Mic_on.png")
        new_pixmap = pixmap.scaled(60, 60)
        self.icon_label.setPixmap(new_pixmap)
        self.icon_label.setFixedSize(150,150)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.toggled = True
        self.toggle_icon()
        self.icon_label.mousePressEvent = self.toggle_icon
        self.label = QLabel("")
        self.label.setStyleSheet("color:white; font-size:16px; margin-bottom:0;")
        content_layout.addWidget(gif_label, alignment=Qt.AlignCenter)
        content_layout.addWidget(self.label, alignment=Qt.AlignCenter)
        content_layout.addWidget(self.icon_label, alignment=Qt.AlignCenter)
        content_layout.setContentsMargins(0, 0, 0, 150)
        self.setLayout(content_layout)
        self.setFixedHeight(screen_height)
        self.setFixedWidth(screen_width)
        self.setStyleSheet("background-color: black")
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.SpeechRecogText)
        self.timer.start(5)
        
    def SpeechRecogText(self):
        with open(rf'{TempDirPath}/Status.data', 'r', encoding='utf-8') as file:
            messages = file.read()
            self.label.setText(messages)
            
    def load_icons(self, path, width=60, height=60):
        pixmap = QPixmap(path)
        new_pixmap = pixmap.scaled(width, height)
        self.icon_label.setPixmap(new_pixmap)
        
    def toggle_icon(self, event=None):
        if self.toggled:
            self.load_icons(rf"{GraphicsDirPath}/Mic_on.png", 60, 60)
            SetMicrophoneStatus("False")
        
        else:
            self.load_icons(rf"{GraphicsDirPath}/Mic_off.png", 60, 60)
            SetMicrophoneStatus("True")
        
        self.toggled = not self.toggled

class MessageScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        desktop = QApplication.desktop()
        screen_width = desktop.screenGeometry().width()
        screen_height = desktop.screenGeometry().height()
        layout = QVBoxLayout()
        label = QLabel("")
        layout.addWidget(label)
        chat_selection = ChatSelection()
        layout.addWidget(chat_selection)
        self.setLayout(layout)
        self.setStyleSheet("background-color: black;")
        self.setFixedHeight(screen_height)
        self.setFixedWidth(screen_width)

class CustomTopBar(QWidget):
    def __init__(self, parent, stacked_widget):
        super().__init__(parent)
        self.initUI()
        self.current_screen = None
        self.stacked_widget = stacked_widget
    
    def initUI(self):
        self.setFixedHeight(50)
        layout = QHBoxLayout(self)
        layout.setAlignment(Qt.AlignRight)
        
        # Home button
        home_button = QPushButton()
        home_icon = QIcon(rf"{GraphicsDirPath}/Home.png")
        home_button.setIcon(home_icon)
        home_button.setText("  Home")
        home_button.setStyleSheet("height:40px; line-height:40px; background-color:white; color:black")
        home_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        
        # Chat button
        message_button = QPushButton()
        message_icon = QIcon(rf"{GraphicsDirPath}/Chats.png")
        message_button.setIcon(message_icon)
        message_button.setText("  Chat")
        message_button.setStyleSheet("height: 40px; line-height: 40px; background-color:white; color:black")
        message_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        
        # Settings button
        settings_button = QPushButton()
        settings_icon = QIcon(rf"{GraphicsDirPath}/Settings.png")
        settings_button.setIcon(settings_icon)
        settings_button.setText("  Settings")
        settings_button.setStyleSheet("height: 40px; line-height: 40px; background-color:white; color:black")
        
        # Window control buttons
        minimize_button = QPushButton()
        minimize_icon = QIcon(rf"{GraphicsDirPath}/Minimize2.png")
        minimize_button.setIcon(minimize_icon)
        minimize_button.setStyleSheet("background-color:white")
        minimize_button.clicked.connect(self.minimizeWindow)
        
        self.maximize_button = QPushButton()
        self.maximize_icon = QIcon(rf"{GraphicsDirPath}/Maximize.png")
        self.minimize_icon = QIcon(rf"{GraphicsDirPath}/Minimize.png")
        self.maximize_button.setIcon(self.maximize_icon)
        minimize_button.setFlat(True)
        self.maximize_button.setStyleSheet("background-color:white")
        self.maximize_button.clicked.connect(self.maximizeWindow)
        
        close_button = QPushButton()
        close_icon = QIcon(rf"{GraphicsDirPath}/Close.png")
        close_button.setIcon(close_icon)
        close_button.setStyleSheet("background-color:white")
        close_button.clicked.connect(self.closeWindow)
        
        # Separator line
        line_frame = QFrame()
        line_frame.setFixedHeight(1)
        line_frame.setFrameShape(QFrame.HLine)
        line_frame.setFrameShadow(QFrame.Sunken)
        line_frame.setStyleSheet("border-color: black;")
        
        # Title label
        title_label = QLabel(f" {str(AssistantName).capitalize()} AI   ")
        title_label.setStyleSheet("color: black; font-size: 18px; background-color:white")
        
        # Add widgets to layout
        layout.addWidget(title_label)
        layout.addStretch(1)
        layout.addWidget(home_button)
        layout.addWidget(message_button)
        layout.addWidget(settings_button)
        layout.addWidget(minimize_button)
        layout.addWidget(self.maximize_button)
        layout.addWidget(close_button)
        layout.addWidget(line_frame)
        
        self.draggable = True
        self.offset = None
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.white)
        super().paintEvent(event)
    
    def minimizeWindow(self):
        self.parent().showMinimized()
        
    def maximizeWindow(self):
        if self.parent().isMaximized():
            self.parent().showNormal()
            self.maximize_button.setIcon(self.maximize_icon)
        else:
            self.parent().showMaximized()
            self.maximize_button.setIcon(self.restore_icon)
            
    def closeWindow(self):
        self.parent().close()
    
    def mousePressEvent(self, event):
        if self.draggable:
            self.offset = event.pos()
        
    def mouseMoveEvent(self, event):
        if self.draggable and self.offset:
            new_pos = event.globalPos() - self.offset
            self.parent().move(new_pos)
    
    def showMessageScreen(self):
        if self.current_screen is not None:
            self.current_screen.hide()
            
        message_screen = MessageScreen(self)
        layout = self.parent().layout()
        if layout is not None:
            layout.addWidget(message_screen)
        self.current_screen = message_screen

    def showInitialScreen(self):
        if self.current_screen is not None:
            self.current_screen.hide()
        
        initial_screen = InitialScreen(self)
        layout = self.parent().layout()
        if layout is not None:
            layout.addWidget(initial_screen)
        self.current_screen = initial_screen

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.initUI()
    
    def initUI(self):
        desktop = QApplication.desktop()
        screen_width = desktop.screenGeometry().width()
        screen_height = desktop.screenGeometry().height()
        stacked_widget = QStackedWidget(self)
        initial_screen = InitialScreen()
        message_screen = MessageScreen()
        stacked_widget.addWidget(initial_screen)
        stacked_widget.addWidget(message_screen)
        self.setGeometry(0, 0, screen_width, screen_height)
        self.setStyleSheet("background-color: black;")
        top_bar = CustomTopBar(self, stacked_widget)
        self.setMenuWidget(top_bar)
        self.setCentralWidget(stacked_widget)

def SetMicrophoneStatus(Command):
    with open(rf"{TempDirPath}/Mic.data", "w", encoding='utf-8') as file:
        file.write(Command)
        
def GetMicrophoneStatus():
    with open(rf"{TempDirPath}/Mic.data", "r", encoding='utf-8') as file:
        Status = file.read()
    return Status

def ShowTextToScreen(Text):
    with open(rf'{TempDirPath}/Responses.data', "w", encoding='utf-8') as file:
        file.write(Text)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    
    # Create a timer for processing speech and responses
    def process_loop():
        try:
            if GetMicrophoneStatus() == "True":
                SetAssistantStatus("Listening...")
                Query = SpeechRecognition()
                if Query:
                    SetAssistantStatus("Processing...")
                    Answer = ChatBot(Query)
                    ShowTextToScreen(Answer)
                    TextToSpeech(Answer)
                    SetAssistantStatus("")
                    SetMicrophoneStatus("False")
        except Exception as e:
            print(f"Error in process loop: {e}")
            SetMicrophoneStatus("False")
            SetAssistantStatus("")
    
    # Create a timer that runs every 100ms to check for speech input
    process_timer = QTimer()
    process_timer.timeout.connect(process_loop)
    process_timer.start(100)
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
