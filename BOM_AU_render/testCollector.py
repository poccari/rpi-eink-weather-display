from collector import Collector

# #North Haven
# lat = -34.7999968 #North Haven
# long  = 138.4833314

#Adelaide
lat = -34.92866000   
long =  138.59863000


mycol = Collector(lat, long)
mycol.async_update()
# print(mycol.observations_data['data'])
print(mycol.locations_data)
for icol in mycol.daily_forecasts_data['data']:
    date = icol['date']
    temp_max = icol['temp_max']
    extended_text = icol['extended_text']
    mdi_icon = icol['mdi_icon']
    print(f"{date}\t{temp_max}\t{extended_text}\t{mdi_icon}")

# print("--------------------------------------------------")
# print(mycol.hourly_forecasts_data['data'][0])
# print('&&&')
# print(mycol.hourly_forecasts_data['data'][1])

# for icol in mycol.hourly_forecasts_data['data']:
#     time = icol['time']
#     temp = icol['temp']
#     mdi_icon = icol['mdi_icon']
#     print(f"{time}\t{temp}\t{mdi_icon}")
# print("--------------------------------------------------")
# print(mycol.warnings_data)