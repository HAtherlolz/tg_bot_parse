from datetime import datetime, timedelta
from typing import List
from zoneinfo import ZoneInfo

from telegram import Update
from telegram import Bot as TGBot
from telegram.ext import ContextTypes

from utils.logs import log
from services.google import Google
from cfg.config import settings


class Bot:
    @classmethod
    async def handle_message(
            cls,
            update: Update,
            context: ContextTypes.DEFAULT_TYPE,
    ) -> None:

        if update.message is None:
            log.info("Received an update without message")
            return

        # if update.message.chat.title != settings.CHAT_TITLE:
        #     log.info(f"Wrong chat - {update.message.chat.title}")

        chat_id = update.message.chat_id
        text = update.message.text

        # if text.count("-") <= 4 or text.count("-") >= 7:
        if text.count("-") <=2 or text.count("-") >= 7:
            log.info("Received an update with wrong number of '-'s")
            await Bot.send_message_to_chat(chat_id=chat_id, message="Message is invalid. Please provide the correct format")
            return
        
        if text.count(":") >= 4:
            log.info("Received an update with more than 3 ':'s")
            await Bot.send_message_to_chat(chat_id=chat_id, message="Message is invalid. Please provide the correct format")
            return

        utc_date_time = update.message.date
        gmt_plus_3 = ZoneInfo('Etc/GMT-3')  # 'Etc/GMT-3' corresponds to GMT+3
        local_date_time = utc_date_time.astimezone(gmt_plus_3)

        date_time = local_date_time.strftime('%Y-%m-%d %H:%M')

        # if text.startswith('#'):
        log.info(f"Message from chat {chat_id}: {text}")
        try:
            parsed_msg = cls.message_parser(msg=text, date_time=date_time)
            log.info(f"Parsed message: {parsed_msg}")
            Google.update_sht(parsed_msg)
        except Exception as e:
            log.info(f"Error parsing message: {e}")
            await Bot.send_message_to_chat(chat_id=chat_id, message="Message is invalid. Please provide the correct format")


    @classmethod
    def message_parser(cls, msg: str, date_time: str) -> List:
        res: List = list()
        msg: List = msg.split("\n")

        # Check if the second row contains the word "tomorrow"
        if len(msg) > 1 and "tomorrow" in msg[1].lower():
            caps_date = cls.parse_date(date_time, True)
            log.info("Is for tomorrow?: Yes")
        else:
            caps_date = cls.parse_date(date_time, False)
            log.info("Is for tomorrow?: No")

        for line in msg:
            if "-" in line or (":" in line and "gmt" in line):
                l = [x.strip() for x in line.split("-")] if "-" in line else [x.strip() for x in line.split()]
                res_t = {
                    "Message timestamp": date_time,
                    "title": l[0],  # Use the first part as title if not set
                    "country": l[1],
                    "total_caps": None,
                    "start_time": None,
                    "end_time": None,
                    "time_zone": None,
                    "username": None,
                    "note": None,
                    "Cap day": caps_date,
                }
                for i in range(len(l)):
                    if "cap" in l[i].lower() or l[i].isdigit() and res_t["total_caps"] is None:
                        res_t["total_caps"] = l[i].replace("cap", "").strip()
                    elif ":" not in l[3]:
                        raise ValueError("Message is invalid. Please provide the correct format")
                    elif (":" in l[i] or l[i].isdigit()) and "gmt" not in l[i]:
                        res_t["start_time"] = l[i].strip()
                    elif "gmt" in l[i]:
                        if l[i].count(":") == 2:
                            res_t["start_time"] = l[i].split(" ")[0]
                            res_t["end_time"] = l[i].split(" ")[1]
                            res_t["time_zone"] = "gmt +" + str(l[i].split(" ")[-1].strip()[-1])
                        else:
                            res_t["end_time"] = l[i].split(" ")[0]
                            res_t["time_zone"] = "gmt +" + str(l[i].split(" ")[-1].strip()[-1])
                        if i == range(len(l)):
                            break
                    elif res_t.get("time_zone") is not None and i == len(l) - 2:
                        res_t["username"] = l[i].strip()
                    elif res_t.get("time_zone") is not None and i == len(l) - 1:
                        res_t["note"] = l[i].strip()
                    elif res_t.get("time_zone") is None and i == len(l) - 2:
                        res_t["username"] = l[i].strip()
                    elif res_t.get("time_zone") is None and i == len(l) - 1:
                        res_t["note"] = l[i].strip()
                if any(key not in {"note", "username"} and value is None for key, value in res_t.items()):
                    raise ValueError("Message is invalid. Please provide the correct format")
                else:
                    res.append(res_t)
        return res

    @staticmethod
    def parse_date(date_time: str, is_tomorrow: bool) -> str:
        """
            Parsing str of datetime to change structure
            and if it's tomorrow it will add one more day
        """
        datetime_obj = datetime.strptime(date_time, "%Y-%m-%d %H:%M")
        if is_tomorrow:
            datetime_obj = datetime_obj + timedelta(days=1)
        new_datetime_str = datetime_obj.strftime("%Y-%m-%d")
        return new_datetime_str

    @staticmethod
    async def send_message_to_chat(chat_id: int, message: str) -> None:
        bot = TGBot(token=settings.TG_TOKEN)
        await bot.send_message(chat_id=chat_id, text=message)