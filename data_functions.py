import pandas as pd 
import numpy as np 
import re 

#############################################################################################################
# Remember the division column header has been loaded in as "Division_x" so this could cause bugs in future #
#############################################################################################################

# Read in csv file into DataFrames and create the pam df which we will use 
data = pd.read_csv("/mnt/c/Users/Micha/Downloads/Data_Season4_Summer_Improved.csv", skiprows=1, header=0) 
# data = data.iloc[1:].reset_index(drop=True)
# data.columns = data.iloc[0]  # Use the first row as header


def csv_file_cleaner_and_manipulator(player_data_csv, possession_data_csv): 
    player_data_df = pd.read_csv(player_data_csv, skiprows=1, header=0)
    possession_data_df = pd.read_csv(possession_data_csv, header=0)
    possession_data_df.columns = possession_data_df.columns.str.strip()
    df = pd.merge(player_data_df, possession_data_df, on="Club")
    age_to_int(df)
    transfer_value_clean(df)
    wage_clean(df)
    distance_clean(df)
    clean_percent_stats(df)
    make_per_90(df)
    possession_percent(df)
    adjust_defensive(df)
    adjust_offensive(df)
    new_metrics(df)
    position_group(df)
    percentiles(df)
    return df


def age_to_int(df):
    # Converts age value from string to int
    df["Age"] = df["Age"].astype(int)


def transfer_value_clean(df):
    # Create new column for the cleaned transfer value data
    df["Transfer Value Clean"] = 0.0
    transfer_value_column = df.columns.get_loc("Transfer Value")
    transfer_value_clean_column = df.columns.get_loc("Transfer Value Clean")

    for i in range(len(df)): 
        transfer_value = df.iloc[i, transfer_value_column]

        # If transfer value is completley unknown and takes a string value then an extremely large value is attributed to it so that
        # it is filtered to bottom when performing our player search
        if transfer_value.strip() == "Not for Sale":
            df.iloc[i, transfer_value_clean_column] = 100000000000
    
        elif transfer_value.strip() == "Unknown":
            df.iloc[i, transfer_value_clean_column] = 0


        # If the transfer value is given as a range between 2 values, the data is cleaned and then the mean of the 2 values is taken 
        # and added to the new column
        elif re.search(" - ", transfer_value): 
            lower, upper = df.iloc[i, transfer_value_column].split(" - ") 
            strings = [upper, lower]
            for j in range(len(strings)): 
                if re.search(r"^£\d+(\.\d+)?K$", strings[j]):
                    strings[j] = float(strings[j].replace("£", "").replace("K", "")) * 1000
                elif re.search(r"^£\d+(\.\d+)?M$", strings[j]):
                    strings[j] = float(strings[j].replace("£", "").replace("M", "")) * 1000000
                
                # if transfer value is 0
                else: 
                    strings[j]= float(strings[j].replace("£", "")) 
                
            upper, lower = strings
            mean_transfer_value = (float(upper) + float(lower))/2 
            df.iloc[i, transfer_value_clean_column] = int(mean_transfer_value)

        # If exact transfer value is known, it is simply just cleaned up and then added to the new column
        else: 
            if re.search(r"^£\d+(\.\d+)?K$", transfer_value):
                    transfer_value = float(transfer_value.replace("£", "").replace("K", "")) * 1000
            elif re.search(r"^£\d+(\.\d+)?M$", transfer_value):
                transfer_value = float(transfer_value.replace("£", "").replace("M", "")) * 1000000
            else: 
                transfer_value = float(transfer_value.replace("£", "")) 
            df.iloc[i, transfer_value_clean_column] = int(transfer_value)
        

def wage_clean(df):
    # A new "wage clean" column is created and the new value for it is simply the integer value from the "wage" column
    df["Wage Clean"] = df["Wage"].str.replace("£", "", regex = False)
    df["Wage Clean"] = df["Wage Clean"].str.replace(",", "", regex = False)
    df["Wage Clean"] = df["Wage Clean"].str.replace(" p/w", "", regex = False)
    df["Wage Clean"] = df["Wage Clean"].fillna(0).astype(int)


def possession_percent(df):
    # The possession value from the possesion csv file is converted from a string value to a float decimal
    df["Possession"] = (df["Possession"]).astype(float)/100 


def distance_clean(df): 
    df["Dist/90"] = df["Dist/90"].str.replace("km", "", regex=False)


def clean_percent_stats(df): 
    stats = ["Hdr %", "Tck R"]
    for stat in stats: 
            df[stat] = df[stat].replace("-", "0")
            df[stat] = df[stat].str.replace("%", "", regex=False)
            df[stat] = df[stat].astype(float)/100
            


def make_per_90(df): 
    # The statistics that do not come already as "per 90" from FM are converted to it
    stats = ["CCC", "xG-OP"]
    for stat in stats: 
        df[f"{stat}/90"] = df[stat]/90


def adjust_defensive(df): 
    # Defensive metrics are adjusted for possession
    stats = ["K Tck/90", "Tck/90", "Blk/90", "Clr/90", "Int/90", "Pres A/90", "Pres C/90", "Poss Won/90", 
             "Hdrs W/90", "K Hdrs/90", "Dist/90"]
    for stat in stats: 
        # Data is first cleaned and converted to float such that mathematical operations can be performed
        df[stat] = df[stat].replace("-", 0)
        df[stat] = df[stat].astype(float).round(2)
        df[stat] = round(df[stat] / (1 - df["Possession"]) * 0.5, 2)
        

def adjust_offensive(df): 
    # Offensive metrics are adjusted for possession
    stats = ["Poss Lost/90", "K Ps/90", "CCC/90", "OP-KP/90", "Shot/90", "Pr passes/90", "xA/90", "Cr C/90", "Drb/90", 
             "NP-xG/90", "xG-OP/90", "Ps A/90"] 
    for stat in stats: 
        # Data is first cleaned and converted to float such that mathematical operations can be performed
        df[stat] = df[stat].replace("-", 0)
        df[stat] = df[stat].astype(float).round(2)
        df[stat] = round(df[stat] / df["Possession"] * 0.5, 2) 


def new_metrics(df):  
    # New metrics to be used are created from the existing ones
    df["Poss Diff/90"] = df["Poss Won/90"] - df["Poss Lost/90"]
    df["Def Act/90"] = df["Tck/90"] + df["Blk/90"] + df["Clr/90"] + df["Int/90"]
    df["Pres %"] = df["Pres C/90"] / df["Pres A/90"] * 100
    df["NP-xG per shot/90"] = df["NP-xG/90"] / df["Shot/90"]
    df["(NP-xG + xA)/90"] = df["NP-xG/90"] + df["xA/90"]


# Test what is done so far works on csv file
def position_group(df): 
    # Positions are grouped such that we can compare players in the same position groups to one another
    position_groups = {
        "GK": "Goalkeeper",
        "D (C)": "Centre Back",
        "D (R)": "Fullback",
        "D (L)": "Fullback", 
        "WB (R)": "Fullback", 
        "WB (L)": "Fullback", 
        "DM": "Defensive Midfielder", 
        "M (C)": "Defensive Midfielder", 
        "AM (C)": "Attacking Midfielder", 
        "M (L)": "Attacking Midfielder", 
        "M (R)": "Attacking Midfielder", 
        "AM (L)": "Attacking Midfielder", 
        "AM (R)": "Attacking Midfielder", 
        "ST (C)": "Forward"
    }
    # A new column is created that takes the value of the corresponding position group to their best position as above
    df["Position Group"] = df["Best Pos"].map(position_groups)



def percentiles(df): 
    # The percentile for each metric is calculated against players in the player's position group
    stats = ["K Tck/90", "Tck/90", "Blk/90", "Clr/90", "Int/90", "Pres A/90", "Pres C/90", "Pres %", "Poss Won/90", 
             "Hdrs W/90", "K Hdrs/90", "Poss Lost/90", "K Ps/90", "CCC/90", "OP-KP/90", "Shot/90", "Pr passes/90", "xA/90", 
             "Cr C/90", "Drb/90", "NP-xG/90", "xG-OP/90", "Ps A/90", "Pas %", "Poss Diff/90", "Def Act/90", "NP-xG per shot/90", 
             "(NP-xG + xA)/90", "Dist/90", "Tck R", "Hdr %"]
    for stat in stats: 
        df[f"{stat} Percentile"] = round(df.groupby("Position Group")[stat].rank(pct=True) * 100, 0)




# Create the player search function
position_group_stats = {
    "Goalkeeper": ["xGP/90", "Sv %", "Poss Lost/90", "Poss Won/90", "Ps A/90", "Pas %", "Mins"], 

    "Centre Back": ["K Tck/90", "Tck/90", "Tck R", "Def Act/90", "Hdr %", "Hdrs W/90", "K Hdrs/90", "Poss Diff/90", "Poss Lost/90", 
                    "Poss Won/90", "Pr passes/90", "Pas %", "Ps A/90", "NP-xG/90", "Mins"],

    "Fullback": ["Def Act/90", "Tck R", "Hdr %", "Hdrs W/90", "Poss Diff/90", "Poss Lost/90", 
                    "Poss Won/90", "Pr passes/90", "Pas %", "Ps A/90", "(NP-xG + xA)/90", "Dist/90", "Drb/90", "CCC/90", "Shot/90",
                    "OP-KP/90", "Tck R", "Pres A/90", "Pres %", "Cr C/90", "Mins"],

    "Defensive Midfielder": ["Def Act/90", "Tck R", "Hdr %", "Hdrs W/90", "Poss Diff/90", "Poss Lost/90", 
                    "Poss Won/90", "Pr passes/90", "Pas %", "Ps A/90", "(NP-xG + xA)/90", "Dist/90",
                    "OP-KP/90", "Tck R", "Pres A/90", "Pres %", "Mins"], 

    "Attacking Midfielder": ["Def Act/90", "Hdr %", "Poss Diff/90", "Poss Lost/90", 
                    "Poss Won/90", "Pr passes/90", "Pas %", "Ps A/90", "NP-xG/90", "xA/90", "(NP-xG + xA)/90", "Dist/90", "Drb/90",
                    "CCC/90", "Shot/90", "OP-KP/90", "Pres A/90", "Pres %", "Cr C/90", "Mins"],

    "Forward": ["Def Act/90", "Hdr %", "Hdrs W/90", "Poss Diff/90", "Poss Lost/90", 
                    "Poss Won/90", "Pas %", "Ps A/90", "NP-xG/90", "xA/90","(NP-xG + xA)/90", "Dist/90", "Drb/90", "CCC/90", "Shot/90",
                    "OP-KP/90", "Tck R", "Pres A/90", "Pres %", "Mins"]
}


def player_search(player_uid, df, wage=None, transfer_value=None, age=None, matches=None, percentage=None):

    position_group_stats = {
                                "Goalkeeper": ["xGP/90", "Sv %", "Poss Lost/90", "Poss Won/90", "Ps A/90", "Pas %", "Mins"], 

                                "Centre Back": ["K Tck/90", "Tck/90", "Tck R", "Def Act/90", "Hdr %", "Hdrs W/90", "K Hdrs/90",
                                                 "Poss Diff/90", "Poss Lost/90", "Poss Won/90", "Pr passes/90", "Pas %", "Ps A/90",
                                                   "NP-xG/90", "Mins"],

                                "Fullback": ["Def Act/90", "Hdr %", "Hdrs W/90", "Poss Diff/90", "Poss Lost/90", 
                                                "Poss Won/90", "Pr passes/90", "Pas %", "Ps A/90", "(NP-xG + xA)/90", "Dist/90", 
                                                "Drb/90", "CCC/90", "Shot/90", "OP-KP/90", "Tck R", "Pres A/90", "Pres %", 
                                                "Cr C/90", "Mins"],

                                "Defensive Midfielder": ["Def Act/90", "Hdr %", "Hdrs W/90", "Poss Diff/90", "Poss Lost/90", 
                                                "Poss Won/90", "Pr passes/90", "Pas %", "Ps A/90", "(NP-xG + xA)/90", "Dist/90",
                                                "OP-KP/90", "Tck R", "Pres A/90", "Pres %", "Mins"], 

                                "Attacking Midfielder": ["Def Act/90", "Hdr %", "Poss Diff/90", "Poss Lost/90", 
                                                "Poss Won/90", "Pr passes/90", "Pas %", "Ps A/90", "NP-xG/90", "xA/90", 
                                                "(NP-xG + xA)/90", "Dist/90", "Drb/90", "CCC/90", "Shot/90", "OP-KP/90", 
                                                "Pres A/90", "Pres %", "Cr C/90", "Mins"],

                                "Forward": ["Def Act/90", "Hdr %", "Hdrs W/90", "Poss Diff/90", "Poss Lost/90", 
                                                "Poss Won/90", "Pas %", "Ps A/90", "NP-xG/90", "xA/90","(NP-xG + xA)/90", 
                                                "Dist/90", "Drb/90", "CCC/90", "Shot/90", "OP-KP/90", "Tck R", "Pres A/90", 
                                                "Pres %", "Mins"]
                                }

    # Find the player within the data frame using their UID
    
    player_stats_series = df.loc[df["UID"] == f"{player_uid}"]
    
    if player_stats_series.empty: 
        raise KeyError("Player not found in data frame")
    
    # Set the optional parameters if they are not inputted
    if wage == None: 
        wage = player_stats_series["Wage Clean"].iloc[0]

    if transfer_value == None: 
        transfer_value = player_stats_series["Transfer Value Clean"].iloc[0]

    if age == None: 
        age = player_stats_series["Age"].iloc[0]

    player_position = player_stats_series["Position Group"].iloc[0]
    # Could add in position group to reduce the data frame earlier
    df_reduced = df[(df["Wage Clean"] <= int(wage)) & (df["Transfer Value Clean"] <= int(transfer_value)) & (df["Age"] <= int(age)) 
                    & (df["Position Group"] == player_position)]
    
    if matches == None:
        matches = len(position_group_stats[player_position])

    if percentage == None: 
        percentage = 1

    conditions = []

    for stat in position_group_stats[player_position]: 
        if stat == "Poss Lost/90":
            conditions.append(df_reduced[stat] <= player_stats_series[stat].iloc[0] * percentage)
        else: 
            conditions.append(df_reduced[stat] >= player_stats_series[stat].iloc[0] * percentage)
        
    # Create a data frame that verifies each condition for the position
    bool_df = pd.concat(conditions, axis=1)

    # Count how many of the conditions are met 
    matches_count = bool_df.sum(axis=1)

    # create a data frame that includes the players that meet the required amount of conditions 
    filtered_df = df_reduced[matches_count >= matches]

    # Create columns list of the columns to be displayed to the user
    columns = ["Name", "Position", "Division_x", "Club", "Age", "Transfer Value", "Wage"] + position_group_stats[player_position]
    
    return filtered_df[columns]


# Separate function created to check that percentiles were calculated
def show_percentiles(player_uid, df):
    player_percentiles = df.loc[df["UID"] == f"{player_uid}"]
    stats1 = ["(NP-xG + xA)/90", "Dist/90", "Drb/90", "CCC/90", "Tck R", "Drb/90", "CCC/90", "Tck R"]
    stats2 = ["Pres A/90", "Pres %", "Cr C/90", "Shot/90", "OP-KP/90", "Shot/90", "OP-KP/90"]
    print(player_percentiles[["Position Group", "K Tck/90 Percentile", "Hdrs W/90 Percentile", 
                              "Poss Diff/90 Percentile", "Poss Lost/90 Percentile", "Poss Won/90 Percentile", 
                              "Pr passes/90 Percentile"]])
    print(player_percentiles[[f"{i} Percentile" for i in stats1]])
    print(player_percentiles[[f"{i} Percentile" for i in stats2]])

    


