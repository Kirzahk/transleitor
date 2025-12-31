# transleitor
Subtitulador y Traductor de archivos multimedia

Este programa


1)	Crea un entorno virtual en python, con una versión inferior a la 3.13 de este fantástico lenguaje de script.
2)	Activa el entorno virtual y procedes a instalar todos los requisitos:
pip install -r requirements.txt
3)	El sistema requiere tener las librerías ffmpeg, ffplay y ffprobe en el path. Cuando nada funciona, las pongo donde está el programa de python. Las podéis descargar de:
    https://www.ffmpeg.org/download.html
5)	Ahora mismo sólo funciona con CPU, pero lo puedes cambiar en la línea 150, sustituyendo “cpu” por “cuda”
