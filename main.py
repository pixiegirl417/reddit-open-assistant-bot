import praw
import multiprocessing
from text_generation import InferenceAPIClient
import bot
import time
from util import *
import os
from dotenv import load_dotenv
from praw.exceptions import DuplicateReplaceException

skip_existing = True

# Set up the Reddit API credentials
load_dotenv()
client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')
user_agent = os.getenv('USER_AGENT')
username = os.getenv('USERNAME')
password = os.getenv('PASSWORD')
reddit = praw.Reddit(
    client_id=client_id,
    client_secret=client_secret,
    user_agent=user_agent,
    username=username,
    password=password,
)

def build_final_reply(text, precedingText=''):
    if (len(text.split(' ')) > 500): # 500 words is about 563 tokens
            return append_reply_disclaimer("I would like to reply to your comment, but it is greater than 750 tokens (approx 500 words) and I cannot handle that at the moment. Sorry!")
    
    # Gets rid of the summons !openassistant regardless of where the comment came from.
    text = replace_substring_ignore_case(text, '!openassistant', '')

    response = bot.prompt(text, preceding_text=precedingText, return_full_text=False) 
    print(F'Created response: {response}\n\n')
    return append_reply_disclaimer(response)


def build_preceding_conversation_array(comment, conversation=None):
    if conversation is None:
         conversation = []

    parent = comment.parent()

    if not parent.is_root:
        # Recursively appends comments til we hit the root comment. 
        conversation.append(strip_disclaimer(parent.body))
        build_preceding_conversation_array(parent, conversation)
    else:
         # If it's a root level comment by the bot, then the top level post is the user's initial prompt.
         if (parent.author == username):
              # First get this root level comment body in the list
              conversation.insert(0, strip_disclaimer(parent.body))
              
              # Then get the top level post body in the list
              conversation.insert(0, parent.parent().selftext)
         else:
              # In this case, the root level comment is by the user so it is the initial prompt.
              conversation.insert(0, replace_substring_ignore_case(parent.body, '!openassistant', ''))

    return conversation

# Define a function to handle replies to the bot's comments
def handle__direct_reply(comment):       
        # Get all replies to the comment and see if I replied already.
        if comment.body.startswith('!ignore'): return
        if has_already_replied(comment): 
             return
        
        shortened = ' '.join(comment.body.split(' ')[-10:])
        print(f'Detected new direct reply: {shortened}\n\n')

        conversation = build_preceding_conversation_array(comment)
        precedingText = bot.construct_preceding_text_from_array(conversation)
        comment.reply(build_final_reply(comment.body, precedingText=precedingText))
        

def handle_summons(comment):
    if (comment.author == username):
        return
    
    if has_already_replied(comment): 
        return
    
    shortened = ' '.join(comment.body.split(' ')[-10:])
    print(f'Detected new summons: {shortened}\n\n')
    comment.reply(build_final_reply(comment.body))

# Check if bot has already replied to any given comment (not post).
def has_already_replied(comment):
    # Ignores the "see more" comment to save requests.
    for reply in comment.replies:
         if reply.author == username: return True

    return False

# Define a function to handle new top-level posts
def handle_post(post):    
    if (post.selftext.startswith('!ignore')): return
    if (post.author == username): return
    if (post.selftext == ''): return
    
    # Check if I have replied to the post already.
    post.comments.replace_more(limit=None)
    for comment in post.comments:
         if (comment.author == username): 
              print(f'Detected old post: {post.title}\n\n')
              return
         
    print(f'New post detected: {post.title}\n\n')
    text = post.selftext
    post.reply(build_final_reply(text))


# Set up the subreddits to monitor
oa_subreddits = reddit.subreddit('ask_open_assistant+OpenAssistant')
r_ask_open_assisant = reddit.subreddit('ask_open_assistant')

# For submissions, only monitor r/ask_open_assistant.
def submissions_loop():
    for submission in r_ask_open_assisant.stream.submissions(skip_existing=skip_existing):
        try:
            handle_post(submission)
        except Exception as e:
             print(e)
             continue

def comments_loop():
    for comment in oa_subreddits.stream.comments(skip_existing=skip_existing):
        try:
            parent_comment = comment.parent()
            if parent_comment.author == username:
                handle__direct_reply(comment)

            elif comment.body.lower().startswith('!openassistant'):
                handle_summons(comment)
        except Exception as e:
             print (e)
             continue


def _main():
         # Start the two stream loops in separate processes
        submissions_process = multiprocessing.Process(target=submissions_loop)
        comments_process = multiprocessing.Process(target=comments_loop)
        submissions_process.start()
        comments_process.start()
        submissions_process.join()
        comments_process.join()

if __name__ == '__main__':
    running = False
    while not running:
        try: 
            _main()
            running = True
        except Exception as e:
             print(e)
             running = False