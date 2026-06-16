import locale
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import serial
from escpos.printer import Usb, Network


from fastapi.responses import JSONResponse
from models import TicketData  # importa TicketData (y Producto si lo necesitas)



app = FastAPI()

# IMPORTANTE: Reemplaza esto con el origen o los orígenes reales de tu instancia de Odoo.
ODOC_ORIGINS = [
    "https://172.17.4.62", 
    "http://172.17.4.62",
    "https://172.17.4.62:8069",
    "https://moka-dev.agroasociaciones.com/",
    "http://moka-dev.agroasociaciones.com/",
    "https://moka-dev.agroasociaciones.com"
    "http://localhost:8070",
    "http://localhost"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ODOC_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


# Configuración del puerto serial
SERIAL_PORT = "/dev/ttyUSB2"
SERIAL_PORT = "/dev/ttyUSB1"
BAUDRATE = 9600

# Configuracion de impresora de ticket
VENDOR_ID = 0x1fc9
PRODUCT_ID = 0x2016


@app.get("/")
async def home():
    return {"message": "¡Bienvenido a mi API FastAPI!"}

@app.get("/scales_weight")
async def read_root(serial_port: str, baudrate: int):
    SERIAL_PORT = "/" + serial_port.replace('-','/')
    BAUDRATE = baudrate
    print("SERIAL_PORT",SERIAL_PORT)
    print("BAUDRATE",BAUDRATE)
   
    try:
        with serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1) as ser:
            peso_bruto = ser.readline().decode('utf-8').strip()
            print("peso_brutooooooooooooooooooooooooooooooooooooooooooooo",peso_bruto)
            return {"peso": peso_bruto}
    except serial.SerialException as e:
        return {"error": f"No se pudo leer desde {SERIAL_PORT}: {e}"}
    except Exception as e:
        return {"error": f"Error inesperado: {e}"}

@app.post("/print-ticket")
def print_ticket(data: TicketData):
    try:
        printer = Usb(VENDOR_ID, PRODUCT_ID)
        # printer = Network("172.17.5.242")
        # printer = Network(data.ip)

        # Título
        printer.set(align='center', bold=True, double_height=True)
        printer.text(f"{data.company_name} - {data.company_rif}\n")
        printer.text("TICKET DE COMPRA\n")
        printer.set(align='center', bold=False)
        printer.text(f"{data.purchase} - {data.date}\n")
        printer.text(f"RIF - {data.product_rif}\n\n")
        total_neto = 0.0

        for producto in data.products:
            # Nombre del producto
            printer.set(align='left', bold=True)
            printer.text(f"{producto.name[:32]}\n")  # limita a 32 caracteres

            # Encabezado solo una vez
            printer.set(bold=False, width=0.5, height=0.5)
            printer.text(f"{'Sacos':<6}{'Bruto':>11}{'Tara':>11}{'Neto':>10}{'Precio':>10}\n")
            printer.text("-" * 48 + "\n")

            # Datos
            printer.text(f"{producto.product_qty:<6.2f}{producto.qty_bruto:>10}{producto.qty_tara:>10}{producto.net_weight:>10}{producto.price_unit:>10}\n\n")

            total_neto += producto.net_weight

        # Total Neto centrado
        printer.set(align='center', bold=True)
        printer.text("-" * 35 + "\n")
        printer.text(f"TOTAL NETO: {total_neto:.2f} Kg\n")


        printer.cut()
        printer.close()  # Cierra la conexión USB y libera el recurso
        return JSONResponse(content={"status": "success", "message": "Impresión enviada correctamente"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})
    finally:
        try:
            printer.close()
        except:
            pass

@app.post("/print-ticket-adm")
def print_ticket_admin(data: TicketData):
    try:
        # printer = Usb(VENDOR_ID, PRODUCT_ID)
        printer = Usb(0x1fc9, 0x2016)
        # printer = Network("172.17.5.242")
        printer = Network(data.ip)
        locale.setlocale(locale.LC_ALL, 'es_VE.UTF-8')

        # Título
        printer.set(align='center', bold=True, double_height=True)
        printer.text(f"{data.company_name} \n {data.company_rif}\n")
        printer.text("TICKET DE COMPRA\n")
        printer.set(align='center', bold=False)
        printer.text(f"{data.purchase} - {data.date}\n")
        printer.text(f"C.I: - {data.product_rif}\n\n")
        total_neto = 0.0

        for producto in data.products:
            # Nombre del producto
            printer.set(align='left', bold=True, font="b")
            printer.text(f"{producto.name[:32]}\n")  # limita a 32 caracteres

            # Encabezado solo una vez
            # printer.set(bold=False, width=0, height=0)
            printer.set(font="b")
            if data.ticket_type == 'ticket_with_price':
                printer.text(f"{'Sacos':<8}{'Bruto':>14}{'Tara':>13}{'Neto':>13}{'Precio':>13}\n")
            else:
                printer.text(f"{'Sacos':<8}{'Bruto':>14}{'Tara':>18}{'Neto':>20}\n")


            printer.text("-" * 64 + "\n")
            product_qty =  locale.format_string('%.0f', producto.product_qty, grouping=True)
            qty_bruto =  locale.format_string('%.2f', producto.qty_bruto, grouping=True)
            qty_tara =  locale.format_string('%.2f', producto.qty_tara, grouping=True)
            net_weight =  locale.format_string('%.2f', producto.net_weight, grouping=True)
            price_unit =  locale.format_string('%.0f', producto.price_unit, grouping=True)

            # Datos
            if data.ticket_type == 'ticket_with_price':
                printer.text(f"{producto.product_qty:<6.2f}{qty_bruto:>15}{qty_tara:>15}{net_weight:>14}{price_unit:>11}\n\n")
            else:
                printer.text(f"{producto.product_qty:<6.2f}{qty_bruto:>16}{qty_tara:>19}{net_weight:>20}\n\n")


            total_neto += producto.net_weight
            product_qty_fmt =  locale.format_string('%.2f', total_neto, grouping=True)


        # Total Neto centrado
        printer.set(align='center', bold=True)
        printer.text("-" * 35 + "\n")
        printer.text(f"TOTAL NETO: {product_qty_fmt} Kg\n")

        # Sección de "Pagado en..."
        # printer.set(height=0, width=0)
        printer.text("\n") # Salto de línea para separar
        printer.text(f"Pagado en USD:")
        printer.text(" " * 50)
        printer.text("\n\n")
        printer.text(f"Pagado en Bs:")
        printer.text(" " * 51)
        printer.text("\n\n")
        printer.text(f"Titular:")
        printer.text(" " * 56 )
        printer.text("\n\n")
        printer.text(f"Cedula:")
        printer.text(" " * 57)
        printer.text("\n\n")
        printer.text(f"Nº Cuenta:")
        printer.text(" " * 54)
        printer.text("\n\n")
        printer.text(f"USD Pagados Por:")
        printer.text(" " * 48)
        printer.text("\n\n")
        printer.text(f"Bs Pagado Por:")
        printer.text(" " * 50)
        printer.text("\n\n")
        # A partir de aquí, las variables deben estar definidas en este método
        # --- BLOQUE COMPLETO DEL CUADRO ---
        borde_horizontal = "═"
        borde_vertical = "║"
        esquina_superior_izquierda = "╔"
        esquina_superior_derecha = "╗"
        esquina_inferior_izquierda = "╚"
        esquina_inferior_derecha = "╝"

        union_superior = "╦"
        union_central_izquierda = "╠"
        union_central_derecha = "╣"
        union_inferior = "╩"

        ancho_total = 64
        ancho_columna = (ancho_total - 3) // 2  # 47 - 3 bordes = 44. 44 / 2 = 22
        espacio = " "

        # --- El código que dibuja el cuadro ---
        # Línea superior
        printer.text(esquina_superior_izquierda + borde_horizontal * ancho_columna + union_superior + borde_horizontal * ancho_columna + esquina_superior_derecha + "\n")

        # Primera fila de la primera columna Y la primera fila de la segunda columna
        texto_fila1 = "Nombre:"
        texto_columna2 = "Firma y huella"
        printer.text(
            borde_vertical + f"{texto_fila1:<{ancho_columna}}" + borde_vertical + f"{texto_columna2:^{ancho_columna}}" + borde_vertical + "\n"
        )

        # Línea divisoria entre filas de la primera columna
        printer.text(union_central_izquierda + borde_horizontal * ancho_columna + union_central_derecha + espacio * ancho_columna + borde_vertical + "\n")

        texto_fila_ape = "Apellido:"
        printer.text(
            borde_vertical + f"{texto_fila_ape:<{ancho_columna}}" + borde_vertical + espacio * ancho_columna + borde_vertical + "\n"
        )
        printer.text(union_central_izquierda + borde_horizontal * ancho_columna + union_central_derecha + espacio * ancho_columna + borde_vertical + "\n")

        # Segunda fila de la primera columna
        texto_fila2 = "Cedula:"
        printer.text(
            borde_vertical + f"{texto_fila2:<{ancho_columna}}" + borde_vertical + espacio * ancho_columna + borde_vertical + "\n"
        )

        # Línea divisoria entre filas de la primera columna
        printer.text(union_central_izquierda + borde_horizontal * ancho_columna + union_central_derecha + espacio * ancho_columna + borde_vertical + "\n")

        # Tercera fila de la primera columna
        texto_fila3 = "Fecha:"
        printer.text(
            borde_vertical + f"{texto_fila3:<{ancho_columna}}" + borde_vertical + espacio * ancho_columna + borde_vertical + "\n"
        )

        # Línea inferior
        printer.text(esquina_inferior_izquierda + borde_horizontal * ancho_columna + union_inferior + borde_horizontal * ancho_columna + esquina_inferior_derecha + "\n")
        # --- FIN DEL BLOQUE DEL CUADRO ---

        printer.cut()
        printer.close()  # Cierra la conexión USB y libera el recurso
        return JSONResponse(content={"status": "success", "message": "Impresión enviada correctamente"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})
    finally:
        try:
            printer.close()
        except:
            pass