import base58
from typing import Tuple
from telebot import types
from anchorpy import Provider, Program, Wallet
from anchorpy_core.idl import Idl  # type: ignore
from solana.rpc.async_api import AsyncClient
from anchorpy import Context
from solders.keypair import Keypair  # type: ignore
from solders.pubkey import Pubkey  # type: ignore
import asyncio
from telebot.async_telebot import AsyncTeleBot
from interface import raw_interface 
from wallet import wallet_pvkey
from environs import Env
env = Env()
env.read_env('.env')
# Configuration
BOT_TOKEN = env("BOT_TOKEN")
program_id = Pubkey.from_string("3BGrehnLwFC5tPsmB8SQ4UZgUDa2EMyzBVVb5KMxPbVc")
SYSTEM_PROGRAM_ID = Pubkey.from_string("11111111111111111111111111111111")

bot = AsyncTeleBot(token= BOT_TOKEN)


d_wallet = Keypair.from_base58_string(wallet_pvkey)
wallet = d_wallet.pubkey()


def find_vote_account_address(program_id: Pubkey) -> Tuple[Pubkey, int]:
    return Pubkey.find_program_address(  
        [b"vxtx"],
        program_id
    )

vote_account, bump = find_vote_account_address(program_id)  # Create the vote account where all the data will be stored


async def init_solana():  #Initialize Parameters
    try:
        client = AsyncClient("https://api.devnet.solana.com")
        provider = Provider(client, Wallet(d_wallet))
        idl = Idl.from_json(raw_interface)
        program = Program(idl, program_id, provider)
        return client, program
    except Exception as e:
        print(f"Error initializing Solana: {e}")
        return None, None

def get_keyboard():   # Create Keyboard Menu encapsulating all bot actions
    markup = types.ReplyKeyboardMarkup(row_width=2)
    buttons = [
        "Register to Vote",
        "Cast Vote",
        "View Results"
    ]
    markup.add(*[types.KeyboardButton(button) for button in buttons])
    return markup

# First message handler the user uses to initiate interaction with the bot and 
# call the get_keyboard() function
@bot.message_handler(commands=["start"])  
async def start_handler(message):
    try:
        await bot.reply_to(
            message,
            "Welcome to the Voting Bot! Choose an action:",
            reply_markup=get_keyboard()
        )
    except Exception as e:
        print(f"Start error: {e}")
        await bot.reply_to(message, "❌ An error occurred while starting the bot.")

#This block of code initialize solana connection and call the initialize function
#in the smart contract




@bot.message_handler(func=lambda message: message.text == "Register to Vote")
async def register_vote(message):
    try:
        client, program = await init_solana()  #initializing solana connection
        if not client or not program:
            await bot.reply_to(message, "Failed to initialize Solana connection")
            return
        print(program.provider.wallet.public_key)



        await program.rpc["initialize"](   #calling the initialize function
            wallet,
            bump,
            ctx=Context(
                accounts={
                    "vote_account": vote_account,
                    "user": program.provider.wallet.public_key,
                    "system_program": SYSTEM_PROGRAM_ID
                }
            )
        )

        await client.close()  #closing solana connection

        await bot.reply_to( 
            message,
            f"✅ Registration successful!\nVoting account created at: {vote_account}",
            reply_markup=get_keyboard()
        )
    except Exception as e:
        error_message = f"❌ Registration failed: {str(e)}"
        print(error_message)
        await bot.reply_to(message, error_message)


#Fetching the political parties names in from the solana program
@bot.message_handler(func=lambda message: message.text == "Cast Vote")
async def show_voting_options(message):
    try:
        client, program = await init_solana()  # Initiating solana connection
        if not client or not program:   # Condition checking if solana connection is successful
            await bot.reply_to(message, "Failed to initialize Solana connection")
            return
        
        vote_account_data = await program.account['VoteAccount'].fetch(vote_account)  #fetching the vote account data
        
        markup = types.InlineKeyboardMarkup(row_width=1)   
        
        # Create buttons for each party
        for party in vote_account_data.parties:
            button = types.InlineKeyboardButton(
                text=party.name,
                callback_data=f"vote_{party.name}"
            )
            markup.add(button)
        
        await bot.reply_to(
            message, 
            "Select a party to vote for:", 
            reply_markup=markup
        ) 
        await client.close()   # Closing the solana connection
    except Exception as e:
        error_message = f"❌ Error loading parties: {str(e)}"
        print(error_message)
        await bot.reply_to(message, error_message)


#Calling the castVote function from the lib.rs
@bot.callback_query_handler(func=lambda call: call.data.startswith('vote_'))
async def cast_vote(call):
    try:
        client, program = await init_solana()
        if not client or not program:
            await bot.answer_callback_query(call.id, "Failed to initialize Solana connection")
            return
        

        party_name = call.data.split('_')[1]  # Get party name from callback data

        
        # Call the 'castVote' function with party name
        await program.rpc["cast_vote"](
            party_name,
            ctx=Context(
                accounts={
                    "vote_account": vote_account
                }
            )
        )

        # The error below usually occurs because there is no solana network in the wallet or there is insufficient token in the solana wallet 

#         ❌ Error casting vote: SendTransactionPreflightFailureMessage { message: "Transaction simulation failed: Attempt to debit an account but found 
# no record of a prior credit.",

        await bot.answer_callback_query(call.id, "✅ Vote cast successfully!")
        await bot.edit_message_text(
            "Thank you for voting! Your vote has been recorded.",
            call.message.chat.id,
            call.message.message_id
        )
        await client.close()
    except Exception as x:
        error_message = f"❌ Error casting vote: {str(x)}"
        # import traceback
        print(error_message)
        # traceback.print_exc()
        # await bot.answer_callback_query(call.id, error_message)


# Display the vote results
@bot.message_handler(func=lambda message: message.text == "View Results")
async def view_results(message):
    try:
        client, program = await init_solana()
        if not client or not program:
            await bot.reply_to(message, "Failed to initialize Solana connection")
            return
        
        # Fetch vote account data
        vote_account_data = await program.account["VoteAccount"].fetch(vote_account)

        # Format results
        results_text = "📊 Current Voting Results:\n\n"
        total_votes = sum(party.votes for party in vote_account_data.parties)
        
        for party in vote_account_data.parties:
            percentage = (party.votes / total_votes * 100) if total_votes > 0 else 0
            results_text += f"{party.name}: {party.votes} votes ({percentage:.1f}%)\n"
        
        results_text += f"\nTotal Votes: {total_votes}"
        
        await bot.reply_to(message, results_text)  #displays the results in percentage format to the bot user
        await client.close()
    except Exception as e:
        error_message = f"❌ Error fetching results: {str(e)}"
        print(error_message)
        await bot.reply_to(message, error_message)

if __name__ == "__main__":
    print("Starting bot...")
    asyncio.run(bot.polling())
