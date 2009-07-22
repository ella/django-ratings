"""
This file is for aggregation records from Rating,Agg tables to Agg and TotalRate table
"""

import logging

from datetime import datetime, timedelta
from django_ratings.models import Rating, Agg, TotalRate

logger = logging.getLogger('django_ratings')

# aggregate ratings older than 2 years by year
DELTA_TIME_YEAR = 2*365*24*60*60
# ratings older than 2 months by month
DELTA_TIME_MONTH = 2*30*24*60*60
# rest of the ratings (last 2 months) aggregate daily
DELTA_TIME_DAY = -24*60*60

TIMES_ALL = {DELTA_TIME_YEAR : 'year', DELTA_TIME_MONTH : 'month', DELTA_TIME_DAY : 'day'}

def transfer_agg_to_totalrate():
    """
    Transfer aggregation data from table Agg to table TotalRate
    """
    logger.info("transfer_agg_to_totalrate BEGIN")
    if TotalRate.objects.count() != 0:
        TotalRate.objects.all().delete()
    Agg.objects.agg_to_totalrate()
    logger.info("transfer_agg_to_totalrate END")


def transfer_agg_to_agg():
    """
    aggregation data from table Agg to table Agg
    """
    logger.info("transfer_agg_to_agg BEGIN")
    timenow = datetime.now()
    for t in TIMES_ALL:
        TIME_DELTA = t
        time_agg = timenow - timedelta(seconds=TIME_DELTA)
        Agg.objects.move_agg_to_agg(time_agg, TIMES_ALL[t])
    Agg.objects.agg_assume()
    logger.info("transfer_agg_to_agg END")


def transfer_data():
    """
    transfer data from table Rating to table Agg
    """
    logger.info("transfer_data BEGIN")
    timenow = datetime.now()
    for t in sorted(TIMES_ALL.keys(), reverse=True):
        TIME_DELTA = t
        time_agg = timenow - timedelta(seconds=TIME_DELTA)
        Rating.objects.move_rate_to_agg(time_agg, TIMES_ALL[t])
    transfer_agg_to_agg()
    transfer_agg_to_totalrate()
    logger.info("transfer_data END")

