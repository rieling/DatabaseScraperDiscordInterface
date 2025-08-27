import discord
import sqlite3
import asyncio
import json
import nltk
nltk.download('wordnet')
nltk.download('averaged_perceptron_tagger')
from nltk.stem import WordNetLemmatizer

from discord.ext import commands

# Create the bot instance
intents = discord.Intents.default()
intents.guilds = True  # Enable guilds intent
intents.members = True  # Enable member intent
intents.messages = True  # Enable receiving messages
intents.message_content = True  # Explicitly enable message content intent
bot = commands.Bot(command_prefix="!", intents=intents)

# Initialize the lemmatizer globally
lemmatizer = WordNetLemmatizer()

import sqlite3

try:
    # Load the Greek Strong's dictionary
    with open('strongs-greek-dictionary.json', 'r', encoding='utf-8') as f:
        strongs_greek = json.load(f)

    # Load the Hebrew Strong's dictionary
    with open('strongs-hebrew-dictionary.json', 'r', encoding='utf-8') as f:
        strongs_hebrew = json.load(f)

    print("Successfully loaded both dictionaries!")
except FileNotFoundError as e:
    print(f"File not found: {e}")
except json.JSONDecodeError as e:
    print(f"JSON decoding failed: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")

    
# Strong's lookup command
@bot.command()
async def strongs(ctx, *, strongs_number: str):
    try:
        print(f"Raw message received: '{strongs_number}'")

        # Check if the command is a search query
        if strongs_number.lower().startswith("search "):
            search_keyword = strongs_number[len("search "):].strip()
            print(f"Detected search query with keyword: '{search_keyword}'")
            await search_strongs(ctx, search_keyword)
            return

        # If not a search query, treat it as a Strong's number
        strongs_number = strongs_number.upper().strip()  # Ensure uppercase and trim spaces
        print(f"Looking up Strong's number: '{strongs_number}'")

        # Direct lookup for Greek or Hebrew
        result = None
        if strongs_number.startswith('G'):
            result = strongs_greek.get(strongs_number)
        elif strongs_number.startswith('H'):
            result = strongs_hebrew.get(strongs_number)
        else:
            await ctx.send("Invalid Strong's number. Please use 'G' for Greek or 'H' for Hebrew.")
            return

        # If result found, construct and send the response
        if result:
            transliteration = result.get('translit') or result.get('xlit', 'N/A')

            # Extract related numbers from the derivation field
            derivation = result.get('derivation', 'N/A')
            related_numbers = []
            if derivation != 'N/A':
                related_numbers = [
                    part.strip('()') for part in derivation.split()
                    if part.startswith("G") or part.startswith("H")
                ]
            
            # Format related numbers as clickable links
            related_numbers_str = (
    ", ".join(
        f"[{num}](https://www.blueletterbible.org/lexicon/{num}/kjv/\u200b)"  # Add \u200b to disable embeds
        for num in related_numbers
    )
    if related_numbers else "N/A"
)


            # Construct the response
            response = (
                f"**Strong's {strongs_number}**\n"
                f"**Lemma**: {result.get('lemma', 'N/A')}\n"
                f"**Transliteration**: {transliteration}\n"
                f"**Definition**: {result.get('strongs_def', 'N/A')}\n"
                f"**Derivation**: {derivation}\n"
                f"**Related Numbers**: {related_numbers_str}\n"
                f"**KJV Definition**: {result.get('kjv_def', 'N/A')}"
            )
            print(f"Sending response: {response}")
            await ctx.send(response)
        else:
            print(f"No result found for Strong's number: '{strongs_number}'")
            await ctx.send(f"Sorry, Strong's number {strongs_number} not found.")
    except Exception as e:
        print(f"An error occurred: {e}")
        await ctx.send("An error occurred while processing your request.")

        
async def search_strongs(ctx, keyword: str):
    keyword = keyword.strip()
    filter_greek = "-g" in keyword
    filter_hebrew = "-h" in keyword

    # Remove filter flags from the keyword
    keyword = keyword.replace("-g", "").replace("-h", "").strip()

    results = []

    # Search Greek dictionary if no filter or Greek filter is applied
    if not filter_hebrew or filter_greek:
        for number, entry in strongs_greek.items():
            if keyword.lower() in entry.get('lemma', '').lower() or \
               keyword.lower() in entry.get('translit', '').lower() or \
               keyword.lower() in entry.get('strongs_def', '').lower() or \
               keyword.lower() in entry.get('kjv_def', '').lower():  # Added `kjv_def` check
                results.append(
                    f"**[{number}](https://www.blueletterbible.org/lexicon/{number}/kjv/\u200b)**\n"
                    f"**Lemma**: {entry.get('lemma', 'N/A')}\n"
                    f"**Transliteration**: {entry.get('translit', 'N/A')}\n"
                    f"**Definition**: {entry.get('strongs_def', 'N/A')}\n"
                    f"**Derivation**: {entry.get('derivation', 'N/A')}\n"
                    f"**KJV Definition**: {entry.get('kjv_def', 'N/A')}\n"
                )

    # Search Hebrew dictionary if no filter or Hebrew filter is applied
    if not filter_greek or filter_hebrew:
        for number, entry in strongs_hebrew.items():
            if keyword.lower() in entry.get('lemma', '').lower() or \
               keyword.lower() in entry.get('xlit', '').lower() or \
               keyword.lower() in entry.get('strongs_def', '').lower() or \
               keyword.lower() in entry.get('kjv_def', '').lower():  # Added `kjv_def` check
                results.append(
                    f"**[{number}](https://www.blueletterbible.org/lexicon/{number}/kjv/\u200b)**\n"
                    f"**Lemma**: {entry.get('lemma', 'N/A')}\n"
                    f"**Transliteration**: {entry.get('xlit', 'N/A')}\n"
                    f"**Definition**: {entry.get('strongs_def', 'N/A')}\n"
                    f"**Derivation**: {entry.get('derivation', 'N/A')}\n"
                    f"**KJV Definition**: {entry.get('kjv_def', 'N/A')}\n"
                )

    # Debug the results
    print(f"Results before sending: {results}")

    # Send the results or handle large messages
    if results:
        message = "\n".join(results[:10])  # Limit to 10 results
        print(f"Message length: {len(message)}")
        try:
            if len(message) > 2000:
                chunks = [message[i:i + 2000] for i in range(0, len(message), 2000)]
                for chunk in chunks:
                    await ctx.send(chunk)
            else:
                await ctx.send(message)
        except Exception as e:
            print(f"Error sending message: {e}")
    else:
        await ctx.send(f"No results found for '{keyword}'.")
        

@bot.command()
async def bible(ctx, *, reference: str):
    try:
        print(f"Raw message received: '{reference}'")
        use_strongs = "-strongs" in reference
        reference = reference.replace("-strongs", "").strip().lower()

        if ' ' not in reference:
            await ctx.send("Invalid reference format. Use BOOK CHAPTER:VERSE or BOOK CHAPTER:VERSE-VERSE.")
            return

        parts = reference.split(' ', 1)
        book = parts[0]
        chapter_verse = parts[1]

        if ':' not in chapter_verse:
            await ctx.send("Invalid reference format. Use BOOK CHAPTER:VERSE or BOOK CHAPTER:VERSE-VERSE.")
            return

        if '-' in chapter_verse:
            chapter_part, verse_range = chapter_verse.split(':', 1)
            start_verse, end_verse = verse_range.split('-', 1)
        else:
            chapter_part, start_verse = chapter_verse.split(':', 1)
            end_verse = start_verse

        chapter = int(chapter_part)
        start_verse = int(start_verse)
        end_verse = int(end_verse)


        # Map the book name to its corresponding integer ID
        book_to_int = {
            "genesis": 1, "exodus": 2, "leviticus": 3, "numbers": 4, "deuteronomy": 5,
            "joshua": 6, "judges": 7, "ruth": 8, "1 samuel": 9, "2 samuel": 10,
            "1 kings": 11, "2 kings": 12, "1 chronicles": 13, "2 chronicles": 14,
            "ezra": 15, "nehemiah": 16, "esther": 17, "job": 18, "psalms": 19,
            "proverbs": 20, "ecclesiastes": 21, "song of solomon": 22, "isaiah": 23,
            "jeremiah": 24, "lamentations": 25, "ezekiel": 26, "daniel": 27,
            "hosea": 28, "joel": 29, "amos": 30, "obadiah": 31, "jonah": 32,
            "micah": 33, "nahum": 34, "habakkuk": 35, "zephaniah": 36, "haggai": 37,
            "zechariah": 38, "malachi": 39, "matthew": 40, "mark": 41, "luke": 42,
            "john": 43, "acts": 44, "romans": 45, "1 corinthians": 46, "2 corinthians": 47,
            "galatians": 48, "ephesians": 49, "philippians": 50, "colossians": 51,
            "1 thessalonians": 52, "2 thessalonians": 53, "1 timothy": 54,
            "2 timothy": 55, "titus": 56, "philemon": 57, "hebrews": 58, "james": 59,
            "1 peter": 60, "2 peter": 61, "1 john": 62, "2 john": 63, "3 john": 64,
            "jude": 65, "revelation": 66
        }

        if book not in book_to_int:
            await ctx.send("Invalid book name. Please use the full book name.")
            return

        book_id = book_to_int[book]
        conn = sqlite3.connect('kjv.sqlite')
        cursor = conn.cursor()

        verses = []
        for verse_number in range(start_verse, end_verse + 1):
            cursor.execute(
                '''SELECT text FROM verses WHERE book = ? AND chapter = ? AND verse = ?''',
                (book_id, chapter, verse_number)
            )
            result = cursor.fetchone()
            if result:
                verse_text = result[0]

                if use_strongs:
                    verse_text = annotate_with_strongs(verse_text)

                verses.append(f"{book} {chapter}:{verse_number} - {verse_text}")
            else:
                verses.append(f"{book} {chapter}:{verse_number} - Verse not found!")

        conn.close()
        await ctx.send("\n".join(verses))

    except Exception as e:
        await ctx.send("An error occurred while fetching the verse.")
        print(f"Error: {e}")

def annotate_with_strongs(verse_text):
    """
    Annotate the given verse text with Strong's numbers and make them clickable links.
    """
    words = verse_text.split()  # Split text into words
    annotated_words = []

    for word in words:
        # Remove punctuation and lowercase for matching
        clean_word = word.strip(",.?!;:\"'[]()").lower()

        # Attempt to find the Strong's number
        strongs_num = find_strongs(clean_word)
        if strongs_num:
            # Append the word with its Strong's number as a clickable link
            link = f"[{strongs_num}](https://www.blueletterbible.org/lexicon/{strongs_num}/kjv/\u200b)"
            annotated_words.append(f"{word} ({link})")
        else:
            # No match; just append the original word
            annotated_words.append(word)
    
    # Join the annotated words back into a single string
    return " ".join(annotated_words)


    return " ".join(annotated_words)

def find_strongs(word):
    """
    Find the Strong's number for a given word from the Greek or Hebrew dictionaries.
    Uses lemmatization as a fallback if no direct match is found.
    """
    
    # Normalize the word to lowercase
    word = word.lower()
    
    # Check in Greek dictionary
    for key, value in strongs_greek.items():
        if value["lemma"].lower() == word or value.get("kjv_def", "").lower() == word:
            # Return key as-is if it already starts with 'G'
            return key if key.startswith("G") else f"G{key}"

    # Check in Hebrew dictionary
    for key, value in strongs_hebrew.items():
        if value["lemma"].lower() == word or value.get("kjv_def", "").lower() == word:
            # Return key as-is if it already starts with 'H'
            return key if key.startswith("H") else f"H{key}"
            
    # If no match, attempt lemmatization
    lemma = lemmatizer.lemmatize(word)
    # Retry matching with lemmatized word
    for key, value in strongs_greek.items():
        if value["lemma"].lower() == lemma or value.get("kjv_def", "").lower() == lemma:
            return key if key.startswith("G") else f"G{key}"
    for key, value in strongs_hebrew.items():
        if value["lemma"].lower() == lemma or value.get("kjv_def", "").lower() == lemma:
            return key if key.startswith("H") else f"H{key}"

    # No match found
    return None

        
# Event: Bot is ready
@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    print(f'Bot is connected to the following guilds: {bot.guilds}')
    
@bot.event
async def on_message(message):
    print(f"Message received: {message.content}")  # This will print all messages the bot sees
    await bot.process_commands(message)  # This is necessary to process commands
    
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Sorry, I didn't recognize that command.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("You're missing some required arguments!")
        
@bot.command()
async def setprefix(ctx, prefix: str):
    bot.command_prefix = prefix
    await ctx.send(f"Prefix changed to: {prefix}")

@bot.command()
async def ping(ctx):
    await ctx.send("Pong! 🏓")

# Command: Respond to "!hello"
@bot.command()
async def hello(ctx):
    print(f"Received command: {ctx.command}")  # This is to confirm command is received
    try:
        await ctx.send("Hello! 👋")
        
        
        print("Sent response: Hello! 👋")  # Log if the response is successfully sent
    except Exception as e:
        print(f"Error sending message: {e}")  # Log any error that occurs when sending
        
@bot.command()
async def botinfo(ctx):
    help_message = """
    Here are the commands you can use:
    - !hello: Greets the bot
    - !userinfo: Shows your user information
    - !serverinfo: Shows information about the server
    - !setprefix: changes the special character to call commands
    - !ping: pong
    - !poll: makes a quick poll ex: !poll title "topic" "topic" "topic"
    - !listthreads: display all threads in current channel and there info
    - !ratethread: change the rating on a thread for example !ratethread #lucifer 1, 2, 3, 4, 5
    - !bible: type "Book chapter:verse-verse" you can also annotate with strongs. ex: !bible -strongs Proverbs 25:2-3
    - !strongs: type G or H and then the number you are trying to lookup. ex: G2045 you can also type !strongs search "word" and optionally -g or -h to specify only greek or hebrew words. ex !strongs search love -g
    """
    await ctx.send(help_message)

@bot.command()
async def userinfo(ctx):
    user = ctx.author
    user_info = f"Username: {user.name}\nID: {user.id}\nJoined at: {user.joined_at}"
    await ctx.send(user_info)
    

@bot.command()
async def serverinfo(ctx):
    server = ctx.guild
    server_info = f"Server name: {server.name}\nMember count: {server.member_count}"
    await ctx.send(server_info)
    
@bot.command()
async def poll(ctx, question, *options):
    if len(options) < 2:
        await ctx.send("You need at least two options for a poll!")
        return

    embed = discord.Embed(title=question, description="\n".join(f"{i+1}. {option}" for i, option in enumerate(options)))
    poll_message = await ctx.send(embed=embed)
    for emoji in ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣']:
        await poll_message.add_reaction(emoji)
        
        
# Set up the SQLite database (You can replace 'threads.db' with a different name or path)
def setup_db():
    conn = sqlite3.connect('threads.db')
    cursor = conn.cursor()
    
    # Create a table for thread ratings
    cursor.execute('''CREATE TABLE IF NOT EXISTS thread_info (
                        thread_id INTEGER PRIMARY KEY,
                        thread_name TEXT,
                        owner_id INTEGER,
                        rating INTEGER
                    )''')
    
    conn.commit()
    conn.close()

setup_db()

RATING_MESSAGES = {
    1: "Probably Opinion",
    2: "Possible Truth",
    3: "Biblical but Opinion",
    4: "Probably Biblical Truth",
    5: "Irrefutable Truth"
}

@bot.command()
async def ratethread(ctx, thread: discord.Thread, rating: int):
     # Ensure the rating is between 1 and 5
    if rating < 1 or rating > 5:
        await ctx.send("Please provide a rating between 1 and 5.")
        return

    # Get the corresponding message for the rating
    rating_message = RATING_MESSAGES[rating]

    # Connect to the database
    conn = sqlite3.connect('threads.db')
    cursor = conn.cursor()

    # Insert or update the rating for the thread
    cursor.execute('''INSERT OR REPLACE INTO thread_info (thread_id, thread_name, owner_id, rating)
                      VALUES (?, ?, ?, ?)''', 
                   (thread.id, thread.name, thread.owner.id, rating))

    conn.commit()
    conn.close()

    await ctx.send(f"Thread **{thread.name}** has been rated {rating}/5: **{rating_message}**!")
    
        
@bot.command()
async def listthreads(ctx, channel: discord.TextChannel = None):
    # If no channel is provided, use the current channel
    if not channel:
        channel = ctx.channel

    # Fetch active threads in the specified channel
    threads = channel.threads

    # If no threads are found
    if not threads:
        await ctx.send(f"No active threads in the channel {channel.mention}.")
        return
    
    # Prepare a message to display thread details
    thread_info = f"Active Threads in {channel.mention}:\n"
    
    for thread in threads:
        # Fetch rating from the database
        conn = sqlite3.connect('threads.db')
        cursor = conn.cursor()
        cursor.execute("SELECT rating FROM thread_info WHERE thread_id = ?", (thread.id,))
        rating = cursor.fetchone()
        conn.close()
        
        # If no rating is found, set it to 'Unrated' with a rating of 0
        if rating:
            rating_value = rating[0]
            rating_message = RATING_MESSAGES.get(rating_value, "Unrated")
        else:
            rating_value = 0
            rating_message = "Unrated"
        
        # Get the thread information
        thread_name = thread.name
        thread_owner = thread.owner
        thread_creation = thread.created_at.strftime("%Y-%m-%d %H:%M:%S")
        thread_id = thread.id
        thread_info += f"\n**{thread_name}** (ID: {thread_id})\nOwner: {thread_owner}\nCreated at: {thread_creation}\nRating: {rating_value}/5 - {rating_message}\n"

    await ctx.send(thread_info)
    
    # Clear command messages and bot messages
@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, limit: int = 100):
    """Clear bot messages and command messages from the last `limit` messages."""
    def is_target_message(message):
        # Check if the message is from the bot or a command message (starts with the command prefix)
        return message.author == bot.user or message.content.startswith("!")

    try:
        deleted = await ctx.channel.purge(limit=limit, check=is_target_message)
        await ctx.send(f"Cleared {len(deleted)} bot and command messages.", delete_after=5)
    except discord.Forbidden:
        await ctx.send("I don't have permission to manage messages in this channel.", delete_after=5)
    except discord.HTTPException as e:
        await ctx.send(f"An error occurred: {e}", delete_after=5)


# Run the bot
bot.run("MTMxODcwOTczNTA1MDE4MjcxNw.GW-vQS.X_D9GUt22HmOgVtcsn_YOYXyzy7tsVqbW0fsWg")
