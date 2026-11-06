"""Pruebas automatizadas de Kirby's Dream Shop con Selenium y Firefox.

Se ejecutan contra la URL publica de Render. Los selectores salen del HTML real
de la tienda (index.html y functions.js):
  #name, #price, #addProduct, #productsGrid, .productCard, .productName,
  .productPrice, .delete-btn, #totalProducts, #totalValue

La tienda no tiene campo de cantidad; la prueba negativa se hace con el campo
de precio (#price), que es el unico campo numerico.

Uso:
    python test_tienda_selenium.py [URL] [--headless]
"""

import sys
import time
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import NoAlertPresentException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

URL = "https://versionamiento-yerlan-suastegui.onrender.com/"
EVIDENCIAS = Path(__file__).parent / "evidencias"
PRODUCTO_PRUEBA = "Kirby Selenium Test"
PRECIO_PRUEBA = "12.50"


def contar_productos(driver):
    return len(driver.find_elements(By.CSS_SELECTOR, "#productsGrid .productCard"))


def buscar_tarjetas(driver, nombre):
    return [
        card for card in driver.find_elements(By.CSS_SELECTOR, "#productsGrid .productCard")
        if card.find_element(By.CSS_SELECTOR, ".productName").text == nombre
    ]


def llenar_formulario(driver, nombre, precio):
    campo_nombre = driver.find_element(By.ID, "name")
    campo_precio = driver.find_element(By.ID, "price")
    campo_nombre.clear()
    campo_nombre.send_keys(nombre)
    campo_precio.clear()
    campo_precio.send_keys(precio)


def captura(driver, archivo, elemento=None):
    if elemento is not None:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elemento)
        time.sleep(0.3)
    else:
        driver.execute_script("window.scrollTo(0, 0);")
    driver.save_screenshot(str(EVIDENCIAS / archivo))


def prueba_agregar(driver, wait):
    antes = contar_productos(driver)
    llenar_formulario(driver, PRODUCTO_PRUEBA, PRECIO_PRUEBA)
    driver.find_element(By.ID, "addProduct").click()

    wait.until(lambda d: contar_productos(d) == antes + 1)
    tarjetas = buscar_tarjetas(driver, PRODUCTO_PRUEBA)
    assert len(tarjetas) == 1, "El producto no aparece en el catalogo"

    precio = tarjetas[0].find_element(By.CSS_SELECTOR, ".productPrice").text
    assert precio == "$12.50", f"Precio mostrado incorrecto: {precio}"
    total = driver.find_element(By.ID, "totalProducts").text
    assert total == str(antes + 1), f"El resumen muestra {total} productos"

    captura(driver, "11_selenium_agregar.png", tarjetas[0])
    return f"productos {antes} -> {antes + 1}, precio mostrado {precio}"


def prueba_eliminar(driver, wait):
    tarjetas = buscar_tarjetas(driver, PRODUCTO_PRUEBA)
    assert tarjetas, "No existe el producto de prueba para eliminar"
    antes = contar_productos(driver)

    tarjetas[0].find_element(By.CSS_SELECTOR, ".delete-btn").click()

    wait.until(lambda d: contar_productos(d) == antes - 1)
    assert not buscar_tarjetas(driver, PRODUCTO_PRUEBA), "El producto sigue en el catalogo"
    total = driver.find_element(By.ID, "totalProducts").text
    assert total == str(antes - 1), f"El resumen muestra {total} productos"

    captura(driver, "12_selenium_eliminar.png")
    return f"productos {antes} -> {antes - 1}, '{PRODUCTO_PRUEBA}' ya no aparece"


def prueba_precio_negativo(driver, wait):
    nombre = "Kirby Precio Negativo"
    antes = contar_productos(driver)
    valor_antes = driver.find_element(By.ID, "totalValue").text

    llenar_formulario(driver, nombre, "-10")
    valor_campo = driver.find_element(By.ID, "price").get_attribute("value")
    captura(driver, "13_selenium_negativo_formulario.png")
    driver.find_element(By.ID, "addProduct").click()

    try:
        alerta = wait.until(EC.alert_is_present())
        mensaje = alerta.text
        alerta.accept()
    except (TimeoutException, NoAlertPresentException):
        mensaje = None

    time.sleep(1)
    assert mensaje is not None, "No se mostro ningun aviso al usar un precio negativo"
    assert contar_productos(driver) == antes, "Se agrego un producto con precio negativo"
    assert not buscar_tarjetas(driver, nombre), "El producto con precio negativo aparece en el catalogo"
    assert driver.find_element(By.ID, "totalValue").text == valor_antes, "El valor total cambio"

    captura(driver, "14_selenium_negativo_resultado.png")
    return f"el campo acepto escribir '{valor_campo}', la app mostro el aviso \"{mensaje}\" y no agrego el producto"


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    url = args[0] if args else URL
    EVIDENCIAS.mkdir(exist_ok=True)

    options = Options()
    if "--headless" in sys.argv:
        options.add_argument("-headless")

    # Selenium Manager localiza Firefox y descarga GeckoDriver si hace falta
    driver = webdriver.Firefox(options=options)
    driver.set_window_size(1280, 900)
    wait = WebDriverWait(driver, 10)
    resultados = []

    try:
        print(f"Firefox {driver.capabilities.get('browserVersion')} | URL: {url}")
        driver.get(url)
        # Render (plan gratuito) puede tardar en despertar el servicio
        WebDriverWait(driver, 90).until(EC.presence_of_element_located((By.ID, "addProduct")))
        wait.until(lambda d: d.find_element(By.ID, "totalProducts").text != "0" or contar_productos(d) == 0)
        time.sleep(1)
        print(f"Productos iniciales: {contar_productos(driver)}\n")

        pruebas = [
            ("Prueba 1: agregar producto", prueba_agregar),
            ("Prueba 2: eliminar producto", prueba_eliminar),
            ("Prueba 3: precio negativo", prueba_precio_negativo),
        ]
        for nombre, prueba in pruebas:
            try:
                detalle = prueba(driver, wait)
                resultados.append(True)
                print(f"[PASS] {nombre} - {detalle}")
            except Exception as error:
                resultados.append(False)
                print(f"[FAIL] {nombre} - {error}")
    finally:
        driver.quit()

    print(f"\nResultado: {sum(resultados)} de {len(resultados)} pruebas aprobadas")
    sys.exit(0 if all(resultados) else 1)


if __name__ == "__main__":
    main()
