import datetime

dt_wrong = datetime.datetime(year=int(2003),
                       month=int(3),
                       day=int(8),
                       hour=int(11),
                       minute=int(23),
                       second=int(3),
                       tzinfo=datetime.timezone.utc)

dt_right = datetime.datetime(year=int(2022),
                       month=int(10),
                       day=int(22),
                       hour=int(10),
                       minute=int(23),
                       second=int(3),
                       tzinfo=datetime.timezone.utc)

dt_delta = dt_right - dt_wrong
print(dt_delta)
print(dt_wrong + dt_delta)

dt_orig = datetime.datetime(year=int(2003),
                       month=int(3),
                       day=int(11),
                       hour=int(4),
                       minute=int(45),
                       second=int(23),
                       tzinfo=datetime.timezone.utc)

dt_cor = dt_orig + dt_delta
print(dt_cor)
