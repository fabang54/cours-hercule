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
# ENSEIGNANT
# =========================

st.header("👨‍🏫 Votre enseignant")

st.subheader(
    "Enseignant certifié en mathématiques (CAPES)"
)

st.write(
    """
    Ayant suivi la formation  **Master MEEF**, et enseignant expérimenté
    en mathématiques, j'accompagne les élèves du
    **collège au lycée**, ainsi que les étudiants en **BTS**.

    Mon objectif est de permettre à chaque élève de
    **comprendre les notions, acquérir des méthodes efficaces
    et progresser durablement**, avec un accompagnement
    adapté à son niveau et à ses objectifs.
    """
)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 🎓 Formation")
    st.write(
        """
        • Master MEEF (Métiers de l'Enseignement,
  de l'Éducation et de la Formation)
        • CAPES de mathématiques
        """
    )

with col2:
    st.markdown("### 📚 Niveaux")
    st.write(
        """
        • Collège
        • Lycée
        • BTS
        """
    )

with col3:
    st.markdown("### 📐 Spécialité")
    st.write(
        """
        • Mathématiques
        • Accompagnement personnalisé
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
    Laissez votre prénom et au moins un moyen de contact :
    téléphone ou adresse e-mail.
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

        # -------------------------
        # PRÉNOM
        # -------------------------

        prenom_parent = st.text_input(
            "Votre prénom *",
            placeholder="Ex. Sophie"
        )


        # -------------------------
        # TÉLÉPHONE
        # -------------------------

        telephone = st.text_input(
            "Téléphone",
            placeholder="Ex. 06 12 34 56 78"
        )


        # -------------------------
        # EMAIL
        # -------------------------

        email_parent = st.text_input(
            "Adresse e-mail",
            placeholder="Ex. sophie@email.com"
        )


        # -------------------------
        # MESSAGE
        # -------------------------

        message_parent = st.text_area(
            "Votre message",
            placeholder="Quelques mots sur votre demande..."
        )


        # -------------------------
        # BOUTON
        # -------------------------

        envoyer = st.form_submit_button(
            "📨 Être recontacté(e)"
        )


        # =========================
        # VALIDATION
        # =========================

        if envoyer:

            if not prenom_parent.strip():

                st.error(
                    "Merci d'indiquer votre prénom."
                )

            elif (
                not telephone.strip()
                and not email_parent.strip()
            ):

                st.error(
                    "Merci d'indiquer votre téléphone "
                    "ou votre adresse e-mail."
                )

            else:

                # Pour l'instant,
                # la demande n'est pas encore
                # enregistrée dans Supabase.

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
