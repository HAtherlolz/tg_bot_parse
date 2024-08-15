from datetime import datetime, timedelta
from typing import List
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.ext import ContextTypes

from utils.logs import log
from services.google import Google


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

        chat_id = update.message.chat_id
        text = update.message.text

        utc_date_time = update.message.date
        gmt_plus_3 = ZoneInfo('Etc/GMT-3')  # 'Etc/GMT-3' corresponds to GMT+3
        local_date_time = utc_date_time.astimezone(gmt_plus_3)

        date_time = local_date_time.strftime('%Y-%m-%d %H:%M')

        if text.startswith('#'):
            log.info(f"Message from chat {chat_id}: {text}")
            parsed_msg = cls.message_parser(msg=text, date_time=date_time)
            # log.info(f"Parsed message: {parsed_msg}")

            Google.update_sht(parsed_msg)

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
            if "#" in line:
                title = line.strip().lstrip("#")[:-4]
            elif (line.count("-") == 0 or line.count("-") == 1) and ("total" not in line.lower()):
                continue
            elif "-" in line:
                l = [x.strip() for x in line.split("-")]
                res_t = {
                    "Message timestamp": date_time,
                    "Cap day": caps_date,
                    "title": title,
                    "country": None,
                    "total_caps": None,
                    "start_time": None,
                    "end_time": None,
                    "time_zone": None,
                    "cpa": None,
                    "note": None
                }
                for i in l:
                    if i == l[0] and ("Total" not in i or "total" not in i):
                        res_t["country"] = i.strip()
                    elif "Total" in i or "total" in i:
                        res_t["total_caps"] = i.split(" ")[1]
                    elif ":" in i and "gmt" not in i:
                        res_t["start_time"] = i.strip()
                    elif ":" in i and "gmt" in i:
                        res_t["end_time"] = i.strip().split(" ", 1)[0]
                        res_t["time_zone"] = i.strip().split(" ", 1)[1]
                    elif res_t.get("time_zone") is not None and i == l[-2]:
                        res_t["cpa"] = i.strip()
                    elif res_t.get("time_zone") is not None and i == l[-1]:
                        res_t["note"] = i.strip()
                    elif res_t.get("time_zone") is None and i == l[-2]:
                        res_t["cpa"] = i.strip()
                    elif res_t.get("time_zone") is None and i == l[-1]:
                        res_t["note"] = i.strip()
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
