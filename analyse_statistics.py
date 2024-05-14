import glob
import ast

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Sample data from a statistics file
# {'lateral_resolution': '0.5', 
# 'min_lat_gap': '0.5', 
# 'probability': '0.01', 
# 'modal_bike_split': '0.3', 
# 'TotalVehicles': 19, 
# 'TotalBicycles': 2, 
# 'TotalOncomingCars': 11, 
# 'TotalSameDirectionCars': 6, 
# 'AverageTripTimeSameDirectionCars': 154.00000000000003, 
# 'AverageOvertakingDistance': 0.6249999999999997, 
# 'TotalOvertakingEvents': 4, 
# 'MinOvertakingDistance': 0.5849999999999996, 
# 'MaxOvertakingDistance': 0.6649999999999997}


# Specify the folder path
folder_path = '/data/HLRS/sumo_test/sublane_model_4_4/generated/'

# Define the pattern to match
file_pattern = '*statistics.txt'

# Get a list of all matching file paths
file_paths = glob.glob(folder_path + file_pattern)

# Create an empty list to hold the data
data_list = []

# Iterate over each file and perform analysis
for file_path in file_paths:
    with open(file_path, 'r') as file:
        # Parse the file contents as a dictionary
        data = ast.literal_eval(file.read())

        # Add the data to the list
        data_list.append(data)

#print(data_list)

# Convert the list of dictionaries to a DataFrame
df = pd.DataFrame(data_list)
df['TotalOvertakingEvents'] = df['TotalOvertakingEvents'].fillna(0)

# Now data_list contains the data from all files
# You can use this list for your analysis

def plot_overtaking_events(df):
    # Convert 'probability', 'modal_bike_split' and 'lateral_resolution' to numeric types
    df['probability'] = pd.to_numeric(df['probability'])
    df['modal_bike_split'] = pd.to_numeric(df['modal_bike_split'])
    df['lateral_resolution'] = pd.to_numeric(df['lateral_resolution'])

    # Create a scatter plot with different markers for different lateral resolutions
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=df, x='probability', y='TotalOvertakingEvents', hue='modal_bike_split', style='lateral_resolution', markers={0.5: 'X', 2.5: 'P'}, palette='viridis')

    # Set the plot title and labels
    plt.title('Number of Overtaking Events over Probability for Different Modal Splits')
    plt.xlabel('Probability (Vehicles per Second)')
    plt.ylabel('Total Overtaking Events')

    # Show the plot
    plt.show()


def plot_average_trip_time(df):
    # Convert 'probability', 'modal_bike_split' and 'lateral_resolution' to numeric types
    df['probability'] = pd.to_numeric(df['probability'])
    df['modal_bike_split'] = pd.to_numeric(df['modal_bike_split'])
    df['lateral_resolution'] = pd.to_numeric(df['lateral_resolution'])

    # Replace None with 0 in 'AverageTripTimeSameDirectionCars'
    df['AverageTripTimeSameDirectionCars'] = df['AverageTripTimeSameDirectionCars'].fillna(0)

    # Create a scatter plot with different markers for different lateral resolutions
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=df, x='modal_bike_split', y='AverageTripTimeSameDirectionCars', hue='probability', style='lateral_resolution', markers={0.5: 'X', 2.5: 'P'}, palette='tab10')

    # Set the plot title and labels
    plt.title('Average Trip Time of Same Direction Cars over Modal Split for different Probablities (Veh/s)')
    plt.xlabel('Bicycle Modal Split (Fraction of Bicycles)')
    plt.ylabel('Average Trip Time of Same Direction Cars')
 
    # Rescale the y-axis to the data range
    plt.ylim(df['AverageTripTimeSameDirectionCars'].min()-10, df['AverageTripTimeSameDirectionCars'].max()+10)


    # Place the legend outside of the plot
    #plt.legend(bbox_to_anchor=(0.5, -0.05), loc=2, borderaxespad=0.)  # Place the legend inside the plot
    #plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
   
    # Save the plot as a high-resolution PNG image
    plt.savefig('average_trip_time.png', dpi=300)
  
    # Show the plot
    plt.show()

plot_average_trip_time(df)