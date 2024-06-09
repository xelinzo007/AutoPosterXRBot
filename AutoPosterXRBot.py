from telethon import TelegramClient, events, Button
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
from telethon.errors import FloodWaitError
import asyncio
import motor.motor_asyncio

# Your API ID, API hash, and bot token
api_id = "22181658"
api_hash = '3138df6840cbdbc28c370fd29218139a'
bot_token = '7452901508:AAHuEOrkSYcDlaoUX8GD5msVimjJJ1iLJ1E'

# Initialize the Telegram client and bot
client = TelegramClient('user_session', api_id, api_hash)
bot = TelegramClient('bot_session', api_id, api_hash).start(bot_token=bot_token)

# Initialize MongoDB client
mongo_client = motor.motor_asyncio.AsyncIOMotorClient('mongodb+srv://forwd:forwdo@cluster0.nkmhi9a.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db = mongo_client['telegram_bot']
collection = db['schedules']

# Dictionary to keep track of tasks
tasks = {}

# Function to forward messages
async def forward_messages(user_id, schedule_name, source_channel_id, destination_channel_id, batch_size, delay):
    post_counter = 0

    async with client:
        async for message in client.iter_messages(int(source_channel_id), reverse=True):
            if post_counter >= batch_size:
                await asyncio.sleep(delay)
                post_counter = 0

            # Check if the message is a photo, video, or document
            if isinstance(message.media, (MessageMediaPhoto, MessageMediaDocument)):
                try:
                    await client.send_message(int(destination_channel_id), message)
                    post_counter += 1
                except FloodWaitError as e:
                    print(f"FloodWaitError: Sleeping for {e.seconds} seconds")
                    await asyncio.sleep(e.seconds)
                except Exception as e:
                    print(f"An error occurred: {e}")

            if schedule_name not in tasks[user_id] or tasks[user_id][schedule_name].cancelled():
                break



# Event handler for starting the bot
@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    user_id = event.sender_id

    async with bot.conversation(user_id) as conv:
        await conv.send_message('Please provide a name for the schedule:')
        schedule_name = await conv.get_response()

        await conv.send_message('Please provide the source channel ID:')
        source_channel_id = await conv.get_response()
        if not source_channel_id.text.lstrip('-').isdigit():
            await conv.send_message('Invalid channel ID. Please restart the process with /start.')
            return

        await conv.send_message('Please provide the destination channel ID:')
        destination_channel_id = await conv.get_response()
        if not destination_channel_id.text.lstrip('-').isdigit():
            await conv.send_message('Invalid channel ID. Please restart the process with /start.')
            return

        await conv.send_message('How many posts do you want to forward in each batch?')
        post_limit = await conv.get_response()
        if not post_limit.text.isdigit():
            await conv.send_message('Invalid number of posts. Please restart the process with /start.')
            return

        await conv.send_message('What is the time interval between batches in seconds?')
        delay = await conv.get_response()
        if not delay.text.isdigit():
            await conv.send_message('Invalid delay. Please restart the process with /start.')
            return

        await conv.send_message(f'You have set up the following schedule:\nSchedule Name: {schedule_name.text}\nSource Channel ID: {source_channel_id.text}\nDestination Channel ID: {destination_channel_id.text}\nPost Limit: {post_limit.text}\nDelay: {delay.text} seconds\n\nDo you want to start forwarding? (yes/no)')
        confirmation = await conv.get_response()
        if confirmation.text.lower() != 'yes':
            await conv.send_message('Schedule setup cancelled.')
            return

        # Store the schedule in the MongoDB collection
        await collection.update_one(
            {'user_id': user_id},
            {'$push': {
                'schedules': {
                    'name': schedule_name.text,
                    'source_channel_id': int(source_channel_id.text),
                    'destination_channel_id': int(destination_channel_id.text),
                    'post_limit': int(post_limit.text),
                    'delay': int(delay.text)
                }
            }},
            upsert=True
        )

        await conv.send_message(f'Forwarding messages from {source_channel_id.text} to {destination_channel_id.text} every {delay.text} seconds...')

        if user_id not in tasks:
            tasks[user_id] = {}

        # Start forwarding messages
        task = asyncio.create_task(forward_messages(user_id, schedule_name.text, int(source_channel_id.text), int(destination_channel_id.text), int(post_limit.text), int(delay.text)))
        tasks[user_id][schedule_name.text] = task

# Event handler for creating a new schedule
@bot.on(events.NewMessage(pattern='/newschedule'))
async def new_schedule(event):
    user_id = event.sender_id

    async with bot.conversation(user_id) as conv:
        await conv.send_message('Please provide a name for the schedule:')
        schedule_name = await conv.get_response()

        await conv.send_message('Please provide the source channel ID:')
        source_channel_id = await conv.get_response()
        if not source_channel_id.text.lstrip('-').isdigit():
            await conv.send_message('Invalid channel ID. Please restart the process with /newschedule.')
            return

        await conv.send_message('Please provide the destination channel ID:')
        destination_channel_id = await conv.get_response()
        if not destination_channel_id.text.lstrip('-').isdigit():
            await conv.send_message('Invalid channel ID. Please restart the process with /newschedule.')
            return

        await conv.send_message('How many posts do you want to forward in each batch?')
        post_limit = await conv.get_response()
        if not post_limit.text.isdigit():
            await conv.send_message('Invalid number of posts. Please restart the process with /newschedule.')
            return

        await conv.send_message('What is the time interval between batches in seconds?')
        delay = await conv.get_response()
        if not delay.text.isdigit():
            await conv.send_message('Invalid delay. Please restart the process with /newschedule.')
            return

        await conv.send_message(f'You have set up the following schedule:\nSchedule Name: {schedule_name.text}\nSource Channel ID: {source_channel_id.text}\nDestination Channel ID: {destination_channel_id.text}\nPost Limit: {post_limit.text}\nDelay: {delay.text} seconds\n\nDo you want to start forwarding? (yes/no)')
        confirmation = await conv.get_response()
        if confirmation.text.lower() != 'yes':
            await conv.send_message('Schedule setup cancelled.')
            return

        # Store the schedule in the MongoDB collection
        await collection.update_one(
            {'user_id': user_id},
            {'$push': {
                'schedules': {
                    'name': schedule_name.text,
                    'source_channel_id': int(source_channel_id.text),
                    'destination_channel_id': int(destination_channel_id.text),
                    'post_limit': int(post_limit.text),
                    'delay': int(delay.text)
                }
            }},
            upsert=True
        )

        await conv.send_message(f'Forwarding messages from {source_channel_id.text} to {destination_channel_id.text} every {delay.text} seconds...')

        if user_id not in tasks:
            tasks[user_id] = {}

        # Cancel any existing task with the same schedule name
        if schedule_name.text in tasks[user_id] and not tasks[user_id][schedule_name.text].cancelled():
            tasks[user_id][schedule_name.text].cancel()

        # Start forwarding messages
        task = asyncio.create_task(forward_messages(user_id, schedule_name.text, int(source_channel_id.text), int(destination_channel_id.text), int(post_limit.text), int(delay.text)))
        tasks[user_id][schedule_name.text] = task

# Event handler for stopping the forwarding process
@bot.on(events.NewMessage(pattern='/stop'))
async def stop(event):
    user_id = event.sender_id

    if user_id in tasks and tasks[user_id]:
        for task in tasks[user_id].values():
            if not task.cancelled():
                task.cancel()
        await event.respond('All forwarding processes stopped.')
    else:
        await event.respond('No active forwarding process found.')

# Event handler for showing schedules
@bot.on(events.NewMessage(pattern='/schedules'))
async def show_schedules(event):
    user_id = event.sender_id
    user_data = await collection.find_one({'user_id': user_id})

    if not user_data or 'schedules' not in user_data:
        await event.respond('No schedules found.')
        return

    schedules = user_data['schedules']
    buttons = [Button.inline(schedule['name'], data=schedule['name']) for schedule in schedules]
    await event.respond('Your schedules:', buttons=buttons)

# Event handler for managing individual schedules
@bot.on(events.CallbackQuery)
async def manage_schedule(event):
    user_id = event.sender_id
    schedule_name = event.data.decode('utf-8')

    user_data = await collection.find_one({'user_id': user_id})
    if not user_data or 'schedules' not in user_data:
        await event.respond('No schedules found.')
        return

    schedule = next((s for s in user_data['schedules'] if s['name'] == schedule_name), None)
    if not schedule:
        await event.respond('Schedule not found.')
        return

    buttons = [
        [Button.inline('Update Post Limit', data=f'update_post_limit:{schedule_name}')],
        [Button.inline('Update Delay', data=f'update_delay:{schedule_name}')],
    ]
    await event.respond(f'Schedule: {schedule_name}', buttons=buttons)

# Event handler for updating post limit
@bot.on(events.CallbackQuery(data=re.compile(b'update_post_limit:(.+)')))
async def update_post_limit(event):
    schedule_name = event.data.decode('utf-8').split(':')[1]
    user_id = event.sender_id

    async with bot.conversation(user_id) as conv:
        await conv.send_message('Enter the new post limit:')
        post_limit = await conv.get_response()
        if not post_limit.text.isdigit():
            await conv.send_message('Invalid number of posts. Please restart the process.')
            return

        # Update the post limit in the MongoDB collection
        await collection.update_one(
            {'user_id': user_id, 'schedules.name': schedule_name},
            {'$set': {'schedules.$.post_limit': int(post_limit.text)}}
        )

        await conv.send_message(f'Post limit for schedule {schedule_name} updated to {post_limit.text}.')

        # Restart the forwarding task with the new post limit
        user_data = await collection.find_one({'user_id': user_id})
        schedule = next((s for s in user_data['schedules'] if s['name'] == schedule_name), None)

        if schedule_name in tasks[user_id] and not tasks[user_id][schedule_name].cancelled():
            tasks[user_id][schedule_name].cancel()

        task = asyncio.create_task(forward_messages(user_id, schedule_name, schedule['source_channel_id'], schedule['destination_channel_id'], int(post_limit.text), schedule['delay']))
        tasks[user_id][schedule_name] = task

# Event handler for updating delay
@bot.on(events.CallbackQuery(data=re.compile(b'update_delay:(.+)')))
async def update_delay(event):
    schedule_name = event.data.decode('utf-8').split(':')[1]
    user_id = event.sender_id

    async with bot.conversation(user_id) as conv:
        await conv.send_message('Enter the new delay (in seconds):')
        delay = await conv.get_response()
        if not delay.text.isdigit():
            await conv.send_message('Invalid delay. Please restart the process.')
            return

        # Update the delay in the MongoDB collection
        await collection.update_one(
            {'user_id': user_id, 'schedules.name': schedule_name},
            {'$set': {'schedules.$.delay': int(delay.text)}}
        )

        await conv.send_message(f'Delay for schedule {schedule_name} updated to {delay.text} seconds.')

        # Restart the forwarding task with the new delay
        user_data = await collection.find_one({'user_id': user_id})
        schedule = next((s for s in user_data['schedules'] if s['name'] == schedule_name), None)

        if schedule_name in tasks[user_id] and not tasks[user_id][schedule_name].cancelled():
            tasks[user_id][schedule_name].cancel()

        task = asyncio.create_task(forward_messages(user_id, schedule_name, schedule['source_channel_id'], schedule['destination_channel_id'], schedule['post_limit'], int(delay.text)))
        tasks[user_id][schedule_name] = task

# Run the bot
bot.start(bot_token=bot_token)

# Run the event loop indefinitely
asyncio.get_event_loop().run_forever()
