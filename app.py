from datetime import datetime
import re

import streamlit.components.v1 as components
import streamlit as st
import webbrowser

from nano_pubs import NanoPubs
from constans import TEXT_NOT_FOUND


nano_pubs = NanoPubs()


def display_comments(
        comments: list,
        level: int = 0, is_last_list: list = None, prefix: str = ""
        ) -> None:

    if is_last_list is None:
        is_last_list = []

    for i, comment in enumerate(comments):
        is_last = (i == len(comments) - 1)

        line_prefix = ""
        for last in is_last_list:
            line_prefix += "    " if last else "│   "
        line_prefix += "└── " if is_last else "├── "

        new_is_last_list = is_last_list + [is_last]

        date = parse_date(comment["date"])
        msg = f"{line_prefix} {date} - **[USER]({comment['author']})**"
        msg += f" wrote: [{comment['text']}]({comment['uri']})"
        st.markdown(msg, unsafe_allow_html=True)

        if len(comment["reactions"]) != 0:
            sorted_reactions = sorted(
                comment["reactions"].items(),
                key=lambda item: item[1],
                reverse=True
            )
            html_code = '<div style="display: flex; gap: 10px; flex-wrap: wrap;">'
            for reaction in sorted_reactions:
                emoji = reaction[0]
                count = reaction[1]
                html_code += f"""
                    <div style="border: 1px solid #ddd; border-radius: 5px; 
                                padding: 5px 10px; text-align: center;">
                        <span style="font-size: 20px;">{emoji}</span><br>
                        <span style="font-size: 14px; color: #555;">{count}</span>
                    </div>
                """
            html_code += '</div>'

            components.html(html_code, height=70)

        button_prefix = ""
        for last in is_last_list:
            button_prefix += "    " if last else "│   "
        button_prefix += "    "
        with st.container():
            cols = st.columns([1, 20])
            cols[0].markdown(button_prefix, unsafe_allow_html=True)
            button_key = f"add_reply_{comment['uri']}"
            if cols[1].button("Add reply", key=button_key):
                print("NEW COMM pressed:", comment["uri"])
                url = f"https://nanodash.petapico.org/publish?5&template=http://purl.org/np/RA3gQDMnYbKCTiQeiUYJYBaH6HUhz8f3HIg71itlsZDgA&param_thing={comment['uri']}"
                webbrowser.open(url)

        if comment.get("comments"):
            display_comments(comment["comments"], level + 1, new_is_last_list)


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
        date = parse_date(nano_pubs.get_date(npub_uri=selected_uri))
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
