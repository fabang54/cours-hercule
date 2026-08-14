import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import date, time, datetime


# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Cours Hercule",
    page_icon="📚",
    layout="wide"
)


# ============================================================
# CONNEXION SUPABASE
# ============================================================

supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)


# ============================================================
# PROTECTION ENSEIGNANT
# ============================================================

mot_de_passe = st.text_input(
    "Mot de passe enseignant",
    type="password"
)

if mot_de_passe != st.secrets["mot_de_passe"]:
    st.info("🔒 Espace réservé à l'enseignant.")
    st.stop()


# ============================================================
# LISTES
# ============================================================

ELEVES = [
    "Nino",
    "Emma",
    "Lucas",
    "Sarah"
]

DISCIPLINES = [
    "Mathématiques",
    "Physique",
    "Informatique",
    "Français",
    "Anglais",
    "Technologie",
    "Cultures générales"
]

CONTENUS = [
    "Équations simples",
    "Fractions",
    "Calcul littéral",
    "Pythagore",
    "Fonctions",
    "Proportionnalité",
    "Géométrie",
    "Statistiques",
    "Probabilités",
    "Autre"
]

TRAVAUX = [
    "Exercices du manuel",
    "Exercices supplémentaires",
    "Revoir le cours",
    "Apprendre le cours",
    "Préparer le prochain cours",
    "Aucun",
    "Autre"
]

OBSERVATIONS = [
    "Élève attentif",
    "Élève fatigué",
    "Élève distrait",
    "Difficultés importantes",
    "Bonne participation",
    "Très bonne séance",
    "Progrès constatés",
    "Autre"
]


# ============================================================
# TITRE
# ============================================================

st.title("📚 Cours Hercule")


# ============================================================
# MENU
# ============================================================

menu = st.sidebar.radio(
    "Menu",
    [
        "📚 Gestion des séances",
        "📖 Cahier de texte",
        "✏️ Modifier une séance",
        "📊 Bilan",
        "🧾 Facturation"
    ]
)


# ============================================================
# RÉCUPÉRATION DES SÉANCES
# ============================================================

def recuperer_seances():

    resultat = (
        supabase
        .table("seances")
        .select("*")
        .order("date", desc=True)
        .execute()
    )

    donnees = resultat.data

    if not donnees:
        return pd.DataFrame()

    return pd.DataFrame(donnees)


# ============================================================
# GESTION DES SÉANCES
# ============================================================

if menu == "📚 Gestion des séances":

    st.header("📚 Gestion des séances")

    st.subheader("Nouvelle séance")


    # ========================================================
    # ÉLÈVE
    # ========================================================

    eleve = st.selectbox(
        "Élève",
        ELEVES,
        key="nouvelle_eleve"
    )


    # ========================================================
    # DATE ET HEURES
    # ========================================================

    date_seance = st.date_input(
        "Date de la séance",
        value=date.today(),
        key="nouvelle_date"
    )

    heure_debut = st.time_input(
        "Heure de début",
        value=time(14, 0),
        key="nouvelle_heure_debut"
    )

    heure_fin = st.time_input(
        "Heure de fin",
        value=time(15, 0),
        key="nouvelle_heure_fin"
    )


    # ========================================================
    # MODE
    # ========================================================

    mode = st.selectbox(
        "Mode",
        ["Présentiel", "Distanciel"],
        key="nouvelle_mode"
    )


    # ========================================================
    # DISCIPLINES
    # ========================================================

    disciplines = st.multiselect(
        "Discipline(s)",
        DISCIPLINES,
        key="nouvelles_disciplines"
    )


    # ========================================================
    # CONTENU
    # ========================================================

    contenu_selection = st.multiselect(
        "Contenu de la séance",
        CONTENUS,
        key="nouveaux_contenus"
    )

    contenu_manuel = st.text_area(
        "Saisie manuelle du contenu",
        key="contenu_manuel"
    )

    contenu_final = ", ".join(contenu_selection)

    if contenu_manuel.strip():

        if contenu_final:
            contenu_final += " — "

        contenu_final += contenu_manuel.strip()


    # ========================================================
    # TRAVAIL À FAIRE
    # ========================================================

    travail_selection = st.selectbox(
        "Travail à faire",
        TRAVAUX,
        key="nouveau_travail_selection"
    )

    if travail_selection == "Autre":

        travail = st.text_input(
            "Préciser le travail à faire",
            key="nouveau_travail_autre"
        )

    else:

        travail = travail_selection


    # ========================================================
    # OBSERVATIONS
    # ========================================================

    observations_selection = st.multiselect(
        "Observations",
        OBSERVATIONS,
        key="nouvelles_observations"
    )

    observation_manuel = st.text_area(
        "Saisie manuelle de l'observation",
        key="observation_manuel"
    )

    observation_finale = ", ".join(observations_selection)

    if observation_manuel.strip():

        if observation_finale:
            observation_finale += " — "

        observation_finale += observation_manuel.strip()


    # ========================================================
    # ENREGISTREMENT
    # ========================================================

    if st.button(
        "💾 Enregistrer la séance",
        type="primary"
    ):

        debut_minutes = (
            heure_debut.hour * 60
            + heure_debut.minute
        )

        fin_minutes = (
            heure_fin.hour * 60
            + heure_fin.minute
        )

        duree_minutes = fin_minutes - debut_minutes


        if duree_minutes <= 0:

            st.error(
                "❌ L'heure de fin doit être après l'heure de début."
            )


        elif not disciplines:

            st.error(
                "❌ Sélectionnez au moins une discipline."
            )


        elif not contenu_final.strip():

            st.error(
                "❌ Indiquez le contenu de la séance."
            )


        else:

            nouvelle_seance = {

                "eleve": eleve,

                "date": date_seance.isoformat(),

                "heure_debut":
                    heure_debut.strftime("%H:%M:%S"),

                "heure_fin":
                    heure_fin.strftime("%H:%M:%S"),

                "duree_minutes":
                    duree_minutes,

                "mode":
                    mode,

                "disciplines":
                    ", ".join(disciplines),

                "contenu":
                    contenu_final,

                "travail":
                    travail,

                "observations":
                    observation_finale
            }


            try:

                supabase \
                    .table("seances") \
                    .insert(nouvelle_seance) \
                    .execute()

                st.success(
                    "✅ Séance enregistrée dans Supabase !"
                )

            except Exception as e:

                st.error(
                    "❌ Erreur lors de l'enregistrement."
                )

                st.write(e)


# ============================================================
# CAHIER DE TEXTE
# ============================================================

elif menu == "📖 Cahier de texte":

    st.header("📖 Cahier de texte")

    df = recuperer_seances()


    if df.empty:

        st.info("Aucune séance enregistrée.")


    else:

        eleve_cahier = st.selectbox(
            "Choisir l'élève",
            ELEVES,
            key="cahier_eleve"
        )

        df_eleve = df[
            df["eleve"] == eleve_cahier
        ].copy()


        if df_eleve.empty:

            st.info(
                "Aucune séance enregistrée pour cet élève."
            )


        else:

            df_eleve = df_eleve.sort_values(
                "date",
                ascending=False
            )


            for _, ligne in df_eleve.iterrows():

                st.markdown("---")

                st.subheader(
                    f"📅 {ligne['date']}"
                )

                st.write(
                    f"**Horaire :** "
                    f"{ligne['heure_debut']} → "
                    f"{ligne['heure_fin']}"
                )

                st.write(
                    f"**Discipline(s) :** "
                    f"{ligne['disciplines']}"
                )

                st.write(
                    f"**Contenu :** "
                    f"{ligne['contenu']}"
                )

                st.write(
                    f"**Travail à faire :** "
                    f"{ligne['travail']}"
                )

                st.write(
                    f"**Observations :** "
                    f"{ligne['observations']}"
                )


# ============================================================
# MODIFICATION D'UNE SÉANCE
# ============================================================

elif menu == "✏️ Modifier une séance":

    st.header("✏️ Modifier une séance")

    df = recuperer_seances()


    if df.empty:

        st.info("Aucune séance enregistrée.")


    else:

        eleve_modification = st.selectbox(
            "Élève",
            sorted(
                df["eleve"]
                .dropna()
                .unique()
            ),
            key="modif_eleve"
        )


        df_eleve = df[
            df["eleve"] == eleve_modification
        ].copy()


        df_eleve = df_eleve.sort_values(
            "date",
            ascending=False
        )


        choix = []

        for _, ligne in df_eleve.iterrows():

            choix.append(
                f"{ligne['date']} - "
                f"{ligne['heure_debut']} - "
                f"{ligne['contenu']}"
            )


        index_choisi = st.selectbox(
            "Séance à modifier",
            range(len(choix)),
            format_func=lambda x: choix[x],
            key="choix_seance"
        )


        ligne = df_eleve.iloc[index_choisi]

        identifiant = ligne["id"]


        # ====================================================
        # FORMULAIRE
        # ====================================================

        st.subheader("Modifier la séance")


        nouvelle_date = st.date_input(
            "Date",
            value=datetime.strptime(
                str(ligne["date"]),
                "%Y-%m-%d"
            ).date(),
            key="modif_date"
        )


        try:

            heure_debut_initiale = datetime.strptime(
                str(ligne["heure_debut"]),
                "%H:%M:%S"
            ).time()

        except ValueError:

            heure_debut_initiale = datetime.strptime(
                str(ligne["heure_debut"]),
                "%H:%M"
            ).time()


        try:

            heure_fin_initiale = datetime.strptime(
                str(ligne["heure_fin"]),
                "%H:%M:%S"
            ).time()

        except ValueError:

            heure_fin_initiale = datetime.strptime(
                str(ligne["heure_fin"]),
                "%H:%M"
            ).time()


        nouvelle_heure_debut = st.time_input(
            "Heure de début",
            value=heure_debut_initiale,
            key="modif_heure_debut"
        )


        nouvelle_heure_fin = st.time_input(
            "Heure de fin",
            value=heure_fin_initiale,
            key="modif_heure_fin"
        )


        nouveau_mode = st.selectbox(
            "Mode",
            ["Présentiel", "Distanciel"],
            index=(
                0
                if ligne["mode"] == "Présentiel"
                else 1
            ),
            key="modif_mode"
        )


        nouvelle_disciplines = st.text_input(
            "Discipline(s)",
            value=str(ligne["disciplines"]),
            key="modif_disciplines"
        )


        nouveau_contenu = st.text_area(
            "Contenu",
            value=str(ligne["contenu"]),
            key="modif_contenu"
        )


        nouveau_travail = st.text_area(
            "Travail à faire",
            value=str(ligne["travail"]),
            key="modif_travail"
        )


        nouvelles_observations = st.text_area(
            "Observations",
            value=str(ligne["observations"]),
            key="modif_observations"
        )


        # ====================================================
        # SAUVEGARDE
        # ====================================================

        if st.button(
            "💾 Enregistrer les modifications",
            type="primary"
        ):

            debut_minutes = (
                nouvelle_heure_debut.hour * 60
                + nouvelle_heure_debut.minute
            )

            fin_minutes = (
                nouvelle_heure_fin.hour * 60
                + nouvelle_heure_fin.minute
            )

            duree_minutes = fin_minutes - debut_minutes


            if duree_minutes <= 0:

                st.error(
                    "❌ L'heure de fin doit être après "
                    "l'heure de début."
                )


            else:

                modifications = {

                    "date":
                        nouvelle_date.isoformat(),

                    "heure_debut":
                        nouvelle_heure_debut.strftime("%H:%M:%S"),

                    "heure_fin":
                        nouvelle_heure_fin.strftime("%H:%M:%S"),

                    "duree_minutes":
                        duree_minutes,

                    "mode":
                        nouveau_mode,

                    "disciplines":
                        nouvelle_disciplines,

                    "contenu":
                        nouveau_contenu,

                    "travail":
                        nouveau_travail,

                    "observations":
                        nouvelles_observations
                }


                try:

                    supabase \
                        .table("seances") \
                        .update(modifications) \
                        .eq("id", identifiant) \
                        .execute()

                    st.success(
                        "✅ Séance modifiée avec succès !"
                    )

                    st.rerun()


                except Exception as e:

                    st.error(
                        "❌ Erreur lors de la modification."
                    )

                    st.write(e)


# ============================================================
# BILAN
# ============================================================

elif menu == "📊 Bilan":

    st.header("📊 Bilan de l'élève")

    df = recuperer_seances()


    if df.empty:

        st.info("Aucune séance enregistrée.")


    else:

        eleve_bilan = st.selectbox(
            "Élève",
            ELEVES,
            key="bilan_eleve"
        )


        df_eleve = df[
            df["eleve"] == eleve_bilan
        ].copy()


        if df_eleve.empty:

            st.info(
                "Aucune séance pour cet élève."
            )


        else:

            total_minutes = pd.to_numeric(
                df_eleve["duree_minutes"],
                errors="coerce"
            ).fillna(0).sum()


            total_heures = total_minutes / 60

            nombre_seances = len(df_eleve)


            col1, col2 = st.columns(2)

            with col1:

                st.metric(
                    "Nombre de séances",
                    nombre_seances
                )

            with col2:

                st.metric(
                    "Heures travaillées",
                    f"{total_heures:.2f} h"
                )


            st.subheader("📚 Séances")


            st.dataframe(
                df_eleve[
                    [
                        "date",
                        "disciplines",
                        "contenu",
                        "observations"
                    ]
                ],
                use_container_width=True
            )


# ============================================================
# FACTURATION
# ============================================================

elif menu == "🧾 Facturation":

    st.header("🧾 Facturation")

    df = recuperer_seances()


    if df.empty:

        st.info("Aucune séance enregistrée.")


    else:

        eleve_facturation = st.selectbox(
            "Élève",
            ELEVES,
            key="facturation_eleve"
        )


        # ====================================================
        # PÉRIODE
        # ====================================================

        type_periode = st.selectbox(
            "Période de facturation",
            [
                "Mensuelle",
                "Hebdomadaire",
                "Personnalisée",
                "Toutes les séances"
            ],
            key="type_periode"
        )


        # ====================================================
        # MENSUELLE
        # ====================================================

        if type_periode == "Mensuelle":

            mois = st.selectbox(
                "Mois",
                list(range(1, 13)),
                index=date.today().month - 1,
                key="facturation_mois"
            )


            annee = st.number_input(
                "Année",
                min_value=2020,
                max_value=2100,
                value=date.today().year,
                step=1,
                key="facturation_annee"
            )


            df["date"] = pd.to_datetime(
                df["date"]
            )


            df_filtre = df[
                (df["eleve"] == eleve_facturation)
                &
                (df["date"].dt.month == mois)
                &
                (df["date"].dt.year == annee)
            ]


        # ====================================================
        # HEBDOMADAIRE
        # ====================================================

        elif type_periode == "Hebdomadaire":

            date_debut = st.date_input(
                "Début de la semaine",
                key="semaine_debut"
            )


            date_fin = (
                date_debut
                + pd.Timedelta(days=6)
            )


            df["date"] = pd.to_datetime(
                df["date"]
            )


            df_filtre = df[
                (df["eleve"] == eleve_facturation)
                &
                (df["date"].dt.date >= date_debut)
                &
                (df["date"].dt.date <= date_fin)
            ]


        # ====================================================
        # PERSONNALISÉE
        # ====================================================

        elif type_periode == "Personnalisée":

            date_debut = st.date_input(
                "Date de début",
                key="periode_debut"
            )


            date_fin = st.date_input(
                "Date de fin",
                key="periode_fin"
            )


            df["date"] = pd.to_datetime(
                df["date"]
            )


            df_filtre = df[
                (df["eleve"] == eleve_facturation)
                &
                (df["date"].dt.date >= date_debut)
                &
                (df["date"].dt.date <= date_fin)
            ]


        # ====================================================
        # TOUTES LES SÉANCES
        # ====================================================

        else:

            df_filtre = df[
                df["eleve"] == eleve_facturation
            ].copy()


        # ====================================================
        # RÉSULTATS
        # ====================================================

        if df_filtre.empty:

            st.warning(
                "Aucune séance pour cette période."
            )


        else:

            total_minutes = pd.to_numeric(
                df_filtre["duree_minutes"],
                errors="coerce"
            ).fillna(0).sum()


            total_heures = total_minutes / 60


            st.subheader("Résumé")


            col1, col2 = st.columns(2)


            with col1:

                st.metric(
                    "Nombre de séances",
                    len(df_filtre)
                )


            with col2:

                st.metric(
                    "Nombre d'heures",
                    f"{total_heures:.2f} h"
                )


            # =================================================
            # TARIF
            # =================================================

            tarif = st.number_input(
                "Tarif horaire (€)",
                min_value=0.0,
                value=30.0,
                step=1.0,
                key="tarif_horaire"
            )


            montant = total_heures * tarif


            st.metric(
                "Montant de la facture",
                f"{montant:.2f} €"
            )


            # =================================================
            # DÉTAIL
            # =================================================

            st.subheader("Détail des séances")


            st.dataframe(
                df_filtre[
                    [
                        "date",
                        "heure_debut",
                        "heure_fin",
                        "disciplines",
                        "contenu",
                        "duree_minutes"
                    ]
                ],
                use_container_width=True
            )
