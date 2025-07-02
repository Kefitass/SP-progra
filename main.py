import pygame
import time

from pygame_init import *
from funciones import *

pantalla, reloj = configurar_entorno_pygame()

iniciar_graficos()
escuchar_musica('musica_fondo.mp3', 0.5)

##aca lo que hice fue "dividir" a los distintos modos en los q estaria el jugador/juego

MENU = 0
JUGANDO = 1
RANKING = 2 #pantalla ranking
PEDIR_NOMBRE_RANKING = 3 #luego de terminar el juego te pide el nombre 

estado_juego = MENU
estado_anterior = None

ejecutando = True
while ejecutando:
    reloj.tick(FPS)

    if estado_juego == RANKING and estado_anterior != RANKING: #aca verifico si estaba en la pantalla ranking asi cargo los datos
        ranking_cache = cargar_ranking()
    estado_anterior = estado_juego #actualizo con los cambios nuevos

    if estado_juego == MENU: #de aca en adelante son las funciones que manejan cada estado del juego
        nuevo_estado = manejar_menu(pantalla, estado_juego)
    elif estado_juego == JUGANDO:
        nuevo_estado = manejar_juego(pantalla, estado_juego)
    elif estado_juego == RANKING:
        nuevo_estado = manejar_ranking(pantalla, estado_juego)
    elif estado_juego == PEDIR_NOMBRE_RANKING: 
        nuevo_estado = manejar_nombre(pantalla, estado_juego)

    if nuevo_estado is False: #esta para finalizar el juego
        ejecutando = False
    else:
        estado_juego = nuevo_estado

    pygame.display.flip() #muestra todo lo que llame antes

pygame.quit()