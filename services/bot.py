from datetime import datetime, timedelta
from typing import List
from zoneinfo import ZoneInfo

from telegram import Update
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

        if update.message.chat.title != settings.CHAT_TITLE:
            log.info(f"Wrong chat - {update.message.chat.title}")

        chat_id = update.message.chat_id
        text = update.message.text

        utc_date_time = update.message.date
        gmt_plus_3 = ZoneInfo('Etc/GMT-3')  # 'Etc/GMT-3' corresponds to GMT+3
        local_date_time = utc_date_time.astimezone(gmt_plus_3)

        date_time = local_date_time.strftime('%Y-%m-%d %H:%M')

        # if text.startswith('#'):
        log.info(f"Message from chat {chat_id}: {text}")
        parsed_msg = cls.message_parser(msg=text, date_time=date_time)
        log.info(f"Parsed message: {parsed_msg}")

            # Google.update_sht(parsed_msg)

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

        title = None
        for line in msg:
            if "-" in line or (":" in line and "gmt" in line):
                l = [x.strip() for x in line.split("-")] if "-" in line else [x.strip() for x in line.split()]
                res_t = {
                    "Message timestamp": date_time,
                    "Cap day": caps_date,
                    "title": title if title else l[0],  # Use the first part as title if not set
                    "country": None,
                    "total_caps": None,
                    "start_time": None,
                    "end_time": None,
                    "time_zone": None,
                    "username": None,
                    "note": None
                }
                for i in range(len(l)):
                    if i == 0 and title is None:
                        res_t["country"] = l[i].strip()
                    elif "cap" in l[i].lower() or l[i].isdigit() and res_t["total_caps"] is None:
                        res_t["total_caps"] = l[i].replace("cap", "").strip()
                    elif (":" in l[i] or l[i].isdigit()) and "gmt" not in l[i]:
                        res_t["start_time"] = l[i].strip()
                    elif "gmt" in l[i]:
                        time_parts = l[i].split(" ")
                        if len(time_parts) <= 3:  # case where "17:00 24:00 gmt+3"
                            res_t["end_time"] = time_parts[0].strip()
                            if "gmt" in time_parts[1].strip():
                                res_t["time_zone"] = time_parts[1].strip()[-1]
                        else:  # standard "17:00-24:00 gmt+3"
                            res_t["start_time"] = time_parts[0].strip()
                            res_t["end_time"] = time_parts[1].strip()
                            res_t["time_zone"] = time_parts[-1].replace("+", "gmt+").replace("-", "gmt-").strip()
                    elif res_t.get("time_zone") is not None and i == len(l) - 2:
                        res_t["username"] = l[i].strip()
                    elif res_t.get("time_zone") is not None and i == len(l) - 1:
                        res_t["note"] = l[i].strip()
                    elif res_t.get("time_zone") is None and i == len(l) - 2:
                        res_t["username"] = l[i].strip()
                    elif res_t.get("time_zone") is None and i == len(l) - 1:
                        res_t["note"] = l[i].strip()
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
