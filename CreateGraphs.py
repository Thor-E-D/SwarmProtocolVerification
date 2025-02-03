import pandas as pd
import os
import matplotlib.pyplot as plt
import numpy as np

base_path = os.path.dirname(os.path.abspath(__file__))

folder_name = "TimingProtocol"
path_to_folder = os.path.join(base_path, "src", folder_name)

def make_graph_ra_da_se(input_file: str, role_name: str):
    file_path = os.path.join(path_to_folder, input_file)
    df = pd.read_csv(file_path)

    unique_roles_amounts = df[f"role_amount.{role_name}"].unique()
    unique_delay_types = df[f"delay_type.{role_name}"].unique()

    # Create the plot
    plt.figure(figsize=(10, 6))

    # Plot each role_amount as a separate series
    for delay_type in unique_delay_types:
        for role_amount in unique_roles_amounts:
            subset = df[df[f"role_amount.{role_name}"] == role_amount]
            subset2 = subset[subset[f"delay_type.{role_name}"] == delay_type]
            plt.plot(subset2[f"delay_amount.{role_name}"], subset2["time"], marker='o', linestyle='-', label=f'r: {role_amount}, dt: {delay_type}')


    plt.xticks(np.unique(df[f"delay_amount.{role_name}"]))

    # Labels and title
    plt.xlabel(f"Delay Amount ({role_name})")
    plt.ylabel("Time in seconds (log scale)")
    #plt.title("Forklift Delay vs Time for Different Role Amounts")
    plt.yscale("log")  # Apply logarithmic scale to the y-axis
    #plt.legend(title=f"{role_name} settings", bbox_to_anchor=(0.8,0.5))
    plt.legend(title=f"{role_name} settings", loc = "center right")
    plt.grid(True, which="both", linestyle="--", linewidth=0.5)

    # Show the plot
    plt.show()


def make_graph_ra_da(input_file: str, role_name: str):
    file_path = os.path.join(path_to_folder, input_file)
    df = pd.read_csv(file_path)

    unique_roles_amounts = df[f"role_amount.{role_name}"].unique()

    # Create the plot
    plt.figure(figsize=(10, 6))

    # Plot each role_amount as a separate series
    for role_amount in unique_roles_amounts:
        subset = df[df[f"role_amount.{role_name}"] == role_amount]
        plt.plot(subset[f"delay_amount.{role_name}"], subset["time"], marker='o', linestyle='-', label=f'{role_amount}')


    plt.xticks(np.unique(df[f"delay_amount.{role_name}"]))

    # Labels and title
    plt.xlabel(f"Delay Amount ({role_name})")
    plt.ylabel("Verification time in seconds (log scale)")
    #plt.title("Forklift Delay vs Time for Different Role Amounts")
    plt.yscale("log")  # Apply logarithmic scale to the y-axis
    plt.legend(title=f"Instanses of {role_name}")
    plt.grid(True, which="both", linestyle="--", linewidth=0.5)

    # Show the plot
    plt.show()

def make_graph_logsize(input_file: str):
    file_path = os.path.join(path_to_folder, input_file)
    df = pd.read_csv(file_path)


    # Create the plot
    plt.figure(figsize=(10, 6))

    plt.plot(df["log_size"], df["time"], marker='o', linestyle='-', label=f'log_size')


    #plt.xticks(np.unique(df[f"delay_amount.{role_name}"]))

    # Labels and title
    plt.xlabel(f"Log size")
    plt.ylabel("Verification time in seconds")
    plt.grid(True, which="both", linestyle="--", linewidth=0.5)

    # Show the plot
    plt.show()


def make_graph_build_time(input_file: str):
    file_path = os.path.join(base_path, "src", "example_protocols", input_file)
    df = pd.read_csv(file_path)

    # Create the plot
    plt.figure(figsize=(10, 6))

    plt.plot(df["roles"], df["build_time"], marker='.', linestyle = "None", label=f'roles')


    #plt.xticks(np.unique(df[f"delay_amount.{role_name}"]))
    # Fit a linear trend line
    z = np.polyfit(df["roles"], df["build_time"], 1)  # 1 for linear fit
    p = np.poly1d(z)
    
    # Plot the trend line
    plt.plot(df["roles"], p(df["roles"]), linestyle='-', color='red', label='Trend Line')


    # Labels and title
    plt.xlabel(f"Roles")
    plt.ylabel("Build time in seconds")
    plt.grid(True, which="both", linestyle="--", linewidth=0.5)

    # Show the plot
    plt.show()


if __name__ == "__main__":
    #make_graph_ra_da("outputForklift.csv", "Forklift")
    #make_graph_ra_da("output1.csv", "Forklift")
    #make_graph_ra_da_se("outputForkliftES.csv", "Forklift")
    #make_graph_ra_da_se("outputTransportES.csv", "Transport")
    #make_graph_ra_da_se("outputDoorES.csv", "Door")
    #make_graph_logsize("outputLogSize2.csv")
    make_graph_build_time("outputBuildTime.csv")