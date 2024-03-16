import os
import pandas as pd
import streamsync as ss
from module.bq_db import SmashDatabase

# EVENT HANDLERS

def update(state):
    _update_datetime_select(state)
    _update_show_df_table(state)

# LOAD DATA

def _get_main_df():
    ssbu_db = SmashDatabase('ssbu_dataset')
    return ssbu_db.select_analysis_data()

def _merge_df(main_df, filter_columns=[[]], querys=[], new_column=[]):
    select_dfs = []
    for i,filter_column in enumerate(filter_columns):
        if len(filter_columns)==len(querys): select_df = main_df.query(querys[i])
        select_df = select_df[filter_column]
        if len(filter_column)==len(new_column): select_df.columns = new_column
        select_dfs.append(select_df)
    return pd.concat(select_dfs, axis=0)

def _get_select(filter_columns=[[]], sort_column=None, select_column=None, querys=[], new_column=[], main_df=_get_main_df()):
    #print(main_df)
    if len(new_column)==0: select_df = main_df[filter_columns]
    else: select_df = _merge_df(main_df, filter_columns, querys, new_column)
    #print(select_df)
    select_df = select_df.sort_values(sort_column)
    select_df = select_df[[select_column]]
    select_df = select_df[~select_df.duplicated(keep='first')]
    select_df = select_df[select_column]
    select_dict = select_df.to_dict()
    # Pythonで辞書同士を結合（連結・マージ） https://note.nkmk.me/python-dict-merge/
    select_dict = {v: v for v in select_dict.values()}
    return select_dict

def _get_player_select():
    return _get_select(
        ['target_player_name'], 'target_player_name', 'target_player_name'
    )

def _get_fighter_select():
    return _get_select(
        [["chara_id_1p", "chara_name_1p"], ["chara_id_2p", "chara_name_2p"]], 'target_chara_id', 'target_chara_name',
        ['target_player_is_1p == True', 'target_player_is_1p == False'], ['target_chara_id', 'target_chara_name']
    )

def _get_vs_fighter_select():
    return _get_select(
        [["chara_id_1p", "chara_name_1p"], ["chara_id_2p", "chara_name_2p"]], 'target_chara_id', 'target_chara_name',
        ['target_player_is_1p == False', 'target_player_is_1p == True'], ['target_chara_id', 'target_chara_name']
    )

def _get_category_select():
    return _get_select(
        ['category'], 'category', 'category'
    )

def _get_win_lose_select():
    return _get_select(
        ['target_player_is_win'], 'target_player_is_win', 'target_player_is_win'
    )

def _get_datetime_select():
    return _get_select(
        ['game_start_datetime'], 'game_start_datetime', 'game_start_datetime'
    )

def _get_show_df(show_df=_get_main_df()):
    return show_df[[
        'target_player_name', 'chara_name_1p', 'chara_name_2p',
        'category', 'target_player_is_win', 'game_start_datetime', 
        'game_start_url'
    ]]

def _get_show_table(show_df=_get_show_df()):
    show_df = show_df.replace('https(.*)', r"<a href=https\1 target='_blank'> https\1 </a>", regex=True)
    # Pythonで表をHTMLに変換する https://blog.shikoan.com/python-table-html/
    show_table = f'<span style="color:#000000">{show_df.style.hide().to_html()}</span>'
    # show_table = show_table.replace('table id(.*)"', r'table id\1 border=1"', regex=True)
    print(show_table)
    return show_table
    
# UPDATES

def _filter_df(state, filter_datetime=True):
    if len(state["show_df"])<=1: state["filter"]["datetime"]=None
    show_df = state["buf_df"]
    if state["filter"]["player"]!=None:
        show_df = show_df.query(f'target_player_name == "{state["filter"]["player"]}"')
    if state["filter"]["fighter"]!=None:
        show_df = show_df.query(f'chara_name_1p == "{state["filter"]["fighter"]}" or chara_name_2p == "{state["filter"]["fighter"]}"')
    if state["filter"]["vs_fighter"]!=None:
        show_df = show_df.query(f'chara_name_1p == "{state["filter"]["vs_fighter"]}" or chara_name_2p == "{state["filter"]["vs_fighter"]}"')
    if state["filter"]["category"]!=None:
        show_df = show_df.query(f'category == "{state["filter"]["category"]}"')
    if state["filter"]["win_lose"]!=None:
        show_df = show_df.query(f'target_player_is_win == "{state["filter"]["win_lose"]}"')
    if state["filter"]["datetime"]!=None and filter_datetime:
        show_df = show_df.query(f'game_start_datetime == "{state["filter"]["datetime"]}"')
    return show_df

def _update_datetime_select(state):
    state["datetime_select"] = _get_select(
        ['game_start_datetime'], 'game_start_datetime', 'game_start_datetime',
        main_df=_filter_df(state, filter_datetime=False)
    )

def _update_show_df_table(state):
    state["show_df"] = _filter_df(state)
    state["show_table"] = _get_show_table(state["show_df"])

# STATE INIT

# initial_state = ss.init_state({
#     "main_df": _get_main_df(),
#     "filter": {
#         "player": None,
#         "fighter": None,
#         "vs_fighter": None,
#         "category": None,
#         "win_lose": None,
#         "datetime": None
#     },
#     "player_select": _get_player_select(),
#     "fighter_select": _get_fighter_select(),
#     "vs_fighter_select": _get_vs_fighter_select(),
#     "category_select": _get_category_select(),
#     "win_lose_select": _get_win_lose_select(),
#     "datetime_select": _get_datetime_select(),
#     "show_df": _get_show_df(),
#     "show_table": _get_show_table(),
#     "buf_df": _get_show_df(),
# })
account = {
    "type": "service_account",
    "project_id": os.environ.get("GCP_PROJECT_ID"),
    "private_key_id": os.environ.get("GCS_PRIVATE_KEY_ID"),
    "private_key": os.environ.get("GCS_PRIVATE_KEY"),
    "client_email": os.environ.get("GCS_CLIENT_MAIL"),
    "client_id": os.environ.get("GCS_CLIENT_ID"),
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": os.environ.get("GCS_CLIENT_X509_CERT_URL")
}
print(account)
