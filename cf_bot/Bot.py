from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes, JobQueue
)

from Monitor import *
from Participant import *
from User import *


WAIT, SELECT_CONTEST, CONFIRMATION = range(3)
CHOOSE, REMOVE = range(2)

class CodeforcesMonitorBot:
    def __init__(self, token, api_key, api_secret):
        self.job_queue = JobQueue()
        self.application = Application.builder().token(token).job_queue(self.job_queue).build()
        
        self.monitor = Monitor(
            api_key=api_key,
            api_secret=api_secret,
            participantsFile="participants.csv",
            datafile="data.txt"
        )
        
        self._init_handlers()
        
        self.job_queue = self.application.job_queue
        self.job_queue.run_repeating(
            self._check_submissions,
            interval=20.0,
            first=0.0
        )

        self.job_queue.run_repeating(
            self._unload,
            interval=1200.0,
            first=1200.0
        )
    
    def _init_handlers(self):
        add_handler = ConversationHandler(
            entry_points=[CommandHandler('start', self.start), CommandHandler('add', self.add_input)],
            states={
                WAIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.add_input)],
                SELECT_CONTEST: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.select_contest)]
            },
            fallbacks=[CommandHandler('cancel', self.cancel)]
        )

        remove_handler = ConversationHandler(
            entry_points=[CommandHandler('remove', self.remove_input)],
            states={
                CHOOSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.remove_input)],
                REMOVE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.remove_contest)]
            },
            fallbacks=[CommandHandler('cancel', self.cancel)]
        )
        
        self.application.add_handler(add_handler)
        self.application.add_handler(remove_handler)

        self.application.add_handler(CommandHandler("add", self.add_input))
        self.application.add_handler(CommandHandler("mycontests", self.show_contests))
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        user = update.message.from_user
        await update.message.reply_text(
            f"Привет, {user.first_name}! Я мониторю контесты Codeforces. Введи id контестов через пробел"
        )
        return SELECT_CONTEST
    
    async def add_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        await update.message.reply_text("Введите id контестов через пробел")
        return SELECT_CONTEST
    
    async def select_contest(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        try:
            user_id = update.message.from_user.id
            contests_id = list(map(int, update.message.text.strip().split()))
        
            for contest_id in contests_id:

                if user_id in self.monitor.users:
                    current_contests = self.monitor.users[user_id].contests
                    if contest_id in current_contests:
                        await update.message.reply_text("Этот контест уже в вашем списке!")
                    else:
                        self.monitor.addUserContests(user_id, [contest_id])
                        await update.message.reply_text(f"Контест {contest_id} добавлен для мониторинга!")
                else:
                    self.monitor.addUser(User(user_id, [contest_id]))
                    await update.message.reply_text(f"Контест {contest_id} добавлен для мониторинга!")
                
            return ConversationHandler.END
        except ValueError:
            await update.message.reply_text("Пожалуйста, введите числовой ID контеста!")
            return SELECT_CONTEST
     
    async def show_contests(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.message.from_user.id
        if user_id in self.monitor.users:
            contests = self.monitor.users[user_id].contests
            await update.message.reply_text(
                f"Ваши контесты: {', '.join(map(str, contests))}"
            )
        else:
            await update.message.reply_text("У вас нет отслеживаемых контестов.")
    
    async def remove_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        await update.message.reply_text("Введите id контестов для удаления через пробел")
        return REMOVE
 
    async def remove_contest(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        try:
            user_id = update.message.from_user.id
            contests_id = list(map(int, update.message.text.strip().split()))
            
            for contest_id in contests_id:
                if user_id in self.monitor.users:
                    current_contests = self.monitor.users[user_id].contests
                    if contest_id in current_contests:
                        self.monitor.removeUserContest(user_id, [contest_id])
                        await update.message.reply_text(f"Контест {contest_id} удален из мониторинга")
                    else:
                        await update.message.reply_text(f"Контеста {contest_id} нет в вашем списке")
                else:
                    await update.message.reply_text(f"Контест удален")
                
            return ConversationHandler.END
        except:
            await update.message.reply_text("Введите числовые значения")
            return REMOVE

    
    async def _check_submissions(self, context: ContextTypes.DEFAULT_TYPE):
        """Периодическая проверка новых посылок"""
        self.monitor.updateSubmissions()
        
        for contest_id, submissions in self.monitor.new_submissions.items():
            if contest_id not in self.monitor.contestIDsTOUserIDs:
                continue
                
            for user_id in self.monitor.contestIDsTOUserIDs[contest_id]:
                for submission in submissions:
                    try:
                            
                        handle = submission['author']['members'][0]['handle']
                        
                        handle = handle.split('=', 1)
                        if len(handle) == 2: handle = handle[1] 
                        else: handle = handle[0].strip()                        
                        participant = self.monitor.participants.get(handle)
                        
                        if participant:
                            message = (
                                f"Новая посылка в контесте {contest_id}!\n"
                                f"Участник: {participant.name} (@{handle})\n"
                                f"Группа: {participant.group}\n"
                                f"Задача: {submission['problem']['index']} - {submission['problem']['name']}\n"
                                f"Вердикт: {submission['verdict']}"
                            )
                        else:
                            message = (
                                f"Новая посылка в контесте {contest_id}!\n"
                                f"Участник: {handle}\n"
                                f"Задача: {submission['problem']['index']} - {submission['problem']['name']}\n"
                                f"Вердикт: {submission['verdict']}"
                            )
                        
                        await context.bot.send_message(chat_id=user_id, text=message)
                    except:
                        pass

    async def _unload(self, context: ContextTypes.DEFAULT_TYPE):
        self.monitor.unloadData()

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        await update.message.reply_text("Действие отменено.")
        return ConversationHandler.END

    def run(self):
        self.application.run_polling()
