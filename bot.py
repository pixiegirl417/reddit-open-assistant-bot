from text_generation import InferenceAPIClient
import os
from dotenv import load_dotenv

HF_TOKEN = os.getenv('HF_TOKEN')
oa = InferenceAPIClient("OpenAssistant/oasst-sft-1-pythia-12b", token=HF_TOKEN, timeout=90)

def prompt(promptText, preceding_text = '', return_full_text=True):
    promptText = "<|prompter|>{}<|endoftext|><|assistant|>".format(promptText)
    final_text = preceding_text + promptText

    # Left-truncate text to fit in 500 words.
    final_text = ' '.join(final_text.split(' ')[-500:])
    text = oa.generate(final_text, max_new_tokens=500, return_full_text=return_full_text).generated_text
    return text

# Takes list of string comments in order that represents conversation between user and bot (beginning with user).
# Outputs precedingText in correct format for OA.
def construct_preceding_text_from_array(responses):
    output = ''
    for idx, response in enumerate(responses):
        if idx % 2 == 0: 
            # Human prompt
            output += '<|prompter|>{}<|endoftext|><|assistant|>'.format(response)
        elif idx % 2 != 0:
            # Bot reply
            output += '{}<|endoftext|>'.format(response)
    return output

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
