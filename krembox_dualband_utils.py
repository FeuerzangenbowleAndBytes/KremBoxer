import datetime

def parse_header(fields, header):
    dt = datetime.datetime(year=int(header[fields.index('YEAR')]),
                           month=int(header[fields.index('MONTH')]),
                           day=int(header[fields.index('DAY')]),
                           hour=int(header[fields.index('HOURS(UTC)')]),
                           minute=int(header[fields.index('MINUTES')]),
                           second=int(header[fields.index('SECONDS')]),
                           tzinfo=datetime.timezone.utc)
    lat, lon = int(header[fields.index('LATITUDE(deg/100000)')]) / 1000000, \
               int(header[fields.index('LONGITUDE(deg/100000)')]) / 1000000
    return dt, lat, lon