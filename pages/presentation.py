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

st.subheader("📞 Appelez-nous directement")

st.markdown(
    """
    ## **06 XX XX XX XX**
    """
)


# =========================
# EMAIL
# =========================

st.subheader("✉️ Écrivez-nous")

st.markdown(
    """
    📧 **TON_ADRESSE_EMAIL**
    """
)

st.write(
    "N'hésitez pas à nous contacter pour obtenir un premier renseignement."
)

st.divider()


# =========================
# ÊTRE RECONTACTÉ
# =========================

st.subheader("📩 Vous préférez être recontacté(e) ?")

st.write(
    """
    Laissez simplement votre prénom et votre numéro
    de téléphone.
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

    with st.form("formulaire_contact_telephone"):

        prenom_parent = st.text_input(
            "Votre prénom *",
            placeholder="Ex. Sophie"
        )

        telephone = st.text_input(
            "Votre numéro de téléphone *",
            placeholder="Ex. 06 12 34 56 78"
        )

        message_telephone = st.text_area(
            "Votre message",
            placeholder="Quelques mots sur votre demande..."
        )

        envoyer_telephone = st.form_submit_button(
            "📨 Être recontacté(e)"
        )

        if envoyer_telephone:

            if not prenom_parent.strip():

                st.error(
                    "Merci d'indiquer votre prénom."
                )

            elif not telephone.strip():

                st.error(
                    "Merci d'indiquer votre numéro de téléphone."
                )

            else:

                st.session_state.contact_envoye = True
                st.rerun()


st.divider()


# =========================
# ÉCRIVEZ-NOUS
# =========================

st.subheader("✉️ Écrivez-nous")

st.write(
    """
    Vous préférez nous contacter par e-mail ?
    Laissez-nous votre message.
    """
)

if "email_envoye" not in st.session_state:
    st.session_state.email_envoye = False


if st.session_state.email_envoye:

    st.success(
        "✅ Votre message a bien été envoyé. Merci !"
    )

    if st.button("Nouveau message"):

        st.session_state.email_envoye = False
        st.rerun()

else:

    with st.form("formulaire_email"):

        prenom_email = st.text_input(
            "Votre prénom *",
            placeholder="Ex. Sophie"
        )

        email = st.text_input(
            "Votre adresse e-mail *",
            placeholder="Ex. sophie@email.com"
        )

        message_email = st.text_area(
            "Votre message *",
            placeholder=(
                "Écrivez votre demande ici..."
            )
        )

        envoyer_email = st.form_submit_button(
            "✉️ Envoyer"
        )

        if envoyer_email:

            if not prenom_email.strip():

                st.error(
                    "Merci d'indiquer votre prénom."
                )

            elif not email.strip():

                st.error(
                    "Merci d'indiquer votre adresse e-mail."
                )

            elif not message_email.strip():

                st.error(
                    "Merci d'écrire votre message."
                )

            else:

                st.session_state.email_envoye = True
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
