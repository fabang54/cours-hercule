import streamlit as st

st.set_page_config(
    page_title="Cours Hercule",
    page_icon="📚",
    layout="wide"
)

# =========================
# EN-TÊTE
# =========================

st.title("📚 Cours Hercule")

st.subheader(
    "Cours particuliers de mathématiques, physique et informatique"
)

st.write(
    """
    **Comprendre • Progresser • Réussir**

    Un accompagnement personnalisé adapté au niveau,
    aux objectifs et aux besoins de chaque élève.
    """
)

st.divider()

# =========================
# MATIÈRES
# =========================

st.header("Nos matières")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("📐 Mathématiques")
    st.write(
        """
        Collège, lycée et enseignement supérieur.

        • Compréhension du cours
        • Exercices et méthodes
        • Préparation aux contrôles et examens
        """
    )

with col2:
    st.subheader("⚛️ Physique")
    st.write(
        """
        • Compréhension des notions
        • Méthodes de résolution
        • Exercices d'application
        """
    )

with col3:
    st.subheader("💻 Informatique")
    st.write(
        """
        • Python
        • SQL
        • Bases de données
        • Algorithmique
        """
    )

st.divider()

# =========================
# MODALITÉS
# =========================

st.header("Nos modalités")

col1, col2 = st.columns(2)

with col1:
    st.subheader("💻 Cours à distance")
    st.write(
        """
        Cours en visioconférence depuis votre domicile,
        avec accompagnement personnalisé.
        """
    )

with col2:
    st.subheader("🏠 Cours en présentiel")
    st.write(
        """
        Cours en présentiel selon les possibilités
        géographiques.
        """
    )

st.divider()

# =========================
# POUR QUI ?
# =========================

st.header("Un accompagnement adapté")

st.write(
    """
    Les séances peuvent répondre à différents objectifs :

    • reprendre les bases ;
    • comprendre une notion difficile ;
    • progresser en autonomie ;
    • préparer un contrôle ;
    • préparer un examen ;
    • bénéficier d'un suivi régulier.
    """
)

st.divider()

# =========================
# CONTACT
# =========================

st.header("📞 Contact")

st.write(
    """
    Vous souhaitez obtenir des informations ou organiser
    un premier échange ?
    """
)

# =========================
# CONTACT TELEPHONIQUE
# =========================

st.subheader("📞 Appelez-nous directement")

st.markdown(
    """
    ### **06 XX XX XX XX**
    """
)

st.write(
    "N'hésitez pas à appeler pour obtenir un premier renseignement."
)

# =========================
# CONTACT PAR EMAIL
# =========================

st.subheader("✉️ Écrivez-nous")

st.write(
    "Vous pouvez également nous contacter par e-mail :"
)

st.markdown(
    "[📧 TON_EMAIL@gmail.com](mailto:TON_EMAIL@gmail.com)"
)

st.divider()

# =========================
# PIED DE PAGE
# =========================

st.caption(
    "Cours Hercule — Accompagnement scolaire personnalisé"
)
