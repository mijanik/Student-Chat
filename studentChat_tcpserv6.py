#********************************************************#
# Autorzy: Milosz Janik, Kacper Czepiec i Antoni Kijania #
#       Programowanie Sieciowe - zajecia projektowe      #
#           AGH - Elektronika i Telekomunikacja          #
#              Prowadzacy: mgr. Karol Salwik             #
#********************************************************#


import atexit       # Modul definiujacy funkcje do wykonania przy zakonczeniu dzialania programu
import socket
import threading
max_users = 0       # Decydujemy o maksymalnej liczbie klientow, ktorzy zostana zaakceptowani

# Watek akceptujacy klientow - 1 dla wszystkich, uruchamiany w main
# Akceptuje zadanie polaczenia i przechowuje gniazdo jako obiekt oraz jego adres IP
def connectionThread(sock):
    while True:
        try:
            client, address = sock.accept()
        except:
            print("Accept error") 
            break
        print("{} podlaczyl sie.".format(address[0]))
        addresses[client] = address                                    #wpis do slownika klientow i odpowiadajacym im adresow
        threading.Thread(target=clientThread, args=(client,)).start()  #uruchomienie watku klienta


# Obsluga klienta, uruchomiona przez watek przyjmujacy klientow
# Kazdy klient ma swoj watek:
def clientThread(client):
  
    address = addresses[client][0]      # Odczytanie adresu ze slownika
    client.send("Witaj w pokoju rozmow!".encode("utf8"))
    try:
        user = getNickname(client)      # Pobieranie nazwy uzytkownika
    except:
        print("Blad ustawiania pseudonimu dla {}!".format(address))
        del addresses[client]
        client.close()
        return
    
    print("{} ustawil swoj pseudonim na {}!".format(address, user))
    users[client] = user               # Wpis w slowniku pseudonimow klientow jako wartosc
    

    #Obsluga klienta, gdy serwer przepelniony (ograniczenie nadane przez administratora)
    if len(users) > max_users :
        try:
            client.send("Witaj {}! Pokoj jest aktualnie przepelniony. Sprobuj ponownie pozniej!".format(user).encode("utf8"))
        except:
            print("Blad komunikacji z {} ({}).".format(address, user))
            
        print("Klient o adresie {} i nazwie uzytkownika {} zostal rozlaczony z powodu przepelnienia serwera.".format(address, user))
        del addresses[client]
        del users[client]
        client.close()
        return
    

    try:
        client.send("Witaj {}! Zostales podlaczony do czatu. Wpisz \"/pomoc\" aby wyswietlic liste dostepnych polecen!".format(user).encode("utf8"))
    except:
        print("Blad komunikacji z {} ({}).".format(address, user))
        del addresses[client]
        del users[client]
        client.close()
        return
    sendtoall("{} dolaczyl do pokoju rozmow!".format(user))

    # Obsluga polecen uzytkownika
    while True:
        try:
            msg = client.recv(2048).decode("utf8")
            
            #opuszczanie czatu przez klienta
            if msg == "/wyjdz":
                client.send("Opusciles czat!".encode("utf8"))
                del addresses[client]
                del users[client]
                client.close()
                print("{} ({}) rozlaczyl sie.".format(address, user))
                sendtoall("{} wyszedl z czatu.".format(user))
                break
            
            #sprawdzenie listy uzytkownikow online
            elif msg == "/online":
                onlineUsers = ', '.join([user for user in sorted(users.values())])
                client.send("Dostepni uzytkownicy: {}".format(onlineUsers).encode("utf8"))

            #sprawdzenie listy dostepnych komend
            elif msg == "/pomoc":
                client.send("Dostepne polecenia to /msg (wiadomosc prywatna), /changename, /online, /pomoc oraz /wyjdz".encode("utf8"))

            #zmiana nazwy uzytkownika
            elif msg == "/changename":
                try:
                  client.send("Rozpoczeto zmiane nazwy uzytkownika\n".encode("utf8"))
                  user = getNickname(client)      # Pobieranie nazwy uzytkownika
                  users[client] = user
                  client.send("Zmiana nazwy uzytkownika zakonczona powodzeniem!".encode("utf8"))
                except:
                  print("Blad zmiany pseudonimu dla {}!".format(address))
                  del addresses[client]
                  client.close()
                  return

            #wysylanie wiadomosci prywatnej
            elif msg == "/msg":
                client.send("Podaj grupe i nazwe uzytkownika w formacie np. '3 Antoni'".encode("utf8"))
                recipient_name = client.recv(2048).decode("utf8")

                if recipient_name in users.values(): #sprawdzanie czy uzytkownik istnieje przed nadaniem wiadomosci
                    client.send("Podaj wiadomosc".encode("utf8"))
                    recipient_msg = client.recv(2048).decode("utf8")
                    client.send("Wysylasz do {} prywatna wiadomosc: {}".format(recipient_name, recipient_msg).encode("utf8"))

                    for sock_rec, name_rec in users.items(): #iteracja po slowniku uzytkownikow
                        if name_rec == recipient_name:       #porownywanie wartosci w slowniku - nazwy uzytkownika
                            sock_rec.send("[prywatna] {}: {}".format(user, recipient_msg).encode("utf8"))
                        
                else:
                    client.send("Taki uzytkownik nie istnieje!".encode("utf8"))

            #wysylanie zwyklej wiadomosci do wszystkich
            else:
                print("{} ({}): {}".format(address, user, msg))
                sendtoall(msg, user)

        #problem z obsluga wiadomosci     
        except:
            print("{} ({}) rozlaczyl sie.".format(address, user))
            del addresses[client]
            del users[client]
            client.close()
            sendtoall("{} wyszedl z czatu.".format(user))
            break

# Pobranie pseudonimu od uzytkownika zarowno przy dolaczeniu do serwera, jak i uzyciu opcji /changename
def getNickname(client):
    client.send("Podaj numer swojej grupy laboratoryjnej: ".encode("utf8"))
    group = client.recv(2048).decode("utf8")
    client.send("A teraz podaj swoj pseudonim: ".encode("utf8"))
    nickname = client.recv(2048).decode("utf8")
    alreadyTaken = False        #Zmienna odpowiadajaca za rezerwacje pseudonimu
    if nickname in users.values():
        alreadyTaken = True
        while alreadyTaken:
            client.send("Ten pseudonim jest juz zajety. Wybierz inny:".encode("utf8"))
            nickname = client.recv(2048).decode("utf8")
            if nickname not in users.values():
                alreadyTaken = False
    return group + " " + nickname


# Nadanie 'msg' do wszystkich podlaczonych uzytkownikow
def sendtoall(msg, sentBy = ""):
    try:
        if sentBy == "":
            for user in users:
                user.send(msg.encode("utf8"))
        else:
            for user in users:
                user.send("{}: {}".format(sentBy, msg).encode("utf8"))
    except:
        print("Send error!")


# Zamkniecie wszystkich polaczen z gniazdem, ktore zakonczylo dzialanie programu
def cleanup():
    if len(addresses) != 0:
        for sock in addresses.keys():
            sock.close()
    print("Sprzatanie zakonczone.")


def main():
    atexit.register(cleanup)     # Zarejestrowanie cleanup() jako funkcji wykonwywanej przy zakonczeniu programu
    
    # Host i port dla uslugi czatu
    host = ""
    port = int(input("Podaj numer portu serwera: "))
    global max_users
    max_users = int(input("Podaj maksymalna ilosc uzytkownikow: "))

    # Tworzenie gniazda strumieniowego
    socketFamily = socket.AF_INET6
    socketType = socket.SOCK_STREAM
    serverSocket = socket.socket(socketFamily, socketType)
   
    serverSocket.bind((host, port))    # Powiazanie serverSocket pod okreslonym numerem portu
    serverSocket.listen()             # Uruchamia akceptowanie polaczen

    print("Serwer uruchomiony poprawnie!")
    print("Nasluchiwanie na nowe polaczenia na porcie {}.".format(port))

    # Utworzenie watku (funkcja connectionThread) do akceptowania polaczen przychodzacych
    connThread = threading.Thread(target=connectionThread, args=(serverSocket,))
    connThread.start()
    connThread.join()       # Przyjmowanie polaczen
    
    cleanup()               # Zamykanie gniazd
   
    serverSocket.close()    # Zamykanie serwera
    print("Serwer zostal zamkniety.")

# Slowniki pseudonimow oraz adresow IP z gniazdem (obiekt) jako klucz
users = {}
addresses = {}

if __name__ == "__main__":
    main()
    pass