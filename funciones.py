import pygame
import random
import csv
import time
import os

from pygame_init import *
from cartas import *

pilas_tablero = [] #lista de listas de tuplas de cartas valor, palo, y boca arriba
pilas_recoleccion = [] #lista de listas de tuplas de cartas
mazo_reserva = [] #lista de tuplas de cartas
pila_descarte = [] #lista de tuplas de cartas

tiempo_inicio_juego = 0
movimientos_realizados = 0

ranking_cache = []

carta_en_mano = None #seria una lista de tuplas de cartas
posicion_carta_en_mano = (0, 0)
offset_x = 0
offset_y = 0
origen_arrastre = None

ARCHIVO_RANKING = 'ranking.csv'
nombre_jugador_para_ranking = "" #temporalmente queda asi el nombre del usser

#aca estan las constantes que "marcan" las distintas partes del juego
MENU = 0
JUGANDO = 1
RANKING = 2
PEDIR_NOMBRE_RANKING = 3 


def iniciar_juego():
    global pilas_tablero, pilas_recoleccion, mazo_reserva, pila_descarte
    global tiempo_inicio_juego, movimientos_realizados
    global carta_en_mano, posicion_carta_en_mano, offset_x, offset_y, origen_arrastre

    mazo_completo_barajado = crear_mazo() 
    pilas_tablero_nuevas, fundaciones_nuevas, mazo_reserva_nuevo, pila_descarte_nueva = repartir_juego(mazo_completo_barajado) ##reparto las cartas en las distintas pilas

    pilas_tablero = pilas_tablero_nuevas #son las 7 pilas 
    pilas_recoleccion = fundaciones_nuevas #son las fundaciones; donde dropeas las cartas dsps
    mazo_reserva = mazo_reserva_nuevo 
    pila_descarte = pila_descarte_nueva 

    tiempo_inicio_juego = time.time()
    movimientos_realizados = 0 

    carta_en_mano = None
    origen_arrastre = None


def guardar_ranking(nombre_jugador, tiempo_juego, movimientos):
    nueva_entrada = [nombre_jugador, tiempo_juego, movimientos]

    file = open(ARCHIVO_RANKING, 'a', newline='') #abro el archivo
    
    writer = csv.writer(file) #hago el escritor para el csv
    
    if file.tell() == 0: #esto verifica si esta vacio, si es asi lo va a escribir
        writer.writerow(['Nombre', 'Tiempo (segundos)', 'Movimientos']) # Escribe el encabezado.
        
    writer.writerow(nueva_entrada) #escribe el ranking
    file.close()
    print(f"Ranking guardado: {nombre_jugador}, {tiempo_juego}, {movimientos}")

def criterio_ordenamiento_ranking(entrada_ranking):
    return (entrada_ranking['Tiempo (segundos)'], entrada_ranking['Movimientos'])

def cargar_ranking():
    ranking_data = []
    if not os.path.exists(ARCHIVO_RANKING):
        return ranking_data
        
    file = open(ARCHIVO_RANKING, 'r', newline='')

    reader = csv.reader(file)
    todas_las_filas_csv = list(reader)

    file.close()

    if not todas_las_filas_csv:
        return ranking_data

    lineas_de_datos = todas_las_filas_csv[1:] #ignora la primera fila

    for fila_datos in lineas_de_datos:
        if len(fila_datos) == 3:
            nombre = fila_datos[0]
            tiempo = int(fila_datos[1])
            movimientos = int(fila_datos[2])
            ranking_data.append({
                'Nombre': nombre,
                'Tiempo (segundos)': tiempo,
                'Movimientos': movimientos
            })
    
    global ranking_cache
    ranking_cache.clear()
    ranking_cache.extend(ranking_data) #añado datos nuevos
    
    ranking_cache.sort(key=criterio_ordenamiento_ranking)
    
    return ranking_cache

def manejar_menu(pantalla, estado_juego_param): #aca defini el menu y tenes las opciones para elegir, sencillo
    global sonido_activado
    pantalla.fill(VERDE)
    dibujar_texto_pantalla(pantalla, "SOLITARIO", 80, BLANCO, ANCHO // 2, ALTO // 4)

    rect_jugar = pygame.Rect(ANCHO // 2 - 100, ALTO // 2 - 30, 200, 60)
    pygame.draw.rect(pantalla, ROJO, rect_jugar)
    dibujar_texto_pantalla(pantalla, "JUGAR", 40, BLANCO, ANCHO // 2, ALTO // 2)

    rect_ranking = pygame.Rect(ANCHO // 2 - 100, ALTO // 2 + 50, 200, 60)
    pygame.draw.rect(pantalla, ROJO, rect_ranking)
    dibujar_texto_pantalla(pantalla, "VER RANKING", 40, BLANCO, ANCHO // 2, ALTO // 2 + 80)

    rect_mute_btn = dibujar_btn_silencio(pantalla, sonido_activado)

    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            return False
        if evento.type == pygame.MOUSEBUTTONDOWN:
            if rect_jugar.collidepoint(evento.pos):
                iniciar_juego()
                return JUGANDO
            elif rect_ranking.collidepoint(evento.pos):
                return RANKING
            elif rect_mute_btn.collidepoint(evento.pos):
                alternar_sonido()
    return estado_juego_param

def manejar_juego(pantalla, estado_juego_param):
    global movimientos_realizados, carta_en_mano, posicion_carta_en_mano, offset_x, offset_y, origen_arrastre
    global pilas_tablero, pilas_recoleccion, mazo_reserva, pila_descarte
    global sonido_activado

    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            return False

        if evento.type == pygame.MOUSEBUTTONDOWN: ##se encarga de verificar el click del mouse
            if evento.button == 1:
                rect_mute_btn = dibujar_btn_silencio(pantalla, sonido_activado)
                if rect_mute_btn.collidepoint(evento.pos):
                    alternar_sonido()
                    continue

                mouse_x, mouse_y = evento.pos #obtiene cordenadas x e y del click 

                rect_mazo_reserva = pygame.Rect(mazo_reserva_x, mazo_reserva_y, ancho_carta, alto_carta) 
                if rect_mazo_reserva.collidepoint(mouse_x, mouse_y): #verifica click en mazo d reserva
                    if mazo_reserva:
                        valor, palo, _ = mazo_reserva.pop() #si el mazo tiene cartas las muestra cuando clickeas
                        pila_descarte.append((valor, palo, True))
                        movimientos_realizados += 1 #suma movimiento y queda regfistrado en el ranking
                    else:
                        if reciclar_pila_descarte():
                            movimientos_realizados += 1
                    continue

                if pila_descarte: #es la logica d arrastre 
                    rect_pila_descarte = pygame.Rect(pila_descarte_x, pila_descarte_y, ancho_carta, alto_carta)
                    if rect_pila_descarte.collidepoint(mouse_x, mouse_y):
                        carta_selec = pila_descarte[-1]
                        if carta_selec[2]:
                            carta_en_mano = [pila_descarte.pop()]
                            origen_arrastre = ("descarte", -1, -1)
                            offset_x = mouse_x - pila_descarte_x
                            offset_y = mouse_y - pila_descarte_y
                        continue

                for indice_pila in range(len(pilas_tablero)): #itera en cada pila para ver si hiciste click
                    pila_de_cartas = pilas_tablero[indice_pila]
                    posicion_x_pila = inicio_x_pilas + indice_pila * (ancho_carta + espacio_horizontal_entre_pilas)

                    indice_carta = len(pila_de_cartas) - 1
                    while indice_carta >= 0:
                        carta_actual = pila_de_cartas[indice_carta]
                        posicion_y_carta = inicio_y_pilas + indice_carta * espacio_vertical_dentro_pila

                        rect_carta = pygame.Rect(posicion_x_pila, posicion_y_carta, ancho_carta,
                                                 espacio_vertical_dentro_pila if indice_carta < len(pila_de_cartas) -1 else alto_carta) #se encarga de definir la zona clickeable de la carta 

                        if rect_carta.collidepoint(mouse_x, mouse_y) and carta_actual[2]: 
                            carta_en_mano = pila_de_cartas[indice_carta:] #agarra la carta junto a la "pila" que clickeaste
                            pilas_tablero[indice_pila] = pilas_tablero[indice_pila][:indice_carta]

                            origen_arrastre = ("tablero", indice_pila, indice_carta)
                            offset_x = mouse_x - posicion_x_pila
                            offset_y = mouse_y - posicion_y_carta

                            break
                        indice_carta -= 1
                    if carta_en_mano: break

        elif evento.type == pygame.MOUSEMOTION:
            if carta_en_mano:
                mouse_x, mouse_y = evento.pos #obtiene pos del mouse si tenes una carta arrastrando
                posicion_carta_en_mano = (mouse_x - offset_x, mouse_y - offset_y) #actualiza la pos

        elif evento.type == pygame.MOUSEBUTTONUP:
            if carta_en_mano:
                mouse_x, mouse_y = evento.pos #accede a la pos donde se solto la carta
                soltada_correctamente = False 
                carta_top_mover = carta_en_mano[0]


                for target_pila_idx in range(len(pilas_tablero)): #recorro cada pila
                    target_x_pila = inicio_x_pilas + target_pila_idx * (ancho_carta + espacio_horizontal_entre_pilas)
                    if pilas_tablero[target_pila_idx]: #calculo la pos
                        ultima_carta_y = inicio_y_pilas + (len(pilas_tablero[target_pila_idx]) - 1) * espacio_vertical_dentro_pila
                        rect_destino = pygame.Rect(target_x_pila, ultima_carta_y, ancho_carta, alto_carta)
                    else:
                        rect_destino = pygame.Rect(target_x_pila, inicio_y_pilas, ancho_carta, alto_carta) #si la pila esta vacia seria la primera de la pila

                    if rect_destino.collidepoint(mouse_x, mouse_y):#destino = pila?
                        if origen_arrastre[0] == "tablero" and origen_arrastre[1] == target_pila_idx:
                            for c in reversed(carta_en_mano):
                                pilas_tablero[origen_arrastre[1]].insert(origen_arrastre[2], c)
                            soltada_correctamente = True #si es el mismo lugar, vuelve a su origen
                        else:
                            carta_destino = pilas_tablero[target_pila_idx][-1] if pilas_tablero[target_pila_idx] else None
                            if movimiento_valido_tablero(carta_top_mover, carta_destino):
                                pilas_tablero[target_pila_idx].extend(carta_en_mano)
                                soltada_correctamente = True
                                movimientos_realizados += 1
                            else:
                                print("Movimiento invalido en tablero")
                        break

                if not soltada_correctamente: 
                    for i in range(4): #son los 4 "cupos" para poner las cartas
                        fundacion_x = fundacion_x_base + i * (ancho_carta + espacio_horizontal_entre_pilas)
                        rect_fundacion = pygame.Rect(fundacion_x, fundacion_y, ancho_carta, alto_carta)
                        if rect_fundacion.collidepoint(mouse_x, mouse_y):
                            if len(carta_en_mano) == 1: #solo podes mover una, mas de una en conjunto no 
                                carta_unica_mover = carta_en_mano[0]
                                if origen_arrastre[0] == "fundacion" and origen_arrastre[1] == i: #aca es por si queres soltar la carta en el mismo lugar, vuelvce ahi sin problemas
                                    pilas_recoleccion[i].extend(carta_en_mano)
                                    soltada_correctamente = True
                                else:
                                    if movimiento_valido_fundacion(carta_unica_mover, pilas_recoleccion[i]): #verifico la validez del movimiento con las "reglas"
                                        pilas_recoleccion[i].extend(carta_en_mano)
                                        soltada_correctamente = True
                                        movimientos_realizados += 1
                                    else:
                                        print("Movimiento invalido en fundacion")
                            else:
                                print("Movimiento invalido, solo se puede mover una carta.")
                            break

                if not soltada_correctamente:
                    if origen_arrastre[0] == "tablero":
                        for c in reversed(carta_en_mano): #la dropea en el mismo lado
                            pilas_tablero[origen_arrastre[1]].insert(origen_arrastre[2], c)
                    elif origen_arrastre[0] == "descarte":
                        pila_descarte.extend(carta_en_mano)
                    print("Movimiento invalido o no reconocido, la carta vuelve a su origen.")

                if soltada_correctamente and origen_arrastre[0] == "tablero":
                    voltear_superior_tablero(pilas_tablero[origen_arrastre[1]]) #movimiento valido = se voltea la carta que quedo debajo

                carta_en_mano = None
                origen_arrastre = None

    dibujar_tablero_juego(pantalla, pilas_tablero, mazo_reserva, pila_descarte, pilas_recoleccion)
    dibujar_btn_silencio(pantalla, sonido_activado)

    tiempo_actual = int(time.time() - tiempo_inicio_juego)
    dibujar_texto_pantalla(pantalla, f"Tiempo: {tiempo_actual}s", 25, BLANCO, 100, ALTO - 30)
    dibujar_texto_pantalla(pantalla, f"Movimientos: {movimientos_realizados}", 25, BLANCO, 300, ALTO - 30)

    if carta_en_mano:
        for i, carta_a_dibujar in enumerate(carta_en_mano): #muestra las cartas arrastradas
            mostrar_carta(pantalla, carta_a_dibujar,
                                 posicion_carta_en_mano[0],
                                 posicion_carta_en_mano[1] + i * espacio_vertical_dentro_pila)

    if verificar_condicion_victoria():
        return PEDIR_NOMBRE_RANKING

    return estado_juego_param


def manejar_ranking(pantalla, estado_juego_param): #maneja laspantallas del ranking
    global ranking_cache
    global sonido_activado

    pantalla.fill(NEGRO)
    dibujar_texto_pantalla(pantalla, "RANKING DE SOLITARIO", 60, BLANCO, ANCHO // 2, 50) #muestra el texto
    y_offset = 120 #posicion para las entradas del ranking

    if not ranking_cache:
        dibujar_texto_pantalla(pantalla, "Todavia no hay partidas registradas", 30, BLANCO, ANCHO // 2, y_offset)
    else: #abajo estarian los "titulos" con su respectivo usser y tiempo
        dibujar_texto_pantalla(pantalla, "Nombre", 30, BLANCO, ANCHO // 2 - 150, y_offset)
        dibujar_texto_pantalla(pantalla, "Tiempo", 30, BLANCO, ANCHO // 2 + 0, y_offset)
        dibujar_texto_pantalla(pantalla, "Movimientos", 30, BLANCO, ANCHO // 2 + 150, y_offset)

        y_offset += 40
        for i, entrada in enumerate(ranking_cache):
            if i >= 10: break #con esto limite a los 10 mejores juegos asi no carga otros menos importantes y luego abajo limite los caracteres para evitar inconvenientes
            texto_linea = (f"{entrada['Nombre']:<15}   "
                           f"{entrada['Tiempo (segundos)']:<5}s   "
                           f"{entrada['Movimientos']:<5}")

            dibujar_texto_pantalla(pantalla, texto_linea, 25, BLANCO, ANCHO // 2, y_offset)
            y_offset += 30

    rect_volver_menu = pygame.Rect(ANCHO // 2 - 100, ALTO - 60, 200, 50) #boton de volver al menu cuando te metes al ranking
    pygame.draw.rect(pantalla, ROJO, rect_volver_menu)
    dibujar_texto_pantalla(pantalla, "VOLVER AL MENÚ", 30, BLANCO, ANCHO // 2, ALTO - 35)

    rect_mute_btn = dibujar_btn_silencio(pantalla, sonido_activado)

    for evento in pygame.event.get(): #se fija en los eventos como clicks y demas ocurridos
        if evento.type == pygame.QUIT:
            return False
        if evento.type == pygame.MOUSEBUTTONDOWN:
            if rect_volver_menu.collidepoint(evento.pos): #es para ver si toque el boton de vovlermenu
                return MENU
            elif rect_mute_btn.collidepoint(evento.pos): #lo mismo pero en el de mute
                alternar_sonido()

    return estado_juego_param

def manejar_nombre(pantalla, estado_juego_param): #encargado de pedir nombre y guardar en el csv el ranking post win
    global nombre_jugador_para_ranking, ranking_cache
    global tiempo_inicio_juego, movimientos_realizados

    nombre_actual_local = "" #esto es porque ahi se guarda el nombre del usuario
    input_activo = True

    while input_activo:
        for evento in pygame.event.get(): #aca se revisan todas las pulsaciones y movimientos q hayan
            if evento.type == pygame.QUIT:
                pygame.quit()
                exit()
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_RETURN:
                    input_activo = False #salgo del bucle
                    tiempo_transcurrido = int(time.time() - tiempo_inicio_juego)
                    guardar_ranking(nombre_actual_local, tiempo_transcurrido, movimientos_realizados)
                    ranking_cache = cargar_ranking() 
                    return RANKING
                elif evento.key == pygame.K_BACKSPACE:
                    nombre_actual_local = nombre_actual_local[:-1]
                else:
                    if len(nombre_actual_local) < 15: #le puse un limite asi el nombre no es super largo
                        nombre_actual_local += evento.unicode

        pantalla.fill(NEGRO)
        dibujar_texto_pantalla(pantalla, "Ingresa tu nombre:", 40, BLANCO, ANCHO // 2, ALTO // 3)

        rect_input = pygame.Rect(ANCHO // 2 - 150, ALTO // 2 - 20, 300, 40)
        pygame.draw.rect(pantalla, BLANCO, rect_input, 2)
        dibujar_texto_pantalla(pantalla, nombre_actual_local, 30, BLANCO, ANCHO // 2, ALTO // 2)

        dibujar_texto_pantalla(pantalla, "(toca enter para guardar)", 20, BLANCO, ANCHO // 2, ALTO // 2 + 50)

        pygame.display.flip()

    return estado_juego_param #luego de todo retorna ranking, que es donde tiene que haber un cambio

def reciclar_pila_descarte(): #cuando no hay mas cartas para mostrar vuelven al mazo en el mismo orden
    global mazo_reserva, pila_descarte
    if not mazo_reserva:
        if pila_descarte:
            cartas_a_reciclar = []
            while pila_descarte:
                carta_original = pila_descarte.pop()
                cartas_a_reciclar.append((carta_original[0], carta_original[1], False))
            mazo_reserva.extend(cartas_a_reciclar)
            random.shuffle(mazo_reserva)
            print("Pila de descarte de vuelta en mazo de reserva.")
            return True
        else:
            print("No hay cartas en la pila de descarte para reciclar.")
            return False
    return False

def verificar_condicion_victoria():
    for fundacion in pilas_recoleccion:
        if len(fundacion) != 10: #son 10 por las que me faltan de las cartas del profe
            return False
    print("GANASTE EL JUEGO!!!!")
    return True