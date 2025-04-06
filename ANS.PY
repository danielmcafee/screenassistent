import tkinter as tk
import pyautogui
import pytesseract
import keyboard
import os
import time
from PIL import Image
from dotenv import load_dotenv
from openai import OpenAI

# 🔹 Carregar variáveis de ambiente
load_dotenv()

# 🔹 Obter chave da OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 🔹 Configuração do Tesseract OCR (ajuste conforme necessário)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
os.environ["TESSDATA_PREFIX"] = r"C:\Program Files\Tesseract-OCR\tessdata"

class ScreenCaptureApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.3)  # Janela transparente
        self.root.config(cursor="cross")
        self.root.focus_force()
        self.root.grab_set()

        self.start_x = None
        self.start_y = None
        self.rect_id = None

        self.canvas = tk.Canvas(self.root, bg="black", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

    def on_press(self, event):
        self.start_x, self.start_y = event.x, event.y
        self.rect_id = self.canvas.create_rectangle(self.start_x, self.start_y, event.x, event.y, outline="red", width=2)

    def on_drag(self, event):
        self.canvas.coords(self.rect_id, self.start_x, self.start_y, event.x, event.y)

    def on_release(self, event):
        self.root.destroy()
        x1, y1 = self.start_x, self.start_y
        x2, y2 = event.x, event.y
        self.capture_screen(x1, y1, x2, y2)

    def capture_screen(self, x1, y1, x2, y2):
        time.sleep(0.2)
        region = (min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))
        screenshot = pyautogui.screenshot(region=region)
        screenshot.save("captura.png")

        # 🔹 Extrair texto da imagem
        texto = pytesseract.image_to_string(Image.open("captura.png"), lang="por")
        print("\n📜 Texto extraído:\n", texto)

        if texto.strip():
            resposta = enviar_para_chatgpt(texto)
            print("\n🤖 Resposta da IA:\n", resposta)
            mostrar_resultado(resposta)
        else:
            print("\n⚠️ Nenhum texto foi reconhecido.")
            mostrar_resultado("Nenhum texto foi reconhecido.")

def enviar_para_chatgpt(prompt):
    """ Envia o texto extraído para a API da OpenAI e retorna a resposta. """
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Seja o mais breve possível em sua resposta. Apenas selecione uma alternativa ou uma sequência de Verdadeiros e Falsos."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print("Erro ao gerar resposta:", e)
        return "Erro ao gerar resposta."

def mostrar_resultado(resposta_ia):
    """ Função para exibir o resultado da IA em uma nova janela """
    result_window = tk.Tk()
    result_window.title("Resultado da IA")
    result_window.geometry("500x200+100+100")

    resultado_label = tk.Label(result_window, text=resposta_ia, fg="white", bg="black", font=("Arial", 10), wraplength=480, anchor="w", justify="left")
    resultado_label.pack(fill=tk.X, padx=10, pady=10)

    result_window.after(20000, result_window.destroy)
    result_window.attributes("-topmost", True)
    result_window.mainloop()

def capturar_texto():
    app = ScreenCaptureApp()
    app.root.mainloop()

# 🔹 Atalho para iniciar captura
print("🔥 Pressione 'CTRL + ALT + SHIFT + Print Screen' para capturar a tela. Pressione 'ESC' para sair.")

while True:
    if keyboard.is_pressed("ctrl+alt+shift+print_screen"):
        capturar_texto()
        time.sleep(1)

    if keyboard.is_pressed("esc"):
        print("🚪 Saindo do programa...")
        break
