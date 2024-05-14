import xml.etree.ElementTree as ET
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import argparse
import numpy as np

bicycle_width = 0.65  # meters, defailt in sumo
car_width = 1.8  # meters, default in sumo


def read_fcd_data_xml(file_path):
    # Parse XML data and convert it to a DataFrame
    tree = ET.parse(file_path)
    root = tree.getroot()

    fcd_records = []
    for timestep in root.findall('.//timestep'):
        time = float(timestep.get('time'))
        for vehicle in timestep.findall('.//vehicle'):
            vehicle_id = vehicle.get('id')
            x = float(vehicle.get('x'))
            y = float(vehicle.get('y'))
            speed = float(vehicle.get('speed'))
            type = vehicle.get('type')

            # Add more fields as needed

            # Append data to the list
            fcd_records.append({'Time': time, 'VehicleID': vehicle_id, 'X': x, 'Y': y, 'Speed': speed, 'Type': type})

    # Convert the list of records to a DataFrame
    fcd_data = pd.DataFrame(fcd_records)
    return fcd_data

def analyze_fcd_data(fcd_data):
    # Perform analysis on FCD data
    # For example, you can calculate average speed, plot histograms, etc.
    avg_speed = fcd_data['Speed'].mean()

    # Display the average speed
    print(f"Average Speed: {avg_speed} units")  # Update the unit based on your FCD data

    # Plot a histogram of speeds
    plt.hist(fcd_data['Speed'], bins=20, edgecolor='black')
    plt.xlabel('Speed (units)')  # Update the unit based on your FCD data
    plt.ylabel('Frequency')
    plt.title('Histogram of Speeds')
    plt.show()

def find_bicycle_overtaking_events(fcd_data):
    # Sort the data by time to ensure it is in chronological order
    fcd_data = fcd_data.sort_values(by='Time')

    # Initialize a list to store overtaking events
    overtaking_events = []

    # Filter out rows where the vehicle is a bicycle
    bike_rows = fcd_data[fcd_data['Type'].str.lower().str.contains('bike')]

    # Filter out rows where the vehicle is a car
    car_rows = fcd_data[fcd_data['Type'].str.lower().str.contains('car')]

    # Go through the data and find overtaking events
    for index, row in bike_rows.iterrows():
        vehicle_id = row['VehicleID']
        x_position = row['X']
        bike_speed = row['Speed']
        current_timestep = row['Time']

        # Check if there is any car behind the bicycle within a certain range
        cars_behind = car_rows[
            (car_rows['X'] < x_position) &
            (car_rows['X'] > x_position - 50) &  # Adjust the range as needed
            (car_rows['Speed'] > bike_speed) &
            (car_rows['Time'] == current_timestep)
        ]

        if not cars_behind.empty:
            next_timestep = car_rows[
                (car_rows['Time'] > current_timestep) &
                (car_rows['Time'] < current_timestep + 1)  # Assume we never have a timestep greater than 1
            ].sort_values(by='Time')['Time'].min()

            if pd.notna(next_timestep):
                # loop through the cars behind the bicycle and find overtakers
                for car_index, car_row in cars_behind.iterrows():
                    car_id = car_row['VehicleID']

                    bike_next_timestep = bike_rows[
                        (bike_rows['Time'] == next_timestep) &
                        (bike_rows['VehicleID'] == vehicle_id)
                    ]
                    car_next_timestep = car_rows[
                        (car_rows['Time'] == next_timestep) &
                        (car_rows['VehicleID'] == car_id)
                    ]

                    # Check if the car ends up in front of the bicycle in the next timestep
                    if not bike_next_timestep.empty and not car_next_timestep.empty:
                        if car_next_timestep.at[car_next_timestep.index[0], 'X'] > bike_next_timestep.at[bike_next_timestep.index[0], 'X']:
                            overtaking_distance = car_next_timestep.at[car_next_timestep.index[0], 'Y'] - bike_next_timestep.at[bike_next_timestep.index[0], 'Y'] - bicycle_width / 2 - car_width / 2
                            overtaking_events.append({'Time': row['Time'], 'BicycleID': vehicle_id, 'CarID': car_id, 'Distance': overtaking_distance, 'Type': car_next_timestep.at[car_next_timestep.index[0], 'Type'] })
                            print(f"Overtaking at time {row['Time']}: Bicycle {vehicle_id} by Car {car_id} , distance {overtaking_distance} m. type {car_next_timestep.at[car_next_timestep.index[0], 'Type']}")

    # Convert the list of overtaking events to a DataFrame
    overtaking_events_df = pd.DataFrame(overtaking_events)
    return overtaking_events_df



def analyze_overtaking_data_by_type(overtaking_events, prefix):
    # Perform analysis on overtaking events
    if not overtaking_events.empty:

        # Split the data by type
        grouped = overtaking_events.groupby('Type')

        # Create a color map
        colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
        color_map = {type: colors[i % len(colors)] for i, type in enumerate(grouped.groups.keys())}

        # Define the bins for the histogram
        bins = np.linspace(0.0, 3.0, 15)

        # Calculate the histogram and plot a bar chart for each type
        bar_width = (bins[1] - bins[0]) / (len(grouped.groups) + 1)
        for i, (type, group) in enumerate(grouped):
            frequencies, _ = np.histogram(group['Distance'], bins=bins)
            plt.bar(bins[:-1] + i * bar_width, frequencies, width=bar_width, color=color_map[type], label=type)

        lateral_resolution, min_lat_gap, probability, modal_bike_split = parse_prefix(prefix)
        # Format the string
        subtitle = f"Lateral-resolution: {lateral_resolution}m ; minLatGap {min_lat_gap}m ; probability {probability} ; BikeSplit {modal_bike_split}"

        plt.xlabel('Overtaking Distance (meters)')
        plt.ylabel('Frequency')
        plt.suptitle('Overtaking Distances')
        plt.title(subtitle, fontsize=10)
        plt.legend()

        # Set y-axis to only display integer values
        plt.gca().yaxis.set_major_locator(ticker.MaxNLocator(integer=True))

        fig_filename = prefix + 'overtaker_distance.png'
        plt.savefig(fig_filename, dpi=300)
        
        with open(prefix+'overtaker.txt', 'w') as f:
            # Convert the overtaking_events to a string and write it to the file
            f.write(str(overtaking_events))

        return overtaking_events

def parse_prefix(prefix):
    # Split the prefix by '_'
    parts = prefix.split('_')

    # Extract the lateral resolution and minimum lateral gap
    sim_vars = parts[1].rstrip('-')
    lateral_resolution, min_lat_gap, probability, modal_bike_split = sim_vars.split('-')

    # Remove the trailing dash from min_lat_gap
    modal_bike_split = modal_bike_split.rstrip('-')

    return lateral_resolution, min_lat_gap, probability, modal_bike_split

def calc_trip_statistics(fcd_data, prefix, overtaking_events):
    trip_statistics = {}
    trip_statistics['lateral_resolution'], trip_statistics['min_lat_gap'], trip_statistics['probability'], trip_statistics['modal_bike_split'] = parse_prefix(prefix)
    trip_statistics['TotalVehicles'] = fcd_data['VehicleID'].nunique()
    trip_statistics['TotalBicycles'] = fcd_data[fcd_data['Type'].str.lower().str.contains('bike')]['VehicleID'].nunique()
    trip_statistics['TotalOncomingCars'] = fcd_data[fcd_data['VehicleID'].str.lower().str.contains('cars')]['VehicleID'].nunique()
    # number of vehicles with id containing 'mixed'
    #trip_statistics['TotalSameDirectionCars'] = fcd_data[fcd_data['VehicleID'].str.contains('mixed')]['VehicleID'].nunique()
    trip_statistics['TotalSameDirectionCars'] = fcd_data[(fcd_data['VehicleID'].str.contains('mixed')) & (fcd_data['Type'].str.contains('car'))]['VehicleID'].nunique()
    # averag trip time of vehicles contaning 'mixed'
    grouped = fcd_data[fcd_data['VehicleID'].str.contains('mixed')].groupby('VehicleID')['Time']
    trip_statistics['AverageTripTimeSameDirectionCars'] = (grouped.max() - grouped.min()).mean()
    if 'Distance' in overtaking_events.columns and not overtaking_events.empty:
        trip_statistics['AverageOvertakingDistance'] = overtaking_events['Distance'].mean()
        trip_statistics['TotalOvertakingEvents'] = overtaking_events['Distance'].count()
        trip_statistics['MinOvertakingDistance'] = overtaking_events['Distance'].min()
        trip_statistics['MaxOvertakingDistance'] = overtaking_events['Distance'].max()
    else:
        trip_statistics['AverageOvertakingDistance'] = None
        trip_statistics['TotalOvertakingEvents'] = None
        trip_statistics['MinOvertakingDistance'] = None
        trip_statistics['MaxOvertakingDistance'] = None
    print(trip_statistics)
    with open(prefix+'statistics.txt', 'w') as f:
        # Convert the trip_statistics to a string and write it to the file
        f.write(str(trip_statistics))

# Example usage
if __name__ == "__main__":
    # Provide the path to your FCD XML file
    parser = argparse.ArgumentParser(description = "This program should analyse fcd files, extract overtaking events and output analysis.")
    parser.add_argument("inputfile", type=str, help = "Input bcrtf")
    args = parser.parse_args()

    if args.inputfile.endswith('fcd.xml'):
        print("File is",args.inputfile)

        # Read FCD data from XML
        fcd_data = read_fcd_data_xml(args.inputfile)

        # Separate the filename at '-fcd.xml'
        prefix, _ = args.inputfile.rsplit('fcd.xml', 1)

        # Analyze FCD data
        # analyze_fcd_data(fcd_data)

        # Find bicycle overtaking events
        overtaking_events = find_bicycle_overtaking_events(fcd_data)
        trip_statistics = calc_trip_statistics(fcd_data, prefix, overtaking_events)
        analyze_overtaking_data_by_type(overtaking_events, prefix)

    else:
        print("File is not a fcd.xml")
