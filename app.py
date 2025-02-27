import gradio as gr
import os
import subprocess
import threading
from langchain_ollama import ChatOllama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    AIMessagePromptTemplate,
    ChatPromptTemplate,
    MessagesPlaceholder
)
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import time

# Initialize the chat engine with dynamic Ollama URL
def get_llm_engine(model_name):
    ollama_host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
    print(f"Connecting to Ollama at {ollama_host}")
    try:
        return ChatOllama(model=model_name, base_url=ollama_host, temperature=0.3)
    except Exception as e:
        raise Exception(f"Failed to connect to Ollama at {ollama_host}: {str(e)}")

# System prompt configuration
SYSTEM_TEMPLATE = """You are an expert AI coding assistant. Provide concise, correct solutions 
with strategic print statements for debugging. Always respond in English."""

chat_prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_TEMPLATE),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}")
])

class ChatBot:
    def __init__(self):
        self.message_log = [("Hi! I'm DeepSeek. How can I help you code today? 💻", None)]
        self.chat_history = []
        self.running_process = None

    def generate_ai_response(self, user_input, llm_engine):
        self.chat_history.append(HumanMessage(content=user_input))
        print(f"User input: {user_input}")
        try:
            chain = chat_prompt | llm_engine | StrOutputParser()
            response = chain.invoke({"input": user_input, "chat_history": self.chat_history})
            print(f"AI response: {response}")
            self.chat_history.append(AIMessage(content=response))
            return response
        except Exception as e:
            error_msg = f"Error: Could not generate response. Ensure Ollama is running. Details: {str(e)}"
            print(f"Error in generate_ai_response: {error_msg}")
            self.chat_history.append(AIMessage(content=error_msg))
            return error_msg

    def chat(self, message, model_choice, history):
        if not message:
            return "", history
        llm_engine = get_llm_engine(model_choice)
        self.message_log.append((message, None))
        ai_response = self.generate_ai_response(message, llm_engine)
        self.message_log.append((ai_response, None))
        history.append((message, ai_response))
        return "", history

    def run_ollama_command(self, command, progress=gr.Progress()):
        if self.running_process and self.running_process.poll() is None:
            return "Error: Another download is already in progress. Please wait or stop it."
        
        def execute_command():
            self.running_process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            progress(0, desc="Starting download...")
            while True:
                output = self.running_process.stdout.readline()
                if output == '' and self.running_process.poll() is not None:
                    break
                if output:
                    print(output.strip())
                    progress.update(0.5, desc=output.strip())
            return_code = self.running_process.poll()
            if return_code != 0:
                error = self.running_process.stderr.read()
                return f"Error: Download failed. Details: {error}"
            return "Download completed successfully!"

        thread = threading.Thread(target=lambda: progress.tqdm(execute_command(), total=1))
        thread.start()
        thread.join()
        return self.running_process

    def stop_download(self):
        if self.running_process and self.running_process.poll() is None:
            self.running_process.terminate()
            self.running_process.wait()
            return "Download stopped."
        return "No download in progress."

def create_demo():
    chatbot = ChatBot()
    
    with gr.Blocks(theme="default", css="""
        .main { padding: 20px; background-color: #1a1a1a; color: #e0e0e0; }
        .chatbox { background-color: #2a2a2a; border-radius: 10px; }
        .input-panel { background-color: #333; padding: 10px; border-radius: 5px; }
        .button { background-color: #4a90e2; color: white; border: none; padding: 5px 10px; border-radius: 5px; }
        .button:hover { background-color: #357abd; }
    """) as demo:
        gr.Markdown("# 🧠 DeepSeek Code Companion 2025")
        gr.Markdown("🚀 Your AI Pair Programmer with Model Management")

        with gr.Row():
            with gr.Column(scale=4):
                chatbot_component = gr.Chatbot(value=[("Hi! I'm DeepSeek. How can I help you code today? 💻", None)], height=500, elem_classes="chatbox")
                msg = gr.Textbox(placeholder="Type your coding question here...", show_label=False, elem_classes="input-panel")

            with gr.Column(scale=1):
                model_dropdown = gr.Dropdown(
                    choices=["deepseek-r1:1.5b", "deepseek-r1:3b"],
                    value="deepseek-r1:1.5b",
                    label="Select Model"
                )
                ollama_command = gr.Textbox(placeholder="Enter Ollama command (e.g., ollama pull deepseek-r1:1.5b)", label="Download Model")
                download_button = gr.Button("Download Model", elem_classes="button")
                stop_button = gr.Button("Stop Download", elem_classes="button")
                output_log = gr.Textbox(label="Download Log", interactive=False)

                gr.Markdown("### Features")
                gr.Markdown("""
                - 🐍 Python Expertise
                - 🐞 Debugging Assistant
                - 📝 Code Documentation
                - 💡 Solution Design
                - 🌐 Model Downloads from [Ollama Library](https://ollama.com/library)
                """)

        msg.submit(fn=chatbot.chat, inputs=[msg, model_dropdown, chatbot_component], outputs=[msg, chatbot_component])
        
        download_button.click(
            fn=chatbot.run_ollama_command,
            inputs=[ollama_command],
            outputs=[output_log]
        )
        
        stop_button.click(
            fn=chatbot.stop_download,
            outputs=[output_log]
        )

    return demo

if __name__ == "__main__":
    demo = create_demo()
    demo.launch(server_port=7860, share=True)