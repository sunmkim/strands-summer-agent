import json
import re
import requests
import time
import uuid
from typing import Dict, Iterator, List

import boto3
import streamlit as st
from streamlit.logger import get_logger

logger = get_logger(__name__)
logger.setLevel("INFO")

URL = "http://localhost:8080/invocations"

# Page config
st.set_page_config(
    page_title="Bedrock AgentCore Chat",
    page_icon="static/gen-ai-dark.svg",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Remove Streamlit deployment components
st.markdown(
    """
      <style>
        .stAppDeployButton {display:none;}
        #MainMenu {visibility: hidden;}
      </style>
    """,
    unsafe_allow_html=True,
)

# HUMAN_AVATAR = "static/user-profile.svg"
# AI_AVATAR = "static/gen-ai-dark.svg"





def clean_response_text(text: str, show_thinking: bool = True) -> str:
    """Clean and format response text for better presentation"""
    if not text:
        return text

    # Handle the consecutive quoted chunks pattern
    # Pattern: "word1" "word2" "word3" -> word1 word2 word3
    text = re.sub(r'"\s*"', "", text)
    text = re.sub(r'^"', "", text)
    text = re.sub(r'"$', "", text)

    # Replace literal \n with actual newlines
    text = text.replace("\\n", "\n")

    # Replace literal \t with actual tabs
    text = text.replace("\\t", "\t")

    # Clean up multiple spaces
    text = re.sub(r" {3,}", " ", text)

    # Fix newlines that got converted to spaces
    text = text.replace(" \n ", "\n")
    text = text.replace("\n ", "\n")
    text = text.replace(" \n", "\n")

    # Handle numbered lists
    text = re.sub(r"\n(\d+)\.\s+", r"\n\1. ", text)
    text = re.sub(r"^(\d+)\.\s+", r"\1. ", text)

    # Handle bullet points
    text = re.sub(r"\n-\s+", r"\n- ", text)
    text = re.sub(r"^-\s+", r"- ", text)

    # Handle section headers
    text = re.sub(r"\n([A-Za-z][A-Za-z\s]{2,30}):\s*\n", r"\n**\1:**\n\n", text)

    # Clean up multiple newlines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Clean up thinking
    if not show_thinking:
        text = re.sub(r"<thinking>.*?</thinking>", "", text)

    return text.strip()


def extract_text_from_response(data) -> str:
    """Extract text content from response data in various formats"""
    if isinstance(data, dict):
        # Handle format: {'role': 'assistant', 'content': [{'text': 'Hello!'}]}
        if "role" in data and "content" in data:
            content = data["content"]
            if isinstance(content, list) and len(content) > 0:
                if isinstance(content[0], dict) and "text" in content[0]:
                    return str(content[0]["text"])
                else:
                    return str(content[0])
            elif isinstance(content, str):
                return content
            else:
                return str(content)

        # Handle other common formats
        if "text" in data:
            return str(data["text"])
        elif "content" in data:
            content = data["content"]
            if isinstance(content, str):
                return content
            else:
                return str(content)
        elif "message" in data:
            return str(data["message"])
        elif "response" in data:
            return str(data["response"])
        elif "result" in data:
            return str(data["result"])

    return str(data)


def parse_streaming_chunk(chunk: str) -> str:
    """Parse individual streaming chunk and extract meaningful content"""
    # logger.info(f"parse_streaming_chunk: received chunk: {chunk}")
    # logger.info(f"parse_streaming_chunk: chunk type: {type(chunk)}")

    try:        
        # return chunk as-is
        # logger.info("parse_streaming_chunk: Not JSON, returning as-is")
        return chunk
    except json.JSONDecodeError as e:
        logger.error(f"parse_streaming_chunk: JSON decode error: {e}")
        raise e

def invoke_agent_streaming(
    prompt: str,
    show_tool: bool = True,
) -> Iterator[str]:
    """Invoke agent and yield streaming response chunks"""
    try:
        logger.info("Using streaming response path")
        header = {
            "Content-Type": "application/json"
        }
        body = {
            "prompt": prompt
        }
        response = requests.post(url=URL, json=body, headers=header, stream=True)
        # Handle streaming response
        for line in response.iter_lines(chunk_size=1):
            if line:
                line = line.decode("utf-8")
                # logger.info(f"Raw line: {line}")
                if line.startswith("data: "):
                    line = line[6:]
                    # logger.info(f"Line after removing 'data: ': {line}")
                    # Parse and clean each chunk
                    parsed_chunk = parse_streaming_chunk(line)
                    logger.info(f"parsed_chunk:: {parsed_chunk}")
                    if parsed_chunk.strip():  # Only yield non-empty chunks
                        yield parsed_chunk
                else:
                    logger.info(
                        f"Line doesn't start with 'data: ', skipping: {line}"
                    )
    except Exception as e:
        yield f"Error invoking agent: {e}"


def main():
    st.title("Weather Chat")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Type your message here..."):
       
        # Add user message to chat history
        st.session_state.messages.append(
            {"role": "user", "content": prompt}
        )
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate assistant response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            chunk_buffer = ""

            try:
                # Stream the response
                for chunk in invoke_agent_streaming(
                    prompt,
                ):
                    # Let's see what we get
                    logger.debug(f"MAIN LOOP: chunk type: {type(chunk)}")
                    logger.debug(f"MAIN LOOP: chunk content: {chunk}")

                    # Ensure chunk is a string before concatenating
                    if not isinstance(chunk, str):
                        logger.info(
                            f"MAIN LOOP: Converting non-string chunk to string"
                        )
                        chunk = str(chunk)

                    # Add chunk to buffer
                    chunk_buffer += chunk

                    # Only update display every few chunks or when we hit certain characters
                    if (
                        len(chunk_buffer) % 3 == 0
                        or chunk.endswith(" ")
                        or chunk.endswith("\n")
                    ):
                        
                        # Clean the accumulated response
                        cleaned_response = clean_response_text(chunk_buffer)
                        message_placeholder.markdown(cleaned_response + " ▌")
                      

                    time.sleep(0.01)  # Reduced delay since we're batching updates

                # Final response without cursor
                full_response = clean_response_text(chunk_buffer, True)
    

                message_placeholder.markdown(full_response)

            except Exception as e:
                error_msg = f"❌ **Error:** {str(e)}"
                message_placeholder.markdown(error_msg)
                full_response = error_msg

        # Add assistant response to chat history
        st.session_state.messages.append(
            {"role": "assistant", "content": full_response}
        )


if __name__ == "__main__":
    main()