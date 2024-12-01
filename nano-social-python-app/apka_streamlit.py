import re

import streamlit as st

from nano_pubs import NanoPubs


nano_pubs = NanoPubs()


def display_comments(comments: dict, level: int = 0) -> None:
    for comment in comments:
        indent = " " * (level * 4)
        st.markdown(f"{indent}: {comment['uri']}")

        if comment.get("comments"):
            display_comments(comment["comments"], level + 1)


st.set_page_config(page_title="Aplikacja z zakładkami", layout="wide")

tab1, tab2 = st.tabs(["Zakładka 1", "Zakładka 2"])

if "uri_list" not in st.session_state:
    st.session_state.uri_list = nano_pubs.get_random_npubs(10, True)

with tab1:
    if st.button("Losuj nowe URI"):
        st.session_state.uri_list = nano_pubs.get_random_npubs(10, True)

    regex = r"/(RA[\w\-]+)(?:#|$)"
    items = []
    for uri in st.session_state.uri_list:
        uri_id = uri.split("/")[-1].split("#")[0]
        if bool(re.search(regex, uri)):
            uri = f"https://w3id.org/np/{uri_id}"
            items.append(uri)

    # Układ z kolumnami
    col1, col2 = st.columns([1, 2])  # Proporcje szerokości kolumn

    # Lista URI w lewej kolumnie
    with col1:
        st.header("Publikacje")
        selected_uri = st.session_state.get("selected_uri", None)
        for item in items:
            if st.button(item, key=item):
                st.session_state.selected_uri = item

    # Komentarze w prawej kolumnie
    with col2:
        st.header("Komentarze")
        selected_uri = st.session_state.get("selected_uri", None)
        if selected_uri:
            comments = nano_pubs.get_npub_comments_tree(npub_uri=selected_uri)
            st.write(f"Wybrana nano-publikacja: **{selected_uri}**")
            if comments:
                display_comments(comments)
            else:
                st.write("Brak komentarzy.")

with tab2:
    st.header("Zakładka 2")
    st.write("Tutaj będzie inna funkcjonalność.")
