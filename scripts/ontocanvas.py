"""Where OntoCanvas is deployed: the one address every OntoCanvas link and embed in ADIRO opens.

Read by `generate_docs.py` (the ontology pages) and `pr_guidance.py` (the ADIRO Bot's preview links), so the two cannot
drift apart when the deployment moves. Standard library only: `pr_guidance.py` runs without the docs dependencies.
"""

# The organisation's OntoCanvas deployment.
ONTOCANVAS_URL = "https://burohappoldmachinelearning.github.io/OntoCanvas/"

# OntoCanvas branding icon, served by that deployment.
ONTOCANVAS_ICON_URL = f"{ONTOCANVAS_URL}OntoCanvas.png"
