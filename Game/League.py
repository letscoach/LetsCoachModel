import firebase_db as fb
import datetime
from datetime import datetime
# import Matches as mat
import random

days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

def generate_league(name,  start_date, match_day, teams_lst):
    league_data = dict(name=name, start_date=datetime.strptime(start_date, "%d.%m.%Y"), match_day=match_day,teams=teams_lst)
    league_data['D'] = [0 for i in teams_lst]
    league_data['W'] = [0 for i in teams_lst]
    league_data['L'] = [0 for i in teams_lst]
    league_data['GA'] = [0 for i in teams_lst]
    league_data['GF'] = [0 for i in teams_lst]
    league_data['Points'] = [0 for i in teams_lst]
    fb.insert_or_update_doc(league_data, 'Leagues', 'name')
    # mat.generate_schedule(name, start_date)

def update_league(league_name , team_id_1, team_id_2, score):
    doc = fb.get_document('Leagues','name', league_name)
    team_1_ind = doc['teams'].index(team_id_1)
    team_2_ind = doc['teams'].index(team_id_2)
    if score[0]>score[1]:
        doc['W'][team_1_ind] +=1
        doc['Points'][team_1_ind] +=3
        doc['L'][team_2_ind] +=1
    if score[0]<score[1]:
        doc['W'][team_2_ind] +=1
        doc['Points'][team_2_ind] += 3
        doc['L'][team_1_ind] +=1
    if score[0]==score[1]:
        doc['D'][team_2_ind] +=1
        doc['D'][team_1_ind] +=1
        doc['Points'][team_1_ind] += 1
        doc['Points'][team_2_ind] += 1
    doc['GA'][team_1_ind] += score[1]
    doc['GF'][team_1_ind] += score[0]
    doc['GA'][team_2_ind] += score[0]
    doc['GF'][team_2_ind] += score[1]
    fb.insert_or_update_doc(doc, 'Leagues', 'name')

def get_all_league_names():
    docs = fb.get_all_documents('League')
    return [doc["name"] for doc in docs]
def get_league_data(name):
    doc = fb.get_document('League','name', name)
    leg_data = [{doc['teams'][ind] : dict(D=doc['D'][ind],L=doc['L'][ind],W=doc['W'][ind],GA=doc['GA'][ind],
                                          GF=doc['GF'][ind],Points=doc['Points'][ind])}
                for ind in doc['teams']]
    return leg_data

# generate_league("Nissim League!!",  '30.12.2024', 'Sunday', [
#     "20241124073625277324d4cbad1d516449f9a4efae017ec322d8",
#     "202411240734555256126517b43311464b75adffe6369571f3e1",
#     "2024112407391165006681ef5b5d55344ff8a0f296de619c4fef",
#     "202411240731540490757243593dd4c748c4b9c3836106788d90",
#     "202411240740111065398f25322e176e4c049c13903057c1136f",
#     "20241124073706886919820b4a9ed10f41569d6b1df6826e52e5",
#     "202411240732534142907b5b30bfd6f64e9c9e4797227d8f87b4",
#     "20241124073412252203ea71b1c4674345b5a178c1703f3f74b8",
#     "202411031652073995964cfa443afba5433c88c48f5949a0d15d",
#     "2024112407333030445939924b42c93a4a09876186392a91ff79",
#     "2024110407385859971826150a387a8d4bdebdf7d9eb6a37ee9c",
#     "2024110609335103639965a2b38c9c054435b29e14784aa32da9"
# ])

