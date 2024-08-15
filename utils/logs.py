import logging

formatter = logging.Formatter("%(levelname)s | %(name)s | %(asctime)s | %(message)s")
info_handler = logging.StreamHandler()
info_handler.setLevel(logging.INFO)
info_handler.setFormatter(formatter)

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
log.addHandler(info_handler)

