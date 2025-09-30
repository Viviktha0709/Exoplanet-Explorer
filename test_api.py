import requests
import pandas as pd

url = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
query = "select pl_name,hostname,disc_year,pl_orbper,pl_rade from pscomppars"
params = {
    "query": query,
    "format": "json"
}

response = requests.get(url, params=params)
data = response.json()

df = pd.DataFrame(data)
print(df.head())
