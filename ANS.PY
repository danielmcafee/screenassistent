import tkinter as tk
import pyautogui
import requests
import keyboard
import os
import time
import pyperclip  # Novo para copiar texto
from PIL import Image
from dotenv import load_dotenv
from openai import OpenAI

# 🔹 Carregar variáveis de ambiente
load_dotenv()

# 🔹 Configurar APIs
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
ocr_space_api_key = os.getenv("OCR_SPACE_API_KEY")

class ScreenCaptureApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.attributes("-fullscreen", True, "-topmost", True, "-alpha", 0.3)
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
        screenshot_path = "captura.png"
        screenshot.save(screenshot_path)

        texto = ocr_space_image(screenshot_path, ocr_space_api_key)
        os.remove(screenshot_path)  # Apaga a imagem depois do OCR

        print("\n📜 Texto extraído:\n", texto)

        if texto.strip():
            resposta = enviar_para_chatgpt(texto)
            print("\n🤖 Resposta da IA:\n", resposta)
            mostrar_resultado(resposta)
        else:
            print("\n⚠️ Nenhum texto foi reconhecido.")
            mostrar_resultado("Nenhum texto foi reconhecido.")

def ocr_space_image(filename, api_key):
    """ Envia imagem para OCR.Space API e retorna o texto reconhecido. """
    try:
        with open(filename, 'rb') as f:
            response = requests.post(
                'https://api.ocr.space/parse/image',
                files={'filename': f},
                data={
                    'apikey': api_key,
                    'language': 'por',  # Português
                    'isOverlayRequired': False
                }
            )
        result = response.json()
        if result.get("IsErroredOnProcessing"):
            return f"Erro no OCR: {result.get('ErrorMessage', 'Erro desconhecido')}"
        else:
            parsed_results = result.get("ParsedResults", [])
            if parsed_results:
                return parsed_results[0].get("ParsedText", "").strip()
            else:
                return "Nenhum texto detectado."
    except Exception as e:
        return f"Erro ao usar OCR.Space: {str(e)}"

def enviar_para_chatgpt(texto_extraido):
    """ Envia o texto extraído para a OpenAI e retorna a resposta. """
    try:
        prompt = f"{texto_extraido}\n\nInstrução: Responda de forma breve, indicando apenas a alternativa correta ou a sequência de V/F."
        completion = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        return f"Erro ao conectar com a API da OpenAI: {str(e)}"

def mostrar_resultado(resposta_ia):
    """ Exibe a resposta da IA em uma nova janela e copia para área de transferência """
    pyperclip.copy(resposta_ia)  # Copia automaticamente para o clipboard

    result_window = tk.Tk()
    result_window.title("Resultado da IA")
    result_window.geometry("500x200+100+100")
    result_window.attributes("-topmost", True)

    resultado_label = tk.Label(result_window, text=resposta_ia, fg="white", bg="black", font=("Arial", 10), wraplength=480, anchor="w", justify="left")
    resultado_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    result_window.after(20000, result_window.destroy)  # Fecha após 20 segundos
    result_window.mainloop()

def capturar_texto():
    app = ScreenCaptureApp()
    app.root.mainloop()

# 🔹 Atalhos
print("🔥 Pressione 'CTRL + ALT + SHIFT + Print Screen' para capturar a tela. Pressione 'ESC' para sair.")

keyboard.add_hotkey("ctrl+alt+shift+print_screen", capturar_texto)
keyboard.add_hotkey("esc", lambda: (print("🚪 Saindo do programa..."), os._exit(0)))

keyboard.wait()
