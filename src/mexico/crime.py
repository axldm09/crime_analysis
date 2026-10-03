import io
from urllib.parse import parse_qs, urlparse
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
import requests
from zipfile import ZipFile


# El link de onedrive.aspx es interno del tenant y redirige a login.microsoftonline.com.
# El que si funciona sin cuenta es el link de compartir publicado en gob.mx/sesnsp:
url_mex = "https://sspcgob-my.sharepoint.com/:u:/g/personal/cni_sspc_gob_mx/IQAFSS3C6xafQoJYFch7kJYJARHHIpnBoTyD_tVhtq0HZic?e=AxKIR4"
url_2 = "https://sspcgob-my.sharepoint.com/:u:/r/personal/cni_sspc_gob_mx/Documents/ID/08.ID_DA/Estatal-Delitos-2015-2025_jul2026.zip?d=w2e160ef6aeb54cfd978715a7a0a083c4&csf=1&web=1&e=VEBQfd"

def download_sharepoint_zip(share_url):
    """Abre un link publico de SharePoint y regresa el zip que hay detras."""
    session = requests.Session()
    session.headers["User-Agent"] = "Mozilla/5.0"

    # Esta primera vuelta es la que deja las cookies de invitado y resuelve
    # la ruta real del archivo dentro de la query del visor.
    viewer = session.get(share_url)
    viewer.raise_for_status()
    source_url = parse_qs(urlparse(viewer.url).query)["id"][0]

    download_url = viewer.url.split("?")[0].replace("onedrive.aspx", "download.aspx")
    response = session.get(download_url, params={"SourceUrl": source_url})
    response.raise_for_status()
    return ZipFile(io.BytesIO(response.content))


def read_crime_data(share_url=url_mex):
    """Regresa el CSV de incidencia delictiva que viene dentro del zip."""
    with download_sharepoint_zip(share_url) as archive:
        name = next(n for n in archive.namelist() if n.lower().endswith(".csv"))
        return pd.read_csv(archive.open(name), encoding="utf-8")

def lambda_handler():
    df = read_crime_data()
    print(df.shape)

    
    for col in df.columns:
        if df[col].dtype == 'object' or df[col].nunique() < 20:
            print(f"\n{col}: {df[col].nunique()} unique values")
            #print(df[col].unique()[:80])  # Show first 10 unique values
    
    print(df.sum().notnull)
    
    entidad_crimen = df.groupby(['Entidad', 'Tipo de delito', 'Subtipo de delito']).sum().reset_index()
    
    print(entidad_crimen.shape)      

if __name__ == "__main__":
    
    lambda_handler()
