import asyncio, json, serial, time
from urllib.request import urlopen

id = "unik"
key = "pass"
ser = serial.Serial('COM11', 115200, timeout = 0)

async def receiveFromAndroid(reader, writer, loop):
    while True:
        data = await reader.read(512)
        print(data.decode())
        
        if not data:
            print('not data')
            break
        
        try: #jika program dijalankan dan terjadi error, maka program tidak langsung berhenti dan tetap dijalankan
            jobj = json.loads(data.decode()) #data yang masuk dibaca sebagai json dan dimasukkan ke variable json object

            if jobj.get('id') is None or jobj.get('key') is None or jobj.get('command') is None: #jika payload tidak lengkap maka kirim pesan error ke android
                message = {'error':'invalid message'}
                writer.write(json.dumps(message).encode())
                writer.write(b'\r\n')
                await writer.drain()
                continue #skip fungsi yang ada di bawah continue
            if jobj.get('id') != id or jobj.get('key') != key:#jika pass dan key tidak sama maka kirim pesan error
                message = {'error':'wrong id or key'}
                writer.write(json.dumps(message).encode())
                writer.write(b'\r\n')
                await writer.drain()
                continue
            if jobj.get('command')=='register':#jika register sukses maka kirim pesan sukses
                message ={'success':'login succedd'}
                writer.write(json.dumps(message).encode())
                writer.write(b'\r\n')
                await writer.drain()
                continue

            print('android ', jobj.get('command'))
            ser.write(jobj.get('command').encode(encoding="ascii"))
            ser.write('\n'.encode(encoding="ascii"))#kirim ke arduino
        except ValueError:
            print('json value error')
        except Exception as e:
            print('Exception: ', str(e))

async def send_period(reader, writer):
    loop = asyncio.get_event_loop()
    task = loop.create_task(receiveFromAndroid(reader, writer, loop))
    reading = ''

    while True:
        if ser.inWaiting() > 0:
            c = ser.read().decode()
            if c != '\n':
                reading = reading + c
            else:
                print('arduino :' + reading)
                reading = reading + '\n'
                writer.write(reading.encode())
                await writer.drain()
                reading = ""
        else:
            await asyncio.sleep(0.1)

def isInternetOn():
    try:
        urlopen('https://google.com', timeout = 10)
        return True
    except:
        return False

def main():
    while isInternetOn() == False:
        print('py wait for internet connection')
        time.sleep(2)
    print('internet connected')
    loop = asyncio.get_event_loop()
    coro = asyncio.start_server(send_period, '0.0.0.0', 5000, loop=loop)
    print("before run coro")
    server = loop.run_until_complete(coro)
    print('Serving on {}'.format(server.sockets[0].getsockname()))
    loop.run_forever()
    # Close the server
    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()

if __name__ == "__main__":
    main()
