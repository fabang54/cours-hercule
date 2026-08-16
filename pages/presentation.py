```python
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

st.header("📞 Prise de contact")

st.write(
    """
    Vous souhaitez obtenir des informations sur les cours,
    les tarifs ou les disponibilités ?
    """
)


# =========================
# APPEL DIRECT
# =========================

col1, col2 = st.columns([1, 2])

with col1:

    st.subheader("📞 Appelez-nous")

with col2:

    st.markdown(
        """
        ### **06 XX XX XX XX**

        N'hésitez pas à appeler pour obtenir
        un premier renseignement.
        """
    )


st.divider()


# =========================
# ÊTRE RECONTACTÉ
# =========================

st.subheader("📩 Vous préférez être recontacté(e) ?")

st.write(
    """
    Laissez simplement votre prénom et votre numéro
    de téléphone. Vous pourrez également préciser
    votre demande si vous le souhaitez.
    """
)


if "contact_envoye" not in st.session_state:

    st.session_state.contact_envoye = False


if st.session_state.contact_envoye:

    st.success(
        "✅ Votre demande a bien été envoyée. "
        "Merci ! Nous vous recontacterons prochainement."
    )

    if st.button("Nouvelle demande"):

        st.session_state.contact_envoye = False

        st.rerun()


else:

    with st.form("formulaire_contact"):

        prenom_parent = st.text_input(
            "Votre prénom *",
            placeholder="Ex. Sophie"
        )

        telephone = st.text_input(
            "Votre numéro de téléphone *",
            placeholder="Ex. 06 12 34 56 78"
        )

        message = st.text_area(
            "Votre message (facultatif)",
            placeholder=(
                "Quelques mots sur votre demande..."
            )
        )

        envoyer = st.form_submit_button(
            "📨 Être recontacté(e)"
        )


        if envoyer:

            if not prenom_parent.strip():

                st.error(
                    "Merci d'indiquer votre prénom."
                )

            elif not telephone.strip():

                st.error(
                    "Merci d'indiquer votre numéro de téléphone."
                )

            else:

                # ------------------------------------------------
                # POUR LE MOMENT :
                # on confirme simplement la demande.
                #
                # L'enregistrement Supabase et l'envoi
                # automatique d'un e-mail seront ajoutés
                # ensuite.
                # ------------------------------------------------

                st.session_state.contact_envoye = True

                st.rerun()


# =========================
# CONFIDENTIALITÉ
# =========================

st.caption(
    "🔒 Vos coordonnées sont utilisées uniquement "
    "pour répondre à votre demande."
)


st.divider()


# =========================
# PIED DE PAGE
# =========================

st.caption(
    "Cours Hercule — Accompagnement scolaire personnalisé"
)
```
