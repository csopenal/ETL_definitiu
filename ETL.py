import requests
import pandas as pd
import matplotlib.pyplot as plt
import os
from typing import Dict, Any, Optional, List

""" 
Este script se puede ejecutar directamente.
Generará una carpeta 'datos_salida' con:
- raw_users.csv
- clean_users.csv
- Los 3 gráficos .png
"""

def api_etl(url: str, results: int, seed: str) -> Optional[Dict[str, Any]]:
    """
    Función para extraer los datos de randomuser.me API y devolverlos en formato JSON.
    """
    params: Dict[str, str | int] = {
        "results": results,
        "seed": seed,
        "format": "json"
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error extrayendo los datos: {e}")
        return None

def transform(data: Optional[Dict[str, Any]]) -> Optional[pd.DataFrame]:
    """
    Transformar los datos JSON obtenidos, normalizar y devolver un DataFrame limpio.
    """
    if not data or "results" not in data:
        print("Error: No se recibieron datos válidos para transformar.")
        return None
    
    # Normalizar los Datos JSON a Dataframe
    # NOTA: Este 'df' representa los datos "crudos" en formato tabla
    df = pd.json_normalize(data["results"])
    
    # Columns to rename
    rename_colls = {
        "gender": "Genero",
        "name.first": "Nombre",
        "name.last": "Apellido",
        "nat": "Nacionalidad",
        "dob.age": "Edad",
        "location.country": "Pais"
    }
    
    columnas_seleccionadas = [col for col in rename_colls if col in df.columns]
    
    if "dob.age" not in columnas_seleccionadas:
        print("Error: La columna 'dob.age' (Edad) no se encontró en los datos.")
        return None
        
    df_clean = df[columnas_seleccionadas]
    df_clean = df_clean.rename(columns=rename_colls)
    
    # Conversión de tipos
    df_clean["Genero"] = df_clean["Genero"].astype("category")
    df_clean["Nacionalidad"] = df_clean["Nacionalidad"].astype("category")
    df_clean["Pais"] = df_clean["Pais"].astype("category")
    
    # Añadir 'RangoEdad'
    bins = [18, 30, 40, 50, 60, 70, 100]
    labels = ['18-29', '30-39', '40-49', '50-59', '60-69', '70+']
    df_clean['RangoEdad'] = pd.cut(df_clean['Edad'], bins=bins, labels=labels, right=False)
    
    return df_clean

# --- CORRECCIÓN ---
# La función ahora recibe 'output_dir' para saber dónde guardar los gráficos
def make_plots(df_clean: pd.DataFrame, output_dir: str) -> None:
    """
    Función para calcular estadísticas y generar plots en formato png.
    """
    # 1. Ya no creamos la carpeta aquí, se crea en __main__

    # 2b. Calcular Estadísticas
    print("\nCalculando estadísticas...")
    average_age = df_clean['Edad'].mean()
    gender_counts = df_clean['Genero'].value_counts()
    avg_age_by_gender = df_clean.groupby('Genero')['Edad'].mean()

    print(f"Edad media total: {average_age:.2f}")
    print(f"Conteo por género:\n{gender_counts}")
    print(f"Edad media por género:\n{avg_age_by_gender.round(2)}")
    
    # Gráfico 1: Distribución de Edades (Histograma)
    plt.figure(figsize=(10, 6))
    df_clean['Edad'].plot(kind='hist', bins=20, edgecolor='black', color='lightgreen')
    plt.title(f'Distribución de Edades ({len(df_clean)} Usuarios)')
    plt.xlabel('Edad')
    plt.ylabel('Frecuencia')
    plt.axvline(average_age, color='red', linestyle='dashed', linewidth=2, label=f'Edad Media: {average_age:.2f}')
    plt.legend()
    # Usamos el 'output_dir'
    plot_path_age = os.path.join(output_dir, 'distribucion_edad.png')
    plt.savefig(plot_path_age)
    plt.close()
    print(f"Gráfico de edad guardado en: {plot_path_age}")

    # Gráfico 2: Barras Nacionalidad
    country_counts = df_clean['Pais'].value_counts()
    plt.figure(figsize=(12, 6))
    country_counts.head(20).plot(kind='bar', color='lightcoral')
    plt.title('Distribución de Usuarios por País (Top 20)')
    plt.xlabel('País')
    plt.ylabel('Cantidad de Usuarios')
    plt.xticks(rotation=75)
    plt.tight_layout()
    # Usamos el 'output_dir'
    plot_path_country = os.path.join(output_dir, 'barras_nacionalidad.png')
    plt.savefig(plot_path_country)
    plt.close()
    print(f"Gráfico de barras nacionalidad guardado en: {plot_path_country}")

    # Grafico 3: Barras de usuarios por rango de edad
    rango_counts = df_clean['RangoEdad'].value_counts().sort_index()
    plt.figure(figsize=(8, 5))
    rango_counts.plot(kind='bar', color='orange', edgecolor='black')
    plt.title('Número de Usuarios por Rango de Edad')
    plt.xlabel('Rango de Edad')
    plt.ylabel('Número de Usuarios')
    plt.xticks(rotation=0)
    plt.tight_layout()
    # Usamos el 'output_dir'
    plot_path_rango = os.path.join(output_dir, 'barras_rango_edad.png')
    plt.savefig(plot_path_rango)
    plt.close()
    print(f"Gráfico de barras de rango de edades guardado en: {plot_path_rango}")


if __name__ == "__main__":
    
    print("Iniciando Proceso ETL...")
    
    # --- Parámetros ---
    API_URL = "https://randomuser.me/api"
    NUM_USERS = 1000
    API_SEED = "1234"
    # --- NUEVO: Directorio de salida unificado ---
    OUTPUT_DIR = "datos_salida"

    # --- NUEVO: Crear directorio de salida ---
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 1. Extraer
    print(f"Extrayendo {NUM_USERS} usuarios de la API...")
    data = api_etl(url=API_URL, results=NUM_USERS, seed=API_SEED)
    
    if data:
        # --- AÑADIDO: Guardar raw_users.csv ---
        try:
            print("Normalizando y guardando datos crudos...")
            # Normalizamos el JSON para tener la tabla "raw"
            df_raw = pd.json_normalize(data["results"])
            raw_path = os.path.join(OUTPUT_DIR, "raw_users.csv")
            # Guardamos el CSV
            df_raw.to_csv(raw_path, index=False)
            print(f"Datos crudos guardados en: {raw_path}")
        except Exception as e:
            print(f"Error al guardar raw_users.csv: {e}")
        
        # 2. Transformar
        print("Transformando datos...")
        df_usuarios = transform(data) # df_usuarios es el DataFrame limpio
        
        if df_usuarios is not None:
            # --- AÑADIDO: Guardar clean_users.csv ---
            clean_path = os.path.join(OUTPUT_DIR, "clean_users.csv")
            # Guardamos el CSV
            df_usuarios.to_csv(clean_path, index=False)
            print(f"Datos limpios guardados en: {clean_path}")

            # 3. Cargar (Generar gráficos)
            print("Generando gráficos...")
            # Pasamos el directorio de salida a la función de gráficos
            make_plots(df_usuarios, OUTPUT_DIR)
            
            print(f"\nProceso ETL completado. Archivos guardados en la carpeta '{OUTPUT_DIR}'.")
        else:
            print("Error durante la transformación, no se generarán gráficos ni CSV limpio.")
    else:
        print("Error durante la extracción, el proceso se ha detenido.")