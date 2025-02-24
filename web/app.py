#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 20 16:32:05 2025
@author: rafael

pip install flask flask-socketio

Las aplicaciones Python con Flask deben ejecutarse desde una terminal.
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.

Ejecutar en la nube:
- subir el repositorio a Github
- crear una aplicación en dashboard.render.com
"""
import os, re, time, glob
#from pathlib import Path
import difflib
import threading

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
#from dotenv import load_dotenv

from gtts import gTTS
from io import BytesIO
import soundfile as sf
import pyworld as pw
from pydub import AudioSegment
from pydub.playback import play

import playsound as plays
import pyaudio
import speech_recognition as sr

# -----------------
# variables globals
#
titol = "casats"
actor = ""
estat = "inici"
en_pausa = False
stop = False

pattern_person = "^(\w*?\s?)(:\s?)(.*$)"
pattern_narrador = "([^\(]*)(\(.*?\))(.*)"

dir_dades = "dades"
dir_recursos = "static/img"
arxiu_text = titol

seq_fragment = 0  #numero sequencial per a la generacio del nom d'arxiu wav de sortida d'una sentencia
seq_actor = 0     #numero sequencial per a la generacio del nom d'arxiu wav temporal de la veu de l'actor
pendent_escolta = False  #indica si ha arribat el moment d'escoltar l'actor

Personatges = {'Joan':   {'speed': 1.20, 'grave': 3.6, 'reduction': 0.6},
               'Gisela': {'speed': 1.30, 'grave': 0.9, 'reduction': 1.7},
               'Mar':    {'speed': 1.40, 'grave': 0.6, 'reduction': 1.4},
               'Emma':   {'speed': 1.40, 'grave': 0.7, 'reduction': 1.0},
               'Tina':   {'speed': 1.30, 'grave': 1.1, 'reduction': 1.0},
               'Justa':  {'speed': 1.40, 'grave': 1.8, 'reduction': 0.9},
               'Pompeu': {'speed': 1.40, 'grave': 2.2, 'reduction': 0.9},
               'Canut':  {'speed': 1.50, 'grave': 2.0, 'reduction': 1.0}}
Narrador = {'speed': 1.22, 'grave': 1.6, 'reduction': 1.7}
Narrador = "narrador"


def crear_app():
   app = Flask(__name__) #instancia de Flask
   socketio = SocketIO(app)
   key_secret = os.getenv("API_KEY")

   #%%
   @app.route("/index")
   def index():
      return render_template("index.tpl")

   #%%
   @app.route("/apuntador", methods = ["GET", "POST"])
   def apuntador():
      global actor
      if request.method == "POST":
         actor = request.form.get("seleccio_escenes")
      if actor:
         return render_template("apuntador4.tpl", actor=actor)
      else:
         return render_template("index.tpl")


   #%%
   def beep():
      plays.playsound(f"{dir_recursos}/beep.wav")

   def beep_error():
      plays.playsound(f"{dir_recursos}/laser.wav")

   '''
   Compara 2 textos i indica el percentatge de semblances
   '''
   def ComparaSekuenciesDeText(text_1, text_2):
      # normalitza el text original
      replace = "[.,!¡¿?()]"
      while re.search(replace, text_1):
         for r in replace:
            text_1 = text_1.replace(r, " ")
      text_1 = re.sub("\s+", " ", text_1).lower()
      encert = difflib.SequenceMatcher(None, text_1, text_2).ratio() * 100
      return encert

   '''
   Transforma un audio en text (utilitza speech_recognition)
   @type audio: AudioSource; audio d'entrada que es vol convertir a text
   @type r: Recognizer; instància de speech_recognition.Recognizer()
   '''
   def ReconeixementDeAudio(audio, r):
      text_reconegut = ""
      # Google Speech Recognition
      try:
         # for testing purposes, we're just using the default API key
         # to use another API key, use `r.recognize_google(audio, key="GOOGLE_SPEECH_RECOGNITION_API_KEY")`
         text_reconegut = r.recognize_google(audio, language="ca")
         print(f"- {text_reconegut}")
      except sr.UnknownValueError:
         print("Google Speech Recognition could not understand audio")
      except sr.RequestError as e:
         print("Could not request results from Google Speech Recognition service; {0}".format(e))

      return text_reconegut

   '''
   Genera un arxiu de text a partir d'un arxiu d'audio
   @type warxiu: string; nom del fitxer wav del que es vol extraure el text
   '''
   def audio_a_text(warxiu):
      r = sr.Recognizer()
      with sr.AudioFile(warxiu) as source:
         audio = r.record(source)  # read the entire audio file

      text_reconegut = ReconeixementDeAudio(audio, r)
      return text_reconegut


   '''
   Grava un text a un arxiu d'audio
   @type text: string; text que es grava
   @type file_name: string; nom del fitxer wav on es grava la veu
   '''
   def grava_audio(text, wf):
      fragment = 1024
      format = pyaudio.paInt16
      canals = 1     # channels, must be one for forced alignment toolkit to work
      taxa = 16000   # freqüència de mostreig (sample rate)
      temps = 5      # nombre de segons de temps per poder dir la frase

      #print(f"Llegeix en veu alta: {text}", end=" ")
      beep()

      p = pyaudio.PyAudio()
      stream = p.open(format=format, channels=canals, rate=taxa, input=True, frames_per_buffer=fragment)

      frames = []
      for i in range(0, int(taxa / fragment * temps)):
         data = stream.read(fragment)
         frames.append(data)

      stream.stop_stream()
      stream.close()
      p.terminate()

      wf.setnchannels(canals)
      wf.setsampwidth(p.get_sample_size(format))
      wf.setframerate(taxa)
      wf.writeframes(b''.join(frames))
      wf.close()

   '''
   Grava en viu la veu de l'actor, genera el text corresponent i el compara amb el text que li correspon
   @type text: string; text que es vol gravar
   @type warxiu: string; nom del fitxer wav on es gravarà la veu
   '''
   def escolta_actor(text):
      global actor
      wav_buf = BytesIO()
      grava_audio(text, wav_buf)
      nou_text = audio_a_text(wav_buf)
      encert = 0
      if nou_text:
         encert = ComparaSekuenciesDeText(text, nou_text)
      if encert < 90:
         beep_error()
         print(f"encert: {encert}", " ")
         text_a_audio(text, Personatges[actor], "\n")

   '''
   Genera l'arxiu d'audio corresponent al text
   @type text: string; text que es vol convertir en veu
   @type veu_params: llsta; llista de paràmetres de veu del personatge a tractar
   @type ends: string; marca de final de la instrucció print
                       (": ") indica que el paràmetre text és el nom del personatge
   '''
   def text_a_audio(text, veu_params, ends):
      # Si ends == ": " significa que text és el nom del personatge, per tant, no es genera audio
      # Si veu_params == "narrador" no es genera audio
      # if ends != ": " and veu_params != "narrador":
      #    # obtenir els parametres
      #    speed, grave, reduction = list(veu_params.values())

      #    # Generar un arxiu d'audio temporal amb gTTS
      #    tts = gTTS(text, lang='ca')
      #    mp3_buf = BytesIO()
      #    tts.write_to_fp(mp3_buf)

      #    # Convertir l'objecte mp3 a wav
      #    audio = AudioSegment.from_mp3(mp3_buf)
      #    #play(audio)
      #    wav_buf = BytesIO()
      #    audio.export(wav_buf, format="wav")

      #    # tractament de l'audio
      #    data, samplerate = sf.read(wav_buf)
      #    f0, sp, ap = pw.wav2world(data, samplerate)
      #    yy = pw.synthesize(f0/grave, sp/reduction, ap, samplerate/speed, pw.default_frame_period)
      #    wav_buf = BytesIO()
      #    wav_buf.name = 'file.wav'
      #    sf.write(wav_buf, yy, samplerate)
      #    wav_buf.seek(0)
      #    audio = AudioSegment.from_wav(wav_buf)
      #    play(audio)

      return mostra_sentencia(text, ends)

   def codifica_html(text):
      cerca = "ÀÈÉÍÒÓÚàèéíòóú"
      subs = ["&Agrave;","&Egrave;","&Eacute;","&Iacute;","&Ograve;","&Oacute;","&Uacute;","&agrave;","&egrave;","&eacute;","&iacute;","&ograve;","&oacute;","&uacute;"]
      i = 0
      for s in cerca:
         text.replace(s, subs[i])
         i += 1
      return text

   '''
   Mostra el text que s'està processant.
   '''
   def mostra_sentencia(text, ends):
      time.sleep(.5)
      text = codifica_html(text) + ends
      return text

   """
   Parteix la sentència en fragments que puguin ser processats per gTTs
   @type text: string; text que es tracta
   @type to_veu: list; paràmetres de veu
   @type ends: string; caracter de finalització de la funció print
   """
   def processa_fragment(text, escena, to_veu, ends):
      global seq_fragment, seq_actor, pendent_escolta
      ret = ""
      long_text = len(text)
      ini = 0
      while ini < long_text:
         long_max = 600
         if long_max < long_text:
            long_max = text[ini:].find(" ", long_max)
         if long_max == -1 or long_max > long_text:
            long_max = long_text
         text = text[ini:ini+long_max]

         seq_fragment += 1
         if text == actor:
            pendent_escolta = True
            ret = mostra_sentencia(text, ends)
         elif pendent_escolta == True:
            pendent_escolta = False
            seq_actor += 1
            escolta_actor(text)
            break
         else:
            ret += text_a_audio(text, to_veu, ends)

         ini += long_max

      return ret

   '''
   Lectura del text sencer o de l'escena seleccionada de l'obra
   Partició del text en sentències (una sentència correspón a una línia del text)
   Cada sentència pot pertanyer, bé al narrador, bé a un personatge
   '''
   def processa_escena(arxiu_escena=""):
      global stop, en_pausa
      escena = f"_{arxiu_escena}_" if arxiu_escena else "_"
      if not os.path.isfile(arxiu_escena):
         arxiu_escena = f"{dir_dades}/{arxiu_text}.txt"

      with open(arxiu_escena, 'r', encoding="utf-8") as f:
         sentencies = f.read().split('\n')

      for sentencia in sentencies:
         ret = ""
         if sentencia:
            # extraure el personatje ma(1) i el text ma(3)
            ma = re.match(pattern_person, sentencia)
            if ma:
               personatje = ma.group(1)
               ret = processa_fragment(personatje, escena, Narrador, ": ")
               to_veu = Personatges[personatje] if personatje in Personatges else Narrador
               # extraure, del text ma(3), els comentaris del narrador
               mb = re.match(pattern_narrador, ma.group(3))
               if mb:
                  if mb.group(1) and mb.group(2) and mb.group(3):
                     ret += processa_fragment(mb.group(1), escena, to_veu, " ")
                     ret += processa_fragment(mb.group(2), escena, Narrador, " ")
                     ret += processa_fragment(mb.group(3), escena, to_veu, "\n")
                  elif mb.group(1) and mb.group(2):
                     ret += processa_fragment(mb.group(1), escena, to_veu, " ")
                     ret += processa_fragment(mb.group(2), escena, Narrador, "\n")
                  elif mb.group(2) and mb.group(3):
                     ret += processa_fragment(mb.group(2), escena, Narrador, " ")
                     ret += processa_fragment(mb.group(3), escena, to_veu, "\n")
               else:
                  ret += processa_fragment(ma.group(3), escena, to_veu, "\n")
            else:
               ret += processa_fragment(sentencia, escena, Narrador, "\n")

         if stop:
            break  # Detener la lectura
         while en_pausa:
            time.sleep(0.1)  # Esperar mientras esté en pausa

         print(ret)
         socketio.emit('new_line', {'frase': ret, 'estat': estat})  # Enviar la línea al cliente
         time.sleep(1)

   def principal():
      global actor, arxiu_text
      print("actor:", actor)
      if actor == "sencer":
         processa_escena("")
      else:
         escenes = glob.glob(f"{dir_dades}/{arxiu_text}-{actor}-*")
         if not escenes:
            processa_escena(actor)
         else:
            arxiu_text += f"-{actor}-"
            #escenes = os.scandir(f"{dir_dades}")
            escenes.sort()
            print("escenes:", escenes)
            for e in escenes:
               print("escena actual:", e)
               processa_escena(e)


   #%%
   # Evento que se dispara cuando un cliente se conecta
   @socketio.on('connect')
   def handle_connect():
       print("Client connectat")
       # Iniciamos la lectura del archivo en un hilo separado para no bloquear el servidor

   @socketio.on('inici')
   def handle_start():
       global estat, stop, en_pausa
       print("botó inici")
       estat = "stop"
       stop = False
       en_pausa = False
       threading.Thread(target=principal).start()

   @socketio.on('pausa')
   def handle_pause():
       global en_pausa
       print("botó pausa")
       en_pausa = not en_pausa

   @socketio.on('stop')
   def handle_stop():
       global stop
       print("botó stop")
       stop = True  # Detener la lectura del archivo

   #%%
   @app.route("/inici")
   def inici():
      global estat
      estat = "stop"
      ret = principal()
      return ret


   #%%
   @app.route("/stop", methods = ["GET", "POST"])
   def stop():
      global estat
      estat = "inici"
      return render_template("apuntador4.tpl", actor=actor, estat=estat)


   #%%
   @app.route("/anterior", methods = ["GET", "POST"])
   def anterior():
      global estat
      return render_template("apuntador4.tpl", actor=actor, estat=estat)


   #%%
   @app.route("/seguent", methods = ["GET", "POST"])
   def seguent():
      global estat
      return render_template("apuntador4.tpl", actor=actor, estat=estat)


   return app

   #%%
if __name__ == "__main__":
   '''
   Permet la creació de l'aplicació a GitHub
   '''
   app = crear_app()
   '''
   Inicia los servicios flask en la terminal, lo cual, activa el acceso web
   equivale a ejecutar en una terminal el comando: flask run
   así, se activa el reconocimento de las aplicaciones Python en el puerto 5000 de localhost
   '''
   app.run(host='localhost', port=5000, debug=False)
