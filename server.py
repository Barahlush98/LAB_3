import json
import socket
import random

def recvall(sock, count):
    data = bytearray()
    while len(data) < count:
        pack = sock.recv(count-len(data))
        print('Получено {0} bytes'.format(len(pack)))
        if not pack:
            return None
        data.extend(pack)
    return data

def generate_cards_pool(max):
    cards={}
    cards['cards']=[]
    for i in range(5):
        cards['cards'].append({'s': random.randint(1,max),
                               'a': random.randint(1,max),
                               'i': random.randint(1,max)})
    return cards

def fight_cards(a_choice, b_choice, a_json, b_json):
    a_card = a_json['cards'][a_choice] 
    b_card = b_json['cards'][b_choice]
    dec=0
    for i in ['s','a','i']:
        if a_card[i] != b_card[i]:
            dec+=(1 if a_card[i]>b_card[i] else -1)
    if dec!=0:
        if dec < 0:
            del a_json['cards'][a_choice]
        else:
            del b_json['cards'][b_choice]
    return dec

def main():
	sock = socket.socket()
	sock.bind(('localhost',9090))
	sock.listen(2)
	cons, addrs = [], []

	print('Подключение игроков...')
	for i in range(2):
		con, addr = sock.accept()#принимаем подключение. возвращаем кортеж с двумя элементами: новый сокет и адрес клиента
		con.sendall(i.to_bytes(8,byteorder='big')) #1
		cons.append(con)
		print('Игрок {} присоединился'.format(i+1))

	print('Все игроки присоединились. Начало игры...')
	print('Генерация героев...')
	cards_pool = [generate_cards_pool(100) for i in range(2)]
	print('Герои сгенерированы.')

	while(len(cards_pool[0]['cards']) > 0 and len(cards_pool[1]['cards']) > 0):
		for i in zip(cons,cards_pool,range(2)):
			raw_data = json.dumps(i[1], ensure_ascii=False).encode('utf-8')
			print('Отправка размера JSON-файла...')
			a = len(raw_data)
			ab = a.to_bytes(8,byteorder='big')
			i[0].sendall(ab) #2
			print('Отправка JSON-файла...')
			i[0].sendall(raw_data) #3

		players_dec=[]
		for con in zip(cons,range(2)):
			print('Ожидание выбора героя игроком {}...'.format(con[1]+1))
			ba = recvall(con[0], 8) #4
			players_dec.append(int.from_bytes(ba, byteorder='big', signed=False))

		result = fight_cards(players_dec[0],players_dec[1], cards_pool[0],cards_pool[1])

		for con in cons:
			con.sendall(result.to_bytes(8,byteorder='big',signed=True))#5
		a = len(cards_pool[0]['cards']) > 0 and len(cards_pool[1]['cards']) > 0
		ab = a.to_bytes(8,byteorder='big')
		for con in cons:
			con.sendall(ab) #6

	print('Игровая сессия завершена')
	sock.close()
	
main()