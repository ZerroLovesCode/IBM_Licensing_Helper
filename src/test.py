from pathlib import Path
from oracle import search_official_ibm_documentation

base_path = Path(__file__)
print(base_path.parent)
print(search_official_ibm_documentation.invoke({"query": "What is PVU?"}))