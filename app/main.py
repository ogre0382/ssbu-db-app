import pandas as pd
import subprocess
import streamsync as ss
import sys
import webbrowser
from module.bq_db import SmashDatabase

#print(webbrowser.get())

print(sys.path)
#subprocess.call('ls -l /opt/render/project/.render/'.split())

# EVENT HANDLERS

def update(state):
    _update_show_df(state)
    _update_datetime_select(state)
    _update_yt_url(state)
    _update_yt_title(state)

def handle_yt_button_click(state):
    # main_df = state["main_df"]
    # show_df = state["show_df"]
    # if len(show_df)==1: 
    #     main_df = main_df.set_index("game_start_datetime")
    #     print(show_df.iloc[0,5])
    #     webbrowser.open_new_tab(main_df.at[f'{show_df.iloc[0,5]}', 'game_start_url'])
    # else:
    #     webbrowser.open_new_tab("https://www.youtube.com/")
    pass

# LOAD DATA

def _get_main_df():
    ssbu_db = SmashDatabase('ssbu_dataset')
    main_df = ssbu_db.select_analysis_data()
    main_df.loc[:, 'target_player_is_win'] = main_df.loc[:, 'target_player_is_win'].astype(str)
    # [Python] pandas 条件抽出した行の特定の列に、一括で値を設定する https://note.com/kohaku935/n/n5836a09b96a6
    main_df.loc[main_df["target_player_is_win"]=="True", "target_player_is_win"] = "Win"
    main_df.loc[main_df["target_player_is_win"]=="False", "target_player_is_win"] = "Lose"
    return main_df

def _merge_df(main_df, filter_columns=[[]], querys=[], new_column=[]):
    select_dfs = []
    for i,filter_column in enumerate(filter_columns):
        if len(filter_columns)==len(querys): select_df = main_df.query(querys[i])
        select_df = select_df[filter_column]
        if len(filter_column)==len(new_column): select_df.columns = new_column
        select_dfs.append(select_df)
    return pd.concat(select_dfs, axis=0)

def _get_select(filter_columns=[[]], sort_column=None, select_column=None, querys=[], new_column=[], df=None):
    if df is None: main_df = _get_main_df()
    else: main_df = df
    print(main_df)
    if len(new_column)==0: select_df = main_df[filter_columns]
    else: select_df = _merge_df(main_df, filter_columns, querys, new_column)
    print(select_df)
    select_df = select_df.sort_values(sort_column)
    select_df = select_df[[select_column]]
    select_df = select_df[~select_df.duplicated(keep='first')]
    select_df = select_df[select_column]
    select_dict = select_df.to_dict()
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

def _get_show_df():
    main_df = _get_main_df()
    return main_df[[
        'target_player_name', 'chara_name_1p', 'chara_name_2p',
        'category', 'target_player_is_win', 'game_start_datetime'
    ]]
    # show_df = main_df[['title', 'game_start_url']]
    # #'<a href="http://www.google.com/" target="_blank">Button</a>'
    # show_df = show_df.replace('https(.*)', r"<a href=https\1 target='_blank'> https\1 </a>", regex=True)
    # #show_df['game_start_url'] = f"<a href={show_df['game_start_url']} target='_blank'>{show_df['game_start_url']}</a>"
    # return show_df

# UPDATES

def _filter_df(state, filter_datetime=True):
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
        ['game_start_datetime'], 'game_start_datetime', 'game_start_datetime', df=_filter_df(state, filter_datetime=False)
    )

def _update_yt_url(state):
    show_df = state["show_df"]
    if len(show_df)==1: 
        main_df = state["main_df"]
        main_df = main_df.set_index("game_start_datetime")
        state["yt_url"] = main_df.at[f'{show_df.iloc[0,5]}', 'game_start_url']

def _update_yt_title(state):
    show_df = state["show_df"]
    if len(show_df)==1: 
        main_df = state["main_df"]
        main_df = main_df.set_index("game_start_datetime")
        state["yt_title"] = main_df.at[f'{show_df.iloc[0,5]}', 'title']

def _update_show_df(state):
    state["show_df"] = _filter_df(state)

# STATE INIT

initial_state = ss.init_state({
    "main_df": _get_main_df(),
    "filter": {
        "player": None,
        "fighter": None,
        "vs_fighter": None,
        "category": None,
        "win_lose": None,
        "datetime": None
    },
    "player_select": _get_player_select(),
    "fighter_select": _get_fighter_select(),
    "vs_fighter_select": _get_vs_fighter_select(),
    "category_select": _get_category_select(),
    "win_lose_select": _get_win_lose_select(),
    "datetime_select": _get_datetime_select(),
    "yt_url": "https://www.youtube.com/",
    "yt_title": "[YouTube Title]",
    "show_df": _get_show_df(),
    "buf_df": _get_show_df()
})
