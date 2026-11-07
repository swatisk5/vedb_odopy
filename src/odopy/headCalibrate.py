TEST_VAR="EDITABLE WORKS"

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Calibration of VEDB T265
@author: brianszekely, christiansinnott
"""
# from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
import pupil_recording_interface as pri
import rigid_body_motion as rbm
import os
import yaml
from scipy.signal import savgol_filter
from scipy import stats
from datetime import datetime
import plotly.graph_objects as go
from scipy.spatial.transform import Rotation as R
import hvplot 
from plotly.subplots import make_subplots
import numpy as np
from matplotlib.colors import LogNorm

plt.rcParams['font.weight'] = 'bold'
plt.rcParams['font.size'] = 12
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.labelweight'] = 'bold'
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['axes.titleweight'] = 'bold'
class headCalibrate():
    def __init__(self):
        self.name = None 
        self.odometry = None
        self.accel = None
        self.fps = 200

    def set_odometry_local(self, folder):
        isdir = os.path.isdir(folder) 
        if isdir == False:
            print('Folder does not exist. Check the path')
        elif isdir == True:
            self.folder = folder
            # accel_local = os.path.join(folder, 'accel.pldata')
            # odo_local = os.path.join(folder, 'odometry.pldata')
            self.odometry = pri.load_dataset(folder,odometry='recording',cache=False)
            self.accel = pri.load_dataset(folder,accel='recording',cache=False)
            
    # def set_odometry_cloud(self, date_lookup):
    #     dbi = vedb_store.docdb.getclient()
    #     sessions = dbi.query('+date', type="Session")
    #     # # print(sessions.sort(key=myFunc))
    #     for i in range(len(sessions)):
    #         temp_date = sessions[i]['date']
    #         if temp_date == date_lookup:
    #             try:
    #                 temp_path = sessions[i].paths["odometry"][1]
    #                 self.folder = os.path.dirname(sessions[i].paths["odometry"][1])
    #                 temp_path = '/'.join(temp_path.split('/')[0:-1])
    #                 self.odometry = pri.load_dataset(temp_path,
    #                                                   odometry='recording',
    #                                                   cache=False)
    #                 self.accel = pri.load_dataset(temp_path,
    #                                               accel="recording", 
    #                                               cache=False)
    #             except:
    #                 print('=================================')
    #                 print('Sessions returned no paths. Please mount the VEDB to hard drive')
    #                 print('=================================')
        
    def start_end_plot(self):
        path_odo = os.path.join(self.folder, 'odo_times.yaml')
        path_exists = os.path.exists(path_odo)
        # print(type(self.odometry.time.values[0]))
        # print(self.odometry.time.values[:5])
        # time_local = pd.DatetimeIndex(self.odometry.time.values) - pd.Timedelta(hours=4)
        t_world = np.load(self.folder / 'odometry_timestamps_0start.npy')
        if path_exists == True:
            print('Found odo_times.yaml.')
            with open(path_odo) as file:
                time_list = yaml.load(file, Loader=yaml.FullLoader)
            try:
                self.pitch_start = time_list[0]['calibration']['pitch_start']
                self.pitch_end = time_list[0]['calibration']['pitch_end']
                self.yaw_start = time_list[0]['calibration']['yaw_start']
                self.yaw_end = time_list[0]['calibration']['yaw_end']
            except:
                print('wrong index. try without indexing [0]')
                self.pitch_start = time_list['pitch_start']
                self.pitch_end = time_list['pitch_end']
                self.yaw_start = time_list['yaw_start']
                self.yaw_end = time_list['yaw_end']
            self.times = {'calibration':
            {'pitch_start': self.pitch_start,
             'pitch_end': self.pitch_end,
             'yaw_start': self.yaw_start,
             'yaw_end': self.yaw_end
             }}
        else:
            #smooth data for better viewing purposes
            pitch_vel = savgol_filter(self.odometry.angular_velocity[:, 0], 201, 2)
            yaw_vel = savgol_filter(self.odometry.angular_velocity[:, 1], 201, 2)
            roll_vel = savgol_filter(self.odometry.angular_velocity[:, 2], 201, 2)
            # print(type(self.odometry.time.values[0]))
            # print(self.odometry.time.values[:5])
            print(f"pitch shape: {pitch_vel.shape}")
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=self.odometry.time.values,
                y=pitch_vel,
                name="pitch"       # this sets its legend entry
                ))
            fig.add_trace(go.Scatter(
                x=self.odometry.time.values,
                y=yaw_vel,
                name="yaw"       # this sets its legend entry
                ))
            fig.add_trace(go.Scatter(
            x=self.odometry.time.values,
            y=roll_vel,
            name="roll"       # this sets its legend entry
            ))
            fig.update_layout(
                title="Angular velocity odometry",
                xaxis_title="Time stamps (datetime)",
                yaxis_title="Angular Velocity (radians/second)",
                )
            fig.show()
            # show(fig)
            
            pitch_start = float(input('Pitch Start (seconds): '))
            pitch_end = float(input('Pitch End (seconds): '))
            yaw_start = float(input('Yaw Start (seconds): '))
            yaw_end = float(input('Yaw End (seconds): '))

            self.pitch_start = pitch_start
            self.pitch_end = pitch_end
            self.yaw_start = yaw_start
            self.yaw_end = yaw_end
            # pitch_start = input('Pitch Timestamp Start (HH:mm:ss format): ')
            # pitch_end = input('Pitch Timestamp End (HH:mm:ss format): ')
            # yaw_start = input('Yaw Timestamp Start (HH:mm:ss format): ')
            # yaw_end = input('Yaw Timestamp End (HH:mm:ss format): ')
            # #df_time = pd.Series(time_local[0])
            # df_time= t_world
            # self.pitch_start = datetime.combine(df_time.dt.date.values[0],
            #                              datetime.strptime(pitch_start, '%H:%M:%S').time())
            # self.pitch_end = datetime.combine(df_time.dt.date.values[0],
            #                              datetime.strptime(pitch_end, '%H:%M:%S').time())
            # self.yaw_start = datetime.combine(df_time.dt.date.values[0],
            #                              datetime.strptime(yaw_start, '%H:%M:%S').time())
            # self.yaw_end = datetime.combine(df_time.dt.date.values[0],
            #                              datetime.strptime(yaw_end, '%H:%M:%S').time())
            save_to_yaml = {'pitch_start': self.pitch_start,
                            'pitch_end': self.pitch_end,
                            'yaw_start': self.yaw_start,
                            'yaw_end': self.yaw_end
                            }
            yaml_file = os.path.join(self.folder, 'odo_times.yaml')
            # if os.path.exists(yaml_file):
            #     raise ValueError('File %s already exists! Please rename or remove it if you wish to overwrite.'%(str(yaml_file)))
            # else:
            with open(yaml_file, mode='w') as fid:
                yaml.dump(save_to_yaml, fid)
            self.times = {'calibration':
                {'pitch_start': self.pitch_start,
                'pitch_end': self.pitch_end,
                'yaw_start': self.yaw_start,
                'yaw_end': self.yaw_end
                }}
            print(self.times)

    def calculate_world_coordinate_system(self):
        #TODO: check the means of each axis for every take and save those to notes
        # print(f'Mean X,Y,Z accel: [{np.mean(self.accel.linear_acceleration[:,0].values)},{np.mean(self.accel.linear_acceleration[:,1].values)},{np.mean(self.accel.linear_acceleration[:,2].values)}]')
        # input()
        path_odo = os.path.join(self.folder, 'reids_plane.yaml')
        self.path_exists_reids = os.path.exists(path_odo)
        if self.path_exists_reids == True:
            with open(path_odo) as file:
                time_reids = yaml.load(file, Loader=yaml.FullLoader)
            print('Read reids_plane.yaml file')
            mean_g = self.accel.linear_acceleration.sel(
                time=slice(time_reids["reids_start"], time_reids["reids_end"])
            ).reduce(np.linalg.norm, "cartesian_axis").mean()
            print(f'mean g over reids plane: {mean_g.values}')
        else:
            # mean_g = self.accel.linear_acceleration.reduce(np.linalg.norm, "cartesian_axis").mean()
            #  # Swati: change it to median
            median_g = self.accel.linear_acceleration.reduce(np.linalg.norm, "cartesian_axis").median()

        g_world = xr.DataArray(
            [0, 0, median_g],
            coords={"cartesian_axis": ["x", "y", "z"]},
            dims="cartesian_axis",
            name="gravity",
        )
    
        
        g_target = xr.broadcast(self.accel.linear_acceleration, g_world)[1] #this makes g_worlds have the same shape as the data
        #this transformation does nothing as the data are already in vestibular coordinates
        # print(f'g_world before out of world and into t265_calib: {g_world}')
        
        # # calculate gravity centered coord frame rotation from calibrated data (kinematic)
        #gravity_world_coords = rbm.transform_vectors(g_world, outof="world", into="t265_calib") #was t265_calib in old code
        
        # calculate gravity centered coord frame rotation directly from uncalibrated data
        gravity_world_coords = rbm.transform_vectors(g_world, outof="world", into="t265_vestibular") #was t265_calib in old code
        # print(f'gravity_world_previous:{gravity_world_coords_1}')
        # print(f'gravity_world_prev_length:{len(gravity_world_coords_1)}')
        #it should be gravity_head_co-ord
        #new_variable= into t265_vestibular, g before calibartion

        length_gravity_world_coords = len(gravity_world_coords)
        length_g_target = len(g_target)
        downsampling_factor = length_gravity_world_coords // length_g_target
        #Downsample gravity_world_coords to match the length of g_target
        gravity_world_coords = gravity_world_coords.isel(time=slice(0, length_g_target * downsampling_factor, downsampling_factor))
        
        #Swati Commented out
        print(f'gworld: {g_world.values}')
        print(f'g target: {g_target.values}')
        print(f'gravity_world:{gravity_world_coords}')
        print(f'gravity_world length:{length_gravity_world_coords}')
        print(f' self accel: {self.accel.linear_acceleration}')

        self.rot_world = rbm.qmean(rbm.shortest_arc_rotation(gravity_world_coords, g_target).values)
        #print(self.rot_world)
        #print(f'before weirdness: {self.rot_world}')
        # self.rot_world[[1, 3]] = 0
        self.rot_world /= np.linalg.norm(self.rot_world)
        #print(f'after weirdness: {self.rot_world}')
        rbm.register_frame(
            #rotation=self.rot_world, name="world_coord", parent="t265_calib", update=True, inverse=True,
            rotation=self.rot_world, name="world_coord", parent="t265_vestibular", update=True, inverse=True,
        )

        # if self.path_exists_reids == True:
        #     gravity = rbm.transform_vectors(g_world, outof="world", into="world_coord")
        # else:
        #     gravity = rbm.transform_vectors(g_world, outof="world", into="t265_calib")

        #head in world (gravity centered)
        gravity_world = rbm.transform_vectors(g_world, outof="world", into="world_coord")
        #gravity = rbm.transform_vectors(g_world, outof="world", into="t265_vestibular")
        norm_gravity = gravity_world.reduce(np.linalg.norm, "cartesian_axis")
        self.head_roll_world = np.rad2deg(np.arctan(gravity_world[:,1]/gravity_world[:,2]))
        self.head_pitch_world = np.rad2deg(-np.arcsin(gravity_world[:,0]/norm_gravity))

        #Swati Commented out
        # print(f'g_head_roll:{self.head_roll_world}')
        # print(f'g_head_pitch:{self.head_pitch_world}')
        plt.figure(figsize=(10,8))
        #plt.plot(self.head_roll_world, self.head_pitch_world, color='blue', markersize=1, alpha=0.4, label='Gravity Centroid (world_coord)')

        #head in kinematic(after calibration)
        gravity_kinematic = rbm.transform_vectors(g_world, outof="world", into="world_coord") ##Swati: prevs it was t265_calib and now its world_coord
        norm_kinematic = gravity_kinematic.reduce(np.linalg.norm, "cartesian_axis")
        self.head_roll_kinematic = np.rad2deg(np.arctan(gravity_kinematic[:,1]/gravity_kinematic[:,2]))
        self.head_pitch_kinematic = np.rad2deg(-np.arcsin(gravity_kinematic[:,0]/norm_kinematic))

        # print("gravity_world:", gravity_world.values)
        # print("gravity_kinematic:", gravity_kinematic.values)

        #Swati Commented out plts
        # plt.plot(self.head_roll_kinematic, self.head_pitch_kinematic, color='red', markersize=1, alpha=0.4, label='Calibrated Kinematic Frame (t265_calib)')
        gravity_center = np.mean(self.head_roll_world), np.mean(self.head_pitch_world)
        # plt.scatter(gravity_center[0], gravity_center[1], color='blue', marker='o', s=100, label='Gravity Centroid (world_coord)')
        head_calibrated = np.mean(self.head_roll_kinematic), np.mean(self.head_pitch_kinematic)
        # print(f"Gravity Centroid (world_coord)  {gravity_center}")
        # print(f"Calibrated Kinematic Frame (t265_calib) {head_calibrated}")
        # plt.scatter(head_calibrated[0], head_calibrated[1], color='red', marker='o', s=100, label='Calibrated Kinematic Frame (t265_calib)')
        # plt.scatter(0, 0, color='black', marker='x', s=300, linewidths=3,
        #     label='Origin (0,0)', zorder=5)
        # plt.ylabel('Pitch (degrees)')
        # plt.xlabel('Roll (degrees)')
        # plt.legend()
        # plt.grid(True,alpha=0.3)
        # plt.savefig('kin_to_gravity.png',dpi=450)
        # plt.close()

        #Swati changed
        #head in vestibular(before calibration)

        gravity = rbm.transform_vectors(g_world, outof="world", into="t265_vestibular")
        norm = gravity.reduce(np.linalg.norm, "cartesian_axis")
        self.head_roll_before = np.rad2deg(np.arctan(gravity[:, 1] / gravity[:, 2]))
        self.head_pitch_before = np.rad2deg(-np.arcsin(gravity[:, 0] / norm)) 
        head_uncalibrated = (np.mean(self.head_roll_before), np.mean(self.head_pitch_before))
       
        # #Swati Commented out 
        # #Create the plot
        # fig, ax = plt.subplots(figsize=(10, 8))
        
        # # Plot trajectories
        # ax.plot(self.head_roll_before, self.head_pitch_before, color='green', linewidth=1.5, 
        #         alpha=0.6, label='Before Calibration')
        # ax.plot(self.head_roll_kinematic, self.head_pitch_kinematic, color='red', linewidth=1.5, 
        #         alpha=0.6, label='After Calibration')
        
        # # Plot centroids
        # ax.scatter(head_uncalibrated[0], head_uncalibrated[1], color='green', marker='o', 
        #         s=200, edgecolors='darkblue', linewidths=2, 
        #         label='Before Centroid', zorder=5)
        # ax.scatter(head_calibrated[0], head_calibrated[1], color='red', marker='o', 
        #         s=200, edgecolors='darkred', linewidths=2, 
        #         label='After Centroid', zorder=5)
        
        # ax.scatter(0, 0, color='black', marker='x', s=300, linewidths=3, 
        #         label='Origin (0,0)', zorder=5)
        
        # ax.set_xlabel('Roll (degrees)', fontsize=15, fontweight='bold')
        # ax.set_ylabel('Pitch (degrees)', fontsize=15, fontweight='bold')
        # ax.tick_params(axis='x', labelsize=15)
        # ax.tick_params(axis='x', labelsize=15)
        # ax.set_title('Head Orientation: Before vs After Calibration', fontsize=15, fontweight='bold')
        # #ax.legend(fontsize=16, loc='upper left', bbox_to_anchor=(1.02, 1))
        # ax.grid(True, alpha=0.3)
        # ax.axhline(y=0, color='k', linestyle='-', linewidth=0.5)
        # ax.axvline(x=0, color='k', linestyle='-', linewidth=0.5)
        
        # plt.tight_layout()
        # plt.show()
        
        # print(f"Before: Roll={head_uncalibrated[0]:.2f}°, Pitch={head_uncalibrated[1]:.2f}°")
        # print(f"After:  Roll={head_calibrated[0]:.2f}°, Pitch={head_calibrated[1]:.2f}°")
        
        #Swati: 2D histograms..
        # #Swati Commented out 
        # bins = 150

        # roll_min = min(self.head_roll_kinematic.min(), self.head_roll_world.min())
        # roll_max = max(self.head_roll_kinematic.max(), self.head_roll_world.max())

        # pitch_min = min(self.head_pitch_kinematic.min(), self.head_pitch_world.min())
        # pitch_max = max(self.head_pitch_kinematic.max(), self.head_pitch_world.max())

        # fig, axes = plt.subplots(1, 2, figsize=(14, 6), sharex=True, sharey=True)
        # h0 = axes[0].hist2d(
        # self.head_roll_kinematic,
        # self.head_pitch_kinematic,
        # bins=bins,
        # range=[[roll_min, roll_max], [pitch_min, pitch_max]],
        # cmap="viridis"
        # )
        
        # axes[0].set_title("Calibrated Kinematic Frame (t265_calib)")
        # axes[0].set_xlabel("Roll (deg)")
        # axes[0].set_ylabel("Pitch (deg)")
        
        # plt.colorbar(h0[3], ax=axes[0])
        # h1 = axes[1].hist2d(
        # self.head_roll_world,
        # self.head_pitch_world,
        # bins=bins,
        # range=[[roll_min, roll_max], [pitch_min, pitch_max]],
        # cmap="viridis"
        # )
        
        # axes[1].set_title("Gravity Centroid (world_coord)")
        # axes[1].set_xlabel("Roll (deg)")
        # axes[1].set_ylabel("Pitch (deg)")
        
        # plt.colorbar(h1[3], ax=axes[1])

        # plt.tight_layout()
        # plt.show()

        # roll_all= np.nanmedian(self.head_roll_kinematic.values)
        # pitch_all= np.nanmedian(self.head_pitch_kinematic.values)

        # #Create the plot
        # fig, ax = plt.subplots(figsize=(10, 8))
        
        # #ax.scatter(self.heading_elevation_after, self.head_pitch_kinematic, alpha=0.5)
        # ax.scatter(roll_all, pitch_all, color='red', s=200, zorder=5, label='Centroid')
        
        # ax.set_xlabel('Roll (degrees)', fontsize=15, fontweight='bold')
        # ax.set_ylabel('Pitch (degrees)', fontsize=15, fontweight='bold')
        # ax.tick_params(axis='x', labelsize=15)
        # ax.tick_params(axis='x', labelsize=15)
        # #ax.set_title('Head Orientation: Before vs After Calibration', fontsize=15, fontweight='bold')
        # #ax.legend(fontsize=16, loc='upper left', bbox_to_anchor=(1.02, 1))
        # ax.grid(True, alpha=0.3)
        # ax.axhline(y=0, color='k', linestyle='-', linewidth=0.5)
        # ax.axvline(x=0, color='k', linestyle='-', linewidth=0.5)
        
        # plt.tight_layout()
        # plt.show()

        # print(f"Roll ={roll_all:.2f}°, Pitch ={pitch_all:.2f}°")        

    def t265_to_head_trans(self):
        # Pull annotated calibration segment times from yaml (LEGACY Fself.timesROM OLD ANALYSIS, NEEDS CHANGED)
        # with open(folder / subject / "meta.yaml") as f:
        #     times = yaml.safe_load(f.read())

        # for annotation in ("pre_calib", "post_calib", "experiment"):
        #     if annotation in times:
        #         times[annotation] = {
        #             k: pd.to_datetime(times["date"]) + pd.to_timedelta(v)
        #             for k, v in times[annotation].items()
        #         }

        # for annotation in ("re_calib", "exclude"):
        #     if annotation in times:
        #         for idx, segment in enumerate(times[annotation]):
        #             times[annotation][idx] = {
        #                 k: pd.to_datetime(times["date"]) + pd.to_timedelta(v)
        #                 for k, v in times[annotation][idx].items()
        #             }
        # Extract calibration segment times:
        # Set-up Reference Frames

        #old way
        self.R_WORLD_ODOM = np.array([[0, 0, -1], 
                                [-1, 0, 0], 
                                [0, 1, 0]])
        self.R_IMU_ODOM = np.array([[-1, 0, 0], 
                              [0, 1, 0], 
                               [0, 0, -1]])
        #new way
        # R_WORLD_ODOM = np.array([[0, -1, 0], 
        #                          [0, 0, 1], 
        #                          [-1, 0, 0]])
        # R_IMU_ODOM = np.array([[0, 1, 0], 
        #                        [0, 0, 1], 
        #                        [1, 0, 0]])


        rbm.register_frame("world",update=True)
        rbm.ReferenceFrame.from_rotation_matrix(self.R_WORLD_ODOM, name="t265_world",
                                                parent="world").register(update=True)

        # rbm.register_frame(
        #     "t265_odom",
        #     translation=self.odometry.position.values,
        #     rotation=self.odometry.orientation.values,
        #     timestamps=self.odometry.time.values,
        #     parent="t265_world",
        #     update=True,
        # )
        
        rbm.ReferenceFrame.from_dataset(self.odometry, translation = "position",
                                        rotation = "orientation", timestamps = "time",
                                        parent = "t265_world", name = "t265_odom").register(update=True)
        
        rbm.ReferenceFrame.from_rotation_matrix(self.R_IMU_ODOM, name="t265_imu", parent="t265_odom").register(update=True)
        rbm.ReferenceFrame.from_rotation_matrix(self.R_WORLD_ODOM, name="t265_vestibular", 
                                                parent="t265_odom", 
                                                inverse=True
                                                ).register(update=True)
        

        # Define first calibrated frame using calibration segments identified in set_calibration method
        # segments = [times["pre_calib"]] + [times["re_calib"]]
        #----------------------------------------------------------------------------------------------------------
##################
        #Swati Changed start:

        # ---- KEY CHANGE: times are now plain floats (elapsed seconds), no datetime conversion needed ----
        # segments = self.times["calibration"]
        # rotations = np.zeros([len(segments), 4])
        
        # # No longer need to convert to np.datetime64 - just use floats directly
        # pitch_start = self.times["calibration"]["pitch_start"]
        # pitch_end   = self.times["calibration"]["pitch_end"]
        # yaw_start   = self.times["calibration"]["yaw_start"]
        # yaw_end     = self.times["calibration"]["yaw_end"]

        # omega = rbm.transform_vectors(self.odometry.angular_velocity, outof="t265_world", into="t265_vestibular")
        
        # # sel() with float seconds works directly now
        # omega_pitch = omega.sel(time=slice(pitch_start, pitch_end))
        # omega_yaw   = omega.sel(time=slice(yaw_start, yaw_end))

        # omega_pitch_target = xr.zeros_like(omega_pitch)
        # omega_pitch_target[:, 1] = np.sign(omega_pitch[:, 1]) * omega_pitch.reduce(np.linalg.norm, "cartesian_axis")
        
        # omega_yaw_target = xr.zeros_like(omega_yaw)
        # omega_yaw_target[:, 2] = np.sign(omega_yaw[:, 2]) * omega_yaw.reduce(np.linalg.norm, "cartesian_axis")
        
        # rotations = rbm.best_fit_rotation(xr.concat((omega_pitch, omega_yaw), "time"),
        #                                 xr.concat((omega_pitch_target, omega_yaw_target), "time"))

        # # timestamps is now just the earlier of the two start times (float)
        # timestamps = min(pitch_start, yaw_start)

        # # argmin_time: find closest time in odometry to our timestamp (float comparison)
        # argmin_time = min(self.odometry.time.values, key=lambda x: abs(x - timestamps))
################

        # segments = self.times["calibration"]
        # rotations = np.zeros([len(segments), 4]) #Original has 4 - yaw, pitch, Reid's
        # timestamps = np.zeros(len(segments), dtype=pd.Timestamp)
        
        # for idx, seg in self.times["calibration"].items():
        #     try:
        #         self.times["calibration"][idx] = np.datetime64(seg)
        #     except ValueError:
        #         self.times["calibration"][idx] = np.datetime64("NaT")

        #     # self.times["calibration"][idx] = np.datetime64(seg)
        # omega = rbm.transform_vectors(self.odometry.angular_velocity, outof="t265_world", into="t265_vestibular")
        # omega_pitch = omega.sel(time=slice(self.times["calibration"]["pitch_start"], 
        #                                    self.times["calibration"]["pitch_end"]))
        # omega_yaw = omega.sel(time=slice(self.times["calibration"]["yaw_start"], 
        #                                  self.times["calibration"]["yaw_end"]))

        # omega_pitch_target = xr.zeros_like(omega_pitch)
        # omega_pitch_target[:, 1] = np.sign(omega_pitch[:, 1]) * omega_pitch.reduce(np.linalg.norm,
        #                                                                            "cartesian_axis")
        # omega_yaw_target = xr.zeros_like(omega_yaw)
        # omega_yaw_target[:, 2] = np.sign(omega_yaw[:, 2]) * omega_yaw.reduce(np.linalg.norm,
        #                                                                      "cartesian_axis")
        # rotations = rbm.best_fit_rotation(xr.concat((omega_pitch, omega_yaw), "time"),
        #                                           xr.concat((omega_pitch_target, omega_yaw_target), "time"))

        # timestamps = min(self.times["calibration"]["pitch_start"],
        #                       self.times["calibration"]["yaw_start"])

        # argmin_time = min(self.odometry.time.values, key=lambda x: abs(x - timestamps))

        #Swati Changes end!
        #----------------------------------------------------------------------------------------------------------


        # for idx, calib_segment in enumerate(self.times["calibration"].items()):
        #     dt64 = np.datetime64(calib_segment[1])
        #     omega = rbm.transform_vectors(self.odometry.angular_velocity, outof="t265_world", into="t265_vestibular")
        #     omega_pitch = omega.sel(time=slice(calib_segment["pitch_start"], calib_segment["pitch_end"]))
        #     omega_yaw = omega.sel(time=slice(calib_segment["yaw_start"], calib_segment["yaw_end"]))

        #     omega_pitch_target = xr.zeros_like(omega_pitch)
        #     omega_pitch_target[:, 1] = np.sign(omega_pitch[:, 1]) * omega_pitch.reduce(np.linalg.norm, "cartesian_axis")

        #     omega_yaw_target = xr.zeros_like(omega_yaw)
        #     omega_yaw_target[:, 2] = np.sign(omega_yaw[:, 2]) * omega_yaw.reduce(np.linalg.norm, "cartesian_axis")

        #     rotations[idx, :] = rbm.best_fit_rotation(xr.concat((omega_pitch, omega_yaw), "time"),
        #                                               xr.concat((omega_pitch_target, omega_yaw_target), "time"))

        #     timestamps[idx] = min(calib_segment["pitch_start"], calib_segment["yaw_start"])
            
        # print(argmin_time) #IS THERE A REASON THIS ARRAY IS ONE VALUE?
        # print(pd.to_datetime(argmin_time))
        
        # print(np.array([argmin_time]))
        # print(np.array([pd.to_datetime(argmin_time)]))

        # Construct discrete reference frame
        # Note - may need to change discrete to false, as final version of calibration script this is ported from
        # incorporates an additional step using Reid's plane, that results in a final continuous calibration frame.

        # rbm.register_frame(rotation=np.array([rotations]), #Hacky but passes, otherwise get ValueError: Expected rotation to be of shape (1, 4), got (4,)
        #                    # timestamps=xr.DataArray(argmin_time),
        #                    # timestamps=np.array([pd.to_datetime(argmin_time)]), #pd.to_datetime(argmin_time)
        ########################
        #                    name="t265_calib", parent="t265_vestibular", inverse=True, discrete=False, update=True)
        # rbm.register_frame(rotation=rotations,
        #                     name="t265_calib", parent="t265_vestibular",
        #                     inverse=True, discrete=False, update=True)
        
        # #calculate world coordinate system from gravity
        ##########################
        self.calculate_world_coordinate_system()
        print(rbm.render_tree("world"))

        #explicity transform the sensor coordinate frame to calibrated coordinate frame 
        #WORK IN PROGRESS
        # print(f'Quaternion that will transform sensor to head coordinates: {rotations}')
        # print(f'Rotation Matrix that will transform sensor to head coordinates: {self.quat_to_rot_mat(rotations)}')
        # print(f'Rotation Matrix that will transform calibrated rf to world coordinates: {self.quat_to_rot_mat(self.rot_world)}')
        # og_euler = self.quat_to_euler(self.odometry.orientation.values)

        # calibrated_orientation = rbm.qmul(self.odometry.orientation.values,rotations)
        # calibrated_orientation_world = rbm.qmul(calibrated_orientation,self.rot_world)
        
        # # calib_euler = self.quat_to_euler(calibrated_orientation_world)

        # #swap the george w with zed axis
        # calibrated_orientation_world[:, [0, -1]] = calibrated_orientation_world[:, [-1, 0]]

        # euler_angles = []
        # for q in (calibrated_orientation):
        #     r = R.from_quat(q)
        #     euler_angles.append(r.as_euler('xyz',degrees=True))
        # # euler_angles = np.vstack([np.pad(arr, (0, max(map(len, euler_angles)) - len(arr))) for arr in euler_angles])
        # euler_angles = np.vstack(euler_angles)
        # euler_angles = euler_angles * -1
        # plt.figure()
        # plt.scatter(euler_angles[:,0], euler_angles[:,1], color='blue',s=1,alpha=0.5,label='quaternion method')
        # plt.scatter(self.head_roll, self.head_pitch, color='red',s=1,alpha=0.5,label='acceleration method')
        # plt.title('Quaternion transformation to euler')
        # plt.ylabel('Pitch wrt to gravity (degrees)')
        # plt.xlabel('Roll wrt to gravity (degrees)')
        # plt.legend()
        # plt.tight_layout()
        # plt.show()
        #STILL WORKING ON TRANSFORMING HEAD TO GRAVITY VIA QUATERNIONS

        # Create a figure and three subplots
        # fig, axs = plt.subplots(3, 1, figsize=(10, 10))

        # # Plot roll
        # axs[0].plot(self.odometry.time.values, og_euler[:, 0], color='red', label='roll before transformation', linewidth=3)
        # axs[0].plot(self.odometry.time.values, euler_angles[:, 0], color='blue', label='roll after transformation', linewidth=3, alpha=0.5)
        # axs[0].set_title('Roll')
        # axs[0].set_ylabel('Degrees')
        # axs[0].legend()

        # # Plot pitch
        # axs[1].plot(self.odometry.time.values, og_euler[:, 1], color='red', label='pitch before transformation', linewidth=3)
        # axs[1].plot(self.odometry.time.values, euler_angles[:, 1], color='blue', label='pitch after transformation', linewidth=3, alpha=0.5)
        # axs[1].set_title('Pitch')
        # axs[1].set_ylabel('Degrees')
        # axs[1].legend()

        # # Plot yaw
        # axs[2].plot(self.odometry.time.values, og_euler[:, 2], color='red', label='yaw before transformation', linewidth=3)
        # axs[2].plot(self.odometry.time.values, euler_angles [:, 2 ], color='blue', label='yaw after transformation', linewidth=3, alpha=0.5)
        # axs[2].set_title('Yaw')
        # axs[2].set_ylabel('Degrees')
        # axs[2].legend()

        # plt.tight_layout()
        # plt.show()
        # # plt.savefig('roll_pitch_yaw.png',dpi=400)
        # plt.close()

        # # Create a figure and three subplots
        # fig, axs = plt.subplots(4, 1, figsize=(10, 10))

        # # Plot roll
        # axs[0].plot(self.odometry.time.values, self.odometry.orientation.values[:, 0], color='red', label='w before transformation', linewidth=3)
        # axs[0].plot(self.odometry.time.values, calibrated_orientation[:, 0], color='blue', label='w after transformation', linewidth=3, alpha=0.3)
        # axs[0].set_title('w')
        # axs[0].set_ylabel('Degrees')
        # axs[0].legend()

        # # Plot pitch
        # axs[1].plot(self.odometry.time.values, self.odometry.orientation.values[:, 1], color='red', label='x before transformation', linewidth=3)
        # axs[1].plot(self.odometry.time.values, calibrated_orientation[:, 1], color='blue', label='x after transformation', linewidth=3, alpha=0.3)
        # axs[1].set_title('x')
        # axs[1].set_ylabel('Degrees')
        # axs[1].legend()

        # # Plot yaw
        # axs[2].plot(self.odometry.time.values, self.odometry.orientation.values[:, 2], color='red', label='y before transformation', linewidth=3)
        # axs[2].plot(self.odometry.time.values, calibrated_orientation[:, 2], color='blue', label='y after transformation', linewidth=3, alpha=0.3)
        # axs[2].set_title('y')
        # axs[2].set_ylabel('Degrees')
        # axs[2].legend()

        # # Plot z
        # axs[3].plot(self.odometry.time.values, self.odometry.orientation.values[:, 3], color='red', label='z before transformation', linewidth=3)
        # axs[3].plot(self.odometry.time.values, calibrated_orientation[:, 3], color='blue', label='z after transformation', linewidth=3, alpha=0.3)
        # axs[3].set_title('z')
        # axs[3].set_ylabel('Degrees')
        # axs[3].legend()

        # plt.tight_layout()
        # plt.show()
        # plt.savefig('quaternion_transformation.png',400)
        # plt.close()

        # ##calc_linear_offset
        # yaw_start = self.times["calibration"]["yaw_start"]
        # yaw_end = self.times["calibration"]["yaw_end"]
        # errors = []

        # record_time = slice(
        #     self.odometry.orientation.time[0].values,
        #     self.odometry.orientation.time[-1].values
        # )
        # for a in np.linspace(-10, 10, 11):

        #     for b in np.linspace(-10, 10, 11):

        #         for c in np.linspace(-10, 10, 11):

        #             rbm.ReferenceFrame(
        #                 translation=(a, b, c),
        #                 rotation=(1, 0, 0, 0),
        #                 parent="t265_calib",
        #                 name="t265_headcenter"
        #             ).register(update=True)

        #             # Transform velocities
        #             self.calib_lin_vel = rbm.transform_vectors(
        #                 self.odometry.linear_velocity.sel(time=slice(yaw_start, yaw_end)),
        #                 outof="t265_world",
        #                 into="t265_headcenter"
        #             )

        #             # Compute vector norm over xyz axis
        #             vel_norm = np.sqrt(
        #                 self.calib_lin_vel.sel(cartesian_axis="x")**2 +
        #                 self.calib_lin_vel.sel(cartesian_axis="y")**2 +
        #                 self.calib_lin_vel.sel(cartesian_axis="z")**2
        #             )

        #             # Mean squared error
        #             error = np.mean(vel_norm.values)

        #             errors.append((a, b, c, error))

        #             # if error < best_error:
        #             #     best_error = error
        #             #     best_translation = (a, b, c)
        #             print("translation:", (a,b,c))
        #             print("error:", error)

        record_time = slice(self.odometry.orientation.time[0].values, self.odometry.orientation.time[-1].values) #Just selecting entire recording for now, but need it as a slice object

        # # Express data in calibrated frame (probably can use iteration to make this cleaner)
        # self.calib_ang_pos = rbm.transform_quaternions(self.odometry.orientation.sel(time=record_time), outof="t265_world", into="world_coord") if self.path_exists_reids == True else rbm.transform_quaternions(self.odometry.orientation.sel(time=record_time), outof="t265_world", into="t265_calib")

        # self.calib_lin_pos = rbm.transform_points(self.odometry.position.sel(time=record_time), outof="t265_world", into="world_coord") if self.path_exists_reids == True else rbm.transform_points(self.odometry.position.sel(time=record_time), outof="t265_world", into="t265_calib")
        # #Get TypeError on into="t265_calib": float() argument must be a string or a number, not 'TimeStamp'
        # self.calib_ang_vel = rbm.transform_vectors(self.odometry.angular_velocity.sel(time=record_time), outof="t265_world", into="world_coord") if self.path_exists_reids == True else rbm.transform_vectors(self.odometry.angular_velocity.sel(time=record_time), outof="t265_world", into="t265_calib")

        # self.calib_lin_vel = rbm.transform_vectors(self.odometry.linear_velocity.sel(time=record_time), outof="t265_world", into="world_coord") if self.path_exists_reids == True else rbm.transform_vectors(self.odometry.linear_velocity.sel(time=record_time), outof="t265_world", into="t265_calib")

        # self.calib_ang_acc = rbm.transform_vectors(self.odometry.angular_acceleration.sel(time=record_time), outof="t265_world", into="world_coord") if self.path_exists_reids == True else rbm.transform_vectors(self.odometry.angular_acceleration.sel(time=record_time), outof="t265_world", into="t265_calib")

        # self.calib_lin_acc = rbm.transform_vectors(self.odometry.linear_acceleration.sel(time=record_time), outof="t265_world", into="world_coord") if self.path_exists_reids == True else rbm.transform_vectors(self.odometry.linear_acceleration.sel(time=record_time), outof="t265_world", into="t265_calib")

        # Express data in data driven calibrated frame 
        self.calib_ang_pos = rbm.transform_quaternions(self.odometry.orientation.sel(time=record_time), outof="t265_world", into="world_coord") 
        
        self.calib_lin_pos = rbm.transform_points(self.odometry.position.sel(time=record_time), outof="t265_world", into="world_coord") 
        #Get TypeError on into="t265_calib": float() argument must be a string or a number, not 'TimeStamp'
        self.calib_ang_vel = rbm.transform_vectors(self.odometry.angular_velocity.sel(time=record_time), outof="t265_world", into="world_coord") 
        
        self.calib_lin_vel = rbm.transform_vectors(self.odometry.linear_velocity.sel(time=record_time), outof="t265_world", into="world_coord") 
        
        self.calib_ang_acc = rbm.transform_vectors(self.odometry.angular_acceleration.sel(time=record_time), outof="t265_world", into="world_coord") 
        
        self.calib_lin_acc = rbm.transform_vectors(self.odometry.linear_acceleration.sel(time=record_time), outof="t265_world", into="world_coord")
        
        # Return data expressed in calibrated frame
        self.calib_odo = xr.Dataset(
            {"ang_pos": self.calib_ang_pos, 
            "lin_pos": self.calib_lin_pos,
            "ang_vel": self.calib_ang_vel,
            "lin_vel": self.calib_lin_vel,
            "ang_acc": self.calib_ang_acc,
            "lin_acc": self.calib_lin_acc}
            )
        print('odometry data are now calibrated')

    def save_calibrated_odometry(self):  
        path_calib_odo = os.path.join(self.folder, 'data_driven_odometry.npz')
        np.savez(
            path_calib_odo,
            data_angular_position=self.calib_ang_pos,
            data_linear_position=self.calib_lin_pos,
            data_angular_velocity=self.calib_ang_vel,
            data_linear_velocity=self.calib_lin_vel,
            data_angular_acceleration=self.calib_ang_acc,
            data_linear_acceleration=self.calib_lin_acc
        )
        print(f"Calibrated odometry data saved")
        print(f"Calibrated odometry saved to: {path_calib_odo}")

    
    def calc_linear_offset(self):
        self.R_WORLD_ODOM = np.array([
            [0, 0, -1],
            [-1, 0, 0],
            [0, 1, 0]
        ])
        rbm.register_frame("world", update=True)
        rbm.ReferenceFrame.from_rotation_matrix(
            self.R_WORLD_ODOM,
            name="t265_world",
            parent="world"
        ).register(update=True)
        best_error = np.inf
        best_translation = None
        yaw_start = self.times["calibration"]["yaw_start"]
        yaw_end = self.times["calibration"]["yaw_end"]
        errors = []
        record_time = slice(
            self.odometry.orientation.time[0].values,
            self.odometry.orientation.time[-1].values
        )
        for a in np.linspace(-10, 10, 11):

            for b in np.linspace(-10, 10, 11):

                for c in np.linspace(-10, 10, 11):

                    rbm.ReferenceFrame(
                        translation=(a, b, c),
                        rotation=(1, 0, 0, 0),
                        parent="t265_calib",
                        name="t265_headcenter"
                    ).register(update=True)

                    # Transform velocities
                    self.calib_lin_vel = rbm.transform_vectors(
                        self.odometry.linear_velocity.sel(time=slice(yaw_start, yaw_end)),
                        outof="t265_world",
                        into="t265_headcenter"
                    )

                    # Compute vector norm over xyz axis
                    vel_norm = np.sqrt(
                        self.calib_lin_vel.sel(cartesian_axis="x")**2 +
                        self.calib_lin_vel.sel(cartesian_axis="y")**2 +
                        self.calib_lin_vel.sel(cartesian_axis="z")**2
                    )

                    # Mean squared error
                    error = np.mean(vel_norm.values)

                    errors.append((a, b, c, error))

                    # if error < best_error:
                    #     best_error = error
                    #     best_translation = (a, b, c)
                    print("translation:", (a,b,c))
                    print("error:", error)

        # print("Best translation:", (a,b,c))
        # print("Best error:", error)
        self.offset_errors = errors        
        return
    
    def calc_gait_variability(self):
        """
        this article is used as a reference for the gait variability metric:
        https://jneuroengrehab.biomedcentral.com/track/pdf/10.1186/1743-0003-2-19.pdf
        """
        # plt.plot(self.odometry.position[:,1])
        # plt.show()
        # peaks_fast, _= find_peaks(fast[:,1],distance=fps / 3)
        # for i in range(len(peaks_slow) - 1):
        #     step_time_slo[i] = (peaks_slow[i+1] - peaks_slow[i]) * (1/fps)
        pass
    
    def calc_inst_force(self):
        pass

    def quat_to_rot_mat(self,quaternion):
        """
        Parameters: 
        -array([-9.99428637e-01, -1.27234994e-02,  3.98607922e-04,  3.13105822e-02]) : Coordinates:'w' 'x' 'y' 'z'

        Returns:
        - numpy.ndarray - 3x3 rotation matrix.
        Output: [[ 9.98038977e-01  6.25752416e-02 -1.59352069e-03]
                [-6.25955284e-02  9.97715520e-01 -2.54074980e-02]
                [ 3.78386558e-16  2.54574206e-02  9.99675907e-01]]
        
        Equation:
        R = | 1 - 2(q_y^2 + q_z^2)  2(q_x*q_y - q_w*q_z)  2(q_x*q_z + q_w*q_y) |
            | 2(q_x*q_y + q_w*q_z)  1 - 2(q_x^2 + q_z^2)  2(q_y*q_z - q_w*q_x) |
            | 2(q_x*q_z - q_w*q_y)  2(q_y*q_z + q_w*q_x)  1 - 2(q_x^2 + q_y^2) |
        """
        q_w, q_x, q_y, q_z = quaternion
        rot_mat_sensor_to_head = np.array([
            [1 - 2 * (q_y**2 + q_z**2), 2 * (q_x*q_y - q_w*q_z), 2 * (q_x*q_z + q_w*q_y)],
            [2 * (q_x*q_y + q_w*q_z), 1 - 2 * (q_x**2 + q_z**2), 2 * (q_y*q_z - q_w*q_x)],
            [2 * (q_x*q_z - q_w*q_y), 2 * (q_y*q_z + q_w*q_x), 1 - 2 * (q_x**2 + q_y**2)]
        ])
        return rot_mat_sensor_to_head

    def calc_head_orientation(self):
        pass
        # x = self.accel.sel(cartesian_axis="x")
        # y = self.accel.sel(cartesian_axis="y")
        # z = self.accel.sel(cartesian_axis="z")
        # self.head_roll = np.rad2deg(np.arctan2(y,x))
        # self.head_pitch = np.rad2deg(np.arctan2(y,z))
        # self.head_yaw = np.rad2deg(np.arctan2(z,x))
        #ASSUMES SPHERICAL COORDINATES
        # norm = self.accel.reduce(np.linalg.norm, "cartesian_axis")
        # self.head_roll = np.rad2deg(np.arctan(y/z))
        # self.head_pitch = np.rad2deg(-np.arcsin(x/norm))
        # self.head_yaw = np.rad2deg(-np.arctan2(y, x))

    def calc_rotation_slice(self):
        t_start = self.times["calibration"]["pitch_start"]
        t_end = self.times["calibration"]["yaw_end"]
        # Only use the calibration interval
        ang_vel = self.calib_odo.ang_vel.sel(time=slice(t_start, t_end))
        x = ang_vel.sel(cartesian_axis="x")
        y = ang_vel.sel(cartesian_axis="y")
        z = ang_vel.sel(cartesian_axis="z")
        norm = self.calib_odo.ang_vel.reduce(np.linalg.norm, "cartesian_axis")
        self.rotation_azimuth_after = np.rad2deg(-np.arctan2(z, x))
        self.rotation_elevation_after = np.rad2deg(np.arcsin(y/norm))

        ang_vel_mag = np.linalg.norm(ang_vel, axis=1)
        avg_ang_vel = np.mean(ang_vel_mag)
        print(f"angular velocity:{avg_ang_vel}")
        return self.rotation_azimuth_after, self.rotation_elevation_after        

    def calc_rotation_after(self):
        #print(list(self.odometry.keys()))
        #print(odo.odometry.data_vars)
        x = self.calib_odo.ang_vel.sel(cartesian_axis="x")
        y = self.calib_odo.ang_vel.sel(cartesian_axis="y")
        z = self.calib_odo.ang_vel.sel(cartesian_axis="z")
        norm = self.calib_odo.ang_vel.reduce(np.linalg.norm, "cartesian_axis")
        self.rotation_azimuth_after = np.rad2deg(-np.arctan2(z, x))
        self.rotation_elevation_after = np.rad2deg(np.arcsin(y/norm))
        return self.rotation_azimuth_after, self.rotation_elevation_after
    
    def calc_heading_before(self):
        #print(list(self.odometry.keys()))
        #print(odo.odometry.data_vars)
        x = self.odometry.linear_velocity.sel(cartesian_axis="x")
        y = self.odometry.linear_velocity.sel(cartesian_axis="y")
        z = self.odometry.linear_velocity.sel(cartesian_axis="z")
        norm = self.odometry.linear_velocity.reduce(np.linalg.norm, "cartesian_axis")
        self.heading_azimuth_before = np.rad2deg(-np.arctan2(y, x))
        self.heading_elevation_before = np.rad2deg(np.arcsin(z/norm))
        return self.heading_azimuth_before, self.heading_elevation_before
    
    def calc_heading_after(self):
        x = self.calib_odo.lin_vel.sel(cartesian_axis="x")
        y = self.calib_odo.lin_vel.sel(cartesian_axis="y")
        z = self.calib_odo.lin_vel.sel(cartesian_axis="z")
        norm = self.calib_odo.lin_vel.reduce(np.linalg.norm, "cartesian_axis")
        self.heading_azimuth_after = np.rad2deg(-np.arctan2(y, x))
        self.heading_elevation_after = np.rad2deg(np.arcsin(z/norm))
        # lin_vel_mag = np.linalg.norm(self.calib_odo.lin_vel, axis=1)
        # avg_lin_vel = np.mean(lin_vel_mag)
        # print(f"linear_velocity: {avg_lin_vel}")
        #heading_centroid= (np.mean(self.heading_azimuth_after),np.mean(self.heading_elevation_after))
        #heading_centroid_before= (np.mean(self.heading_azimuth_before),np.mean(self.heading_elevation_before))
        # heading_centroid = ( np.nanmean(self.head_roll_kinematic) , np.nanmean(self.head_pitch_kinematic))
        # heading_centroid_before=( np.nanmean(self.head_roll_before) , np.nanmean(self.head_pitch_before))     
        # #Create the plot
        # fig, ax = plt.subplots(figsize=(10, 8))
        # # Plot trajectories
        # ax.plot(self.head_roll_before, self.head_pitch_before, color='green', linewidth=1.5, 
        #         alpha=0.6, label='Before Calibration')
        # ax.plot(self.head_roll_kinematic, self.head_pitch_kinematic, color='red', linewidth=1.5, 
        #          alpha=0.6, label='After Calibration')
        # # Plot centroids
        # ax.scatter(heading_centroid[0], heading_centroid[1], color='red', marker='*', 
        #         s=200, edgecolors='darkred', linewidths=2, 
        #         label='After Calibration', zorder=5)
        # ax.scatter(heading_centroid_before[0], heading_centroid_before[1], color='green', marker='o', 
        #                s=200, edgecolors='darkgreen', linewidths=2, 
        #                  label='Before Calibration', zorder=5)
        
        # ax.scatter(0, 0, color='black', marker='x', s=300, linewidths=3, 
        #         label='Origin (0,0)', zorder=5)
        
        # ax.set_xlabel('Roll (degrees)', fontsize=15, fontweight='bold')
        # ax.set_ylabel('Pitch (degrees)', fontsize=15, fontweight='bold')
        # ax.tick_params(axis='x', labelsize=15)
        # ax.tick_params(axis='x', labelsize=15)
        # ax.set_title('Head Orientation Calibration', fontsize=15, fontweight='bold')
        # #ax.legend(fontsize=16, loc='upper left', bbox_to_anchor=(1.02, 1))
        # ax.grid(True, alpha=0.3)
        # ax.axhline(y=0, color='k', linestyle='-', linewidth=0.5)
        # ax.axvline(x=0, color='k', linestyle='-', linewidth=0.5)
        
        # plt.tight_layout()
        # plt.show()

        # print(f"Roll ={heading_centroid[0]:.2f}°, Pitch ={heading_centroid[1]:.2f}°")
        # return self.head_roll_before, self.head_pitch_before

    
    def heading_orienation_centroid(self):

        roll_all= np.nanmedian(self.head_roll_kinematic.values)
        pitch_all= np.nanmedian(self.head_pitch_kinematic.values)

        #Create the plot
        fig, ax = plt.subplots(figsize=(10, 8))
        
        #ax.scatter(self.heading_elevation_after, self.head_pitch_kinematic, alpha=0.5)
        ax.scatter(roll_all, pitch_all, color='red', s=200, zorder=5, label='Centroid')
        
        ax.set_xlabel('Roll (degrees)', fontsize=15, fontweight='bold')
        ax.set_ylabel('Pitch (degrees)', fontsize=15, fontweight='bold')
        ax.tick_params(axis='x', labelsize=15)
        ax.tick_params(axis='x', labelsize=15)
        #ax.set_title('Head Orientation: Before vs After Calibration', fontsize=15, fontweight='bold')
        #ax.legend(fontsize=16, loc='upper left', bbox_to_anchor=(1.02, 1))
        ax.grid(True, alpha=0.3)
        ax.axhline(y=0, color='k', linestyle='-', linewidth=0.5)
        ax.axvline(x=0, color='k', linestyle='-', linewidth=0.5)
        
        plt.tight_layout()
        plt.show()

        print(f"Roll ={roll_all:.2f}°, Pitch ={pitch_all:.2f}°")

        # azimuth_all=np.nanmedian(self.heading_azimuth_after.values)
        # roll_all=np.median(self.head_roll_kinematic.values)
        # #Create the plot
        # fig, ax = plt.subplots(figsize=(10, 8))
        
        # #ax.scatter(self.heading_elevation_after, self.head_pitch_kinematic, alpha=0.5)
        # ax.scatter(azimuth_all, roll_all, color='blue', s=200, zorder=5, label='Centroid')
        
        # ax.set_xlabel('Azimuth (degrees)', fontsize=15, fontweight='bold')
        # ax.set_ylabel('Roll (degrees)', fontsize=15, fontweight='bold')
        # ax.tick_params(axis='x', labelsize=15)
        # ax.tick_params(axis='x', labelsize=15)
        # #ax.set_title('Head Orientation: Before vs After Calibration', fontsize=15, fontweight='bold')
        # #ax.legend(fontsize=16, loc='upper left', bbox_to_anchor=(1.02, 1))
        # ax.grid(True, alpha=0.3)
        # ax.axhline(y=0, color='k', linestyle='-', linewidth=0.5)
        # ax.axvline(x=0, color='k', linestyle='-', linewidth=0.5)
        
        # plt.tight_layout()
        # plt.show()

        # print(f"Azimuth ={azimuth_all:.2f}°, Roll ={roll_all:.2f}°")
        return
    def heading_orienation_centroid_summary_before(self, scatter_elevation_pitch_before, scatter_azimuth_roll_before):

        # --- Elevation vs Pitch ---
        fig, ax = plt.subplots(figsize=(10, 10))

        for d in scatter_elevation_pitch_before:
            ax.scatter(d['datadriven_pitch'], d['datadriven_elevation'],
                    color='green', s=80, zorder=5,
                    edgecolors='darkgreen', linewidths=1)
            # ax.annotate(
            #             d['session'],
            #             xy=(d['pitch_all'], d['elevation_all']),
            #             xytext=(5, 5),
            #             textcoords='offset points',
            #             fontsize=8,
            #             color='darkgreen')
        lim = 40
        ax.plot([-lim, lim], [-lim, lim],
                color='gray', linestyle='--', linewidth=1.5,
                label='y = x', zorder=3)
        for radius in [10, 20, 30]:
            circle = plt.Circle((0, 0), radius, fill=False, color='gray',
                                linestyle='--', linewidth=0.8, alpha=0.5)
            ax.add_patch(circle)
            ax.annotate(f'{radius}°', xy=(radius, 0), fontsize=7, color='gray')
        ax.scatter([], [], color='green', s=80, edgecolors='darkgreen',
                label='Heading Orientation Before')
        ax.set_xlabel("Pitch (degrees)", fontsize=12)
        ax.set_ylabel("Elevation (degrees)", fontsize=12)
        ax.axhline(0, color='k', linewidth=0.5, alpha=0.3)
        ax.axvline(0, color='k', linewidth=0.5, alpha=0.3)
        ax.set_xlim(-lim, lim)
        ax.set_ylim(-lim, lim)
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.2)
        ax.legend(fontsize=11)
        plt.tight_layout()
        plt.show()

        # --- Azimuth vs Roll ---
        fig, ax = plt.subplots(figsize=(10, 10))

        for d in scatter_azimuth_roll_before:
            ax.scatter(d['datadriven_roll'], d['datadriven_azimuth'],
                    color='red', s=80, zorder=5,
                    edgecolors='darkred', linewidths=1)
            # ax.annotate(
            #             d['session'],
            #             xy=(d['roll_all'], d['azimuth_all']),
            #             xytext=(5, 5),
            #             textcoords='offset points',
            #             fontsize=8,
            #             color='darkred')           
        ax.plot([-lim, lim], [-lim, lim],
                color='gray', linestyle='--', linewidth=1.5,
                label='y = x', zorder=3)

        for radius in [10, 20, 30]:
            circle = plt.Circle((0, 0), radius, fill=False, color='gray',
                                linestyle='--', linewidth=0.8, alpha=0.5)
            ax.add_patch(circle)
            ax.annotate(f'{radius}°', xy=(radius, 0), fontsize=7, color='gray')
        ax.scatter([], [], color='red', s=80, edgecolors='darkred',
                label='Heading Orientation Before')
        ax.set_xlabel("Roll (degrees)", fontsize=12)
        ax.set_ylabel("Azimuth (degrees)", fontsize=12)
        ax.axhline(0, color='k', linewidth=0.5, alpha=0.3)
        ax.axvline(0, color='k', linewidth=0.5, alpha=0.3)
        ax.set_xlim(-lim, lim)
        ax.set_ylim(-lim, lim)
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.2)
        ax.legend(fontsize=11)
        plt.tight_layout()
        plt.show()
        return
    
    def heading_orienation_centroid_summary(self, scatter_elevation_pitch, scatter_azimuth_roll):

        # --- Elevation vs Pitch ---
        fig, ax = plt.subplots(figsize=(10, 10))

        for d in scatter_elevation_pitch:
            ax.scatter(d['datadriven_pitch'], d['datadriven_elevation'],
                    color='green', s=80, zorder=5,
                    edgecolors='darkgreen', linewidths=1)
            # ax.annotate(
            #             d['session'],
            #             xy=(d['pitch_all'], d['elevation_all']),
            #             xytext=(5, 5),
            #             textcoords='offset points',
            #             fontsize=8,
            #             color='darkgreen')
        lim = 40
        ax.plot([-lim, lim], [-lim, lim],
                color='gray', linestyle='--', linewidth=1.5,
                label='y = x', zorder=3)
        for radius in [10, 20, 30]:
            circle = plt.Circle((0, 0), radius, fill=False, color='gray',
                                linestyle='--', linewidth=0.8, alpha=0.5)
            ax.add_patch(circle)
            ax.annotate(f'{radius}°', xy=(radius, 0), fontsize=7, color='gray')
        ax.scatter([], [], color='green', s=80, edgecolors='darkgreen',
                label='Heading Orientation After')
        ax.set_xlabel("Pitch (degrees)", fontsize=12)
        ax.set_ylabel("Elevation (degrees)", fontsize=12)
        ax.axhline(0, color='k', linewidth=0.5, alpha=0.3)
        ax.axvline(0, color='k', linewidth=0.5, alpha=0.3)
        ax.set_xlim(-lim, lim)
        ax.set_ylim(-lim, lim)
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.2)
        ax.legend(fontsize=11)
        plt.tight_layout()
        plt.show()

        # --- Azimuth vs Roll ---
        fig, ax = plt.subplots(figsize=(10, 10))

        for d in scatter_azimuth_roll:
            ax.scatter(d['datadriven_roll'], d['datadriven_azimuth'],
                    color='red', s=80, zorder=5,
                    edgecolors='darkred', linewidths=1)
            # ax.annotate(
            #             d['session'],
            #             xy=(d['roll_all'], d['azimuth_all']),
            #             xytext=(5, 5),
            #             textcoords='offset points',
            #             fontsize=8,
            #             color='darkred')           
        ax.plot([-lim, lim], [-lim, lim],
                color='gray', linestyle='--', linewidth=1.5,
                label='y = x', zorder=3)

        for radius in [10, 20, 30]:
            circle = plt.Circle((0, 0), radius, fill=False, color='gray',
                                linestyle='--', linewidth=0.8, alpha=0.5)
            ax.add_patch(circle)
            ax.annotate(f'{radius}°', xy=(radius, 0), fontsize=7, color='gray')
        ax.scatter([], [], color='red', s=80, edgecolors='darkred',
                label='Heading Orientation After')
        ax.set_xlabel("Roll (degrees)", fontsize=12)
        ax.set_ylabel("Azimuth (degrees)", fontsize=12)
        ax.axhline(0, color='k', linewidth=0.5, alpha=0.3)
        ax.axvline(0, color='k', linewidth=0.5, alpha=0.3)
        ax.set_xlim(-lim, lim)
        ax.set_ylim(-lim, lim)
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.2)
        ax.legend(fontsize=11)
        plt.tight_layout()
        plt.show()
        return
    
    def plot_histograms(self):

        print("its working")

        bins = 150
        t_start = self.times["calibration"]["pitch_start"]
        t_end = self.times["calibration"]["yaw_end"]
        # Only use the high-linear-velocity interval
        ang_vel = self.calib_odo.ang_vel.sel(time=slice(t_start, t_end))
        vx = ang_vel.sel(cartesian_axis="x")
        vy = ang_vel.sel(cartesian_axis="y")
        vz = ang_vel.sel(cartesian_axis="z")

        # vx = self.calib_odo.lin_vel.sel(cartesian_axis='x').values
        # vy = self.calib_odo.lin_vel.sel(cartesian_axis='y').values
        # vz = self.calib_odo.lin_vel.sel(cartesian_axis='z').values

        def clean_pair(a, b):
            mask = np.isfinite(a) & np.isfinite(b)
            return a[mask], b[mask]

        vx_vy, vy_xy = clean_pair(vx, vy)
        vx_vz, vz_xz = clean_pair(vx, vz)
        vy_vz, vz_yz = clean_pair(vy, vz)

        #lin_vel_vals = self.calib_odo.lin_vel.values
        #finite_vals = lin_vel_vals[np.isfinite(lin_vel_vals)]
        #lim = np.percentile(np.abs(finite_vals), 99)  # symmetric around 0
        #shared_range = [[-lim, lim], [-lim, lim]]
        shared_range = [[-5, 5], [-5, 5]]
        #print(f"Range used: [{-lim:.4f}, {lim:.4f}]")

        fig, axes = plt.subplots(1, 3, figsize=(18, 6))

        h0 = axes[0].hist2d(
            vx_vy, vy_xy,
            bins=bins,
            range=shared_range,
            cmap='viridis',
        )
        axes[0].set_title("Ang Velocity X vs Y")
        axes[0].set_xlabel("Velocity X")
        axes[0].set_ylabel("Velocity Y")
        plt.colorbar(h0[3], ax=axes[0], label='Counts (log)')

        h1 = axes[1].hist2d(
            vx_vz, vz_xz,
            bins=bins,
            range=shared_range,
            cmap='viridis',
        )
        axes[1].set_title("Ang Velocity X vs Z")
        axes[1].set_xlabel("Velocity X")
        axes[1].set_ylabel("Velocity Z")
        plt.colorbar(h1[3], ax=axes[1], label='Counts (log)')

        h2 = axes[2].hist2d(
            vy_vz, vz_yz,
            bins=bins,
            range=shared_range,
            cmap='viridis',
        )
        axes[2].set_title("Ang Velocity Y vs Z")
        axes[2].set_xlabel("Velocity Y")
        axes[2].set_ylabel("Velocity Z")
        plt.colorbar(h2[3], ax=axes[2], label='Counts (log)')

        plt.tight_layout()
        plt.show()

        return

    def plot_velocity_directions(self, n_directions=24, head_radius=0.10, min_ang_speed=0.005):
        from matplotlib.patches import Circle, Polygon
        t_start = self.times["calibration"]["pitch_start"]
        t_end = self.times["calibration"]["yaw_end"]
        ang_vel = self.calib_odo.ang_vel.sel(time=slice(t_start, t_end))
        vx = ang_vel.sel(cartesian_axis="x")
        #y = ang_vel.sel(cartesian_axis="y")
        vz = ang_vel.sel(cartesian_axis="z")
        # Remove NaN / inf
        mask = np.isfinite(vx) & np.isfinite(vz)
        vx = vx[mask]
        vz = vz[mask]
        ang_speed = np.sqrt(vx**2 + vz**2)
        moving = ang_speed > min_ang_speed
        vx = vx[moving]
        vz = vz[moving]
        angles = -np.arctan2(vz, vx)
        bin_edges = np.linspace(-np.pi, np.pi, n_directions + 1)
        counts, _ = np.histogram(angles, bins=bin_edges)
        percentages = 100 * counts / counts.sum()
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

        # Circular mean direction (preferred heading)
        mean_x = np.mean(np.cos(angles))
        mean_z = np.mean(np.sin(angles))
        preferred_angle = np.arctan2(mean_z, mean_x)
        preferred_angle_deg = np.degrees(preferred_angle)
        concentration = np.sqrt(mean_x**2 + mean_z**2)

        print(f"Preferred angular-velocity direction (high velocity window): {preferred_angle_deg:.1f} degrees")
        print(f"Directional concentration: {concentration:.3f}")
        print(f"N samples: {vx.size}")

        fig, ax = plt.subplots(figsize=(9, 9))

        head = Circle((0, 0), head_radius, facecolor='lightgray', edgecolor='black', linewidth=2, zorder=2)
        ax.add_patch(head)
        nose = Polygon(
            [(0.075, 0.025), (0.15, 0.000), (0.075, -0.025)],
            closed=True, facecolor='lightgray', edgecolor='black', linewidth=2, zorder=3
        )
        ax.add_patch(nose)

        max_length = 0.09
        if percentages.max() > 0:
            arrow_lengths = (percentages / percentages.max()) * max_length
        else:
            arrow_lengths = np.zeros_like(percentages)

        x_start = np.zeros(n_directions)
        z_start = np.zeros(n_directions)
        dx = arrow_lengths * np.cos(bin_centers)
        dz = arrow_lengths * np.sin(bin_centers)

        ax.quiver(x_start, z_start, dx, dz, angles='xy', scale_units='xy', scale=1,
                color='red', alpha=0.75, width=0.006, zorder=4)

        preferred_length = 0.1
        pdx = preferred_length * np.cos(preferred_angle)
        pdz = preferred_length * np.sin(preferred_angle)
        ax.quiver(0, 0, pdx, pdz, angles='xy', scale_units='xy', scale=1,
                color='black', width=0.012, headwidth=5, headlength=7, zorder=5)

        ax.axhline(0, color='black', linewidth=0.7, alpha=0.3)
        ax.axvline(0, color='black', linewidth=0.7, alpha=0.3)  # was axhline twice in original — fixed
        ax.scatter(0, 0, color='black', s=25, zorder=6)

        # ax.text(0.205, 0.005, '+X', color='red', fontsize=12)
        # ax.text(0.005, 0.205, '+Z', color='blue', fontsize=12)
        ax.text(
            -0.19, -0.19,
            f'Preferred direction: {preferred_angle_deg:.1f}°\n',
            fontsize=11,
            bbox=dict(facecolor='white', alpha=0.8)
        )
        ax.set_xlim(-0.20, 0.20)
        ax.set_ylim(-0.20, 0.20)
        ax.set_aspect('equal')
        ax.set_xlabel('X')
        ax.set_ylabel('Z')
        ax.set_title('Angular Velocity Heading — XZ Plane (high linear-velocity window)')
        ax.grid(True, alpha=0.2)
        plt.tight_layout()
        plt.show()    

    def quat_to_euler(self,quaternions):
        """
        Convert quaternions to Euler angles.
        
        Roll (φ) = atan2(2(w x + y z), 1 - 2(x^2 + y^2))
        Pitch (θ) = asin(2(w y - z x))
        Yaw (ψ) = atan2(2(w z + x y), 1 - 2(y^2 + z^2))

        our setup returns data like this [yaw,pitch,roll]
        """
        q_w, q_x, q_y, q_z = quaternions[:, 0], quaternions[:, 1], quaternions[:, 2], quaternions[:, 3]
        #Roll
        roll = np.degrees(np.arctan2(2 * (q_w * q_x + q_y * q_z), 1 - 2 * (q_x**2 + q_y**2)))
        #Pitch
        pitch = np.degrees(np.arcsin(2 * (q_w * q_y - q_z * q_x)))
        #Yaw
        yaw = np.degrees(np.arctan2(2 * (q_w * q_z + q_x * q_y), 1 - 2 * (q_y**2 + q_z**2)))

        return np.column_stack((yaw, roll, pitch)) #roll, pitch, yaw
    

    def plot_calibration_effect(self):
        
        print("PLOTTING REAL CALIBRATION EFFECT")
      
        
        # Step 1: Validate times
        if not hasattr(self, 'times'):
            print(" ERROR: Calibration times not set.")
            return
        
        pitch_start = self.times["calibration"]["pitch_start"]
        pitch_end = self.times["calibration"]["pitch_end"]
        
        print(f"\nPitch calibration segment:")
        print(f"  Start: {pitch_start}")
        print(f"  End:   {pitch_end}")
        
        # Step 2: Transform before calibration
        try:
            omega_before = rbm.transform_vectors(
                self.odometry.angular_velocity, 
                outof="t265_world", 
                into="t265_vestibular"
            )
            print(f"Transform successful, shape: {omega_before.shape}")
        except Exception as e:
            print(f"   ERROR: {e}")
            return
        
        # Step 3: Selecting pitch segment   
        try:
            omega_pitch_before = omega_before.sel(time=slice(pitch_start, pitch_end))
            print(f"   Selected {len(omega_pitch_before)} samples")
            if len(omega_pitch_before) == 0:
                print(f"    WARNING: No samples in this time range!")
                print(f"     Data range: {omega_before.time.values[0]} to {omega_before.time.values[-1]}")
                print(f"     Requested: {pitch_start} to {pitch_end}")
                return
        except Exception as e:
            print(f"   ERROR: {e}")
            return
        
        # Step 4: Transform after calibration
        print(f"\nTransforming to t265_calib (AFTER)...")
        try:
            omega_after = rbm.transform_vectors(
                self.odometry.angular_velocity, 
                outof="t265_world", 
                into="t265_calib"
            )
            print(f"   Transform successful, shape: {omega_after.shape}")
        except Exception as e:
            print(f"   ERROR: {e}")
            return
        
        # Step 5: Select pitch segment
        print(f"\nSelecting pitch segment from after data...")
        try:
            omega_pitch_after = omega_after.sel(time=slice(pitch_start, pitch_end))
            print(f"   Selected {len(omega_pitch_after)} samples")
        except Exception as e:
            print(f"   ERROR: {e}")
            return
        
        # Step 6: Extract values and check for NaN
        print(f"\nExtracting data values...")
        omega_pitch_before_vals = omega_pitch_before.values
        omega_pitch_after_vals = omega_pitch_after.values
        
        #Swati Commented out 
        # print(f"  Before - Contains NaN: {np.isnan(omega_pitch_before_vals).any()}")
        # print(f"  Before - Contains Inf: {np.isinf(omega_pitch_before_vals).any()}")
        # print(f"  After  - Contains NaN: {np.isnan(omega_pitch_after_vals).any()}")
        # print(f"  After  - Contains Inf: {np.isinf(omega_pitch_after_vals).any()}")
        
        if np.isnan(omega_pitch_before_vals).any() or np.isnan(omega_pitch_after_vals).any():
            print(f"\n  WARNING: NaN values detected in data!")
            print(f"   This might be due to frame transformation issues.")
            print(f"   Attempting to proceed anyway...")
        
        # Create comparison plot
        fig, ((ax1, ax2), (ax3,ax4)) = plt.subplots(2, 2, figsize=(12, 8))
        
        # ===== BEFORE CALIBRATION =====
        # Remove NaN values for plotting
        #yaw v/s pitch
        mask_before = ~np.isnan(omega_pitch_before_vals[:, 0]) & ~np.isnan(omega_pitch_before_vals[:, 1])
        
        ax1.scatter(omega_pitch_before_vals[mask_before, 0], 
                omega_pitch_before_vals[mask_before, 1], 
                color='blue', alpha=0.5, s=10)
        ax1.scatter(np.nanmean(omega_pitch_before_vals[:, 0]), 
                np.nanmean(omega_pitch_before_vals[:, 1]), 
                color='darkblue', s=200, marker='o', edgecolors='black', linewidths=2,
                label='Mean')
        ax1.axhline(y=0, color='k', linestyle='--', linewidth=1)
        ax1.axvline(x=0, color='k', linestyle='--', linewidth=1)
        ax1.set_xlabel('X-axis Angular Velocity (rad/s)', fontsize=11, fontweight='bold')
        ax1.set_ylabel('Y-axis Angular Velocity (rad/s)', fontsize=11, fontweight='bold')
        ax1.set_title('BEFORE Calibration (t265_vestibular)\nYaw v/s Pitch Movement', 
                    fontsize=12, fontweight='bold', color='blue')
        ax1.grid(True, alpha=0.3)
        ax1.legend()

        #yaw v/s roll
        mask_before = ~np.isnan(omega_pitch_before_vals[:, 2]) & ~np.isnan(omega_pitch_before_vals[:, 0])

        ax2.scatter(omega_pitch_before_vals[mask_before, 2], 
                omega_pitch_before_vals[mask_before, 0], 
                color='blue', alpha=0.5, s=10)
        ax2.scatter(np.nanmean(omega_pitch_before_vals[:, 2]), 
                np.nanmean(omega_pitch_before_vals[:, 0]), 
                color='darkblue', s=200, marker='o', edgecolors='black', linewidths=2,
                label='Mean')
        ax2.axhline(y=0, color='k', linestyle='--', linewidth=1)
        ax2.axvline(x=0, color='k', linestyle='--', linewidth=1)
        ax2.set_xlabel('X-axis Angular Velocity (rad/s)', fontsize=11, fontweight='bold')
        ax2.set_ylabel('Z-axis Angular Velocity (rad/s)', fontsize=11, fontweight='bold')
        ax2.set_title('BEFORE Calibration (t265_vestibular)\nRoll v/s Pitch Movement', 
                    fontsize=12, fontweight='bold', color='blue')
        ax2.grid(True, alpha=0.3)
        ax2.legend()
        
        # ===== AFTER CALIBRATION =====
        #yaw v/s pitch
        mask_after = ~np.isnan(omega_pitch_after_vals[:, 0]) & ~np.isnan(omega_pitch_after_vals[:, 1])
        
        ax3.scatter(omega_pitch_after_vals[mask_after, 0], 
                omega_pitch_after_vals[mask_after, 1], 
                color='green', alpha=0.5, s=10)
        ax3.scatter(np.nanmean(omega_pitch_after_vals[:, 0]), 
                np.nanmean(omega_pitch_after_vals[:, 1]), 
                color='darkgreen', s=200, marker='o', edgecolors='black', linewidths=2,
                label='Mean')
        ax3.axhline(y=0, color='k', linestyle='--', linewidth=1)
        ax3.axvline(x=0, color='k', linestyle='--', linewidth=1)
        ax3.set_xlabel('X-axis Angular Velocity (rad/s)', fontsize=11, fontweight='bold')
        ax3.set_ylabel('Y-axis Angular Velocity (rad/s)', fontsize=11, fontweight='bold')
        ax3.set_title('AFTER Calibration (t265_calib)\nYaw v/s Pitch Movement', 
                    fontsize=12, fontweight='bold', color='green')
        ax3.grid(True, alpha=0.3)
        ax3.legend()
        
        # Make axes equal
        # lim = 1.5
        # ax1.set_xlim(-lim, lim)
        # ax1.set_ylim(-lim, lim)
        # ax2.set_xlim(-lim, lim)
        # ax2.set_ylim(-lim, lim)

        #yaw v/s roll
        mask_after = ~np.isnan(omega_pitch_after_vals[:, 2]) & ~np.isnan(omega_pitch_after_vals[:, 0])
        
        ax4.scatter(omega_pitch_after_vals[mask_after, 2], 
                omega_pitch_after_vals[mask_after, 0], 
                color='green', alpha=0.5, s=10)
        ax4.scatter(np.nanmean(omega_pitch_after_vals[:, 2]), 
                np.nanmean(omega_pitch_after_vals[:, 0]), 
                color='darkgreen', s=200, marker='o', edgecolors='black', linewidths=2,
                label='Mean')
        ax4.axhline(y=0, color='k', linestyle='--', linewidth=1)
        ax4.axvline(x=0, color='k', linestyle='--', linewidth=1)
        ax4.set_xlabel('X-axis Angular Velocity (rad/s)', fontsize=11, fontweight='bold')

        ax4.set_ylabel('Z-axis Angular Velocity (rad/s)', fontsize=11, fontweight='bold')
        ax4.set_title('AFTER Calibration (t265_calib)\nRoll v/s pitch Movement', 
                    fontsize=12, fontweight='bold', color='green')
        ax4.grid(True, alpha=0.3)
        ax4.legend()
        
        # Make axes equal
        lim = 3
        ax1.set_xlim(-lim, lim)
        ax1.set_ylim(-lim, lim)
        ax2.set_xlim(-lim, lim)
        ax2.set_ylim(-lim, lim)
        ax3.set_xlim(-lim, lim)
        ax3.set_ylim(-lim, lim)
        ax4.set_xlim(-lim, lim)
        ax4.set_ylim(-lim, lim)
        
        plt.suptitle('Calibration Effect: Pure Pitch Movement Should Align with Y-Axis', 
                    fontsize=13, fontweight='bold')
        plt.tight_layout()
        plt.show()
        
        # Print analysis
        print("\nDuring PURE PITCH movement (head nodding):")
        print(f"  X-axis rotation (should be ~0):")
        print(f"    Before: mean={np.nanmean(omega_pitch_before_vals[:, 0]):.4f} rad/s, "
            f"std={np.nanstd(omega_pitch_before_vals[:, 0]):.4f}")
        print(f"    After:  mean={np.nanmean(omega_pitch_after_vals[:, 0]):.4f} rad/s, "
            f"std={np.nanstd(omega_pitch_after_vals[:, 0]):.4f}")
        
        print(f"\n  Y-axis rotation (this is the actual pitch):")
        print(f"    Before: mean={np.nanmean(omega_pitch_before_vals[:, 1]):.4f} rad/s, "
            f"std={np.nanstd(omega_pitch_before_vals[:, 1]):.4f}")
        print(f"    After:  mean={np.nanmean(omega_pitch_after_vals[:, 1]):.4f} rad/s, "
            f"std={np.nanstd(omega_pitch_after_vals[:, 1]):.4f}")
        
        print(f"\n  Z-axis rotation (should be ~0):")
        print(f"    Before: mean={np.nanmean(omega_pitch_before_vals[:, 2]):.4f} rad/s, "
            f"std={np.nanstd(omega_pitch_before_vals[:, 2]):.4f}")
        print(f"    After:  mean={np.nanmean(omega_pitch_after_vals[:, 2]):.4f} rad/s, "
            f"std={np.nanstd(omega_pitch_after_vals[:, 2]):.4f} ")
       

    def plot(self):

        print(type(self.odometry.orientation.time[0].values))
        print(self.odometry.orientation.time[0].values)
        print(self.odometry.orientation.time[-1].values)
        print(self.odometry.time.values[0], self.odometry.time.values[-1])
        print(self.calib_odo.time.values[0], self.calib_odo.time.values[-1])
        print(len(self.odometry.time), len(self.calib_odo.time))
        fig = go.Figure()
        fig.add_trace(go.Scatter(

            x=self.odometry.time.values,
            y=self.odometry.angular_velocity[:, 0],
            name="uncalibrated pitch"       # this sets its legend entry
            ))
        fig.add_trace(go.Scatter(
            x=self.odometry.time.values,
            y=self.odometry.angular_velocity[:, 1],
            name="uncalibrated yaw"       # this sets its legend entry
            ))
        fig.add_trace(go.Scatter(
            x=self.odometry.time.values,
            y=self.odometry.angular_velocity[:, 2],
            name="uncalibrated roll"       # this sets its legend entry
            ))
        fig.add_trace(go.Scatter(
            x=self.odometry.time.values,
            y=self.calib_odo.ang_vel[:, 1],
            name="calibrated pitch"       # this sets its legend entry
            ))
        fig.add_trace(go.Scatter(
            x=self.odometry.time.values,
            y=self.calib_odo.ang_vel[:, 2],
            name="calibrated yaw"       # this sets its legend entry
            ))
        fig.add_trace(go.Scatter(
            x=self.odometry.time.values,
            y=self.calib_odo.ang_vel[:, 0],
            name="calibrated roll"       # this sets its legend entry
            ))
        fig.update_layout(
            title="Angular velocity odometry",
            xaxis_title="Time stamps (datetime)",
            yaxis_title="Angular Velocity (radians/second)",
            width=1200,
            height=600
            )
        
        fig.update_layout(
            title="Angular velocity odometry",
            xaxis=dict(
                title="Time (seconds)",
                title_font=dict(size=22),   # axis label size
                tickfont=dict(size=18)      # tick (timestamp) size
            ),
            yaxis=dict(
                title="Angular Velocity (radians/second)",
                title_font=dict(size=22),
                tickfont=dict(size=18)
            ),
            width=1000,
            height=500
        )
        fig.show()
        # fig, ax = plt.subplots(figsize=(20,8))
        # ax.plot(self.odometry.time.values,self.odometry.angular_velocity[:, 0],label='uncalibrated pitch velocity')
        # ax.plot(self.odometry.time.values,self.odometry.angular_velocity[:, 1],label='uncalibrated yaw velocity')
        # ax.plot(self.odometry.time.values,self.calib_odo.ang_vel[:, 1],label='calibrated pitch velocity')
        # ax.plot(self.odometry.time.values,self.calib_odo.ang_vel[:, 2],label='calibrated yaw velocity')
        # plt.legend()
        # plt.ylabel('Angular velocity (rad/s)')
        # plt.xlabel('Time')
        # plt.show()

    def plot_heading(self):

        
        # fig = go.Figure()
        # fig.add_trace(go.Scatter(

        #     x=self.odometry.time.values,
        #     y=self.odometry.linear_velocity[:, 0],
        #     name="uncalibrated x"       # this sets its legend entry
        #     ))
        # fig.add_trace(go.Scatter(
        #     x=self.odometry.time.values,
        #     y=self.odometry.linear_velocity[:, 1],
        #     name="uncalibrated y"       # this sets its legend entry
        #     ))
        # fig.add_trace(go.Scatter(
        #     x=self.odometry.time.values,
        #     y=self.odometry.linear_velocity[:, 2],
        #     name="uncalibrated z"       # this sets its legend entry
        #     ))
        # fig.add_trace(go.Scatter(
        #     x=self.odometry.time.values,
        #     y=self.calib_odo.lin_vel[:, 1],
        #     name="calibrated x"       # this sets its legend entry
        #     ))
        # fig.add_trace(go.Scatter(
        #     x=self.odometry.time.values,
        #     y=self.calib_odo.lin_vel[:, 2],
        #     name="calibrated y"       # this sets its legend entry
        #     ))
        # fig.add_trace(go.Scatter(
        #     x=self.odometry.time.values,
        #     y=self.calib_odo.lin_vel[:, 0],
        #     name="calibrated z"       # this sets its legend entry
        #    ))
        # fig.add_trace(go.Scatter(
        #     x=self.odometry.time.values,
        #     y=(self.heading_azimuth_after)/90,
        #     name="calibrated azimuth"       # this sets its legend entry
        #     ))
        # fig.add_trace(go.Scatter(
        #     x=self.odometry.time.values,
        #     y=self.heading_elevation_after,
        #     name="calibrated elevation"       # this sets its legend entry
        #     ))
        # fig.add_trace(go.Scatter(
        #     x=self.odometry.time.values,
        #     y=self.calib_odo.ang_vel[:, 2],
        #     name="calibrated yaw"       # this sets its legend entry
        #     ))
        
        # lin_vel_mag = np.linalg.norm(self.calib_odo.lin_vel, axis=1)
        # avg_lin_vel = np.mean(lin_vel_mag)
        # print(f"linear_velocity: {avg_lin_vel}")

        # # fig.update_layout(
        # #     title="Linear velocity odometry",
        # #     xaxis_title="Time stamps (datetime)",
        # #     yaxis_title="Heading (radians/second)",
        # #     width=1200,
        # #     height=600
        # #     )
        
        # fig.update_layout(
        #     title="Linear velocity odometry",
        #     xaxis=dict(
        #         title="Time (seconds)",
        #         title_font=dict(size=22),   # axis label size
        #         tickfont=dict(size=18)      # tick (timestamp) size
        #     ),
        #     yaxis=dict(
        #         title="Angular Velocity (radians/second)",
        #         title_font=dict(size=22),
        #         tickfont=dict(size=18)
        #     ),
        #     width=1000,
        #     height=500
        # )
        # fig.show()

        #Swati: 2D histograms..
        #Swati Commented out 
        bins = 150

        # azimuth_min = min(self.heading_azimuth_before.min(), self.heading_azimuth_after.min())
        # azimuth_max = max(self.heading_azimuth_before.max(), self.heading_azimuth_after.max())

        # elevation_min = min(self.heading_elevation_before.min(), self.heading_elevation_after.min())
        # elevation_max = max(self.heading_elevation_before.max(), self.heading_elevation_after.max())

        fig, axes = plt.subplots(1, 2, figsize=(14, 6), sharex=True, sharey=True)
        h0 = axes[0].hist2d(
        self.head_roll_before,
        self.head_pitch_before,
        bins=bins,
        range=[[-60, 60], [-60, 60]],
        cmap="viridis"
        )
        
        axes[0].set_title("Orientation Before")
        axes[0].set_xlabel("Pitch (deg)")
        axes[0].set_ylabel("Roll (deg)")
        
        plt.colorbar(h0[3], ax=axes[0])


        h1 = axes[1].hist2d(
        self.head_roll_kinematic,
        self.head_pitch_kinematic,
        bins=bins,
        range=[[-60, 60], [-60, 60]],
        cmap="viridis"
        )
        
        axes[1].set_title(" Orientation After")
        axes[1].set_xlabel("Pitch (deg)")
        axes[1].set_ylabel("Roll (deg)")
        
        plt.colorbar(h1[3], ax=axes[1])

        plt.tight_layout()
        plt.show()

    
    def plot_heading_summary(self, hist_heading_after, azimuth_edges, elevation_edges):

        import matplotlib.cm as cm
        import matplotlib.colors as mcolors
        from scipy.stats import gaussian_kde

         # # --- 2D Histograms ---
        # roll_centers  = (roll_edges[:-1] + roll_edges[1:]) / 2
        # pitch_centers = (pitch_edges[:-1] + pitch_edges[1:]) / 2

        #fig, axes = plt.subplots(1, 1, figsize=(14, 14), sharex=True, sharey=True)

        # im0 = axes[0].imshow(hist_heading_before.T, origin='lower', aspect='auto',
        #              extent=[azimuth_edges[0], azimuth_edges[-1], elevation_edges[0], elevation_edges[-1]],
        #              cmap='viridis')
        # axes[0].set_title("Uncalibrated heading (All Sessions)")
        # axes[0].set_xlabel("Azimuth (deg)")
        # axes[0].set_ylabel("Elevation (deg)")
        # plt.colorbar(im0, ax=axes[0])

        fig, ax = plt.subplots(figsize=(14, 14))

        vmax = np.max(hist_heading_after)
        print("vmax:", vmax)

        im = ax.imshow(
            hist_heading_after.T,
            origin='lower',
            aspect='auto',
            extent=[azimuth_edges[0], azimuth_edges[-1],
                    elevation_edges[0], elevation_edges[-1]],
            cmap='viridis'
        )

        ax.set_title("Heading (All Sessions)", fontsize=24, fontweight='bold')
        ax.set_xlabel("Azimuth (deg)", fontsize=20, fontweight='bold')
        ax.set_ylabel("Elevation (deg)", fontsize=20, fontweight='bold')
        ax.tick_params(axis='both', labelsize=15)

        fig.savefig(
         "all_velocity_histogram.png",
         dpi=300,
         bbox_inches="tight"
        )

        plt.colorbar(im, ax=ax)

        plt.tight_layout()
        plt.show()

    def plot_rotation_heading_summary(self, hist_rotation_heading_after, azimuth_edges, elevation_edges):

        fig, ax = plt.subplots(figsize=(10, 8))

        im = ax.imshow(
            hist_rotation_heading_after.T,
            origin='lower',
            aspect='auto',
            extent=[azimuth_edges[0], azimuth_edges[-1],
                    elevation_edges[0], elevation_edges[-1]],
            cmap='viridis'
        )

        ax.set_title("Rotation Heading (All Sessions)", fontsize=14, fontweight='bold')
        ax.set_xlabel("Azimuth (deg)", fontsize=10, fontweight='bold')
        ax.set_ylabel("Elevation (deg)", fontsize=10, fontweight='bold')
        ax.tick_params(axis='both', labelsize=15)

        plt.colorbar(im, ax=ax)
        plt.tight_layout()
        plt.show()

    def plot_heading_orientation(self,scatter_heading):
        
        import matplotlib.cm as cm
        import matplotlib.colors as mcolors 
        colors = cm.tab10(np.linspace(0, 1, len(scatter_heading)))
        # --- Scatter plot for before and after ---
        fig, ax = plt.subplots(figsize=(10, 10))
        for d, color in zip(scatter_heading, colors):
            ax.plot([d['head_azimuth'], d['head_roll']],
                    [d['head_elevation'], d['head_pitch']],
                    color=color, linewidth=1.5, alpha=0.7)
            ax.scatter(d['head_azimuth'], d['head_elevation'],
                    color='green', s=80, zorder=5, edgecolors='darkgreen', linewidths=1)
            ax.scatter(d['head_roll'], d['head_pitch'],
                    color='red', s=80, zorder=5, edgecolors='darkred', linewidths=1)
            ax.annotate(f"{d['ises']}", xy=(d['head_roll'], d['head_pitch']),
                        xytext=(3, 3), textcoords='offset points', fontsize=8, color=color)

        ax.scatter(0, 0, marker='x', color='black', s=200, linewidths=3, zorder=6, label='Origin (0,0)')
        for radius in [10, 20, 30]:
            circle = plt.Circle((0, 0), radius, fill=False, color='gray',
                                linestyle='--', linewidth=0.8, alpha=0.5)
            ax.add_patch(circle)
            ax.annotate(f'{radius}°', xy=(radius, 0), fontsize=7, color='gray')

        ax.scatter([], [], color='green', s=80, edgecolors='darkgreen', label='Heading Calibration')
        ax.scatter([], [], color='red',   s=80, edgecolors='darkred',   label='Orienation Calibration')
        ax.set_xlabel("Azimuth/Roll (degrees)", fontsize=12)
        ax.set_ylabel("Elevation/Pitch (degrees)", fontsize=12)
        ax.set_title("Calibration Effect Across Sessions\nGreen=Before, Red=After, X=Centroid", fontsize=13)
        ax.axhline(0, color='k', linewidth=0.5, alpha=0.3)
        ax.axvline(0, color='k', linewidth=0.5, alpha=0.3)
        ax.set_xlim(-40, 40)
        ax.set_ylim(-40, 40)
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.2)
        plt.tight_layout()
        plt.show()
        plt.close(fig)

    def plot_calibration_summary_new(self, scatter_data, scatter_gravity, hist_vest, hist_kin, hist_world, roll_edges, pitch_edges):

        import matplotlib.cm as cm
        import matplotlib.colors as mcolors
        from scipy.stats import gaussian_kde

        
        colors = cm.tab10(np.linspace(0, 1, len(scatter_data)))

        # --- Scatter plot for before and after ---
        fig, ax = plt.subplots(figsize=(10, 10))
        for d, color in zip(scatter_data, colors):
            ax.plot([d['before_roll'], d['after_roll']],
                    [d['before_pitch'], d['after_pitch']],
                    color=color, linewidth=1.5, alpha=0.7)
            ax.scatter(d['before_roll'], d['before_pitch'],
                    color='green', s=80, zorder=5, edgecolors='darkgreen', linewidths=1)
            ax.scatter(d['after_roll'], d['after_pitch'],
                    color='red', s=80, zorder=5, edgecolors='darkred', linewidths=1)
            ax.annotate(f"{d['ises']}", xy=(d['after_roll'], d['after_pitch']),
                        xytext=(3, 3), textcoords='offset points', fontsize=8, color=color)

        ax.scatter(0, 0, marker='x', color='black', s=200, linewidths=3, zorder=6, label='Origin (0,0)')
        for radius in [10, 20, 30]:
            circle = plt.Circle((0, 0), radius, fill=False, color='gray',
                                linestyle='--', linewidth=0.8, alpha=0.5)
            ax.add_patch(circle)
            ax.annotate(f'{radius}°', xy=(radius, 0), fontsize=7, color='gray')

        ax.scatter([], [], color='green', s=80, edgecolors='darkgreen', label='Before Calibration')
        ax.scatter([], [], color='red',   s=80, edgecolors='darkred',   label='After Calibration')
        ax.set_xlabel("Roll (degrees)", fontsize=12)
        ax.set_ylabel("Pitch (degrees)", fontsize=12)
        ax.set_title("Calibration Effect Across Sessions\nGreen=Before, Red=After, X=Gravity Centroid", fontsize=13)
        ax.axhline(0, color='k', linewidth=0.5, alpha=0.3)
        ax.axvline(0, color='k', linewidth=0.5, alpha=0.3)
        ax.set_xlim(-40, 40)
        ax.set_ylim(-40, 40)
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.2)
        plt.tight_layout()
        plt.show()

        # --- Scatter plot for after and gravity ---
        fig, ax = plt.subplots(figsize=(10, 10))
        for i, color in zip(scatter_gravity, colors):
            ax.plot([i['after_roll'], i['gravity_roll']],
                    [i['after_pitch'], i['gravity_pitch']],
                    color=color, linewidth=1.5, alpha=0.7)
            ax.scatter(i['after_roll'], i['after_pitch'],
                    color='red', s=80, zorder=5, edgecolors='darkred', linewidths=1)
            ax.scatter(i['gravity_roll'], i['gravity_pitch'],
                    color='blue', s=80, zorder=5, edgecolors='darkblue', linewidths=1)
            ax.annotate(f"{i['ises']}", xy=(i['gravity_roll'], i['gravity_pitch']),
                        xytext=(3, 3), textcoords='offset points', fontsize=8, color=color)

        ax.scatter(0, 0, marker='x', color='black', s=200, linewidths=3, zorder=6, label='Origin (0,0)')
        for radius in [10, 20, 30]:
            circle = plt.Circle((0, 0), radius, fill=False, color='gray',
                                linestyle='--', linewidth=0.8, alpha=0.5)
            ax.add_patch(circle)
            ax.annotate(f'{radius}°', xy=(radius, 0), fontsize=7, color='gray')

        ax.scatter([], [], color='red', s=80, edgecolors='darkred', label='After Calibration')
        ax.scatter([], [], color='blue',   s=80, edgecolors='darkblue',   label='Gravity')
        ax.set_xlabel("Roll (degrees)", fontsize=12)
        ax.set_ylabel("Pitch (degrees)", fontsize=12)
        ax.set_title("Calibration Effect Across Sessions After Gravity\n Red=After, Blue=Gravity, X=Gravity Centroid", fontsize=13)
        ax.axhline(0, color='k', linewidth=0.5, alpha=0.3)
        ax.axvline(0, color='k', linewidth=0.5, alpha=0.3)
        ax.set_xlim(-40, 40)
        ax.set_ylim(-40, 40)
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.2)
        plt.tight_layout()
        plt.show()

        # # --- 2D Histograms ---
        # roll_centers  = (roll_edges[:-1] + roll_edges[1:]) / 2
        # pitch_centers = (pitch_edges[:-1] + pitch_edges[1:]) / 2

        fig, axes = plt.subplots(1, 3, figsize=(14, 6), sharex=True, sharey=True)

        im0 = axes[0].imshow(hist_vest.T, origin='lower', aspect='auto',
                     extent=[roll_edges[0], roll_edges[-1], pitch_edges[0], pitch_edges[-1]],
                     cmap='viridis')
        axes[0].set_title("Uncalibrated Frame (All Sessions)")
        axes[0].set_xlabel("Roll (deg)")
        axes[0].set_ylabel("Pitch (deg)")
        plt.colorbar(im0, ax=axes[0])


        im1 = axes[1].imshow(hist_kin.T, origin='lower', aspect='auto',
                     extent=[roll_edges[0], roll_edges[-1], pitch_edges[0], pitch_edges[-1]],
                     cmap='viridis')
        axes[1].set_title("Calibrated Kinematic Frame (All Sessions)")
        axes[1].set_xlabel("Roll (deg)")
        axes[1].set_ylabel("Pitch (deg)")
        plt.colorbar(im1, ax=axes[1])

        im2 = axes[2].imshow(hist_world.T, origin='lower', aspect='auto',
                            extent=[roll_edges[0], roll_edges[-1], pitch_edges[0], pitch_edges[-1]],
                            cmap='viridis')
        axes[2].set_title("Gravity Frame (All Sessions)")
        axes[2].set_xlabel("Roll (deg)")
        axes[2].set_ylabel("Pitch (deg)")
        plt.colorbar(im2, ax=axes[2])

        plt.tight_layout()
        plt.show()

    def get_head_orientation(self):
        return self.head_roll_world, self.head_pitch_world
    
    def get_rbm(self):
        return rbm

    def get_heading(self):
        return self.heading_azimuth, self.heading_elevation
        
    def get_accel(self):
        return self.accel
    
    def get_odometry(self):
        return self.odometry

    def get_calibrated_odo(self):
        return self.calib_odo_
