# -*- coding: utf-8 -*-
"""
GENERADOR DE FONDOS DE GIMNASIO
================================
Crea las texturas de fondo de las plantillas nuevas dentro de la carpeta `img`.
Todas siguen la misma temática fitness: mancuernas, pesas rusas, discos y barras
sobre un degradado del color de cada plantilla.

Se ejecuta a mano solo cuando quieras regenerar o retocar los fondos:

    python generar_fondos.py

Si prefieres usar una foto real en lugar de la textura generada, basta con
guardar tu imagen en `img` con el mismo nombre de archivo (por ejemplo
`bg_rosegold.jpg`) y la app la tomará automáticamente.
"""

import os
import math
import random

from PIL import Image, ImageDraw, ImageFilter, ImageChops

CARPETA = "img"
LADO = 2000           # imagen cuadrada: se recorta bien en vertical y horizontal
SUPERMUESTREO = 4     # los iconos se dibujan en grande y se reducen: bordes suaves


# ==========================================================
# ICONOS DE GIMNASIO
# ==========================================================
def _lienzo_icono(tam):
    grande = tam * SUPERMUESTREO
    lienzo = Image.new("RGBA", (grande, grande), (0, 0, 0, 0))
    return lienzo, ImageDraw.Draw(lienzo), grande


def _terminar(lienzo, tam):
    return lienzo.resize((tam, tam), Image.LANCZOS)


def icono_mancuerna(tam, color):
    """Mancuerna vista de lado."""
    lienzo, dibujo, g = _lienzo_icono(tam)

    def caja(x1, y1, x2, y2, radio):
        dibujo.rounded_rectangle([x1 * g, y1 * g, x2 * g, y2 * g], radius=int(radio * g), fill=color)

    caja(0.30, 0.465, 0.70, 0.535, 0.02)      # barra central
    caja(0.22, 0.360, 0.30, 0.640, 0.02)      # discos internos
    caja(0.70, 0.360, 0.78, 0.640, 0.02)
    caja(0.12, 0.290, 0.21, 0.710, 0.03)      # discos externos
    caja(0.79, 0.290, 0.88, 0.710, 0.03)
    return _terminar(lienzo, tam)


def icono_pesa_rusa(tam, color):
    """Pesa rusa (kettlebell)."""
    lienzo, dibujo, g = _lienzo_icono(tam)
    grosor = int(0.075 * g)

    dibujo.arc([0.30 * g, 0.10 * g, 0.70 * g, 0.58 * g], start=180, end=360, fill=color, width=grosor)
    dibujo.rectangle([0.30 * g, 0.34 * g, 0.37 * g, 0.46 * g], fill=color)
    dibujo.rectangle([0.63 * g, 0.34 * g, 0.70 * g, 0.46 * g], fill=color)
    dibujo.rounded_rectangle([0.36 * g, 0.42 * g, 0.64 * g, 0.54 * g], radius=int(0.03 * g), fill=color)
    dibujo.ellipse([0.22 * g, 0.44 * g, 0.78 * g, 0.92 * g], fill=color)
    return _terminar(lienzo, tam)


def icono_disco(tam, color):
    """Disco olímpico visto de frente."""
    lienzo, dibujo, g = _lienzo_icono(tam)
    dibujo.ellipse([0.08 * g, 0.08 * g, 0.92 * g, 0.92 * g], outline=color, width=int(0.115 * g))
    dibujo.ellipse([0.38 * g, 0.38 * g, 0.62 * g, 0.62 * g], outline=color, width=int(0.055 * g))
    return _terminar(lienzo, tam)


def icono_barra(tam, color):
    """Barra olímpica cargada."""
    lienzo, dibujo, g = _lienzo_icono(tam)

    def caja(x1, y1, x2, y2, radio=0.015):
        dibujo.rounded_rectangle([x1 * g, y1 * g, x2 * g, y2 * g], radius=int(radio * g), fill=color)

    caja(0.04, 0.475, 0.96, 0.525)            # barra
    caja(0.13, 0.375, 0.19, 0.625)            # discos izquierda
    caja(0.21, 0.315, 0.28, 0.685, 0.02)
    caja(0.81, 0.375, 0.87, 0.625)            # discos derecha
    caja(0.72, 0.315, 0.79, 0.685, 0.02)
    return _terminar(lienzo, tam)


ICONOS = [icono_mancuerna, icono_pesa_rusa, icono_disco, icono_barra]


# ==========================================================
# CAPAS DE FONDO
# ==========================================================
def degradado_diagonal(lado, color_a, color_b):
    """Degradado suave en diagonal a partir de una imagen de 2x2 ampliada."""
    medio = tuple((a + b) // 2 for a, b in zip(color_a, color_b))
    semilla = Image.new("RGB", (2, 2))
    semilla.putpixel((0, 0), color_a)
    semilla.putpixel((1, 0), medio)
    semilla.putpixel((0, 1), medio)
    semilla.putpixel((1, 1), color_b)
    return semilla.resize((lado, lado), Image.BICUBIC).convert("RGBA")


def foco_superior(base, color, intensidad):
    """Luz cenital tipo foco de gimnasio sobre la parte alta."""
    lado = base.width
    mascara = Image.new("L", (lado // 8, lado // 8), 0)
    dibujo = ImageDraw.Draw(mascara)
    cx, cy, radio = mascara.width // 2, int(mascara.height * 0.18), int(mascara.width * 0.62)
    pasos = 40
    for i in range(pasos, 0, -1):
        r = radio * i / pasos
        valor = int(intensidad * (1 - i / pasos) ** 1.6)
        dibujo.ellipse([cx - r, cy - r * 0.75, cx + r, cy + r * 0.75], fill=valor)
    mascara = mascara.resize((lado, lado), Image.BICUBIC).filter(ImageFilter.GaussianBlur(lado // 90))
    luz = Image.new("RGBA", (lado, lado), color + (255,))
    return Image.composite(Image.alpha_composite(base, luz), base, mascara)


def capa_iconos(lado, color, alfa, tam_icono, separacion, angulo_base):
    """Rejilla escalonada de iconos de gimnasio, con variación de tamaño y giro."""
    capa = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    aleatorio = random.Random(20260817)

    fila = 0
    y = -tam_icono
    while y < lado + tam_icono:
        desfase = (separacion // 2) if fila % 2 else 0
        x = -tam_icono + desfase
        while x < lado + tam_icono:
            constructor = ICONOS[(fila + x // max(1, separacion)) % len(ICONOS)]
            escala = aleatorio.uniform(0.78, 1.12)
            tam = max(24, int(tam_icono * escala))
            icono = constructor(tam, color + (alfa,))
            icono = icono.rotate(angulo_base + aleatorio.uniform(-14, 14), resample=Image.BICUBIC, expand=True)
            capa.alpha_composite(icono, (int(x), int(y)))
            x += separacion
        y += separacion
        fila += 1
    return capa


def desvanecer_arriba(capa, minimo=40, maximo=255):
    """Baja la intensidad del patrón en la zona del título para que el texto respire."""
    lado = capa.width
    rampa = Image.new("L", (1, lado))
    for y in range(lado):
        t = y / float(lado - 1)
        suave = t * t * (3 - 2 * t)
        rampa.putpixel((0, y), int(minimo + (maximo - minimo) * suave))
    mascara = rampa.resize((lado, lado), Image.BICUBIC)
    alfa = ImageChops.multiply(capa.getchannel("A"), mascara)
    capa.putalpha(alfa)
    return capa


def lineas_diagonales(lado, color, alfa, separacion, grosor):
    """Líneas en diagonal: dan sensación de movimiento y velocidad."""
    capa = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    dibujo = ImageDraw.Draw(capa)
    for x in range(-lado, lado * 2, separacion):
        dibujo.line([(x, lado), (x + lado, 0)], fill=color + (alfa,), width=grosor)
    return capa


def rejilla_tecnica(lado, color, alfa, paso):
    """Cuadrícula tipo plano técnico, para las plantillas más serias."""
    capa = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    dibujo = ImageDraw.Draw(capa)
    for posicion in range(0, lado, paso):
        ancho = 3 if (posicion // paso) % 5 == 0 else 1
        dibujo.line([(posicion, 0), (posicion, lado)], fill=color + (alfa,), width=ancho)
        dibujo.line([(0, posicion), (lado, posicion)], fill=color + (alfa,), width=ancho)
    return capa


def vineta(base, oscura=True, intensidad=90):
    """Oscurece (o aclara) los bordes para centrar la mirada en el contenido."""
    lado = base.width
    mascara = Image.new("L", (lado // 8, lado // 8), 255)
    dibujo = ImageDraw.Draw(mascara)
    pasos = 36
    for i in range(pasos):
        margen = int(mascara.width * 0.5 * (i / pasos) ** 1.7)
        valor = int(255 - intensidad * (1 - i / pasos))
        dibujo.rectangle([margen, margen, mascara.width - margen, mascara.height - margen], outline=valor, width=3)
    mascara = mascara.resize((lado, lado), Image.BICUBIC).filter(ImageFilter.GaussianBlur(lado // 45))
    tono = Image.new("RGBA", (lado, lado), ((0, 0, 0, 255) if oscura else (255, 255, 255, 255)))
    return Image.composite(base, Image.alpha_composite(base, tono), mascara)


def grano(base, alfa=7):
    """Grano fino: evita que el degradado se vea plano o con bandas."""
    lado = base.width
    ruido = Image.frombytes("L", (500, 500), os.urandom(500 * 500))
    ruido = ruido.resize((lado, lado), Image.BILINEAR).filter(ImageFilter.GaussianBlur(1))
    capa = Image.merge("RGBA", (ruido, ruido, ruido, Image.new("L", (lado, lado), alfa)))
    return Image.alpha_composite(base, capa)


# ==========================================================
# RECETA DE CADA PLANTILLA
# ==========================================================
FONDOS = {
    "bg_rosegold.jpg": {
        "degradado": ((253, 246, 244), (238, 209, 203)),
        "patron": (183, 110, 121),
        "alfa_patron": 46,
        "tam_icono": 210,
        "separacion": 300,
        "angulo": -18,
        "lineas": ((183, 110, 121), 16, 130, 3),
        "vineta_oscura": False,
        "vineta": 55,
    },
    "bg_violet.jpg": {
        "degradado": ((26, 19, 48), (49, 33, 84)),
        "patron": (167, 139, 250),
        "alfa_patron": 52,
        "tam_icono": 220,
        "separacion": 310,
        "angulo": -22,
        "foco": ((139, 92, 246), 110),
        "lineas": ((196, 181, 253), 14, 150, 3),
        "vineta_oscura": True,
        "vineta": 110,
    },
    "bg_sunset.jpg": {
        "degradado": ((255, 247, 237), (250, 205, 160)),
        "patron": (234, 88, 12),
        "alfa_patron": 44,
        "tam_icono": 205,
        "separacion": 290,
        "angulo": -25,
        "lineas": ((234, 88, 12), 20, 90, 4),
        "vineta_oscura": False,
        "vineta": 50,
    },
    "bg_steel.jpg": {
        "degradado": ((239, 243, 247), (206, 216, 228)),
        "patron": (45, 72, 99),
        "alfa_patron": 40,
        "tam_icono": 200,
        "separacion": 300,
        "angulo": 0,
        "rejilla": ((45, 72, 99), 16, 100),
        "vineta_oscura": False,
        "vineta": 45,
    },
    "bg_gold.jpg": {
        "degradado": ((20, 18, 14), (43, 36, 24)),
        "patron": (198, 160, 58),
        "alfa_patron": 58,
        "tam_icono": 215,
        "separacion": 305,
        "angulo": -15,
        "foco": ((214, 178, 84), 95),
        "lineas": ((214, 178, 84), 16, 140, 3),
        "vineta_oscura": True,
        "vineta": 115,
    },
}


def construir(receta):
    lienzo = degradado_diagonal(LADO, *receta["degradado"])

    if "foco" in receta:
        lienzo = foco_superior(lienzo, receta["foco"][0], receta["foco"][1])

    if "rejilla" in receta:
        color, alfa, paso = receta["rejilla"]
        lienzo = Image.alpha_composite(lienzo, desvanecer_arriba(rejilla_tecnica(LADO, color, alfa, paso), 60))

    if "lineas" in receta:
        color, alfa, separacion, grosor = receta["lineas"]
        lienzo = Image.alpha_composite(lienzo, lineas_diagonales(LADO, color, alfa, separacion, grosor))

    patron = capa_iconos(LADO, receta["patron"], receta["alfa_patron"],
                         receta["tam_icono"], receta["separacion"], receta["angulo"])
    lienzo = Image.alpha_composite(lienzo, desvanecer_arriba(patron))

    lienzo = vineta(lienzo, receta["vineta_oscura"], receta["vineta"])
    lienzo = grano(lienzo)
    return lienzo.convert("RGB")


def main():
    if not os.path.isdir(CARPETA):
        os.makedirs(CARPETA)
    for nombre, receta in FONDOS.items():
        imagen = construir(receta)
        ruta = os.path.join(CARPETA, nombre)
        imagen.save(ruta, format="JPEG", quality=88, optimize=True, progressive=True)
        print("  %-18s %sx%s  %d KB" % (nombre, imagen.width, imagen.height, os.path.getsize(ruta) // 1024))
    print("Fondos generados en la carpeta '%s'." % CARPETA)


if __name__ == "__main__":
    main()
