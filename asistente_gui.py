import os 
import json 
import threading
import tkinter as tk                                       
from tkinter import scrolledtext
from dotenv import load_dotenv
from google import genai
from google.genai import types

#importar dependencias y todo lo necesario para la interfaz grafica y el uso de la API de Google GenAI

load_dotenv()
API_KEY = os.getenv("API_KEY")

if not API_KEY:
    raise ValueError("API_KEY not found in environment variables. Please set it in the .env file")

MODELO = "gemini-flash-latest" 

#carga la clave de la API desde el archivo .env y define el modelo a utilizar para las respuestas del asistente

def cargar_contexto(ruta="servicios.txt"):
    with open(ruta, "r" , encoding="utf-8") as f:
        return f.read()

SERVICIOS = cargar_contexto()

INSTRUCCIONES = f"""Eres el asistente virtual de una peluquería llamada Brillo Estelar. Responde ÚNICAMENTE usando esta información:

{SERVICIOS}

Reglas:
1. No inventes información que no esté en el contexto proporcionado.
2. Si la pregunta no tiene que ver con la peluquería, responde amablemente que solo puedes ayudar con temas de la peluquería.
3. Si un dato no aparece en la información, di que no lo sabes. No inventes precios ni servicios.
4. Responde en español, de forma breve y amable."""

cliente = genai.Client(api_key=API_KEY)

def preguntar_a_gemini(pregunta):
    respuesta = cliente.models.generate_content(
        model=MODELO,
        contents=pregunta,
        config=types.GenerateContentConfig(
            system_instruction=INSTRUCCIONES

        ),
    )

    datos = json.loads(respuesta.model_dump_json())


    texto = datos["candidates"][0]["content"]["parts"][0]["text"]
    return texto

#Conecta con la API de Google GenAI y define la función para enviar preguntas al modelo y recibir respuestas, asegurando que se sigan las instrucciones y reglas establecidas

def limpiar_markdown(texto):
    texto = texto.replace("**", "")              # quita las negritas de Markdown
    lineas = []
    for linea in texto.split("\n"):              # recorre línea a línea
        if linea.strip().startswith("* "):       # si es una viñeta de Markdown...
            linea = "• " + linea.strip()[2:]     # ...la cambia por un punto estetico 
        lineas.append(linea)
    return "\n".join(lineas)  


def escribir(texto, etiqueta):
    chat.config(state="normal")                 
    chat.insert(tk.END, texto + "\n\n", etiqueta)  
    chat.config(state="disabled")                
    chat.see(tk.END) 

def enviar(event=None):                          
    pregunta = entrada.get().strip()             
    if not pregunta:                             
        return
    escribir("Tú: " + pregunta, "usuario")
    entrada.delete(0, tk.END)                    
    boton.config(state="disabled")               
    hilo = threading.Thread(target=consultar, args=(pregunta,), daemon=True)
    hilo.start()   

def consultar(pregunta):                       
    try:
        texto = limpiar_markdown(preguntar_a_gemini(pregunta))
        ventana.after(0, mostrar_respuesta, "Asistente: " + texto, "asistente")
    except Exception as e:                       
        mensaje = ("Error: no se pudo contactar con el asistente. "
                   "Revisa tu conexión a internet o tu API key.\n(" + str(e) + ")")
        ventana.after(0, mostrar_respuesta, mensaje, "error")

def mostrar_respuesta(texto, etiqueta):         
    escribir(texto, etiqueta)
    boton.config(state="normal")   

ventana = tk.Tk()
ventana.title("Asistente de Peluqueria")
ventana.geometry("600x500")

chat = scrolledtext.ScrolledText(ventana, wrap=tk.WORD, state="disabled", font=("Arial", 11))
chat.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

chat.tag_config("usuario", foreground="blue", font=("Arial", 11, "bold"))
chat.tag_config("asistente", foreground="green")
chat.tag_config("error", foreground="red")

marco = tk.Frame(ventana)
marco.pack(fill=tk.X, padx=10, pady=(0, 10))


entrada = tk.Entry(marco, font=("Arial", 11))
entrada.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
entrada.bind("<Return>", enviar)

boton = tk.Button(marco, text="Enviar", command=enviar, bg="#0078D7", fg="white")
boton.pack(side=tk.RIGHT)

escribir("Bienvenido al Asistente de Peluquería.\nEscribe tu pregunta abajo y presiona 'Enviar'.", "info")

ventana.mainloop()  