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
    chat.config(state="normal")                  # desbloquea el cuadro para poder escribir
    chat.insert(tk.END, texto + "\n\n", etiqueta)  # añade el texto al final con su estilo
    chat.config(state="disabled")                # lo vuelve a bloquear (el usuario no puede editarlo)
    chat.see(tk.END) 

def enviar(event=None):                          # event=None permite llamarla desde el botón y desde Enter
    pregunta = entrada.get().strip()             # lee lo escrito y quita espacios sobrantes
    if not pregunta:                             # si está vacío, no hace nada
        return
    escribir("Tú: " + pregunta, "usuario")
    entrada.delete(0, tk.END)                    # limpia el campo de texto tras enviar
    boton.config(state="disabled")               # desactiva el botón mientras la IA responde
    hilo = threading.Thread(target=consultar, args=(pregunta,), daemon=True)
    hilo.start()   

def consultar(pregunta):                         # se ejecuta en el hilo secundario
    try:
        texto = limpiar_markdown(preguntar_a_gemini(pregunta))
        ventana.after(0, mostrar_respuesta, "Asistente: " + texto, "asistente")
    except Exception as e:                       # sin internet, clave mala, límite de uso...
        mensaje = ("Error: no se pudo contactar con el asistente. "
                   "Revisa tu conexión a internet o tu API key.\n(" + str(e) + ")")
        ventana.after(0, mostrar_respuesta, mensaje, "error")

def mostrar_respuesta(texto, etiqueta):          # se ejecuta de vuelta en el hilo principal
    escribir(texto, etiqueta)
    boton.config(state="normal")   