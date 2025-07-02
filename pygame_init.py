import pygame
import os

ANCHO = 800
ALTO = 600
FPS = 60

BLANCO = (255, 255, 255)
NEGRO = (0, 0, 0)
ROJO = (200, 0, 0)
VERDE = (0, 128, 0)

#constantes de dimensiones y posiciones de cartas
ancho_carta = 90
alto_carta = 120
espacio_horizontal_entre_pilas = 11.6
espacio_vertical_dentro_pila = 30
inicio_x_pilas = 20
inicio_y_pilas = 160
mazo_reserva_x = inicio_x_pilas
mazo_reserva_y = 20
pila_descarte_x = mazo_reserva_x + ancho_carta + espacio_horizontal_entre_pilas
pila_descarte_y = 20
fundacion_final_x = ANCHO - 20
fundacion_x_base = fundacion_final_x - (4 * ancho_carta + 3 * espacio_horizontal_entre_pilas)
fundacion_y = 20

CARPETA_IMAGENES_CARTAS = 'cartas/'
IMAGEN_DORSO_CARTA = None
IMAGENES_CARTAS_CACHE = {}
sonido_activado = True

def configurar_entorno_pygame(): #aca inicialice pygame y configure pantalla, el timer y sonido
    pygame.init()
    pygame.font.init()
    pygame.mixer.init()

    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption("Solitario")
    reloj = pygame.time.Clock()

    return pantalla, reloj

def escuchar_musica(file_path='musica_fondo.mp3', volumen=0.5):
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play(-1) #puse el -1 para q la reproduccion sea infinita
    pygame.mixer.music.set_volume(volumen)


def iniciar_graficos():
    global IMAGEN_DORSO_CARTA, IMAGENES_CARTAS_CACHE

    IMAGEN_DORSO_CARTA = pygame.image.load(CARPETA_IMAGENES_CARTAS + "dorso carta.jpg").convert_alpha()
    IMAGEN_DORSO_CARTA = pygame.transform.scale(IMAGEN_DORSO_CARTA, (ancho_carta, alto_carta))

    IMAGENES_CARTAS_CACHE = {}
def cargar_carta_imagen(valor, palo):
    clave_carta = f"{valor}_{palo}"
    if clave_carta in IMAGENES_CARTAS_CACHE:
        return IMAGENES_CARTAS_CACHE[clave_carta]

    nombre_archivo = f"{valor} de {palo}.jpg"
    ruta_completa = CARPETA_IMAGENES_CARTAS + nombre_archivo
    
    imagen = pygame.image.load(ruta_completa).convert_alpha()
    imagen_escalada = pygame.transform.scale(imagen, (ancho_carta, alto_carta))
    IMAGENES_CARTAS_CACHE[clave_carta] = imagen_escalada
    return imagen_escalada

def mostrar_carta(pantalla_a_dibujar, carta_tupla, x, y): #muestra las cartas en pantalla, recibe y "desempaqueta" la tupla
    valor, palo, boca_arriba = carta_tupla 
    if boca_arriba:
        imagen_a_mostrar = cargar_carta_imagen(valor, palo) #llama a la función con el nuevo nombre
    else:
        imagen_a_mostrar = IMAGEN_DORSO_CARTA
    pantalla_a_dibujar.blit(imagen_a_mostrar, (x, y))

def dibujar_texto_pantalla(pantalla, texto, tamaño, color, x, y): #funcion q muestra el texto en la ventana de pygame, toma tamaño para titulos, la fuente la dictamine por "none" y luego renderiza
    #ahi queda el color y tambien toma el texto que necesito mostrar
    fuente = pygame.font.Font(None, tamaño)
    superficie_texto = fuente.render(texto, True, color)
    rect_texto = superficie_texto.get_rect(center=(x, y))
    pantalla.blit(superficie_texto, rect_texto)

def dibujar_btn_silencio(pantalla, sonido_activado_param): #basicamente dibuja el boton de silencio y acitvbado

    x_btn = ANCHO - 50
    y_btn = 30
    radio = 20
    color_btn = ROJO if not sonido_activado_param else BLANCO
    pygame.draw.circle(pantalla, color_btn, (x_btn, y_btn), radio, 2)
    if sonido_activado_param:
        pygame.draw.polygon(pantalla, color_btn, [(x_btn - 10, y_btn - 10), (x_btn - 10, y_btn + 10), (x_btn + 5, y_btn)])
    else:
        pygame.draw.line(pantalla, color_btn, (x_btn - 15, y_btn - 15), (x_btn + 15, y_btn + 15), 3)
        pygame.draw.line(pantalla, color_btn, (x_btn + 15, y_btn - 15), (x_btn - 15, y_btn + 15), 3)
    return pygame.Rect(x_btn - radio, y_btn - radio, radio * 2, radio * 2)

def alternar_sonido(): #cambia entre activar y desactivar el sonido
    global sonido_activado
    sonido_activado = not sonido_activado
    if sonido_activado:
        pygame.mixer.music.set_volume(0.5)
        print("Sonido activado")
    else:
        pygame.mixer.music.set_volume(0.0)
        print("Sonido silenciado")

def dibujar_tablero_juego(pantalla, pilas_tablero_param, mazo_reserva_param, pila_descarte_param, pilas_recoleccion_param): #muestra el tablero actual del solitario
    pantalla.fill(VERDE)

    #estas son las pilas del tablero
    for indice_pila, pila_de_cartas in enumerate(pilas_tablero_param):
        posicion_x_pila = inicio_x_pilas + indice_pila * (ancho_carta + espacio_horizontal_entre_pilas)
        if not pila_de_cartas:
            pygame.draw.rect(pantalla, BLANCO, (posicion_x_pila, inicio_y_pilas, ancho_carta, alto_carta), 1)
        for indice_carta, carta_completa in enumerate(pila_de_cartas):
            posicion_y_carta = inicio_y_pilas + indice_carta * espacio_vertical_dentro_pila
            mostrar_carta(pantalla, carta_completa, posicion_x_pila, posicion_y_carta)

    if mazo_reserva_param:
        mostrar_carta(pantalla, mazo_reserva_param[-1] if mazo_reserva_param else (0, "", False), mazo_reserva_x, mazo_reserva_y)
    else:
        pygame.draw.rect(pantalla, BLANCO, (mazo_reserva_x, mazo_reserva_y, ancho_carta, alto_carta), 1)

    if pila_descarte_param:
        mostrar_carta(pantalla, pila_descarte_param[-1], pila_descarte_x, pila_descarte_y)
    else:
        pygame.draw.rect(pantalla, BLANCO, (pila_descarte_x, pila_descarte_y, ancho_carta, alto_carta), 1)

    #pilas de recolección (basicamente las q estan arriba a la derecha)
    for i in range(4):
        fundacion_x = fundacion_x_base + i * (ancho_carta + espacio_horizontal_entre_pilas)
        if pilas_recoleccion_param[i]:
            mostrar_carta(pantalla, pilas_recoleccion_param[i][-1], fundacion_x, fundacion_y)
        else:
            pygame.draw.rect(pantalla, BLANCO, (fundacion_x, fundacion_y, ancho_carta, alto_carta), 1)