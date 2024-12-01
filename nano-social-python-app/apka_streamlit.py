from datetime import datetime
import re

import streamlit as st

from nano_pubs import NanoPubs
from constans import TEXT_NOT_FOUND


nano_pubs = NanoPubs()

# print(download_npub_comment("RAigK1MVSCgqvtyDSnoAWRaGYdocdXr36bqb9wrxqWqSI"))


def display_comments(comments: list, level: int = 0, prefix: str = "") -> None:
    for i, comment in enumerate(comments):
        is_last = (i == len(comments) - 1)
        line_prefix = prefix + ("└── " if is_last else "├── ")
        new_prefix = prefix + ("    " if is_last else "│   ")

        date_obj = datetime.strptime(comment["date"], "%Y-%m-%dT%H:%M:%S.%fZ")
        date = date_obj.strftime("%Y-%m-%d %H:%M")

        st.markdown(f"{line_prefix} {date} - **[Użytkownik]({comment['author']})** napisał: [{comment['text']}]({comment['uri']})", unsafe_allow_html=True)

        button_prefix = new_prefix + ("│   " if not is_last else "    ")
        st.markdown(f"{button_prefix}<button style='margin-left: 30px; font-size: 15px;'>{'Dodaj odpowiedź'}</button>", unsafe_allow_html=True)

        if comment.get("comments"):
            display_comments(comment["comments"], level + 1, new_prefix)


def comment_form(parent_uri: str, level: int) -> None:
    with st.form(key=f"form_{parent_uri}_{level}"):
        new_comment = st.text_area("Napisz odpowiedź:")
        submitted = st.form_submit_button("Dodaj odpowiedź")

        if submitted and new_comment.strip():
            st.success("Dodano odpowiedź!")


def XYZ(uri: str) -> None:
    st.success(f"Dodano komentarz do {uri}")


st.set_page_config(page_title="Nano Publications", layout="wide")

if "uri_list" not in st.session_state:
    st.session_state.uri_list = nano_pubs.get_random_npubs(10, True)

if "show_custom_uri_input" not in st.session_state:
    st.session_state.show_custom_uri_input = False

if st.button("Losuj nowe URI"):
    st.session_state.uri_list = nano_pubs.get_random_npubs(10, True)
    st.session_state.show_custom_uri_input = False

if st.button("Własny URI"):
    st.session_state.show_custom_uri_input = True

# Publikacje / Komentarze
col1, col2 = st.columns([1, 2])

with col1:
    st.header("Nano-publikacje publikacje")
    if st.session_state.show_custom_uri_input:
        user_input = st.text_input("Wprowadź własne URI nano-publikacji:")
        if st.button("Sprawdź nano-publikację"):
            if user_input:
                st.session_state.uri_list.append(user_input)
                st.session_state.selected_uri = user_input
                st.success("Załadowano komentarze!")
    else:
        regex = r"/(RA[\w\-]+)(?:#|$)"
        items = []
        for uri in st.session_state.uri_list:
            uri_id = uri.split("/")[-1].split("#")[0]
            new_uri = f"https://w3id.org/np/{uri_id}"
            if bool(re.search(regex, uri)) and new_uri not in items:
                items.append(new_uri)

        selected_uri = st.session_state.get("selected_uri", None)

        for uri in items:
            button_text = nano_pubs.get_npub_text(npub_uri=uri, simple=True)
            if button_text == TEXT_NOT_FOUND:
                button_text = uri

            if st.button(button_text, key=uri):
                st.session_state.selected_uri = uri

with col2:
    st.header("Komentarze")
    selected_uri = st.session_state.get("selected_uri", None)
    if selected_uri:
        author = nano_pubs.get_author(npub_uri=selected_uri)
        date = nano_pubs.get_date(npub_uri=selected_uri)
        text = nano_pubs.get_npub_text(npub_uri=selected_uri)
        if text == selected_uri:
            text = "No text found!"

        st.write(f"**Wybrana nano-publikacja:** {selected_uri}")
        st.write(f"**Author:** {author}")
        st.write(f"**Date:** {date}")
        st.write(f"**Text:** {text}")

        comments = nano_pubs.get_npub_comments_tree(npub_uri=selected_uri)
        if comments:
            display_comments(comments)
        else:
            st.write("Brak komentarzy.")

    if selected_uri and st.button("Dodaj komentarz do wybranej nano-publikacji"):
        XYZ(selected_uri)
