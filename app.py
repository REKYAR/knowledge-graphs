from datetime import datetime
import re

import streamlit.components.v1 as components
import streamlit as st
import webbrowser

from nano_pubs import NanoPubs
from constans import TEXT_NOT_FOUND, DATE_NOT_FOUND

nano_pubs = NanoPubs()

phonetic_alphabet = [
    "ALFA", "BRAVO", "CHARLIE", "DELTA", "ECHO", "FOXTROT",
    "GOLF", "HOTEL", "INDIA", "JULIETT", "KILO", "LIMA",
    "MIKE", "NOVEMBER", "OSCAR", "PAPA", "QUEBEC", "ROMEO",
    "SIERRA", "TANGO", "UNIFORM", "VICTOR", "WHISKEY", "X-RAY",
    "YANKEE", "ZULU"
]


class NickGenerator:
    def __init__(self, phonetic_alphabet):
        self.phonetic_alphabet = phonetic_alphabet
        self.nicks_assigned = {}
        self.used_nicks = set()
        self.counter = 0
        self.next_index = 0

    def get_nick(self, user_uri):
        if user_uri in self.nicks_assigned:
            return self.nicks_assigned[user_uri]

        while True:
            base_nick = self.phonetic_alphabet[self.next_index]
            nick = f"{base_nick}{self.counter}" if base_nick in self.used_nicks else base_nick

            self.next_index = (self.next_index + 1) % len(self.phonetic_alphabet)
            if self.next_index == 0:
                self.counter += 1

            if nick not in self.used_nicks:
                self.used_nicks.add(nick)
                self.nicks_assigned[user_uri] = nick
                return nick


nicks = NickGenerator(phonetic_alphabet)


def extract_authors(comments) -> list[str]:
    authors = []

    def traverse_comments(comments):
        for comment in comments:
            authors.append(comment["author"])

            if "comments" in comment and comment["comments"]:
                traverse_comments(comment["comments"])

    traverse_comments(comments)
    return list(set(authors))


def display_comments(comments: list, level: int = 0) -> None:
    html_code = '<div style="font-family: Arial, sans-serif;">'
    comments_count = 0
    reactions_count = 0

    authors = extract_authors(comments)

    def build_html(comments: list, level: int):
        nonlocal html_code
        nonlocal comments_count
        nonlocal reactions_count

        for comment in comments:
            date = parse_date(comment["date"])
            text = comment["text"] if comment["text"] else "No text found"
            author_link = comment["author"]
            author_nick = nicks.get_nick(author_link).title()
            comments_count += 1

            html_code += f"""
            <div style="margin-left: {level * 20}px; border-left: 2px solid #ccc;
                        padding-left: 10px; margin-top: 10px;">
                <div>
                    <strong><a href="{author_link}" style="text-decoration: none; color: #0078D4;" target="_blank">User {author_nick}</a></strong>
                    <span style="font-size: 12px; color: #777;">({date})</span>
                </div>
                <div style="margin-top: 5px;">{text}</div>
            """

            if comment.get("reactions"):
                reactions_count += 1
                html_code += '<div style="display: flex; gap: 5px; margin-top: 5px;">'
                sorted_comments = sorted(
                    comment["reactions"].items(),
                    key=lambda item: int(item[1]),
                    reverse=True
                    )

                for emoji, count in sorted_comments:
                    html_code += f"""
                    <div style="border: 1px solid #ddd; border-radius: 5px;
                                padding: 2px 5px; text-align: center;">
                        <span style="font-size: 18px;">{emoji}</span> {count}
                    </div>
                    """
                html_code += '</div>'

            if comment.get("comments") and len(comment["comments"]) > 0:
                build_html(comment["comments"], level + 1)

            html_code += "</div>"

    build_html(comments, level)
    html_code += '</div>'

    components.html(html_code, height=comments_count*60+reactions_count*60)


def comment_form(parent_uri: str, level: int) -> None:
    with st.form(key=f"form_{parent_uri}_{level}"):
        new_comment = st.text_area("Reply:")
        submitted = st.form_submit_button("Add reply")

        if submitted and new_comment.strip():
            st.success("Reply added")


def parse_date(date: str) -> str:
    date_obj = datetime.strptime(date, "%Y-%m-%dT%H:%M:%S.%fZ")
    date = date_obj.strftime("%Y-%m-%d %H:%M")
    return date


st.set_page_config(page_title="Nano Publications", layout="wide")

if "uri_list" not in st.session_state:
    st.session_state.uri_list = nano_pubs.get_random_npubs(10, True)

if "show_custom_uri_input" not in st.session_state:
    st.session_state.show_custom_uri_input = False

if st.button("Random URI"):
    st.session_state.uri_list = nano_pubs.get_random_npubs(10, True)
    st.session_state.show_custom_uri_input = False

if st.button("Own URI"):
    st.session_state.show_custom_uri_input = True

# Publications / Comments
col1, col2 = st.columns([1, 2])


with col1:  # Publications
    st.header("Nano-publications publications")

    if st.session_state.show_custom_uri_input:  # Custom nano-pub
        user_input = st.text_input("Enter own nanopub URI:")
        if st.button("Load nano-publication"):
            if user_input:
                st.session_state.uri_list.append(user_input)
                st.session_state.selected_uri = user_input
                st.success("Loading nano-publication ...")

    else:  # Random nano-pub
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


with col2:  # Comments
    st.header("Comments")
    selected_uri = st.session_state.get("selected_uri", None)
    if selected_uri:
        author = nano_pubs.get_author(npub_uri=selected_uri)

        date = nano_pubs.get_date(npub_uri=selected_uri)
        if date != DATE_NOT_FOUND:
            date = parse_date(date)

        text = nano_pubs.get_npub_text(npub_uri=selected_uri)
        if text == selected_uri:
            text = "No text found!"

        st.write(f"**Selected Nanopub:** {selected_uri}")
        st.write(f"**Author:** {author}")
        st.write(f"**Date:** {date}")
        st.write(f"**Text:** {text}")

        comments = nano_pubs.get_npub_comments_tree(npub_uri=selected_uri)
        if comments:
            display_comments(comments)
        else:
            st.write("No comments.")

    if selected_uri and st.button("Add comment to selected nanopub"):
        print("NEW NPUB pressed", selected_uri)
        url = f"https://nanodash.petapico.org/publish?5&template=http://purl.org/np/RA3gQDMnYbKCTiQeiUYJYBaH6HUhz8f3HIg71itlsZDgA&param_thing={selected_uri}"
        webbrowser.open(url)
