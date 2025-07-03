import random

def crear_mazo():
    palos = ["espada", "basto", "copa", "oro"]
    valores = [1, 2, 3, 4, 5, 6, 7, 10, 11, 12]
    mazo = []
    for palo in palos:
        for valor in valores:
            mazo.append((valor, palo, False)) 
    random.shuffle(mazo)
    return mazo

def repartir_juego(mazo_completo):

    pilas_tablero_local = [[] for _ in range(7)]
    fundaciones_local = [[] for _ in range(4)]
    mazo_reserva_temp_local = list(mazo_completo)

    for i in range(7):
        for j in range(i + 1):
            if len(mazo_reserva_temp_local) > 0:
                valor, palo, _ = mazo_reserva_temp_local.pop(0)
                boca_arriba = (j == i) 
                pilas_tablero_local[i].append((valor, palo, boca_arriba))

    mazo_reserva_local = mazo_reserva_temp_local
    pila_descarte_local = []
    return pilas_tablero_local, fundaciones_local, mazo_reserva_local, pila_descarte_local

def voltear_superior_tablero(pila):
    if pila and not pila[-1][2]: 
        ultima_carta = pila.pop() #da vuelta a la ultima carta

        pila.append((ultima_carta[0], ultima_carta[1], True))
        return True
    return False

def movimiento_valido_tablero(carta_mover, carta_destino): #aca defini que cartas se pueden mover, aunque hay una exepcion entre el 7 y 10

    if not carta_destino:  #si la pila destino está vacía no se puede mover cualquier carta
        return False

    valor_mover, palo_mover, _ = carta_mover
    valor_destino, palo_destino, _ = carta_destino

    condicion_valor = False
    if valor_mover == valor_destino - 1: #el valor debe ser uno menos para poder dropearla
        condicion_valor = True
    elif valor_mover == 7 and valor_destino == 10:
        condicion_valor = True

    condicion_palo = palo_mover != palo_destino

    return condicion_valor and condicion_palo

def movimiento_valido_fundacion(carta_a_mover_tupla: tuple, pila_destino_list: list): #verifica si un movimiento a una fundacion es válido

    valor_mover = carta_a_mover_tupla[0]#obtengo numero y palo
    palo_mover = carta_a_mover_tupla[1] 

    if not pila_destino_list: #lo mismo q arriba
        return valor_mover == 1 #solo un 1 puede ir a una fundación vacía
    else:
        carta_superior_destino = pila_destino_list[-1] 
        valor_destino = carta_superior_destino[0]
        palo_destino = carta_superior_destino[1]

        condicion_valor = valor_mover == valor_destino + 1 #el valor debe ser uno más
        condicion_palo = palo_mover == palo_destino #el palo debe ser el mismo
        return condicion_valor and condicion_palo #retorna si valor es uno mas y palo es el mismo