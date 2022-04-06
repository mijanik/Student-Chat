#********************************************************#
# Autorzy: Milosz Janik, Kacper Czepiec i Antoni Kijania #
#       Programowanie Sieciowe - zajecia projektowe      #
#           AGH - Elektronika i Telekomunikacja          #
#              Prowadzacy: mgr. Karol Salwik             #
#********************************************************#

import socket
import datetime
import threading

def currentTime():
    # Pozyskanie lokalnego czasu w formacie HH:MM:SS
    now = datetime.datetime.now()
    formattedTime = now.strftime("%H:%M:%S")
    return formattedTime

# Watek 1 - Obsluga wysylania wiadomości do serwera
def send(sock):
    while threadFlag:
        try:
            wiadomosc = input()
            sock.send(wiadomosc.encode("utf8"))
        except:
            print("Send error")
            break

# Watek 2 - Obsluga odbierania wiadomości z serwera
def receive(sock):
    while threadFlag:
        try:
            wiadomosc = sock.recv(2048).decode()
            if wiadomosc:
                print("[{}] {}".format(currentTime(), wiadomosc))
            else:
                # Kiedy serwer zamyka gniazdo, otrzymane wiadomości sa puste
                break
        except:
            print("Receive error")
            break


# Globalna flaga uzywana do zamykania procesow
threadFlag = True

def main():
  
    global threadFlag #Flaga dzialania komunikacji, uzywana do zamykania watkow w przypadku gdy jeden z nich przestaje dzialac
    
    host = input("Podaj adres IP serwera: ")
    port = int(input("Podaj numer portu serwera: "))
    
    # Utworzenie gniazda TCP
    socketFamily = socket.AF_INET6
    socketType = socket.SOCK_STREAM
    clientSocket = socket.socket(socketFamily, socketType)
   
    # Laczenie z serwerem
    clientSocket.connect((host, port))
    
    # Utworzenie dwoch watkow dla wysylania i odbierania wiadomości z serwera (kazdy ma swoja funkcje wyzej zdefiniowana)
    sendingThread = threading.Thread(target=send, args=(clientSocket,))
    receivingThread = threading.Thread(target=receive, args=(clientSocket,))
    
    # Uruchomienie watkow
    receivingThread.start()
    sendingThread.start()

    # Sprawdzenie czy oba watki sa 'zywe'
    while receivingThread.is_alive() and sendingThread.is_alive():
        continue
    threadFlag = False

    # Zamkniecie gniazda
    clientSocket.close()
    print("\nPolaczenie zostalo zamkniete. Wcisnij Enter aby zamknac aplikacje.")


if __name__ == "__main__":
    main()
    pass