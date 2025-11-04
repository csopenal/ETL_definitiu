import requests
import pandas as pd
import matplotlib.pyplot as plt
import os
from typing import Dict, Any, Optional, List

"""
Este script se puede ejecutar directamente.
Generará una carpeta 'data_output' con:
- raw_users.csv
- clean_users.csv
- statistics_summary.csv  <-- NUEVO
- Los 3 gráficos .png
"""

# --- Constantes de Configuración ---
API_URL = "https://randomuser.me/api"
NUM_USERS = 1000
API_SEED = "1234"
OUTPUT_DIR = "data_output"


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
        response.raise_for_status()  # Lanza un error para respuestas HTTP 4xx/5xx
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
    df = pd.json_normalize(data["results"])
    
    # --- Definición de la transformación ---
    RENAME_COLS = {
        "gender": "Genero",
        "name.first": "Nombre",
        "name.last": "Apellido",
        "nat": "Nacionalidad",
        "dob.age": "Edad",
        "location.country": "Pais"
    }
    
    # Constantes para rangos de edad
    BINS = [18, 30, 40, 50, 60, 70, 100]
    LABELS = ['18-29', '30-39', '40-49', '50-59', '60-69', '70+']
    # -------------------------------------

    # Asegurarse de que solo seleccionamos columnas que existen
    columnas_seleccionadas = [col for col in RENAME_COLS if col in df.columns]
    
    if "dob.age" not in columnas_seleccionadas:
        print("Error: La columna 'dob.age' (Edad) no se encontró en los datos.")
        return None
        
    # Aplicar selección y renombrado. Usar .copy() para evitar SettingWithCopyWarning
    df_clean = df[columnas_seleccionadas].rename(columns=RENAME_COLS).copy()
    
    # Conversión de tipos para ahorrar memoria y optimizar
    df_clean["Genero"] = df_clean["Genero"].astype("category")
    df_clean["Nacionalidad"] = df_clean["Nacionalidad"].astype("category")
    df_clean["Pais"] = df_clean["Pais"].astype("category")
    
    # Añadir 'RangoEdad'
    df_clean['RangoEdad'] = pd.cut(df_clean['Edad'], bins=BINS, labels=LABELS, right=False)
    
    return df_clean


def calculate_statistics(df_clean: pd.DataFrame) -> Dict[str, Any]:
    """
    Calcula estadísticas descriptivas clave del DataFrame limpio.
    """
    print("\nCalculando estadísticas...")
    stats = {
        "average_age": df_clean['Edad'].mean(),
        "gender_counts": df_clean['Genero'].value_counts(),
        "avg_age_by_gender": df_clean.groupby('Genero')['Edad'].mean()
    }
    return stats


def save_statistics_to_csv(stats: Dict[str, Any], output_dir: str) -> None:
    """
    Guarda las estadísticas calculadas en un único archivo CSV en formato largo (tidy).
    """
    stats_list = []

    # 1. Edad Media Total
    stats_list.append({
        "Metrica": "Edad_Media_Total",
        "Categoria": "General",
        "Valor": stats["average_age"]
    })

    # 2. Conteo por Género
    for category, value in stats["gender_counts"].items():
        stats_list.append({
            "Metrica": "Conteo_Genero",
            "Categoria": category,
            "Valor": value
        })

    # 3. Edad Media por Género
    for category, value in stats["avg_age_by_gender"].items():
        stats_list.append({
            "Metrica": "Edad_Media_Genero",
            "Categoria": category,
            "Valor": value
        })

    # Convertir a DataFrame y guardar
    try:
        stats_df = pd.DataFrame(stats_list)
        stats_df["Valor"] = stats_df["Valor"].round(2)
        
        stats_path = os.path.join(output_dir, "statistics_summary.csv")
        stats_df.to_csv(stats_path, index=False)
        print(f"Estadísticas guardadas en: {stats_path}")
    except Exception as e:
        print(f"Error al guardar el CSV de estadísticas: {e}")


def make_plots(df_clean: pd.DataFrame, stats: Dict[str, Any], output_dir: str) -> None:
    """
    Función para generar y guardar gráficos en formato png.
    Recibe las estadísticas precalculadas.
    """
    print("Generando gráficos...")
    average_age = stats['average_age'] # Obtener la estadística precalculada

    # Gráfico 1: Distribución de Edades (Histograma)
    try:
        plt.figure(figsize=(10, 6))
        df_clean['Edad'].plot(kind='hist', bins=20, edgecolor='black', color='lightgreen')
        plt.title(f'Distribución de Edades ({len(df_clean)} Usuarios)')
        plt.xlabel('Edad')
        plt.ylabel('Frecuencia')
        plt.axvline(average_age, color='red', linestyle='dashed', linewidth=2, label=f'Edad Media: {average_age:.2f}')
        plt.legend()
        
        plot_path_age = os.path.join(output_dir, 'distribucion_edad.png')
        plt.savefig(plot_path_age)
        plt.close()
        print(f"Gráfico de edad guardado en: {plot_path_age}")
    except Exception as e:
        print(f"Error al generar gráfico de edad: {e}")

    # Gráfico 2: Barras Nacionalidad
    try:
        country_counts = df_clean['Pais'].value_counts()
        plt.figure(figsize=(12, 6))
        country_counts.head(20).plot(kind='bar', color='lightcoral')
        plt.title('Distribución de Usuarios por País (Top 20)')
        plt.xlabel('País')
        plt.ylabel('Cantidad de Usuarios')
        plt.xticks(rotation=75)
        plt.tight_layout()
        
        plot_path_country = os.path.join(output_dir, 'barras_nacionalidad.png')
        plt.savefig(plot_path_country)
        plt.close()
        print(f"Gráfico de barras nacionalidad guardado en: {plot_path_country}")
    except Exception as e:
        print(f"Error al generar gráfico de nacionalidad: {e}")

    # Grafico 3: Barras de usuarios por rango de edad
    try:
        rango_counts = df_clean['RangoEdad'].value_counts().sort_index()
        plt.figure(figsize=(8, 5))
        rango_counts.plot(kind='bar', color='orange', edgecolor='black')
        plt.title('Número de Usuarios por Rango de Edad')
        plt.xlabel('Rango de Edad')
        plt.ylabel('Número de Usuarios')
        plt.xticks(rotation=0)
        plt.tight_layout()
        
        plot_path_rango = os.path.join(output_dir, 'barras_rango_edad.png')
        plt.savefig(plot_path_rango)
        plt.close()
        print(f"Gráfico de barras de rango de edades guardado en: {plot_path_rango}")
    except Exception as e:
        print(f"Error al generar gráfico de rango de edad: {e}")


if __name__ == "__main__":
    
    print("Iniciando Proceso ETL...")
    
    # Crear directorio de salida
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 1. Extraer
    print(f"Extrayendo {NUM_USERS} usuarios de la API...")
    data = api_etl(url=API_URL, results=NUM_USERS, seed=API_SEED)
    
    if data:
        # --- Guardar datos crudos ---
        try:
            print("Normalizando y guardando datos crudos...")
            df_raw = pd.json_normalize(data["results"])
            raw_path = os.path.join(OUTPUT_DIR, "raw_users.csv")
            df_raw.to_csv(raw_path, index=False)
            print(f"Datos crudos guardados en: {raw_path}")
        except Exception as e:
            print(f"Error al guardar raw_users.csv: {e}")
        
        # 2. Transformar
        print("Transformando datos...")
        df_usuarios = transform(data) # df_usuarios es el DataFrame limpio
        
        if df_usuarios is not None:
            # --- Guardar datos limpios ---
            clean_path = os.path.join(OUTPUT_DIR, "clean_users.csv")
            df_usuarios.to_csv(clean_path, index=False)
            print(f"Datos limpios guardados en: {clean_path}")

            # 3. Calcular y Cargar Estadísticas
            # Calcular estadísticas
            stats = calculate_statistics(df_usuarios)
            
            # Imprimir estadísticas en consola
            print(f"Edad media total: {stats['average_age']:.2f}")
            print(f"Conteo por género:\n{stats['gender_counts']}")
            print(f"Edad media por género:\n{stats['avg_age_by_gender'].round(2)}")

            # --- NUEVO: Guardar estadísticas en CSV ---
            save_statistics_to_csv(stats, OUTPUT_DIR)

            # 4. Cargar (Generar gráficos)
            # Pasamos el DataFrame Y las estadísticas precalculadas
            make_plots(df_usuarios, stats, OUTPUT_DIR)
            
            print(f"\nProceso ETL completado. Archivos guardados en la carpeta '{OUTPUT_DIR}'.")
        else:
            print("Error durante la transformación, no se generarán gráficos ni CSV limpio.")
    else:
        print("Error durante la extracción, el proceso se ha detenido.")
