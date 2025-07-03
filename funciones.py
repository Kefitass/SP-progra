import pygame
import random
import csv
import time
import os

from pygame_init import *
from cartas import *

#aca estan las constantes que "marcan" las distintas partes del juego
MENU = 0
JUGANDO = 1
RANKING = 2
PEDIR_NOMBRE_RANKING = 3 

ARCHIVO_RANKING = 'ranking.csv'
nombre_jugador_para_ranking = "" #temporalmente queda asi el nombre del usser



#hice un diccionario sin globales
def iniciar_juego():
    mazo_completo_barajado = crear_mazo() 
    pilas_tablero_nuevas, fundaciones_nuevas, mazo_reserva_nuevo, pila_descarte_nueva = repartir_juego(mazo_completo_barajado)

    estado = {
        'pilas_tablero': pilas_tablero_nuevas, #son las 7 pilas 
        'pilas_recoleccion': fundaciones_nuevas, #son las fundaciones; donde dropeas las cartas dsps
        'mazo_reserva': mazo_reserva_nuevo, 
        'pila_descarte': pila_descarte_nueva, 
        'tiempo_inicio_juego': time.time(),
        'movimientos_realizados': 0,
        'carta_en_mano': None,
        'posicion_carta_en_mano': (0, 0),
        'offset_x': 0,
        'offset_y': 0,
        'origen_arrastre': None,
        'sonido_activado': True
    }
    return estado

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
    ranking_data.sort(key=criterio_ordenamiento_ranking)
    return ranking_data

def manejar_menu(pantalla, estado_juego_param, estado_app): #aca defini el menu y tenes las opciones para elegir, sencillo
    pantalla.fill(VERDE)
    dibujar_texto_pantalla(pantalla, "SOLITARIO", 80, BLANCO, ANCHO // 2, ALTO // 4)

    rect_jugar = pygame.Rect(ANCHO // 2 - 100, ALTO // 2 - 30, 200, 60)
    pygame.draw.rect(pantalla, ROJO, rect_jugar)
    dibujar_texto_pantalla(pantalla, "JUGAR", 40, BLANCO, ANCHO // 2, ALTO // 2)

    rect_ranking = pygame.Rect(ANCHO // 2 - 100, ALTO // 2 + 50, 200, 60)
    pygame.draw.rect(pantalla, ROJO, rect_ranking)
    dibujar_texto_pantalla(pantalla, "VER RANKING", 40, BLANCO, ANCHO // 2, ALTO // 2 + 80)

    rect_mute_btn = dibujar_btn_silencio(pantalla, estado_app['sonido_activado'])

    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            return False, estado_app
        if evento.type == pygame.MOUSEBUTTONDOWN:
            if rect_jugar.collidepoint(evento.pos):
                return JUGANDO, estado_app
            elif rect_ranking.collidepoint(evento.pos):
                return RANKING, estado_app
            elif rect_mute_btn.collidepoint(evento.pos):
                estado_app['sonido_activado'] = not estado_app['sonido_activado']
    return estado_juego_param, estado_app

def manejar_juego(pantalla, estado_juego_param, estado, imagen_dorso_carta, imagenes_cartas_cache):
    #bucle principal de eventos del juego
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            return False, estado

        if evento.type == pygame.MOUSEBUTTONDOWN: #se encarga de verificar el click del mouse
            if evento.button == 1:
                rect_mute_btn = dibujar_btn_silencio(pantalla, estado['sonido_activado'])
                if rect_mute_btn.collidepoint(evento.pos):
                    
                    alternar_sonido(estado)
                    continue

                mouse_x, mouse_y = evento.pos #obtiene cordenadas x e y del click

                rect_mazo_reserva = pygame.Rect(mazo_reserva_x, mazo_reserva_y, ancho_carta, alto_carta)
                if rect_mazo_reserva.collidepoint(mouse_x, mouse_y): #verifica click en mazo d reserva
                    if estado['mazo_reserva']:
                        valor, palo, _ = estado['mazo_reserva'].pop()
                        estado['pila_descarte'].append((valor, palo, True))
                        estado['movimientos_realizados'] += 1
                    else:
                        if reciclar_pila_descarte(estado):
                            estado['movimientos_realizados'] += 1
                    continue

                if estado['pila_descarte']:
                    rect_pila_descarte = pygame.Rect(pila_descarte_x, pila_descarte_y, ancho_carta, alto_carta)
                    if rect_pila_descarte.collidepoint(mouse_x, mouse_y):
                        carta_selec = estado['pila_descarte'][-1]
                        if carta_selec[2]:
                            estado['carta_en_mano'] = [estado['pila_descarte'].pop()]
                            estado['origen_arrastre'] = ("descarte", -1, -1)
                            estado['offset_x'] = mouse_x - pila_descarte_x
                            estado['offset_y'] = mouse_y - pila_descarte_y
                        continue

                for indice_pila in range(len(estado['pilas_tablero'])):
                    pila_de_cartas = estado['pilas_tablero'][indice_pila]
                    posicion_x_pila = inicio_x_pilas + indice_pila * (ancho_carta + espacio_horizontal_entre_pilas)

                    indice_carta = len(pila_de_cartas) - 1
                    while indice_carta >= 0:
                        carta_actual = pila_de_cartas[indice_carta]
                        posicion_y_carta = inicio_y_pilas + indice_carta * espacio_vertical_dentro_pila

                        rect_carta = pygame.Rect(posicion_x_pila, posicion_y_carta, ancho_carta,
                                                 espacio_vertical_dentro_pila if indice_carta < len(pila_de_cartas) -1 else alto_carta)

                        if rect_carta.collidepoint(mouse_x, mouse_y) and carta_actual[2]:
                            estado['carta_en_mano'] = pila_de_cartas[indice_carta:]
                            estado['pilas_tablero'][indice_pila] = estado['pilas_tablero'][indice_pila][:indice_carta]

                            estado['origen_arrastre'] = ("tablero", indice_pila, indice_carta)
                            estado['offset_x'] = mouse_x - posicion_x_pila
                            estado['offset_y'] = mouse_y - posicion_y_carta

                            break
                        indice_carta -= 1
                    if estado['carta_en_mano']:
                        break

        elif evento.type == pygame.MOUSEMOTION:
            if estado['carta_en_mano'] is not None:
                mouse_x, mouse_y = evento.pos
                estado['posicion_carta_en_mano'] = (mouse_x - estado['offset_x'], mouse_y - estado['offset_y']) #actualiza posición de arrastre

        elif evento.type == pygame.MOUSEBUTTONUP:
            if estado['carta_en_mano'] is not None:
                mouse_x, mouse_y = evento.pos
                soltada_correctamente = False
                carta_top_mover = estado['carta_en_mano'][0]

                for target_pila_idx in range(len(estado['pilas_tablero'])):
                    target_x_pila = inicio_x_pilas + target_pila_idx * (ancho_carta + espacio_horizontal_entre_pilas)
                    if estado['pilas_tablero'][target_pila_idx]:
                        ultima_carta_y = inicio_y_pilas + (len(estado['pilas_tablero'][target_pila_idx]) - 1) * espacio_vertical_dentro_pila
                        rect_destino = pygame.Rect(target_x_pila, ultima_carta_y, ancho_carta, alto_carta)
                    else:
                        rect_destino = pygame.Rect(target_x_pila, inicio_y_pilas, ancho_carta, alto_carta)

                    if rect_destino.collidepoint(mouse_x, mouse_y):
                        if estado['origen_arrastre'] is not None and estado['origen_arrastre'][0] == "tablero" and estado['origen_arrastre'][1] == target_pila_idx:
                            for c in reversed(estado['carta_en_mano']):
                                estado['pilas_tablero'][estado['origen_arrastre'][1]].insert(estado['origen_arrastre'][2], c)
                            soltada_correctamente = True
                        else:
                            carta_destino = estado['pilas_tablero'][target_pila_idx][-1] if estado['pilas_tablero'][target_pila_idx] else None
                            if movimiento_valido_tablero(carta_top_mover, carta_destino):
                                estado['pilas_tablero'][target_pila_idx].extend(estado['carta_en_mano'])
                                soltada_correctamente = True
                                estado['movimientos_realizados'] += 1
                            else:
                                print("Movimiento invalido en tablero")
                        break

                if not soltada_correctamente:
                    for i in range(4):
                        fundacion_x = fundacion_x_base + i * (ancho_carta + espacio_horizontal_entre_pilas)
                        rect_fundacion = pygame.Rect(fundacion_x, fundacion_y, ancho_carta, alto_carta)
                        if rect_fundacion.collidepoint(mouse_x, mouse_y):
                            if len(estado['carta_en_mano']) == 1:
                                carta_unica_mover = estado['carta_en_mano'][0]
                                if estado['origen_arrastre'] is not None and estado['origen_arrastre'][0] == "fundacion" and estado['origen_arrastre'][1] == i:
                                    estado['pilas_recoleccion'][i].extend(estado['carta_en_mano'])
                                    soltada_correctamente = True
                                else:
                                    if movimiento_valido_fundacion(carta_unica_mover, estado['pilas_recoleccion'][i]):
                                        estado['pilas_recoleccion'][i].extend(estado['carta_en_mano'])
                                        soltada_correctamente = True
                                        estado['movimientos_realizados'] += 1
                                    else:
                                        print("Movimiento invalido en fundacion")
                            else:
                                print("Movimiento invalido, solo se puede mover una carta.")
                            break

                if not soltada_correctamente:
                    if estado['origen_arrastre'] is not None and estado['origen_arrastre'][0] == "tablero":
                        for c in reversed(estado['carta_en_mano']):
                            estado['pilas_tablero'][estado['origen_arrastre'][1]].insert(estado['origen_arrastre'][2], c)
                    elif estado['origen_arrastre'] is not None and estado['origen_arrastre'][0] == "descarte":
                        estado['pila_descarte'].extend(estado['carta_en_mano'])
                    print("Movimiento invalido o no reconocido, la carta vuelve a su origen.")

                if soltada_correctamente and estado['origen_arrastre'] is not None and estado['origen_arrastre'][0] == "tablero":
                    voltear_superior_tablero(estado['pilas_tablero'][estado['origen_arrastre'][1]]) #voltea carta superior si corresponde

                estado['carta_en_mano'] = None
                estado['origen_arrastre'] = None

    dibujar_tablero_juego(pantalla, estado['pilas_tablero'], estado['mazo_reserva'], estado['pila_descarte'], estado['pilas_recoleccion'], imagen_dorso_carta, imagenes_cartas_cache) #dibuja todo el tablero
    dibujar_btn_silencio(pantalla, estado['sonido_activado']) #dibuja el botón de sonido

    tiempo_actual = int(time.time() - estado['tiempo_inicio_juego'])
    dibujar_texto_pantalla(pantalla, f"Tiempo: {tiempo_actual}s", 25, BLANCO, 100, ALTO - 30) #muestra tiempo
    dibujar_texto_pantalla(pantalla, f"Movimientos: {estado['movimientos_realizados']}", 25, BLANCO, 300, ALTO - 30) #muestra movimientos

    if estado['carta_en_mano']:
        for i, carta_a_dibujar in enumerate(estado['carta_en_mano']):
            mostrar_carta(pantalla, carta_a_dibujar,
                                 estado['posicion_carta_en_mano'][0],
                                 estado['posicion_carta_en_mano'][1] + i * espacio_vertical_dentro_pila,
                                 imagen_dorso_carta, imagenes_cartas_cache) #dibuja carta arrastrada

    if verificar_condicion_victoria(estado):
        return PEDIR_NOMBRE_RANKING, estado #si ganaste, pasa a pedir nombre

    return estado_juego_param, estado #devuelve el estado actual y la pantalla


def manejar_ranking(pantalla, estado_juego_param, estado_app): #maneja laspantallas del ranking
    pantalla.fill(NEGRO)
    dibujar_texto_pantalla(pantalla, "RANKING DE SOLITARIO", 60, BLANCO, ANCHO // 2, 50) #muestra el texto
    y_offset = 120 #posicion para las entradas del ranking
    ranking_cache = estado_app.get('ranking_cache', [])
    if not ranking_cache:
        dibujar_texto_pantalla(pantalla, "Todavias no hay partidas registradas", 30, BLANCO, ANCHO // 2, y_offset)
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
    rect_mute_btn = dibujar_btn_silencio(pantalla, estado_app['sonido_activado'])
    for evento in pygame.event.get(): #se fija en los eventos como clicks y demas ocurridos
        if evento.type == pygame.QUIT:
            return False, estado_app
        if evento.type == pygame.MOUSEBUTTONDOWN:
            if rect_volver_menu.collidepoint(evento.pos): #es para ver si toque el boton de vovlermenu
                return MENU, estado_app
            elif rect_mute_btn.collidepoint(evento.pos): #lo mismo pero en el de mute
                estado_app['sonido_activado'] = not estado_app['sonido_activado']
    return estado_juego_param, estado_app

def manejar_nombre(pantalla, estado_juego_param, estado, estado_app): #encargado de pedir nombre y guardar en el csv el ranking post win
    nombre_actual_local = ""  #ahi guardo el usser
    input_activo = True
    cerrar = False
    while input_activo and not cerrar:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                cerrar = True
                break
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_RETURN:
                    input_activo = False
                    tiempo_transcurrido = int(time.time() - estado['tiempo_inicio_juego'])
                    guardar_ranking(nombre_actual_local, tiempo_transcurrido, estado['movimientos_realizados'])
                    estado_app['ranking_cache'] = cargar_ranking()
                    return RANKING, estado, estado_app
                elif evento.key == pygame.K_BACKSPACE:
                    nombre_actual_local = nombre_actual_local[:-1]
                else:
                    if len(nombre_actual_local) < 15:
                        nombre_actual_local += evento.unicode
        if cerrar:
            return False, estado, estado_app
        pantalla.fill(NEGRO)
        dibujar_texto_pantalla(pantalla, "Ingresa tu nombre:", 40, BLANCO, ANCHO // 2, ALTO // 3)
        rect_input = pygame.Rect(ANCHO // 2 - 150, ALTO // 2 - 20, 300, 40)
        pygame.draw.rect(pantalla, BLANCO, rect_input, 2)
        dibujar_texto_pantalla(pantalla, nombre_actual_local, 30, BLANCO, ANCHO // 2, ALTO // 2)
        dibujar_texto_pantalla(pantalla, "(toca enter para guardar)", 20, BLANCO, ANCHO // 2, ALTO // 2 + 50)
        pygame.display.flip()
    return estado_juego_param, estado, estado_app  #retorna el estado sin cambios si no se guarda el nombre

def reciclar_pila_descarte(estado): #cuando no hay mas cartas para mostrar vuelven al mazo en el mismo orden
    if not estado['mazo_reserva']:
        if estado['pila_descarte']:
            cartas_a_reciclar = []
            while estado['pila_descarte']:
                carta_original = estado['pila_descarte'].pop()
                cartas_a_reciclar.append((carta_original[0], carta_original[1], False))
            estado['mazo_reserva'].extend(cartas_a_reciclar)
            random.shuffle(estado['mazo_reserva'])
            print("Pila de descarte de vuelta en mazo de reserva.")
            return True
        else:
            print("No hay cartas en la pila de descarte para reciclar.")
            return False
    return False

def verificar_condicion_victoria(estado):
    for fundacion in estado['pilas_recoleccion']:
        if len(fundacion) != 10: #son 10 por las que me faltan de las cartas del profe
            return False
    print("GANASTE EL JUEGO!!!!")
    return True