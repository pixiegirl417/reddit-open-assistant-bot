from text_generation import InferenceAPIClient
import os
from dotenv import load_dotenv

HF_TOKEN = os.getenv('HF_TOKEN')
oa = InferenceAPIClient("OpenAssistant/oasst-sft-1-pythia-12b", token=HF_TOKEN, timeout=30)

def prompt(promptText, preceding_text = '', return_full_text=True):
    promptText = "<|prompter|>{}<|endoftext|><|assistant|>".format(promptText)
    final_text = preceding_text + promptText

    # Left-truncate text to fit in 1000 characters.
    final_text = final_text[-1000:]
    text = oa.generate(final_text, max_new_tokens=1000, return_full_text=return_full_text).generated_text
    return text

def getReplyFromFullConversation(text):
    return text.split('<|assistant|>')[-1]

def start_chat():
    preceding_text = ''
    while True:
        try:
            user_prompt = input("Prompt >>> ")
            if user_prompt == '!reset':
                preceding_text = ''
                continue

            # Gets reply using new prompt + conversation from before.
            full_text_reply = prompt(user_prompt, preceding_text=preceding_text)

            # Add this prompt + reply to preceding text for use in next iteration of the loop.
            preceding_text += full_text_reply

            print(getReplyFromFullConversation(full_text_reply))
        except Exception as e: 
            preceding_text = ''
            print(e)
    

