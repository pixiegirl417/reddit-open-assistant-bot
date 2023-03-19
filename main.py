import praw
import multiprocessing
from text_generation import InferenceAPIClient
import bot
import time
from util import *
import os
from dotenv import load_dotenv

skip_existing = False

# Set up the Reddit API credentials
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

# Set up the subreddit to monitor
subreddit = reddit.subreddit('ask_open_assistant')

def build_final_reply(text):
    if (len(text) > 1000):
            return append_reply_disclaimer("I would like to reply to your comment, but it is greater than 1000 characters and I cannot handle that at the moment. Sorry!")
    
    # Gets rid of the summons !openassistant regardless of where the comment came from.
    text = replace_substring_ignore_case(text, '!openassistant', '')

    # Always prompt with no preceding text for now, we are disabling bot memory because limitation is 1000 tokens.
    response = bot.prompt(text, preceding_text='', return_full_text=False) 
    print('Created response: ' + response)
    return append_reply_disclaimer(response)


# Define a function to handle replies to the bot's comments
def handle__direct_reply(comment):       
        # TODO: retrieve previous comments, build conversation and feed it as preceding text to enable bot memory

        # Get all replies to the comment and see if I replied already.
        if has_already_replied(comment): 
             print(f'Detected old direct reply: {comment.body}')
             return
        
        print(f'Detected new direct reply: {comment.body}')
        comment.reply(build_final_reply(comment.body))
        

def handle_summons(comment):
    if (comment.author == username):
        print('Summons was self, ignoring.')
        return
    
    if has_already_replied(comment): 
        print(f'Detected old summons: {comment.body}')
        return
    
    print(f'Detected new summons: {comment.body}')
    comment.reply(build_final_reply(comment.body))

# Check if bot has already replied to any given comment (not post).
def has_already_replied(comment):
    while True:
         try:
              comment.refresh()
              comment.replies.replace_more(limit=None)
              break
         except Exception:
              time.sleep(1)

    for reply in comment.replies:
         print(f'Found reply with author: {reply.author} and body: {reply.body}')
         if reply.author == username: return True

    return False

# Define a function to handle new top-level posts
def handle_post(post):    
    if (post.author == username): return
    if (post.selftext == ''): return
    
    # Check if I have replied to the post already.
    post.comments.replace_more(limit=None)
    for comment in post.comments:
         if (comment.author == username): 
              print(f'Detected old post: {post.title}')
              return
         
    print(f'New post detected: {post.title}')
    text = post.selftext
    post.reply(build_final_reply(text))

# Define a function to run the subreddit.stream.submissions() loop
def submissions_loop():
    for submission in subreddit.stream.submissions(skip_existing=skip_existing):
        handle_post(submission)

# Define a function to run the subreddit.stream.comments() loop
def comments_loop():
    for comment in subreddit.stream.comments(skip_existing=skip_existing):
        parent_comment = comment.parent()
        if parent_comment.author == username:
            handle__direct_reply(comment)

        elif comment.body.lower().startswith('!openassistant'):
            handle_summons(comment)

def _main():
         # Start the two stream loops in separate processes
        submissions_process = multiprocessing.Process(target=submissions_loop)
        comments_process = multiprocessing.Process(target=comments_loop)
        submissions_process.start()
        comments_process.start()
        submissions_process.join()
        comments_process.join()

if __name__ == '__main__':
    while True:
        try: 
            _main()
        except Exception as e:
             print(e)
             continue
        break