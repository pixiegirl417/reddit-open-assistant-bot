def replace_substring_ignore_case(initial_str, substr, replacement_str):
     x = initial_str.split()
     for i in x:
          if (i.lower() == substr.lower()):
               initial_str = initial_str.replace(i, replacement_str)
     return initial_str

def append_reply_disclaimer(text):
    disclaimer = '''
    \n\nI am OpenAssistant. 
    I reply to all top-level text posts in /r/ask_open_assistant. You can summon me to reply to any comment by putting "!OpenAssistant" at the top. I  also reply to any comments that reply directly to me. 
    \n\nI am in beta testing, and I have a few limitations.
    \n\nAt the moment, I do not remember previous messages, although I am capable of doing so.
    \n\nStay tuned!'''

    disclaimer = disclaimer.split()
    new_disclaimer = []
    for word in disclaimer:
         new_disclaimer.append('^' + word)
    
    disclaimer = ' '.join(new_disclaimer)
    return text + "\n\n" + disclaimer