import json
import re
import time
from typing import Dict, Iterator, List

import boto3
import streamlit as st
from streamlit.logger import get_logger

logger = get_logger(__name__)
logger.setLevel("INFO")


# Page config
st.set_page_config(
    page_title="Bedrock AgentCore Chat",
    page_icon="static/gen-ai-dark.svg",
    layout="wide",
    initial_sidebar_state="expanded",
)



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
    try:        
        # return chunk as-is
        # logger.info("parse_streaming_chunk: Not JSON, returning as-is")
        return chunk
    except json.JSONDecodeError as e:
        logger.error(f"parse_streaming_chunk: JSON decode error: {e}")
        raise e


def get_agent_runtimes(region: str = "us-east-1") -> List[Dict]:
    """Fetch available agent runtimes from bedrock-agentcore-control"""
    try:
        client = boto3.client("bedrock-agentcore-control", region_name=region)
        response = client.list_agent_runtimes(maxResults=10)

        # Filter only READY agents and sort by name
        ready_agents = [
            agent
            for agent in response.get("agentRuntimes", [])
            if agent.get("status") == "READY"
        ]

        # Sort by most recent update time (newest first)
        ready_agents.sort(key=lambda x: x.get("lastUpdatedAt", ""), reverse=True)

        return ready_agents
    except Exception as e:
        st.error(f"Error fetching agent runtimes: {e}")
        return []

def invoke_agent_streaming(
    prompt: str,
    agent_arn: str,
    show_tool: bool = True,
    region: str = "us-east-1"
) -> Iterator[str]:
    """Invoke agent and yield streaming response chunks"""
    try:
        agentcore_client = boto3.client("bedrock-agentcore", region_name=region)

        logger.info("Using streaming response path")

        # invoke agent hosted on AWS
        response = agentcore_client.invoke_agent_runtime(
            agentRuntimeArn=agent_arn,
            payload=json.dumps({"prompt": prompt}),
        )

        for line in response["response"].iter_lines(chunk_size=1):
            if line:
                line = line.decode("utf-8")
                # logger.info(f"Raw line: {line}")
                if line.startswith("data: "):
                    line = line[6:]
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


    # get available agent runtimes
    available_agents = get_agent_runtimes()
    runtime_arn = available_agents[0]['agentRuntimeArn']

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

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
            with st.spinner("AI is thinking..."): 
                try:
                    # Stream the response
                    for chunk in invoke_agent_streaming(
                        prompt,
                        runtime_arn
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